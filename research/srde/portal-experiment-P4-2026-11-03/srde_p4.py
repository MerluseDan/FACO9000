#!/usr/bin/env python3
"""SRDE-P4. Preregistered retrospective NOAA Niño 3.4 anomaly forecasting.

Stage validate creates training and validation labels only (through 2013) and
freezes a model-selection manifest. Stage evaluate checks all hashes, fits
on <=2013 and evaluates 2014-2025 exactly once. CPU only.

This is a state-conditional stochastic analog model, NOT a model of brains,
physical portals, universal causality, subjective valence, or real-time ENSO.
"""
from __future__ import annotations
import argparse, hashlib, json, os, platform, sys, time
from pathlib import Path
import numpy as np
import pandas as pd
import scipy, sklearn
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.neighbors import NearestNeighbors
from sklearn.metrics import roc_auc_score

SEED=20261103
HORIZON=3
EVENT_THRESHOLD=0.50
PARTICLES=128
STATE_COLS=['anomaly_now','change_1','change_3','change_6','change_12','accel_2','volatility_6']
CAL_COLS=['sin_year','cos_year','sin2_year','cos2_year']
FEATURES=STATE_COLS+CAL_COLS
SHA=lambda b:hashlib.sha256(b).hexdigest()


def data(p:Path):
    raw=p.read_text(encoding='utf-8')
    lines=[line.split() for line in raw.splitlines() if line.strip()]
    assert len(lines)==76 and all(len(row)==13 for row in lines), 'NOAA snapshot must be 76 years x 12 months'
    assert [int(r[0]) for r in lines]==list(range(1950,2026))
    y=np.array([float(n) for row in lines for n in row[1:]],dtype=float)
    assert y.shape==(912,) and np.isfinite(y).all() and np.min(y)>-99
    assert y[0]==-1.41 and y[-1]==-0.39
    dates=pd.date_range('1950-01-01','2025-12-01',freq='MS')
    assert len(dates)==len(y)
    return y,dates


def features(history,month0):
    h=np.asarray(history,dtype=float)
    if h.ndim==1:h=h.reshape(1,-1)
    assert h.shape[1]==13
    m=np.asarray(month0,dtype=int)
    if m.ndim==0:m=np.full(len(h),int(m))
    dif=np.diff(h[:,-7:],axis=1)
    st=np.column_stack((h[:,-1],h[:,-1]-h[:,-2],h[:,-1]-h[:,-4],
      h[:,-1]-h[:,-7],h[:,-1]-h[:,0],h[:,-1]-2*h[:,-2]+h[:,-3],dif.std(axis=1)))
    theta=2*np.pi*m/12
    ca=np.column_stack([np.sin(theta),np.cos(theta),np.sin(2*theta),np.cos(2*theta)])
    return st,ca


def make_rows(vals,dates,cutoff=None):
    rows=[]
    for i in range(12,len(vals)-HORIZON):
        target_date=dates[i+HORIZON]
        if cutoff is not None and target_date>pd.Timestamp(cutoff):break
        month=(dates[i].month-1)
        st,ca=features(vals[i-12:i+1],month)
        r={'idx':int(i),'issue_date':dates[i].strftime('%Y-%m-%d'),
           'target_date':target_date.strftime('%Y-%m-%d'),'issue_year':int(dates[i].year),
           'month':month,'anomaly_future':float(vals[i+HORIZON]),
           'next_delta':float(vals[i+1]-vals[i]),
           'target':int(vals[i+HORIZON]-vals[i]>=EVENT_THRESHOLD)}
        r.update({n:float(v) for n,v in zip(FEATURES,np.r_[st[0],ca[0]])})
        rows.append(r)
    return pd.DataFrame(rows)


