#!/usr/bin/env python3
"""SRDE-P5: ordered portal residue, valence-conditioned contraction, and reverse instability.

Synthetic controlled mathematics only. No real-world causality or mental-state inference.
Reproducible, CPU-only. Frozen protocol PREREGISTRATION.md.
"""
from __future__ import annotations
import argparse, hashlib, json, math, platform, time
from pathlib import Path
import numpy as np
import scipy
from scipy.special import ndtr

SEED=20261103
N=4096
DEPTH=100
NOISE=0.04
REVERSE_SIGMA=1e-4
BOOT=2000


def sha(p:Path):return hashlib.sha256(p.read_bytes()).hexdigest()


def endpoint(x,u,v,a,order,depth=DEPTH):
    """Reference recurrence. AB means A first, then B; BA inverse ordering."""
    xx=np.asarray(x,dtype=float).copy()
    alpha=np.asarray(a).reshape(-1,1)
    for i in range(depth):
        anchor=u if ((i%2==0)==(order=='AB')) else v
        xx=alpha*xx+(1-alpha)*anchor
    return xx


def both_endpoints(x,u,v,a):
    """Independent closed form, compared with recurrence (do not use as fit)."""
    aa=np.asarray(a).reshape(-1,1)
    old=(aa**DEPTH)*x
    mass=(1-aa**DEPTH)/(1+aa)
    ab=old+mass*(aa*u+v)
    ba=old+mass*(aa*v+u)
    return ab,ba


def metrics(y,p):
    pp=np.clip(p,1e-12,1-1e-12)
    return {'brier':float(np.mean((pp-y)**2)),
            'log_loss':float(-np.mean(y*np.log(pp)+(1-y)*np.log(1-pp))),
            'accuracy_at_0_5':float(np.mean((pp>=0.5)==y))}


def conf_interval(d,seed=20261104):
    rng=np.random.default_rng(seed)
    n=len(d)
    vals=np.empty(BOOT)
    for i in range(BOOT):vals[i]=float(d[rng.integers(0,n,n)].mean())
    return list(map(float,np.percentile(vals,[2.5,97.5])))


def rx(angle):
    c,s=np.cos(angle),np.sin(angle)
    return np.array([[1,0,0],[0,c,-s],[0,s,c]])


def ry(angle):
    c,s=np.cos(angle),np.sin(angle)
    return np.array([[c,0,s],[0,1,0],[-s,0,c]])


