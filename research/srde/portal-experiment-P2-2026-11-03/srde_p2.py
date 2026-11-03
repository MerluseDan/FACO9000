#!/usr/bin/env python3
"""SRDE-P2. Retrospective, pre-registered, time-ordered CO2 event forecasts.

Usage:
    python srde_p2.py --stage validate --output-dir ./results
    python srde_p2.py --stage evaluate --output-dir ./results

The validate stage does not inspect or compute test labels or test metrics.
The evaluate stage uses frozen selected configs and never tunes to test.
"""
from __future__ import annotations
import argparse, hashlib, json, math, platform, time, warnings
from dataclasses import dataclass
from pathlib import Path
import numpy as np
import pandas as pd
import sklearn
import statsmodels
from statsmodels.datasets import co2
from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.metrics import brier_score_loss, log_loss, roc_auc_score, accuracy_score

SEED=20261103
HORIZON=4
LAGS=(1,4,8,13,26,52)
COLS=['year_sin','year_cos']+[f'diff_{i}' for i in LAGS]
COORD_COLS=(0,1,3)  # year sine, cosine, four-week recent change


def sha_bytes(b): return hashlib.sha256(b).hexdigest()

def gini(y):
    p=float(np.mean(y))
    return 2*p*(1-p)


def make_rows(raw):
    """No missing data imputation. target index i+4; features only <= i."""
    vals=raw['co2'].to_numpy(dtype=float)
    dates=pd.DatetimeIndex(raw.index)
    rec=[]
    for i in range(max(LAGS),len(vals)-HORIZON):
        past=[i-k for k in (0,*LAGS)]
        if not np.isfinite(vals[past]).all() or not np.isfinite(vals[i+HORIZON]):
            continue
        d=dates[i]
        phase=2*math.pi*(d.dayofyear-1)/365.25
        row={'issue_date':d.strftime('%Y-%m-%d'), 'target_date':dates[i+HORIZON].strftime('%Y-%m-%d'),
             'co2_at_issue':float(vals[i]),'co2_at_target':float(vals[i+HORIZON]),
             'year_sin':math.sin(phase),'year_cos':math.cos(phase),
             'target':int(vals[i+HORIZON]>vals[i])}
        for lag in LAGS:row[f'diff_{lag}']=float(vals[i]-vals[i-lag])
        rec.append(row)
    return pd.DataFrame.from_records(rec)


def split_rows(df):
    issues=pd.to_datetime(df.issue_date)
    ends=pd.to_datetime(df.target_date)
    train=df.loc[(issues < '1989-01-01')&(ends <= '1988-12-31')].copy()
    val=df.loc[(issues >= '1989-01-01')&(issues < '1995-01-01')&(ends <= '1994-12-31')].copy()
    test=df.loc[(issues >= '1995-01-01')&(issues < '2002-01-01')&(ends <= '2001-12-31')].copy()
    assert len(train)>700 and len(val)>250 and len(test)>250
    assert (pd.to_datetime(train.target_date) <= pd.Timestamp('1988-12-31')).all()
    assert (pd.to_datetime(val.target_date) <= pd.Timestamp('1994-12-31')).all()
    assert (pd.to_datetime(test.issue_date) >= pd.Timestamp('1995-01-01')).all()
    assert df.issue_date.is_unique
    assert (pd.to_datetime(df.target_date)>pd.to_datetime(df.issue_date)).all()
    return train,val,test