def partition(df):
    targets=pd.to_datetime(df.target_date)
    issues=pd.to_datetime(df.issue_date)
    tr=df.loc[targets<=pd.Timestamp('2002-12-01')].copy()
    va=df.loc[(issues>=pd.Timestamp('2003-01-01'))&(targets<=pd.Timestamp('2013-12-01'))].copy()
    te=df.loc[(issues>=pd.Timestamp('2014-01-01'))&(targets<=pd.Timestamp('2025-12-01'))].copy()
    assert len(tr)>550 and len(va)>100
    assert tr.target_date.max()<va.issue_date.min() and va.target_date.max()<'2014-01-01'
    return tr,va,te


def score(y,p):
    y=np.asarray(y,int);p=np.asarray(p,float)
    assert len(y)==len(p) and np.isfinite(p).all() and ((p>=0)&(p<=1)).all()
    q=np.clip(p,1e-8,1-1e-8)
    ece=0.0
    b=np.minimum((10*p).astype(int),9)
    for i in range(10):
        mask=(b==i)
        if mask.any():ece+=float(mask.mean()*abs(y[mask].mean()-p[mask].mean()))
    return {'n':int(len(y)),'positive_rate':round(float(y.mean()),7),
      'brier':round(float(np.mean((p-y)**2)),8),
      'log_loss':round(float(np.mean(-y*np.log(q)-(1-y)*np.log(1-q))),8),
      'auc':None if len(np.unique(y))<2 else round(float(roc_auc_score(y,p)),8),
      'accuracy_0_5':round(float(np.mean((p>=.5)==y)),8), 'ece10':round(ece,8)}


def grid():
    return {
      'constant':[{'method':'constant'}],
      'calendar_logistic':[{'method':'calendar_logistic','C':1.0}],
      'logistic':[{'method':'logistic','C':c} for c in [0.1,1.0,10.0]],
      'random_forest':[{'method':'random_forest','min_samples_leaf':x} for x in [5,15]],
      'hist_boost':[{'method':'hist_boost','max_leaf_nodes':x} for x in [7,15]],
      'direct_analog':[{'method':'direct_analog','k':k,'tau':tau} for k in [12,36] for tau in [0.5,1.5]],
      'season_portal':[{'method':'season_portal'}],
      'state_portal':[{'method':'state_portal','k':k,'tau':tau} for k in [6,12,24] for tau in [0.4,1.2]],
    }


def nn_weights(d,tau):
    w=np.exp(-(d-d[:,[0]])/tau)
    return w/np.sum(w,axis=1,keepdims=True)


class MonthKernel:
    """State-conditioned empirical one-step transitions, month-specific donor pools."""
    def __init__(self,fit,shuffle_seed=None):
        self.fit=fit.reset_index(drop=True)
        self.scaler=StandardScaler().fit(self.fit[STATE_COLS].to_numpy(float))
        coords=self.scaler.transform(self.fit[STATE_COLS].to_numpy(float))
        self.groups={};self.nn={};self.means={};self.delta={}
        for month in range(12):
            idx=np.flatnonzero(self.fit.month.to_numpy(int)==month)
            assert len(idx)>=30
            self.groups[month]=idx
            self.nn[month]=NearestNeighbors(n_neighbors=min(24,len(idx)),algorithm='auto',n_jobs=1).fit(coords[idx])
            dd=self.fit.next_delta.to_numpy(float)[idx].copy()
            self.means[month]=float(np.mean(dd))
            if shuffle_seed is not None:
                rng=np.random.default_rng(int(shuffle_seed)+month*113)
                dd=rng.permutation(dd)
            self.delta[month]=dd
    def forecast_one(self,history,month0,idx,stage_id,method,k=12,tau=.4,freeze=False,steps=3,diag=False):
        rng=np.random.default_rng(SEED+stage_id*1000000+int(idx))
        curr=np.broadcast_to(np.asarray(history,dtype=float).reshape(1,13),(PARTICLES,13)).copy()
        origin=float(curr[0,-1]);checkpoint=[]
        if freeze:root_coord=features(curr,month0)[0]
        for hop in range(steps):
            month=(month0+hop)%12
            u=rng.random(PARTICLES)
            dlt=self.delta[month]
            if method=='season_portal':
                chosen=np.minimum((u*len(dlt)).astype(int),len(dlt)-1)
            else:
                st=root_coord if freeze else features(curr,month)[0]
                dis,ind=self.nn[month].kneighbors(self.scaler.transform(st),n_neighbors=k,return_distance=True)
                weights=nn_weights(dis,tau)
                chosen_local=np.minimum((u[:,None]>np.cumsum(weights,axis=1)).sum(axis=1),k-1)
                chosen=ind[np.arange(PARTICLES),chosen_local]
            increment=dlt[chosen] # equivalent to seasonal mean + (sampled delta - seasonal mean)
            curr=np.column_stack((curr[:,1:],curr[:,-1]+increment))
            if diag and hop+1 in [1,3,12,25,50,100]:
                checkpoint.append({'hop':hop+1,'mean_anomaly':float(curr[:,-1].mean()),
                    'std_anomaly':float(curr[:,-1].std()),'outside_training_range':float(np.mean((curr[:,-1]<-2.18)|(curr[:,-1]>2.21)))})
        event=(curr[:,-1]-origin)>=EVENT_THRESHOLD
        return (float((event.sum()+0.5)/(PARTICLES+1)),checkpoint)

    def forecast(self,frame,series,stage_id,method,k=12,tau=.4,freeze=False,steps=3):
        forecasts=[]
        for rec in frame.itertuples(index=False):
            history=series[rec.idx-12:rec.idx+1]
            pr,_=self.forecast_one(history,rec.month,rec.idx,stage_id,method,k,tau,freeze,steps)
            forecasts.append(pr)
        return np.asarray(forecasts,float)