def run(out:Path):
    t0=time.perf_counter()
    out.mkdir(parents=True,exist_ok=True)
    protocol=out/'PREREGISTRATION.md'
    assert protocol.exists(), 'Preregistered protocol missing'
    rng=np.random.default_rng(SEED)
    x=rng.normal(size=(N,3))
    u=rng.normal(size=(N,3))
    v=rng.normal(size=(N,3))
    too_close=np.linalg.norm(v-u,axis=1)<0.05
    while too_close.any():
        v[too_close]=rng.normal(size=(int(too_close.sum()),3))
        too_close=np.linalg.norm(v-u,axis=1)<0.05
    w=rng.normal(size=(N,3));w=w/np.linalg.norm(w,axis=1,keepdims=True)
    f=rng.choice(np.array([0.,0.5,1.]),size=N)
    a=0.72+0.18*f
    orders=rng.choice(np.array(['AB','BA']),size=N)
    eps=rng.normal(scale=NOISE,size=N)

    # Numerically independent methods: recurrence and closed-form two-step block.
    ab=endpoint(x,u,v,a,'AB')
    ba=endpoint(x,u,v,a,'BA')
    cab,cba=both_endpoints(x,u,v,a)
    max_formula_error=float(max(np.max(np.abs(ab-cab)),np.max(np.abs(ba-cba))))
    theo_delta=(1-a**DEPTH)[:,None]*((1-a)/(1+a))[:,None]*(v-u)
    residual=ab-ba
    max_resid_error=float(np.max(np.abs(residual-theo_delta)))
    norm_residual=np.linalg.norm(residual,axis=1)/np.linalg.norm(v-u,axis=1)
    theory_ratio=(1-a**DEPTH)*(1-a)/(1+a)
    assert max_formula_error<1e-11 and max_resid_error<1e-11
    assert np.max(np.abs(norm_residual-theory_ratio))<1e-11

    anchor_same=endpoint(x,u,u,a,'AB')
    anchor_same_reverse=endpoint(x,u,u,a,'BA')
    commute_null=float(np.max(np.abs(anchor_same-anchor_same_reverse)))
    assert commute_null<1e-12

    # Synthetic event is caused by ordered terminal x PLUS observational noise.
    actual=np.where((orders=='AB')[:,None],ab,ba)
    y=(np.einsum('ij,ij->i',actual,w)+eps>0).astype(int)
    mab=np.einsum('ij,ij->i',ab,w)
    mba=np.einsum('ij,ij->i',ba,w)
    pab=ndtr(mab/NOISE)
    pba=ndtr(mba/NOISE)
    p_ordered=np.where(orders=='AB',pab,pba)
    p_unordered=(pab+pba)/2
    p_wrong=np.where(orders=='AB',pba,pab)
    p_root=ndtr(np.einsum('ij,ij->i',(a**DEPTH)[:,None]*x,w)/NOISE)
    p_half=np.full(N,0.5)
    # Closed-form method uses identical information, not a weaker baseline.
    pcab=ndtr(np.einsum('ij,ij->i',cab,w)/NOISE)
    pcba=ndtr(np.einsum('ij,ij->i',cba,w)/NOISE)
    p_closed=np.where(orders=='AB',pcab,pcba)
    assert np.max(np.abs(p_closed-p_ordered))<1e-11

    score={
        'srde_order_aware':metrics(y,p_ordered),
        'conventional_order_aware_closed_form':metrics(y,p_closed),
        'order_blind_bayesian_mixture':metrics(y,p_unordered),
        'wrong_order_negative_control':metrics(y,p_wrong),
        'root_only_no_anchor':metrics(y,p_root),
        'uninformed_0_5':metrics(y,p_half)
    }
    d=(p_ordered-y)**2-(p_unordered-y)**2
    ci=conf_interval(d)

    # Reverse exact maps in reverse order; deliberately add measurement error.
    rr=np.random.default_rng(SEED+20)
    rev=[]
    for ff in (0.,0.5,1.):
        k=256;aa=float(.72+.18*ff)
        xx=rr.normal(size=(k,3));uu=rr.normal(size=(k,3));vv=rr.normal(size=(k,3))
        yy=endpoint(xx,uu,vv,np.full(k,aa),'AB')
        noise=rr.normal(scale=REVERSE_SIGMA,size=(k,3))
        def inverse(end):
            z=end.copy()
            for i in reversed(range(DEPTH)):
                anchor=uu if i%2==0 else vv
                z=(z-(1-aa)*anchor)/aa
            return z
        zr=inverse(yy+noise)
        z0=inverse(yy)
        measured=np.linalg.norm(zr-xx,axis=1)
        theoretical=np.linalg.norm(noise,axis=1)*(aa**(-DEPTH))
        no_noise=np.linalg.norm(z0-xx,axis=1)
        rev.append({'F':ff,'a':aa,'root_memory_coefficient':aa**DEPTH,
           'inverse_noise_condition_number':aa**(-DEPTH),
           'median_observed_root_error':float(np.median(measured)),
           'median_predicted_noise_amplification':float(np.median(theoretical)),
           'median_noiseless_float_roundoff_error':float(np.median(no_noise)),
           'median_observed_over_theoretical':float(np.median(measured/theoretical))})

    # Different-axis orientations are noncommutative; same-axis null.
    rotation_rng=np.random.default_rng(SEED+30)
    angle1=rotation_rng.uniform(.15,1.05,size=1024)
    angle2=rotation_rng.uniform(.15,1.05,size=1024)
    comm=[];null=[]
    for t,s in zip(angle1,angle2):
        A=rx(t);B=ry(s);C=rx(s)
        comm.append(np.linalg.norm(B@A-A@B,ord='fro'))
        null.append(np.linalg.norm(C@A-A@C,ord='fro'))
    comm=np.asarray(comm);null=np.asarray(null)

    # Store independent rows for full audit / reproducibility.
    import csv
    csv_path=out/'synthetic_worlds_4096.csv'
    with csv_path.open('w',newline='',encoding='utf-8') as handle:
        writer=csv.writer(handle)
        columns=['id','F','alpha','order','y','noise']+[f'x0_{i}' for i in range(3)]+[f'u_{i}' for i in range(3)]+[f'v_{i}' for i in range(3)]+[f'w_{i}' for i in range(3)]+['p_ordered','p_closed','p_unordered','p_wrong','p_root','p_half','normalized_residue','theory_ratio']
        writer.writerow(columns)
        for i in range(N):
            row=[i,f[i],a[i],orders[i],y[i],eps[i],*x[i],*u[i],*v[i],*w[i],p_ordered[i],p_closed[i],p_unordered[i],p_wrong[i],p_root[i],p_half[i],norm_residual[i],theory_ratio[i]]
            writer.writerow([str(z) for z in row])

    f_rows=[]
    for ff in (0.,.5,1.):
        aa=.72+.18*ff
        mask=f==ff
        f_rows.append({'F':ff,'a':aa,'worlds':int(mask.sum()),
           'normalized_order_residue_mean':float(norm_residual[mask].mean()),
           'analytic_ratio':float((1-aa**100)*(1-aa)/(1+aa)),
           'root_memory_after_100':float(aa**100)})

    result={
       'title':'SRDE-P5 portal ordering and reverse-path instability',
       'experiment_date':'2026-11-03',
       'status':'synthetic_analytic_experiment_not_real_world_prediction',
       'seed':SEED,'worlds':N,'depth':DEPTH,'protocol_sha256':sha(protocol),
       'source_sha256':sha(Path(__file__)), 'synthetic_worlds_csv_sha256':sha(csv_path),
       'python':platform.python_version(),'numpy':np.__version__,'scipy':scipy.__version__,
       'equations':{
         'A':'a*x+(1-a)*u','B':'a*x+(1-a)*v','a_F':'0.72+0.18*F',
         'AB_minus_BA_at_100':'(1-a**100)*(1-a)/(1+a)*(v-u)',
         'root_memory':'a**100','backward_noise_gain':'a**(-100)'},
       'numeric_verification':{'max_forward_formula_coordinate_error':max_formula_error,
         'max_portal_residual_coordinate_error':max_resid_error,
         'max_commuting_same_anchor_error':commute_null,
         'by_valence':f_rows},
       'forecasts':{'event_definition':'1[projection of 100-step terminal + Normal(0,0.04^2) > 0]',
         'worlds':N,'metrics':score,
         'primary_ordered_minus_unordered_brier':float(d.mean()),
         'world_bootstrap_ci95':ci,'bootstrap_replicates':BOOT,
         'claim_of_improvement_on_constructed_mechanism':bool(ci[1]<0)},
       'reverse':{'endpoint_3d_noise_std':REVERSE_SIGMA,'worlds_per_F':256,'observations':rev},
       'orientation':{'worlds':1024,'different_axis_frobenius_residue_mean':float(comm.mean()),
         'different_axis_frobenius_residue_min':float(comm.min()),
         'same_axis_null_max':float(null.max())},
       'important_limits':['The ordered synthetic event was generated by the same known affine equations; score advantage is designed into the task',
         'The identical conventional order-aware closed form ties the SRDE operator',
         'Same-anchor and same-axis controls show no effect',
         'F is a simulated coordinate, not measured feeling',
         'These maps illustrate path memory, not a novel theorem or evidence that the brain works this way',
         'Reverse-map instability depends on numerical noise and strong contraction; not a proof that backward reasoning is impossible generally'],
       'elapsed_seconds':float(time.perf_counter()-t0)}
    (out/'results.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    return result


def main():
    pa=argparse.ArgumentParser();pa.add_argument('--out',type=Path,required=True)
    args=pa.parse_args()
    result=run(args.out)
    print('P5 runs',result['worlds'],'depth',result['depth'])
    print('FORECAST SCORES',json.dumps(result['forecasts'],indent=2))
    print('REVERSE',json.dumps(result['reverse']['observations'],indent=2))
    print('CHECKS',json.dumps(result['numeric_verification'],indent=2))

if __name__=='__main__':main()