class PortalTree(BaseEstimator,ClassifierMixin):
    """Geometrically gated local-logistic model tree.

    This is a conventional probabilistic model tree implementing one *portal*
    hypothesis. Children are correlated, not independent voting witnesses.
    All split thresholds and models learned exclusively on fitting data.
    """
    def __init__(self,max_depth=6,alpha=0.35,min_leaf=100,min_gain=0.005):
        self.max_depth=max_depth;self.alpha=alpha;self.min_leaf=min_leaf;self.min_gain=min_gain

    def _fit_local(self,X,y):
        if np.unique(y).size<2:
            return {'constant':float(np.mean(y))}
        p=make_pipeline(StandardScaler(), LogisticRegression(C=0.3,solver='lbfgs',max_iter=600,random_state=SEED))
        p.fit(X,y)
        return {'model':p}

    @staticmethod
    def _node_predict(m,X):
        if 'constant' in m: return np.full(X.shape[0],m['constant'])
        return m['model'].predict_proba(X)[:,1]

    def _build(self,Xs,y,idx,depth):
        n=len(idx)
        node={'n':n,'depth':depth,'local':self._fit_local(Xs[idx],y[idx]),'feature':None,'threshold':None}
        self.nodes_+=1
        self.deepest_=max(depth,self.deepest_)
        if depth>=self.max_depth or n<2*self.min_leaf or np.unique(y[idx]).size==1:return node
        base=gini(y[idx]); best=(0,None,None,None)
        for ax in COORD_COLS:
            vals=Xs[idx,ax]
            for q in (0.30,0.50,0.70):
                t=float(np.quantile(vals,q))
                left=vals<=t
                nl=int(np.sum(left));nr=n-nl
                if nl<self.min_leaf or nr<self.min_leaf:continue
                gain=base-nl/n*gini(y[idx[left]])-nr/n*gini(y[idx[~left]])
                if gain>best[0]+1e-12:best=(gain,ax,t,left)
        gain,ax,t,left=best
        if ax is None or gain<self.min_gain:return node
        node.update(feature=int(ax),threshold=float(t),split_gain=float(gain),
                    left=self._build(Xs,y,idx[left],depth+1),
                    right=self._build(Xs,y,idx[~left],depth+1))
        return node

    def fit(self,X,y):
        X=np.asarray(X,dtype=float);y=np.asarray(y,dtype=int)
        self.fit_scaler_=StandardScaler().fit(X)
        self.scaled_train_=self.fit_scaler_.transform(X)
        self.nodes_=0;self.deepest_=0;self.classes_=np.array([0,1])
        self.root_=self._build(self.scaled_train_,y,np.arange(len(X)),0)
        return self

    def predict_proba(self,X):
        Xs=self.fit_scaler_.transform(np.asarray(X,dtype=float))
        result=self._node_predict(self.root_['local'],Xs)
        def walk(node,idx):
            if len(idx)==0:return
            if node['depth']>0:
                local=self._node_predict(node['local'],Xs[idx]); w=self.alpha*node['n']/(node['n']+80)
                result[idx]=(1-w)*result[idx]+w*local
            if node['feature'] is None:return
            left=Xs[idx,node['feature']]<=node['threshold']
            walk(node['left'],idx[left]);walk(node['right'],idx[~left])
        if self.root_['feature'] is not None:
            idx=np.arange(len(Xs))
            left=Xs[idx,self.root_['feature']]<=self.root_['threshold']
            walk(self.root_['left'],idx[left]);walk(self.root_['right'],idx[~left])
        out=np.clip(result,1e-6,1-1e-6)
        return np.column_stack([1-out,out])

    def trace(self,x):
        xs=self.fit_scaler_.transform(np.asarray(x,dtype=float).reshape(1,-1))
        node=self.root_;r=[]
        p=float(self._node_predict(node['local'],xs)[0]);r.append({'depth':0,'support':node['n'],'prediction':round(p,6)})
        while node['feature'] is not None:
            ax=node['feature'];t=node['threshold'];go='left' if xs[0,ax]<=t else 'right'
            nxt=node[go];q=float(self._node_predict(nxt['local'],xs)[0]);w=self.alpha*nxt['n']/(nxt['n']+80)
            p=(1-w)*p+w*q
            r.append({'depth':nxt['depth'],'support':nxt['n'], 'split_coordinate':COLS[ax],
                      'split_threshold_scaled':round(t,5),'direction':go,'local_prediction':round(q,6),
                      'blended_prediction':round(p,6)})
            node=nxt
        return r


def method_grid():
    return {
      'constant':[{'name':'constant'}],
      'seasonal_logistic':[{'name':'seasonal_logistic','C':0.3}],
      'logistic':[{'name':'logistic','C':c} for c in (0.03,0.3,3.0)],
      'decision_tree':[{'name':'decision_tree','max_depth':d} for d in (2,4,6,100)],
      'random_forest':[{'name':'random_forest','min_samples_leaf':leaf} for leaf in (10,30,60)],
      'hist_gradient_boosting':[{'name':'hist_gradient_boosting','max_leaf_nodes':leaves} for leaves in (7,15,31)],
      'srde_portal':[{'name':'srde_portal','max_depth':depth,'alpha':alpha}
                     for depth in (1,3,6,100) for alpha in (0.35,0.65)],
    }


