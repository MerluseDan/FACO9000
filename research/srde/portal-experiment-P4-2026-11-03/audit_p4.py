#!/usr/bin/env python3
"""Independent audit of saved SRDE-P4 outputs. No model fitting or reuse of SRDE-P4 scoring code."""
import hashlib,json,math
from pathlib import Path
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parent
sha=lambda p: hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
lock=json.loads((ROOT/'locked_selection.json').read_text())
results=json.loads((ROOT/'results.json').read_text())
pred=pd.read_csv(ROOT/'test_predictions.csv')
raw=[]
for line in (ROOT/'source_noaa_nino34_1950_2025.txt').read_text().splitlines():
    values=line.split();raw.append((int(values[0]),list(map(float,values[1:]))))
assert len(raw)==76 and [r[0] for r in raw]==list(range(1950,2026))
series=np.array([q for _,vals in raw for q in vals])
assert len(series)==912
print('SOURCES')
checks={k:(sha(fn)==lock[k]) for k,fn in [
 ('protocol_sha256','PREREGISTRATION.md'),
 ('source_sha256','source_noaa_nino34_1950_2025.txt'),
 ('code_sha256','srde_p4.py')]}
assert all(checks.values()),checks
# Git blob hash matches the byte-exact NOAA source published before evaluation.
import subprocess
blob=subprocess.check_output(['git','hash-object',str(ROOT/'source_noaa_nino34_1950_2025.txt')]).decode().strip()
assert blob=='1baa53c6c65a9ce6f02e6f11dd3673d051c42963'
assert lock['partitions']['train']==621 and lock['partitions']['validation']==129
assert lock['partitions']['holdout']=='NOT MATERIALIZED'
assert len(pred)==141 and pred.issue_date.is_unique
assert pred.issue_date.iloc[0]=='2014-01-01' and pred.issue_date.iloc[-1]=='2025-09-01'
assert pred.target_date.iloc[-1]=='2025-12-01'
assert list(pred.issue_year.unique())==list(range(2014,2026))
dates=pd.date_range('1950-01-01','2025-12-01',freq='MS')
for row in pred.itertuples(index=False):
    ti=np.where(dates==pd.Timestamp(row.issue_date))[0];assert len(ti)==1
    i=int(ti[0]);assert str(dates[i+3].date())==row.target_date
    assert row.target==int(series[i+3]-series[i]>=.5)
y=pred.target.to_numpy(dtype=int)
assert int(y.sum())==29
assert all(x in pred.columns for x in ['prob_'+k for k in results['methods']])

scores={};warnings=[]
for name, entry in results['methods'].items():
    probs=pred['prob_'+name].to_numpy(float)
    assert np.all(np.isfinite(probs)) and probs.min()>=0 and probs.max()<=1
    brier=float(np.mean((probs-y)**2))
    loss=float(np.mean(-y*np.log(np.clip(probs,1e-8,1-1e-8))-(1-y)*np.log(np.clip(1-probs,1e-8,1-1e-8))))
    assert abs(brier-entry['metrics']['brier'])<2e-8,(name,brier,entry['metrics']['brier'])
    assert abs(loss-entry['metrics']['log_loss'])<2e-8,(name,loss,entry['metrics']['log_loss'])
    scores[name]=brier
assert results['dataset']['test']==141
assert abs(results['dataset']['test_positive_rate']-float(y.mean()))<1e-9
q=pred.prob_state_portal.to_numpy(float)
ps=pred.prob_season_portal.to_numpy(float)
shuffle_cols=[f'prob_shuffled_{j}' for j in range(5)]
shuffles=pred[shuffle_cols].to_numpy(float)
shuffle_briers=np.mean((shuffles-y[:,None])**2,axis=0)
assert np.allclose(shuffle_briers,results['primary_B_state_vs_five_month_shuffles']['shuffled_brier_each'],atol=1e-9)
assert abs(float(shuffle_briers.mean())-results['primary_B_state_vs_five_month_shuffles']['average_shuffled_brier'])<1e-9
assert abs(scores['state_portal']-results['primary_B_state_vs_five_month_shuffles']['state_portal_brier'])<1e-9
assert abs(scores['state_portal']-scores['season_portal']-results['primary_A_state_vs_season']['portal_minus_comparator'])<1e-8
assert abs(scores['state_portal']-float(shuffle_briers.mean())-results['primary_B_state_vs_five_month_shuffles']['difference'])<1e-9

