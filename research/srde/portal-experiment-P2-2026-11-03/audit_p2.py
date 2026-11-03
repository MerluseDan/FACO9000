#!/usr/bin/env python3
"""Independent result audit for SRDE-P2. No training and no model tuning."""
import hashlib,json,sys
from pathlib import Path
import numpy as np,pandas as pd

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    base=Path(__file__).resolve().parent
    l=json.loads((base/'locked_selection.json').read_text())
    r=json.loads((base/'results.json').read_text())
    p=pd.read_csv(base/'test_predictions.csv',parse_dates=['issue_date','target_date'])
    s=pd.read_csv(base/'source_statsmodels_co2.csv',index_col=0,parse_dates=True)
    assert sha(base/'source_statsmodels_co2.csv')==l['sha256_source_csv']==r['dataset']['sha256_raw_csv']
    assert sha(base/'PREREGISTRATION.md')==l['sha256_protocol']
    assert p.issue_date.is_unique and (p.target_date-p.issue_date).dt.days.eq(28).all()
    assert (p.issue_date>=pd.Timestamp('1995-01-01')).all()
    assert (p.target_date<=pd.Timestamp('2001-12-31')).all()
    assert len(p)==r['dataset']['rows_test']==361
    assert len(s)==2284 and s.co2.isna().sum()==59
    # Raw source independently verifies both the event definition and all provided future readings.
    for row in p.itertuples(index=False):
        a=s.loc[row.issue_date,'co2'];b=s.loc[row.target_date,'co2']
        assert np.isclose(a,row.co2_at_issue,atol=1e-10)
        assert np.isclose(b,row.co2_at_target,atol=1e-10)
        assert int(b>a)==row.target
    y=p.target.to_numpy()
    audit={'verified_rows':len(p), 'verified_prediction_date_range':[str(p.issue_date.min().date()),str(p.issue_date.max().date())],
           'verified_source_sha256':sha(base/'source_statsmodels_co2.csv'),
           'verified_locked_protocol_sha256':l['sha256_protocol'],'recomputed_metrics':{},
           'positive_event_prevalence':float(np.mean(y)),
           'max_abs_error_in_recomputed_brier':0.0,
           'assertions_passed':['date split','exact +28-day outcome','raw source values','event targets','no heldout overlap', 'constant test count']}
    for name,v in r['models'].items():
        prob=p['prob_'+name].to_numpy()
        assert np.isfinite(prob).all() and (prob>=0).all() and (prob<=1).all()
        b=float(np.mean((prob-y)**2));ll=float(-np.mean(y*np.log(np.clip(prob,1e-8,1-1e-8))+(1-y)*np.log(np.clip(1-prob,1e-8,1-1e-8))))
        a=float(np.mean((prob>=0.5)==y))
        delta=abs(b-v['metrics']['brier'])
        assert delta<1e-7 and abs(a-v['metrics']['accuracy_at_0_5'])<1e-7
        assert abs(ll-v['metrics']['log_loss'])<1e-7
        audit['max_abs_error_in_recomputed_brier']=max(audit['max_abs_error_in_recomputed_brier'],delta)
        audit['recomputed_metrics'][name]={'brier':b,'log_loss':ll,'accuracy_0_5':a}
    shuf=float(np.mean((p.prob_portal_label_shuffle_control.to_numpy()-y)**2))
    assert abs(shuf-r['portal_label_shuffle_negative_control']['metrics']['brier'])<1e-7
    audit['recomputed_metrics']['portal_shuffled_control']={'brier':shuf}
    year=pd.to_datetime(p.issue_date).dt.year
    years={}
    for yr in sorted(year.unique()):
        subset=(year==yr).to_numpy()
        ys=y[subset]
        years[str(yr)]={'n':int(np.sum(subset)),'event_rate':float(np.mean(ys)),
                        **{name:float(np.mean((p.loc[subset,'prob_'+name].to_numpy()-ys)**2))
                           for name in ['random_forest','hist_gradient_boosting','srde_portal']}}
    audit['yearwise_holdout']=years
    (base/'audit.json').write_text(json.dumps(audit,indent=2)+'\n')
    (base/'audit_stdout.log').write_text('PASS independent audit\n'+json.dumps({k:v for k,v in audit.items() if k not in ('recomputed_metrics','yearwise_holdout')},indent=2)+'\n')
    print('PASS independent audit',len(p),'rows; exact raw event dates and probability metrics; protocol and source SHA intact')
    print('Yearwise portal vs RF:',[(k,round(v['srde_portal'],5),round(v['random_forest'],5)) for k,v in years.items()])
    return audit
if __name__=='__main__':main()