def init_model(c):
    name=c['name']
    if name=='seasonal_logistic':return make_pipeline(StandardScaler(),LogisticRegression(C=c['C'],max_iter=600,random_state=SEED))
    if name=='logistic':return make_pipeline(StandardScaler(),LogisticRegression(C=c['C'],max_iter=600,random_state=SEED))
    if name=='decision_tree':return DecisionTreeClassifier(max_depth=c['max_depth'],min_samples_leaf=40,random_state=SEED)
    if name=='random_forest':return RandomForestClassifier(n_estimators=200,min_samples_leaf=c['min_samples_leaf'],random_state=SEED,n_jobs=1)
    if name=='hist_gradient_boosting':return HistGradientBoostingClassifier(max_iter=200,learning_rate=0.05,max_leaf_nodes=c['max_leaf_nodes'],min_samples_leaf=20,l2_regularization=1,random_state=SEED)
    if name=='srde_portal':return PortalTree(max_depth=c['max_depth'],alpha=c['alpha'])
    return None


def X_for(df,name):
    feats=['year_sin','year_cos'] if name=='seasonal_logistic' else COLS
    return df[feats].to_numpy(dtype=float)


def fit_predict(c,train,evalset):
    name=c['name'];y=train.target.to_numpy(dtype=int)
    before=time.perf_counter()
    if name=='constant':
        p=np.full(len(evalset),float(np.mean(y)))
        return p,{'train_sec':0.0,'predict_sec':0.0,'model':None}
    model=init_model(c)
    model.fit(X_for(train,name),y)
    fit_s=time.perf_counter()-before
    before=time.perf_counter()
    p=model.predict_proba(X_for(evalset,name))[:,1]
    pred_s=time.perf_counter()-before
    assert np.isfinite(p).all() and ((p>=0)&(p<=1)).all()
    return p,{'train_sec':round(fit_s,6),'predict_sec':round(pred_s,6),'model':model}


def metrics(y,p):
    y=np.asarray(y,int);p=np.clip(np.asarray(p,float),1e-8,1-1e-8)
    assert len(y)==len(p) and np.isfinite(p).all()
    ece=0.0
    for k in range(10):
        mask=(np.minimum((p*10).astype(int),9)==k)
        if np.any(mask):ece+=np.mean(mask)*abs(float(np.mean(y[mask]))-float(np.mean(p[mask])))
    return {'n':int(len(y)),'positive_rate':round(float(np.mean(y)),6),
            'brier':round(float(brier_score_loss(y,p)),8),
            'log_loss':round(float(log_loss(y,p,labels=[0,1])),8),
            'roc_auc':None if len(np.unique(y))<2 else round(float(roc_auc_score(y,p)),8),
            'accuracy_at_0_5':round(float(accuracy_score(y,p>=0.5)),8),
            'ece10':round(float(ece),8)}


