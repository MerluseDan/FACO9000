#!/usr/bin/env python3
"""SRDE-P3 REPAIRED COPY: retrospective conditional stochastic portal forecasting, independent dataset.
Two stages: validate locks methods without holdout labels; evaluate scores once.
CPU only, deterministic seeds. Uses historical NOAA ERSST.v3b Niño 1+2 temperatures
packaged with statsmodels. This is not real-time ENSO or human affect research.
"""
from __future__ import annotations
import argparse, hashlib, json, math, time, platform, os
from pathlib import Path
import numpy as np
import pandas as pd
import sklearn, statsmodels
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.neighbors import NearestNeighbors
from sklearn.metrics import brier_score_loss, roc_auc_score, accuracy_score, log_loss

SEED=20261103
HORIZON=3
THRESHOLD=0.5
N_PARTICLES=256
FEATURES=['temp_now','change_1','change_3','change_6','change_12','accel_2','volatility_6','month_sin','month_cos']
MONTH_NAMES=['JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC']


def digest(b):return hashlib.sha256(b).hexdigest()


def source_snapshot(base:Path):
    p=base/'source_elnino_1950_2010.csv'
    if not p.exists():
        import statsmodels.api as sm
        raw=sm.datasets.elnino.load_pandas().data
        raw.to_csv(p,index=False,float_format='%.5f')
    raw=pd.read_csv(p)
    assert list(raw.columns)==['YEAR']+MONTH_NAMES and raw.shape==(61,13)
    assert int(raw.YEAR.min())==1950 and int(raw.YEAR.max())==2010
    assert np.isfinite(raw[MONTH_NAMES].to_numpy(float)).all()
    return raw,p


def series_from_raw(raw):
    dates=[];vals=[]
    for _,r in raw.iterrows():
        for m,name in enumerate(MONTH_NAMES,1):
            dates.append(pd.Timestamp(year=int(r.YEAR),month=m,day=1))
            vals.append(float(r[name]))
    return pd.DatetimeIndex(dates),np.array(vals,dtype=float)


def feature_matrix(hist,month):
    """hist: N x 13 chronological; month: zero-based Jan-Dec for current t."""
    h=np.asarray(hist,dtype=float)
    if h.ndim==1:h=h.reshape(1,13)
    m=np.asarray(month,dtype=int)
    if m.ndim==0:m=np.full(len(h),int(m),dtype=int)
    changes=np.diff(h[:,-7:],axis=1)
    f=np.column_stack([h[:,-1],h[:,-1]-h[:,-2],h[:,-1]-h[:,-4],
                       h[:,-1]-h[:,-7],h[:,-1]-h[:,0],
                       h[:,-1]-2*h[:,-2]+h[:,-3],
                       np.std(changes,axis=1),
                       np.sin(2*np.pi*m/12),np.cos(2*np.pi*m/12)])
    assert f.shape==(len(h),9) and np.isfinite(f).all()
    return f


def make_rows(dates,vals):
    result=[]
    for i in range(12,len(vals)-HORIZON):
        h=vals[i-12:i+1]
        row={'idx':i,'issue_date':str(dates[i].date()),'target_date':str(dates[i+HORIZON].date()),
             'issue_year':dates[i].year,'month':dates[i].month-1,
             'temperature_now':float(vals[i]),'temperature_target':float(vals[i+HORIZON]),
             'one_month_delta':float(vals[i+1]-vals[i]),
             'target':int(vals[i+HORIZON]-vals[i]>=THRESHOLD)}
        for k,v in enumerate(feature_matrix(h,dates[i].month-1)[0]):row[FEATURES[k]]=float(v)
        result.append(row)
    return pd.DataFrame(result)


def partition(df):
    issue=pd.to_datetime(df.issue_date)
    target=pd.to_datetime(df.target_date)
    train=df[target<='1984-12-01'].copy()
    val=df[(issue>='1985-01-01')&(target<='1996-12-01')].copy()
    test=df[(issue>='1997-01-01')&(target<='2010-12-01')].copy()
    assert len(train)>350 and len(val)>120 and len(test)>140
    assert train.target_date.max()<'1985-01-01'
    assert val.issue_date.min()>='1985-01-01' and val.target_date.max()<='1996-12-01'
    assert test.issue_date.min()>='1997-01-01'
    assert df.issue_date.is_unique
    assert (pd.to_datetime(df.target_date)>issue).all()
    return train,val,test


def X(df):return df[FEATURES].to_numpy(float)

def y(df):return df.target.to_numpy(int)