def predict(cfg,fit,evalset,series,stage_id,kernel=None):
    name=cfg['method'];start=time.perf_counter()
    yf=fit.target.to_numpy(int)
    if name=='constant':
        p=np.full(len(evalset),float(yf.mean()))
        return p,{'fit_seconds':0.,'predict_seconds':0.}
    if name in ['season_portal','state_portal']:
        ker=kernel if kernel is not None else MonthKernel(fit)
        train_s=time.perf_counter()-start;start=time.perf_counter()
        p=ker.forecast(evalset,series,stage_id,name,cfg.get('k',12),cfg.get('tau',0.4))
        return p,{'fit_seconds':round(train_s,4),'predict_seconds':round(time.perf_counter()-start,4)}
    if name=='direct_analog':
        scaler=StandardScaler().fit(fit[FEATURES]);X=scaler.transform(fit[FEATURES]);Q=scaler.transform(evalset[FEATURES])
        nn=NearestNeighbors(n_neighbors=cfg['k'],n_jobs=1).fit(X)
        fit_time=time.perf_counter()-start;start=time.perf_counter()
        d,ind=nn.kneighbors(Q)
        p=np.clip(np.sum(nn_weights(d,cfg['tau'])*yf[ind],axis=1),1e-6,1-1e-6)
        return p,{'fit_seconds':round(fit_time,4),'predict_seconds':round(time.perf_counter()-start,4)}
    if name in ['logistic','calendar_logistic']:
        model=make_pipeline(StandardScaler(),LogisticRegression(C=cfg['C'],max_iter=750,random_state=SEED))
        cols=CAL_COLS if name=='calendar_logistic' else FEATURES
    elif name=='random_forest':
        cols=FEATURES; model=RandomForestClassifier(n_estimators=160,min_samples_leaf=cfg['min_samples_leaf'],random_state=SEED,n_jobs=1)
    elif name=='hist_boost':
        cols=FEATURES; model=HistGradientBoostingClassifier(max_iter=140,learning_rate=.05,max_leaf_nodes=cfg['max_leaf_nodes'],min_samples_leaf=18,l2_regularization=1,random_state=SEED)
    else:raise ValueError(name)
    model.fit(fit[cols].to_numpy(float),yf)
    fit_time=time.perf_counter()-start;start=time.perf_counter()
    p=model.predict_proba(evalset[cols].to_numpy(float))[:,1]
    return p,{'fit_seconds':round(fit_time,4),'predict_seconds':round(time.perf_counter()-start,4)}