def validate(out):
    t=time.perf_counter();raw=co2.load_pandas().data
    raw.to_csv(out/'source_statsmodels_co2.csv')
    ds=make_rows(raw);train,val,test=split_rows(ds)
    y=val.target.to_numpy(dtype=int)
    grid=method_grid();records=[];chosen={}
    for name,cfgs in grid.items():
        for cfg in cfgs:
            p,info=fit_predict(cfg,train,val)
            m=metrics(y,p)
            rec={'config':cfg,'method':name,'validation':m,'train_seconds':info['train_sec'],'predict_seconds':info['predict_sec']}
            records.append(rec)
        candidates=[r for r in records if r['method']==name]
        pick=min(candidates,key=lambda z:(z['validation']['brier'],json.dumps(z['config'],sort_keys=True)))
        chosen[name]=pick['config']
    # File SHA binds both data and protocol to locked selection.
    protocol=out/'PREREGISTRATION.md'
    assert protocol.exists(), 'Missing pre-registered protocol'
    source=out/'source_statsmodels_co2.csv'
    selection={'title':'SRDE-P2 validation-locked model selection','generated_at':'2026-11-03',
        'version_info':{'python':platform.python_version(),'numpy':np.__version__,'pandas':pd.__version__,
                        'sklearn':sklearn.__version__,'statsmodels':statsmodels.__version__},
        'sha256_protocol':sha_bytes(protocol.read_bytes()),'sha256_source_csv':sha_bytes(source.read_bytes()),
        'partition_sizes':{'train':len(train),'validation':len(val),'test_unscored':len(test)},
        'date_ranges':{'train':[train.issue_date.min(),train.issue_date.max()],
                       'validation':[val.issue_date.min(),val.issue_date.max()],
                       'test_unscored':[test.issue_date.min(),test.issue_date.max()]},
        'train_positive_rate':float(train.target.mean()),'validation_positive_rate':float(val.target.mean()),
        'chosen':chosen, 'validation_grid':records, 'elapsed_seconds':round(time.perf_counter()-t,4),
        'holdout_access':'no test labels used in validation stage'}
    (out/'locked_selection.json').write_text(json.dumps(selection,indent=2)+'\n')
    print('LOCKED VALIDATION: train',len(train),'validation',len(val),'holdout_unscored',len(test))
    for name in grid:
        winner=next(r for r in records if r['config']==chosen[name] and r['method']==name)
        print(f'{name:25s} val Brier={winner["validation"]["brier"]:.5f} config={chosen[name]}')
    return selection


def year_bootstrap(test,pa,pb,seed=20261104,nrep=5000):
    years=pd.to_datetime(test.issue_date).dt.year.to_numpy()
    keys=np.unique(years)
    idxs=[np.flatnonzero(years==k) for k in keys]
    y=test.target.to_numpy(dtype=int)
    rng=np.random.default_rng(seed)
    deltas=[]
    for _ in range(nrep):
        sel=np.concatenate([idxs[j] for j in rng.integers(len(keys),size=len(keys))])
        da=np.mean((pa[sel]-y[sel])**2-(pb[sel]-y[sel])**2)
        deltas.append(da)
    return {'year_blocks':list(map(int,keys)), 'replicates':nrep,
            'portal_minus_booster_brier_mean':float(np.mean((pa-y)**2-(pb-y)**2)),
            'ci95_year_resample':list(map(float,np.percentile(deltas,[2.5,97.5])))}


def backward_diagnostic(train,test):
    """Bayes: does observed later E suggest earlier 4-week CO2 trend S=1?"""
    def state(df):return (df['diff_4']>0).astype(int).to_numpy()
    ytrain=train.target.to_numpy(int);strain=state(train);ytest=test.target.to_numpy(int);stest=state(test)
    p_s_e={}
    for ev in (0,1):
        m=(ytrain==ev)
        p_s_e[ev]=(np.sum(strain[m])+1)/(np.sum(m)+2)
    prev=float((np.sum(strain)+1)/(len(strain)+2))
    rev=np.where(ytest==1,p_s_e[1],p_s_e[0])
    brier=float(np.mean((rev-stest)**2))
    return {'question':'Given observed future E, infer earlier S=(CO2(t)-CO2(t-4)>0), not reverse causality',
            'P(S=1_given_E=1)':float(p_s_e[1]),'P(S=1_given_E=0)':float(p_s_e[0]),
            'test_brier':brier,'test_baseline_prevalence_brier':float(np.mean((prev-stest)**2)),
            'test_n':len(test)}