def score(y0,p):
    y0=np.asarray(y0,dtype=int);p=np.clip(np.asarray(p,float),1e-8,1-1e-8)
    assert p.shape==y0.shape and np.isfinite(p).all()
    ece=0
    ix=np.minimum((p*10).astype(int),9)
    for i in range(10):
        z=ix==i
        if z.any():ece+=float(z.mean()*abs(y0[z].mean()-p[z].mean()))
    return dict(n=len(y0),positive_rate=round(float(y0.mean()),7),brier=round(float(np.mean((p-y0)**2)),8),
                log_loss=round(float(log_loss(y0,p,labels=[0,1])),8),
                auc=None if np.unique(y0).size<2 else round(float(roc_auc_score(y0,p)),8),
                accuracy=round(float(accuracy_score(y0,p>=.5)),8),ece10=round(ece,8))


def grid():
    ks=(16,32,64);ts=(0.5,1.5)
    return {
      'constant':[{'method':'constant'}],
      'calendar_logistic':[{'method':'calendar_logistic','C':1.0}],
      'logistic':[{'method':'logistic','C':c} for c in (.1,1.,10.)],
      'random_forest':[{'method':'random_forest','min_samples_leaf':k} for k in (5,20)],
      'hist_boost':[{'method':'hist_boost','max_leaf_nodes':k} for k in (7,15)],
      'direct_analog':[{'method':'direct_analog','k':k,'tau':t} for k in ks for t in ts],
      'recursive_portal':[{'method':'recursive_portal','k':k,'tau':t} for k in ks for t in ts],
    }


def model_for(cfg):
    method=cfg['method']
    if method in ('logistic','calendar_logistic'):
        return make_pipeline(StandardScaler(),LogisticRegression(C=cfg['C'],solver='lbfgs',max_iter=1000,random_state=SEED))
    if method=='random_forest':return RandomForestClassifier(n_estimators=200,min_samples_leaf=cfg['min_samples_leaf'],random_state=SEED,n_jobs=1)
    if method=='hist_boost':return HistGradientBoostingClassifier(max_iter=160,learning_rate=.05,max_leaf_nodes=cfg['max_leaf_nodes'],min_samples_leaf=15,l2_regularization=1.,random_state=SEED)
    raise ValueError(method)


def kernel_dist_weights(dist,tau):
    vals=np.exp(-(dist-dist[:,0,None])/tau)
    return vals/vals.sum(axis=1,keepdims=True)


class ConditionalKernel:
    """Train-only empirical Markov kernel; local frame recomputed each portal."""
    def __init__(self,frame,ts,k,tau,shuffle=False):
        self.df=frame.reset_index(drop=True);self.ts=np.asarray(ts,float);self.k=int(k);self.tau=float(tau)
        self.scaler=StandardScaler().fit(X(frame));xt=self.scaler.transform(X(frame))
        self.nn=NearestNeighbors(n_neighbors=self.k,algorithm='auto',n_jobs=1).fit(xt)
        self.next_delta=frame.one_month_delta.to_numpy(float).copy()
        if shuffle:
            rng=np.random.default_rng(20261105)
            for m in range(12):
                idx=np.flatnonzero(frame.month.to_numpy(int)==m)
                self.next_delta[idx]=rng.permutation(self.next_delta[idx])

    def query(self,feat):
        return self.nn.kneighbors(self.scaler.transform(feat),return_distance=True)

    def direct_predict(self,evalset):
        d,indices=self.query(X(evalset))
        w=kernel_dist_weights(d,self.tau)
        return np.clip((w*y(self.df)[indices]).sum(axis=1),1e-6,1-1e-6)

    def _trace(self,h,month0,seed,steps=3,freeze=False,details=False):
        rng=np.random.default_rng(seed)
        n=N_PARTICLES
        current=np.broadcast_to(np.asarray(h,float).reshape(1,13),(n,13)).copy()
        origin=current[0,-1]
        start_month=int(month0)
        delta1=None
        if freeze:
            d,ii=self.query(feature_matrix(current[:1],start_month))
            w=kernel_dist_weights(d,self.tau)
            cum0=np.cumsum(w[0])
            cand0=ii[0]
        checkpoints=[]
        for depth in range(1,steps+1):
            if freeze:
                chosen=np.searchsorted(cum0,rng.random(n),side='right')
                increment=self.next_delta[cand0[np.clip(chosen,0,self.k-1)]]
            else:
                feat=feature_matrix(current,(start_month+depth-1)%12)
                d,ii=self.query(feat)
                w=kernel_dist_weights(d,self.tau)
                cumulative=np.cumsum(w,axis=1)
                chosen=(rng.random(n)[:,None]>cumulative).sum(axis=1)
                increment=self.next_delta[ii[np.arange(n),np.minimum(chosen,self.k-1)]]
            if delta1 is None:delta1=increment.copy()
            current=np.column_stack([current[:,1:],current[:,-1]+increment])
            if details and depth in (1,3,12,25,50,100):
                checkpoints.append({'step':depth,'mean':float(np.mean(current[:,-1])),
                                    'std':float(np.std(current[:,-1])),
                                    'outside_historical_range':float(np.mean((current[:,-1]<self.ts.min())|(current[:,-1]>self.ts.max())))})
        event=current[:,-1]-origin>=THRESHOLD
        return (float((int(event.sum())+.5)/(n+1)),
                {'event_particles':int(event.sum()),'total_particles':n,
                 'first_step_mean_event':float(np.mean(delta1[event])) if event.any() else None,
                 'first_step_mean_nonevent':float(np.mean(delta1[~event])) if (~event).any() else None,
                 'checkpoints':checkpoints})

    def forecast(self,frame,series,stage_id,freeze=False,shuffle=False,diagnostics=False):
        p=[];diagn=[]
        ix_all=frame.idx.to_numpy(dtype=int)
        for i,(ii,month) in enumerate(zip(ix_all,frame.month.to_numpy(int))):
            history=series[ii-12:ii+1]
            pr,diag=self._trace(history,month,SEED+stage_id*1000000+ii,steps=3,freeze=freeze,details=diagnostics)
            p.append(pr)
            if diagnostics:diagn.append({'issue_date':str(frame.iloc[i].issue_date),**diag})
        return np.asarray(p),diagn


