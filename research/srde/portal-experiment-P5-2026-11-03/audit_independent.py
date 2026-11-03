#!/usr/bin/env python3
"""Independently re-score frozen SRDE-P5 worlds. Never imports model code."""
from __future__ import annotations
import csv,hashlib,json,math,sys
from pathlib import Path
import numpy as np
from scipy.special import ndtr

BASE=Path(__file__).parent
R=json.loads((BASE/'results.json').read_text())
sha=lambda path:hashlib.sha256((BASE/path).read_bytes()).hexdigest()
assert sha('PREREGISTRATION.md')==R['protocol_sha256']
assert sha('srde_p5.py')==R['source_sha256']
assert sha('synthetic_worlds_4096.csv')==R['synthetic_worlds_csv_sha256']
with (BASE/'synthetic_worlds_4096.csv').open(newline='') as f:
    items=list(csv.DictReader(f))
assert len(items)==4096

def mat(prefix):
    return np.array([[float(row[f'{prefix}_{k}']) for k in range(3)] for row in items])

def arr(name,dtype=float):return np.array([dtype(row[name]) for row in items])
root=mat('x0');u=mat('u');v=mat('v');w=mat('w')
F=arr('F');alpha=arr('alpha');noise=arr('noise');y=arr('y',int)
order=np.array([i['order'] for i in items])
assert set(order)=={'AB','BA'}
assert np.array_equal(arr('id',int),np.arange(4096))
assert np.array_equal(np.unique(F),np.array([0.,0.5,1.]))
assert np.max(np.abs(alpha-(.72+.18*F)))<1e-15
assert np.max(np.abs(np.linalg.norm(w,axis=1)-1))<1e-13
assert np.min(np.linalg.norm(v-u,axis=1))>=.05
m=(1-alpha**100)/(1+alpha)
xab=(alpha**100)[:,None]*root+m[:,None]*(alpha[:,None]*u+v)
xba=(alpha**100)[:,None]*root+m[:,None]*(alpha[:,None]*v+u)
z=np.where((order=='AB')[:,None],xab,xba)
assert np.array_equal(y,(np.sum(z*w,axis=1)+noise>0).astype(int))
pa=ndtr(np.einsum('ij,ij->i',xab,w)/.04)
pb=ndtr(np.einsum('ij,ij->i',xba,w)/.04)
p_order=np.where(order=='AB',pa,pb)
p_closed=p_order.copy()
p_unorder=(pa+pb)/2
p_wrong=np.where(order=='AB',pb,pa)
p_root=ndtr(np.einsum('ij,ij->i',(alpha**100)[:,None]*root,w)/.04)
p_half=np.full(len(y),.5)
mods={'srde_order_aware':p_order,'conventional_order_aware_closed_form':p_closed,
 'order_blind_bayesian_mixture':p_unorder,'wrong_order_negative_control':p_wrong,
 'root_only_no_anchor':p_root,'uninformed_0_5':p_half}
cols={'srde_order_aware':'p_ordered','conventional_order_aware_closed_form':'p_closed',
 'order_blind_bayesian_mixture':'p_unordered','wrong_order_negative_control':'p_wrong',
 'root_only_no_anchor':'p_root','uninformed_0_5':'p_half'}
sc={}
for name,p in mods.items():
    recorded=arr(cols[name]);assert np.max(np.abs(recorded-p))<1e-13,name
    q=np.clip(p,1e-12,1-1e-12)
    brier=float(np.mean((q-y)**2))
    loss=float(-np.mean(y*np.log(q)+(1-y)*np.log(1-q)))
    accuracy=float(np.mean((q>=.5)==y))
    sc[name]={'brier':brier,'log_loss':loss,'accuracy_at_0_5':accuracy}
    for metric,value in sc[name].items():
        assert abs(value-R['forecasts']['metrics'][name][metric])<1e-11,(name,metric)
resratio=np.linalg.norm(xab-xba,axis=1)/np.linalg.norm(v-u,axis=1)
theory=(1-alpha**100)*(1-alpha)/(1+alpha)
assert np.max(np.abs(resratio-theory))<1e-12
assert np.max(np.abs(arr('normalized_residue')-resratio))<1e-12
assert np.max(np.abs(arr('theory_ratio')-theory))<1e-12
assert abs(R['numeric_verification']['max_commuting_same_anchor_error'])<1e-12
for case in R['numeric_verification']['by_valence']:
    mask=F==case['F']
    assert int(mask.sum())==case['worlds']
    assert abs(float(np.mean(resratio[mask]))-case['normalized_order_residue_mean'])<1e-12
    assert abs((case['a']**100)-case['root_memory_after_100'])<1e-12
# Independent resampling using same prespecified RNG seed, but fresh scoring algebra.
diff=(p_order-y)**2-(p_unorder-y)**2
samples=np.empty(2000)
rng=np.random.default_rng(20261104)
for j in range(2000):
    picks=rng.choice(len(y),len(y),replace=True)
    samples[j]=float(np.sum(diff[picks])/len(picks))
ci=list(map(float,np.quantile(samples,[.025,.975])))
assert np.allclose(ci,R['forecasts']['world_bootstrap_ci95'],rtol=0,atol=1e-13)
assert abs(float(diff.mean())-R['forecasts']['primary_ordered_minus_unordered_brier'])<1e-13
assert abs(sc['srde_order_aware']['brier']-sc['conventional_order_aware_closed_form']['brier'])<1e-15
# Correctly limit inference: this is known-mechanism synthetic forecasting.
notes=['P5 100-level portal effect is an algebraic property of predefined affine maps, not an empirical new law.',
       'The strongest matched conventional order-aware closed form ties SRDE exactly.',
       'The forecast task is generated from known ordered maps and is not a genuine external prediction test.',
       'Subjective feelings, physical brains, independent real-world behavior, and universal meaning were not observed.']
final={'status':'PASS','worlds':len(y),'depth':100,'sha256_checks':{'protocol':True,'code':True,'worlds_csv':True},
       'individual_predictions_reconstructed':True,'all_metrics_recomputed':True,
       'independent_bootstrap_ci95':ci,'paired_brier_difference':float(diff.mean()),
       'max_formula_residual_error_from_csv':float(np.max(np.abs(resratio-theory))),
       'matched_conventional_tie_verified':True,'scoring':sc,'limitations':notes}
(BASE/'audit_independent.json').write_text(json.dumps(final,indent=2)+'\n',encoding='utf-8')
print('AUDIT PASS: 4096 cases, exact hashes, 100 levels, six models, paired CI and controls')
print('Brier comparison',sc['srde_order_aware']['brier'],sc['order_blind_bayesian_mixture']['brier'])