def evaluate(out):
    t0=time.perf_counter(); selection=json.loads((out/'locked_selection.json').read_text())
    assert selection['sha256_protocol']==sha_bytes((out/'PREREGISTRATION.md').read_bytes())
    assert selection['sha256_source_csv']==sha_bytes((out/'source_statsmodels_co2.csv').read_bytes())
    assert not (out/'test_predictions.csv').exists(), 'Holdout was already evaluated. Never overwrite.'
    raw=pd.read_csv(out/'source_statsmodels_co2.csv',index_col=0,parse_dates=True)
    ds=make_rows(raw);train,val,test=split_rows(ds)
    assert [len(train),len(val),len(test)]==[selection['partition_sizes'][k] for k in ('train','validation','test_unscored')]
    trainval=pd.concat([train,val],ignore_index=True)
    out_csv=test[['issue_date','target_date','co2_at_issue','co2_at_target','target']].copy()
    forecasts={}; report={}
    for name,cfg in selection['chosen'].items():
        p,info=fit_predict(cfg,trainval,test)
        out_csv['prob_'+name]=p
        forecasts[name]=p
        m=metrics(test.target.to_numpy(),p)
        row={'config':cfg,'metrics':m,'train_seconds':info['train_sec'],'predict_seconds':info['predict_sec']}
        if name=='srde_portal':
            row.update({'max_observed_depth':info['model'].deepest_,'fitted_nodes':info['model'].nodes_,
                       'illustrative_trace':info['model'].trace(X_for(test.iloc[[0]],'srde_portal'))})
        report[name]=row
        print(f'RESULT {name:25s} test Brier={m["brier"]:.6f} AUC={m["roc_auc"]} n={m["n"]}')
    # Label shuffle negative control uses the exact selected portal config but shuffled fitting outcomes.
    shuffled=trainval.copy();rng=np.random.default_rng(20261105)
    shuffled['target']=rng.permutation(shuffled['target'].to_numpy())
    pshuffle,info=fit_predict(selection['chosen']['srde_portal'],shuffled,test)
    out_csv['prob_portal_label_shuffle_control']=pshuffle
    shuffle_metrics=metrics(test.target.to_numpy(),pshuffle)
    # Compute paired bootstrap on year blocks, not i.i.d. weekly rows.
    b=year_bootstrap(test,forecasts['srde_portal'],forecasts['hist_gradient_boosting'])
    conventional=('logistic','decision_tree','random_forest','hist_gradient_boosting')
    best=min(conventional,key=lambda name:report[name]['metrics']['brier'])
    reverse=backward_diagnostic(trainval,test)
    out_csv.to_csv(out/'test_predictions.csv',index=False)
    full=ds.copy();full['split']='excluded'
    for key,frame in [('train',train),('validation',val),('test',test)]:full.loc[frame.index,'split']=key
    full.to_csv(out/'all_feature_records.csv',index=False)
    result={'title':'SRDE-P2 retrospective future-event prediction on real Mauna Loa weekly CO2',
            'hypothesis_status':'tested in one historical observational dataset, not general validation',
            'timing':{'as_of':'2026-11-03','train_period':'<=1988','validation_period':'1989-1994','holdout_period':'1995-2001'},
            'dataset':{'name':'statsmodels.datasets.co2','rows_original':len(raw),'original_missing':int(raw.co2.isna().sum()),
                       'rows_with_complete_lags_and_target':len(ds),'rows_train':len(train),'rows_validation':len(val),'rows_test':len(test),
                       'sha256_raw_csv':selection['sha256_source_csv']},
            'observed_test_positive_rate':float(test.target.mean()),
            'models':report,'year_block_bootstrap_portal_minus_gradient_booster':b,
            'best_test_conventional_descriptive':{'name':best,'brier':report[best]['metrics']['brier'],
                                                   'portal_minus_best_brier':float(report['srde_portal']['metrics']['brier']-report[best]['metrics']['brier'])},
            'portal_label_shuffle_negative_control':{'metrics':shuffle_metrics,'train_seconds':info['train_sec']},
            'reverse_bayesian_diagnostic':reverse,'elapsed_seconds':time.perf_counter()-t0,
            'important_limits':['Only one historical observational domain','Not real-time forecasts or human cognition',
                                '100 is permitted recursion cap, not realized depth','Correlated local votes are not independent evidence',
                                'No feeling data','Missing samples were dropped rather than estimated',
                                'Historical snapshots may be revised','Year-block bootstrap has only seven blocks']}
    (out/'results.json').write_text(json.dumps(result,indent=2)+'\n')
    assert len(out_csv)==len(test)
    for name in forecasts:
        actual=float(np.mean((test.target.to_numpy()-out_csv['prob_'+name].to_numpy())**2))
        assert abs(actual-report[name]['metrics']['brier'])<1e-7
    assert all(out_csv.target_date >= out_csv.issue_date)
    return result


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--stage',required=True,choices=['validate','evaluate'])
    p.add_argument('--output-dir',default='.')
    args=p.parse_args();o=Path(args.output_dir);o.mkdir(parents=True,exist_ok=True)
    if args.stage=='validate':validate(o)
    else:evaluate(o)

if __name__=='__main__':main()