# Repeat predeclared paired year bootstrap using a separately written implementation.
years=pred.issue_year.to_numpy(int)
parts={yr:np.flatnonzero(years==yr) for yr in range(2014,2026)}

def independent_year_bootstrap(delta,seed=20261106):
    rng=np.random.default_rng(seed)
    out=[]
    for _ in range(5000):
        selected_years=rng.integers(2014,2026,12)
        stacked=np.concatenate([parts[int(year)] for year in selected_years])
        out.append(float(np.sum(delta[stacked])/len(stacked)))
    return [float(v) for v in np.quantile(out,[.025,.975])]
A=(q-y)**2-(ps-y)**2
B=(q-y)**2-np.mean((shuffles-y[:,None])**2,axis=1)
conv_name=results['secondary_C_state_vs_validation_selected_conventional']['name']
assert conv_name=='hist_boost'
C=(q-y)**2-(pred['prob_'+conv_name].to_numpy(float)-y)**2
cA=independent_year_bootstrap(A)
cB=independent_year_bootstrap(B)
cC=independent_year_bootstrap(C)
for calced,record in [(cA,results['primary_A_state_vs_season']['ci95']),
                       (cB,results['primary_B_state_vs_five_month_shuffles']['ci95_year_block']),
                       (cC,results['secondary_C_state_vs_validation_selected_conventional']['ci95'])]:
    assert np.allclose(calced,record,atol=5e-6),(calced,record)

# Independent horizon and split boundary checks on all records.
allrec=pd.read_csv(ROOT/'all_feature_records.csv')
assert allrec.issue_date.is_unique
for subset,mask in [('train',allrec.split=='train'),('validation',allrec.split=='validation'),('test',allrec.split=='test')]:
    rows=allrec.loc[mask]
    assert len(rows)=={'train':621,'validation':129,'test':141}[subset]
assert (pd.to_datetime(allrec.loc[allrec.split=='train','target_date'])<=pd.Timestamp('2002-12-01')).all()
assert (pd.to_datetime(allrec.loc[allrec.split=='validation','target_date'])<=pd.Timestamp('2013-12-01')).all()
assert (pd.to_datetime(allrec.loc[allrec.split=='test','issue_date'])>=pd.Timestamp('2014-01-01')).all()
assert np.allclose(allrec['anomaly_now'].to_numpy(),[
  series[int((pd.Timestamp(d).year-1950)*12+(pd.Timestamp(d).month-1))] for d in allrec.issue_date])

# Observational caveats; not checked from experiment outputs alone.
warnings.extend([
 'This retrospective backtest uses NOAA historical archive rather than point-in-time vintage observations.',
 'NOAA ERSSTv6 monthly Niño3.4 anomalies and previous P3 Niño1+2 SST involve related ocean phenomena.',
 'Only twelve year clusters, overlapping three-month target windows; bootstrap inference exploratory.',
 'Long-chain stability is not 100-month forecast skill or evidence of universal semantic relatedness.',
 'A matched strong conventional direct analog has a slightly better descriptive holdout Brier score.',
 'The predeclared gain criterion is a decision rule, not independent statistical confirmation in another domain.'
])
out={'status':'PASS','audited_at':'2026-11-03','source_code_protocol_hash_checks':checks,
     'source_git_blob_sha':blob,'train_rows':621,'validation_rows':129,
     'holdout_rows':141,'holdout_positive_cases':int(y.sum()),'year_blocks':12,
     'brier_independently_recomputed':scores,
     'primary_A_delta':float(A.mean()),'primary_A_ci95':cA,
     'primary_B_delta':float(B.mean()),'primary_B_ci95':cB,
     'primary_C_validation_selected_name':conv_name,'primary_C_delta':float(C.mean()),'primary_C_ci95':cC,
     'holdout_forecasts_unchanged':True,'caveats':warnings}
(ROOT/'audit_independent.json').write_text(json.dumps(out,indent=2)+'\n')
print('AUDIT PASS',len(pred),'rows',int(y.sum()),'positives')
print('A',A.mean(),cA,'B',B.mean(),cB,'C',C.mean(),cC)