def files(out):
    return out/'PREREGISTRATION.md',out/'source_noaa_nino34_1950_2025.txt',Path(__file__)


def validate(out):
    if (out/'locked_selection.json').exists():raise RuntimeError('Locked selection exists; will not overwrite')
    protocol,source,script=files(out)
    vals,dates=data(source)
    # Holdout labels are NOT even constructed in this phase.
    limit=np.flatnonzero(dates<=pd.Timestamp('2013-12-01'))[-1]+1
    pre=make_rows(vals[:limit],dates[:limit],cutoff='2013-12-01')
    train,val,notest=partition(pre)
    assert len(notest)==0 and val.target_date.max()<='2013-12-01'
    val_y=val.target.to_numpy(int)
    grid_records=[];selected={}
    for name,configs in grid().items():
        sub=[]
        for cfg in configs:
            p,timing=predict(cfg,train,val,vals[:limit],stage_id=1)
            row={'family':name,'config':cfg,'validation':score(val_y,p),**timing}
            grid_records.append(row);sub.append(row)
        pick=min(sub,key=lambda r:(r['validation']['brier'],json.dumps(r['config'],sort_keys=True)))
        selected[name]=pick['config']
        print('VALIDATED',name,'Brier',pick['validation']['brier'],'config',json.dumps(pick['config']))
    fit_info={'numpy':np.__version__,'pandas':pd.__version__,'sklearn':sklearn.__version__,
        'scipy':scipy.__version__,'python':platform.python_version()}
    lock={'status':'FROZEN_VALIDATION','protocol_sha256':SHA(protocol.read_bytes()),
          'source_sha256':SHA(source.read_bytes()),'code_sha256':SHA(script.read_bytes()),
          'date':'2026-11-03','source':'NOAA PSL Niño3.4 ERSSTv6 monthly anomaly, 1950–2025',
          'partitions':{'train':len(train),'validation':len(val),'holdout':'NOT MATERIALIZED'},
          'fit_info':fit_info,'seeds':{'base':SEED,'shuffle':[20261120+i for i in range(5)],'bootstrap':20261106},
          'selected':selected,'validation_grid':grid_records,
          'note':'No test labels or test metrics were created during validation stage'}
    (out/'validation_grid.json').write_text(json.dumps(grid_records,indent=2)+'\n')
    (out/'locked_selection.json').write_text(json.dumps(lock,indent=2)+'\n')
    print('FROZEN',len(train),len(val),'TEST UNOPENED')
    return lock


def year_bootstrap(df,p,q,nrep=5000,seed=20261106):
    yrs=df.issue_year.to_numpy(int);yy=df.target.to_numpy(int)
    uniq=np.unique(yrs);parts=[np.flatnonzero(yrs==k) for k in uniq]
    diff=(p-yy)**2-(q-yy)**2
    rng=np.random.default_rng(seed);sample=np.empty(nrep)
    for i in range(nrep):
        inds=np.concatenate([parts[j] for j in rng.integers(0,len(parts),size=len(parts))])
        sample[i]=float(diff[inds].mean())
    return {'year_blocks':list(map(int,uniq)),'replicates':nrep,
        'portal_minus_comparator':round(float(diff.mean()),8),
        'ci95':[round(float(x),8) for x in np.percentile(sample,[2.5,97.5])],
        'convincing_gain_by_protocol':bool(float(diff.mean())<=-0.005 and float(np.percentile(sample,97.5))<0)}