def make_predict(cfg,fitframe,evalframe,ts,stage_id,freeze=False,shuffle=False):
    t0=time.perf_counter()
    name=cfg['method']
    if name=='constant':
        p=np.full(len(evalframe),float(y(fitframe).mean()))
        return p,{'train_seconds':0.,'predict_seconds':0.},None
    if name in ('direct_analog','recursive_portal'):
        ker=ConditionalKernel(fitframe,ts,cfg['k'],cfg['tau'],shuffle=shuffle)
        ft=time.perf_counter()-t0;t1=time.perf_counter()
        if name=='direct_analog':p=ker.direct_predict(evalframe)
        else:p,_=ker.forecast(evalframe,ts,stage_id,freeze=freeze)
        return p,{'train_seconds':round(ft,5),'predict_seconds':round(time.perf_counter()-t1,5)},ker
    model=model_for(cfg)
    features=FEATURES[-2:] if name=='calendar_logistic' else FEATURES
    model.fit(fitframe[features].to_numpy(float),y(fitframe))
    fit=time.perf_counter()-t0;t1=time.perf_counter()
    p=model.predict_proba(evalframe[features].to_numpy(float))[:,1]
    return p,{'train_seconds':round(fit,5),'predict_seconds':round(time.perf_counter()-t1,5)},model