def evaluate(out):
    if (out/'test_predictions.csv').exists():raise RuntimeError('Holdout already scored; cannot overwrite')
    protocol,source,script=files(out)
    lock=json.loads((out/'locked_selection.json').read_text())
    for key,path in [('protocol_sha256',protocol),('source_sha256',source),('code_sha256',script)]:
        if SHA(path.read_bytes())!=lock[key]:raise RuntimeError('Hash mismatch: '+key)
    vals,dates=data(source)
    full=make_rows(vals,dates)
    train,val,test=partition(full)
    assert [len(train),len(val)]==[lock['partitions'][z] for z in ['train','validation']]
    assert test.issue_date.min()>='2014-01-01' and test.target_date.max()<='2025-12-01'
    fit=pd.concat([train,val],ignore_index=True)
    pred=test[['issue_date','target_date','issue_year','month','target']].copy().reset_index(drop=True)
    report={};probs={}
    kernel=MonthKernel(fit)
    for name,cfg in lock['selected'].items():
        p,timing=predict(cfg,fit,test,vals,stage_id=2,kernel=kernel)
        probs[name]=p;pred['prob_'+name]=p
        report[name]={'config':cfg,'metrics':score(test.target.to_numpy(int),p),**timing}
        print('HOLDOUT',name,'Brier',report[name]['metrics']['brier'])
    cfg=lock['selected']['state_portal'];p=probs['state_portal']
    shuffles=[]
    for rep,seed in enumerate(lock['seeds']['shuffle']):
        k=MonthKernel(fit,shuffle_seed=seed)
        ps=k.forecast(test,vals,2,'state_portal',cfg['k'],cfg['tau'])
        shuffles.append(ps)
        pred['prob_shuffled_'+str(rep)]=ps
    pp=np.column_stack(shuffles)
    shuffled_error_each=np.mean((pp-test.target.to_numpy(int)[:,None])**2,axis=0)
    # Compare per-case mean of *individual* shuffle squared errors (not error of mean probability).
    y=test.target.to_numpy(int)
    placebo_case_loss=np.mean((pp-y[:,None])**2,axis=1)
    portal_case_loss=(p-y)**2
    years=test.issue_year.to_numpy(int);uniq=np.unique(years);blocks=[np.flatnonzero(years==k) for k in uniq]
    rng=np.random.default_rng(20261106);bs=[]
    for _ in range(5000):
        sel=np.concatenate([blocks[j] for j in rng.integers(len(blocks),size=len(blocks))])
        bs.append(float(np.mean(portal_case_loss[sel]-placebo_case_loss[sel])))
    ci_shuf=np.percentile(bs,[2.5,97.5]);diff_shuf=float(np.mean(portal_case_loss-placebo_case_loss))
    pf=kernel.forecast(test,vals,2,'state_portal',cfg['k'],cfg['tau'],freeze=True)
    pred['prob_frozen_root_frame']=pf
    # Label shuffle control: conventional logistic with shuffled targets, no new selection.
    rnglab=np.random.default_rng(20261107)
    labfit=fit.copy();labfit['target']=rnglab.permutation(labfit.target.to_numpy(int))
    plab,_=predict(lock['selected']['logistic'],labfit,test,vals,stage_id=2)
    pred['prob_logistic_label_shuffle']=plab
    # Strong conventional comparator chosen ONLY from validation rankings.
    conventional=['calendar_logistic','logistic','random_forest','hist_boost','direct_analog']
    def validation_brier(name):
        return next(row['validation']['brier'] for row in lock['validation_grid']
             if row['family']==name and row['config']==lock['selected'][name])
    preselected=min(conventional,key=lambda x:(validation_brier(x),x))
    bs_calendar=year_bootstrap(test,p,probs['season_portal'])
    bs_conventional=year_bootstrap(test,p,probs[preselected])
    best_test=min(conventional,key=lambda x:report[x]['metrics']['brier'])
    good_shuf=bool(diff_shuf<=-0.005 and ci_shuf[1]<0)
    # Long chain diagnostics from prespecified VALIDATION years, never future-scored.
    ids=[int(val.iloc[z].idx) for z in [0,len(val)//2,len(val)-1]]
    long=[]
    for i in ids:
        m=int(dates[i].month-1);_,checks=kernel.forecast_one(vals[i-12:i+1],m,i,stage_id=3,
                                  method='state_portal',k=cfg['k'],tau=cfg['tau'],steps=100,diag=True)
        long.append({'issue_date':str(dates[i].date()),'checkpoints':checks})
    pred.to_csv(out/'test_predictions.csv',index=False,float_format='%.10g')
    full.assign(split=np.where(full.issue_date.isin(test.issue_date),'test',
           np.where(full.issue_date.isin(val.issue_date),'validation',
             np.where(full.issue_date.isin(train.issue_date),'train','excluded')))).to_csv(out/'all_feature_records.csv',index=False)
    results={'title':'SRDE P4 state-conditioned portal vs seasonal and shuffle controls',
        'date':'2026-11-03','status':'ONE_RETROSPECTIVE_HOLDOUT_SCORED',
        'source':'NOAA PSL Niño3.4 ERSSTv6 1950-2025, 1981-2010 anomaly reference',
        'source_sha256':lock['source_sha256'],'protocol_sha256':lock['protocol_sha256'],
        'code_sha256':lock['code_sha256'],
        'dataset':{'raw_months':int(len(vals)),'train':int(len(train)),
            'validation':int(len(val)),'test':int(len(test)),
            'test_start':test.issue_date.min(),'test_end':test.issue_date.max(),
            'test_positive_rate':float(y.mean())},
        'methods':report,'primary_A_state_vs_season':bs_calendar,
        'primary_B_state_vs_five_month_shuffles':{
            'shuffled_brier_each':list(map(float,shuffled_error_each)),
            'average_shuffled_brier':float(np.mean(shuffled_error_each)),
            'state_portal_brier':float(np.mean(portal_case_loss)),
            'difference':diff_shuf,'ci95_year_block':list(map(float,ci_shuf)),
            'convincing_gain_by_protocol':good_shuf},
        'secondary_C_state_vs_validation_selected_conventional':{'name':preselected,**bs_conventional},
        'secondary_D_frozen_frame':score(y,pf),
        'negative_label_shuffle':score(y,plab),
        'best_holdout_conventional_descriptive':{'name':best_test,'brier':report[best_test]['metrics']['brier']},
        'hundred_step_validation_era_stability_not_forecasts':long,
        'interpretation_limit':['Historical retrospective observation, no contemporaneous real-time data vintage',
          'Calendar monthly anomalies may have residual seasonality','Nino3.4 related to P3 Nino1+2 but new era and data',
          'No human meaning or feeling states','Overlapping three-month targets are not independent',
          'Year bootstrap limited by holdout duration','No claim of novel probabilistic theorem']}
    (out/'results.json').write_text(json.dumps(results,indent=2)+'\n')
    assert len(pred)==len(test)
    for name,q in probs.items():
        assert abs(float(np.mean((q-y)**2))-report[name]['metrics']['brier'])<6e-8
    print('PRIMARY A',bs_calendar,'PRIMARY B',results['primary_B_state_vs_five_month_shuffles'])
    return results


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--stage',choices=['validate','evaluate','selftest'],required=True)
    ap.add_argument('--out',type=Path,required=True)
    args=ap.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    if args.stage=='validate':validate(args.out)
    elif args.stage=='evaluate':evaluate(args.out)
    else:
        # Only non-holdout algebraic, shape and deterministic checks.
        h=np.linspace(-1,1,13);a,b=features(h,3)
        assert a.shape==(1,7) and b.shape==(1,4)
        assert np.allclose(nn_weights(np.array([[0.1,0.2,0.3]]),.5).sum(axis=1),1)
        assert score([0,1],[.25,.75])['brier']==.0625
        from tempfile import TemporaryDirectory
        with TemporaryDirectory() as td:
            toy=pd.DataFrame({'month':np.tile(np.arange(12),36),
                              'next_delta':np.tile(np.linspace(-.5,.5,12),36),
                              **{col:np.linspace(-1,1,432)+i*.01 for i,col in enumerate(STATE_COLS)}})
            mm=MonthKernel(toy,shuffle_seed=20261120)
            assert all(abs(mm.means[m]-float(toy[toy.month==m].next_delta.mean()))<1e-12 for m in range(12))
        print('SELFTEST OK')

if __name__=='__main__':main()