def validate(out:Path):
    assert not (out/'locked_selection.json').exists(), 'Selection already exists: no overwrite'
    raw,source_path=source_snapshot(out)
    dates,temps=series_from_raw(raw)
    # SEALED: validation materialization ends Dec 1996. This function never even
    # constructs target labels for any 1997-2010 row.
    mask=dates<=pd.Timestamp('1996-12-01')
    df=make_rows(dates[mask],temps[mask]); train,val,_=partition_limited(df)
    assert len(train)>350 and len(val)>120
    print('PRELOCK: train',len(train),'validation',len(val),'no test labels materialized')
    records=[];selected={}
    for name,configs in grid().items():
        sub=[]
        for cfg in configs:
            p,timing,_=make_predict(cfg,train,val,temps[mask],stage_id=1)
            mm=score(y(val),p)
            row={'config':cfg,'method':name,'validation':mm,**timing}
            sub.append(row);records.append(row)
            print('VALIDATE',name,json.dumps(cfg,sort_keys=True),'Brier',mm['brier'])
        best=min(sub,key=lambda row:(row['validation']['brier'],json.dumps(row['config'],sort_keys=True)))
        selected[name]=best['config']
    (out/'validation_grid.json').write_text(json.dumps(records,indent=2)+'\n',encoding='utf-8')
    pprotocol=out/'PREREGISTRATION.md'
    pcode=Path(__file__)
    assert pprotocol.exists()
    manifest={'stage':'VALIDATION_FROZEN','source': 'statsmodels.datasets.elnino (NOAA ERSST.v3b Niño 1+2)',
              'source_sha256':digest(source_path.read_bytes()),
              'protocol_sha256':digest(pprotocol.read_bytes()),
              'code_sha256':digest(pcode.read_bytes()),
              'asof':'2026-11-03','config_seed':SEED,'n_particles':N_PARTICLES,
              'periods':{'train_end_target':'1984-12-01','validation_start_issue':'1985-01-01','validation_end_target':'1996-12-01',
                         'holdout_start_issue':'1997-01-01','holdout_end_target':'2010-12-01'},
              'sizes':{'train':len(train),'validation':len(val),'test':'UNOPENED'},
              'packages':{'numpy':np.__version__,'pandas':pd.__version__,'sklearn':sklearn.__version__,
                         'statsmodels':statsmodels.__version__,'python':platform.python_version()},
              'selected_configs':selected,
              'primary_predeclared_comparison':'SCP vs best validation-selected conventional among logistic,random_forest,hist_boost,direct_analog',
              'source_includes_full_historical_timespan':'yes; only train/validation outcomes materialized before lock'}
    (out/'locked_selection.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    print('LOCKED',len(train),len(val),json.dumps({k:v for k,v in selected.items()}))
    return manifest


def partition_limited(df):
    issue=pd.to_datetime(df.issue_date);target=pd.to_datetime(df.target_date)
    train=df[target<='1984-12-01'].copy()
    val=df[(issue>='1985-01-01')&(target<='1996-12-01')].copy()
    return train,val,None


def bootstrap(df,p1,p2,nrep=5000):
    years=df.issue_year.to_numpy(int);blocks=sorted(np.unique(years))
    group=[np.flatnonzero(years==b) for b in blocks]
    yy=y(df);rng=np.random.default_rng(20261104)
    dif=[]
    for _ in range(nrep):
        idx=np.concatenate([group[j] for j in rng.integers(0,len(group),len(group))])
        dif.append(float(np.mean((p1[idx]-yy[idx])**2-(p2[idx]-yy[idx])**2)))
    return {'n_year_blocks':len(blocks),'years':blocks,'replicates':nrep,
            'difference_portal_minus_baseline':float(np.mean((p1-yy)**2-(p2-yy)**2)),
            'ci95':list(map(float,np.percentile(dif,[2.5,97.5])))}


def evaluate(out:Path):
    assert not (out/'test_predictions.csv').exists(), 'Holdout already evaluated; no overwrite.'
    frozen=json.loads((out/'locked_selection.json').read_text())
    protocol=out/'PREREGISTRATION.md';source=out/'source_elnino_1950_2010.csv'
    assert digest(protocol.read_bytes())==frozen['protocol_sha256']
    assert digest(Path(__file__).read_bytes())==frozen['code_sha256']
    assert digest(source.read_bytes())==frozen['source_sha256']
    raw=pd.read_csv(source);dates,ts=series_from_raw(raw)
    df=make_rows(dates,ts);train,val,test=partition(df)
    assert (len(train),len(val))==(frozen['sizes']['train'],frozen['sizes']['validation'])
    fit=pd.concat([train,val],ignore_index=True)
    predictions=test[['issue_date','target_date','issue_year','month','temperature_now','temperature_target','target']].copy().reset_index(drop=True)
    results={};forecasts={}
    for name,cfg in frozen['selected_configs'].items():
        pr,timing,model=make_predict(cfg,fit,test,ts,stage_id=2)
        mm=score(y(test),pr)
        forecasts[name]=pr;predictions['prob_'+name]=pr
        results[name]={'config':cfg,'metrics':mm,**timing}
        print('HOLDOUT',name,'Brier',mm['brier'],'AUC',mm['auc'],'test_n',mm['n'])
    candidates=('logistic','random_forest','hist_boost','direct_analog')
    winner=min(candidates,key=lambda name:next(z['validation']['brier'] for z in json.loads((out/'validation_grid.json').read_text()) if z['config']==frozen['selected_configs'][name] and z['method']==name))
    selected_ker=ConditionalKernel(fit,ts,**{k:frozen['selected_configs']['recursive_portal'][k] for k in ('k','tau')})
    pa=forecasts['recursive_portal'];pb=forecasts[winner]
    pb_ci=bootstrap(test,pa,pb)
    p_frozen,diag0=selected_ker.forecast(test,ts,stage_id=2,freeze=True)
    shuffled=ConditionalKernel(fit,ts,**{k:frozen['selected_configs']['recursive_portal'][k] for k in ('k','tau')},shuffle=True)
    p_shuf,_=shuffled.forecast(test,ts,stage_id=2)
    neg={'root_frame_frozen':score(y(test),p_frozen), 'calendar_month_delta_shuffle':score(y(test),p_shuf)}
    predictions['prob_frozen_frame_ablation']=p_frozen
    predictions['prob_month_shuffle_negative_control']=p_shuf
    # Reverse *associational* diagnostic: distribution of immediate increment
    # conditional on the generated three-hop event; does not use actual future outcome.
    rdiag=[]
    for ix in [0,len(test)//2,len(test)-1]:
        row=test.iloc[ix]
        _,d=selected_ker._trace(ts[int(row.idx)-12:int(row.idx)+1],int(row.month),SEED+2000000+int(row.idx),details=True)
        rdiag.append({'issue_date':row.issue_date,**d})
    # Diagnostic long portal sequences are exploratory stability, NOT predictions.
    long=[]
    for ix in [0,len(test)//2,len(test)-1]:
        row=test.iloc[ix]
        _,d=selected_ker._trace(ts[int(row.idx)-12:int(row.idx)+1],int(row.month),SEED+3000000+int(row.idx),steps=100,details=True)
        long.append({'issue_date':row.issue_date,'checkpoints':d['checkpoints']})
    byyear=[]
    for year,part in test.groupby('issue_year',sort=True):
        idx=np.flatnonzero(test.issue_year.to_numpy(int)==int(year))
        byyear.append({'year':int(year),'n':len(idx),'portal_brier':float(np.mean((pa[idx]-y(test)[idx])**2)),
                       'baseline_brier':float(np.mean((pb[idx]-y(test)[idx])**2))})
    report={'status':'COMPLETED_SINGLE_HOLDOUT','project':'SRDE-P3 2026-11-03',
            'dataset':'NOAA ERSST.v3b Niño 1+2 temperature via statsmodels.datasets.elnino, 1950-2010',
            'task':'predict temperature change from t to t+3 months >= 0.5 degrees C',
            'sizes':{'raw_months':len(ts),'train':len(train),'validation':len(val),'holdout':len(test)},
            'holdout_period':[test.issue_date.min(),test.issue_date.max()],
            'test_event_prevalence':float(y(test).mean()),
            'selected_primary_comparator':winner,'primary_contrast':pb_ci,
            'methods':results,'ablation_and_negative_controls':neg,
            'by_holdout_year':byyear,'reverse_conditional_simulation':rdiag,
            'hundred_step_stability_only':long,
            'historical_range_celsius':[float(ts.min()),float(ts.max())],
            'important_limits':['One retrospective domain; not real-time or operational ENSO detection',
                 'Contemporaneous historical NOAA archive may differ from real-time vintages',
                 'Three-step transition model, not an effective 100-layer predictor',
                 'Monthly temperatures differ from human semantic or feeling dimensions',
                 'Near-neighbor resampling can underrepresent unprecedented shocks',
                 'Temporal sample dependence and only 14 year blocks',
                 'Sampling noise: 256 fixed particles per case; no repeat/test-driven tuning']}
    predictions.to_csv(out/'test_predictions.csv',index=False)
    (out/'results.json').write_text(json.dumps(report,indent=2,default=lambda v: v.item() if isinstance(v,np.generic) else v.tolist())+'\n')
    df.assign(split=np.where(df.issue_date.isin(test.issue_date),'holdout',np.where(df.issue_date.isin(val.issue_date),'validation',np.where(df.issue_date.isin(train.issue_date),'train','excluded')))).to_csv(out/'all_feature_records.csv',index=False)
    for name,pr in forecasts.items():
        assert abs(float(np.mean((pr-y(test))**2))-results[name]['metrics']['brier'])<5e-8
    assert len(predictions)==len(test) and test.target_date.max()<='2010-12-01'
    print('FINAL:',json.dumps({'winner_validation_baseline':winner,'difference':pb_ci,'ablation':neg},default=lambda v: v.item() if isinstance(v,np.generic) else v.tolist()))
    return report


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--stage',choices=['validate','evaluate'],required=True)
    ap.add_argument('--out',type=Path,required=True)
    args=ap.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    if args.stage=='validate':validate(args.out)
    else:evaluate(args.out)

if __name__=='__main__':main()