#!/usr/bin/env python3
"""SRDE-P6: budgeted state snapshots for 100-step noncommuting Gaussian portal chains.

Frozen under PREREGISTRATION.md. All methods see the identical Gaussian model.
Usage:
 python srde_p6.py selftest --out /path
 python srde_p6.py validate --out /path
 python srde_p6.py evaluate --out /path
CPU-only: NumPy + SciPy. No real-world or subjective affect data.
"""
from __future__ import annotations
import argparse, csv, hashlib, json, math, sys, time
from pathlib import Path
import numpy as np

D=3; T=100; K=8; R=0.04; N_BOOT=5000
SCENARIOS=('steady','bursts','frames','decoys')
ETA_GRID=(0.0,0.5,1.0,2.0)
GAMMA_GRID=(0.0,0.5,1.0)
METHODS=('uniform','random','priority_only','risk_only','srde_hybrid','covariance_greedy')


def sha(b:bytes)->str:return hashlib.sha256(b).hexdigest()

def rot(axis,theta):
    s,c=math.sin(theta),math.cos(theta)
    if axis==0:return np.array([[1.,0,0],[0,c,-s],[0,s,c]])
    if axis==1:return np.array([[c,0,s],[0,1.,0],[-s,0,c]])
    return np.array([[c,-s,0],[s,c,0],[0,0,1.]])

def make_geometry(seed, scenario):
    """No true trajectory or latent innovations are generated here."""
    rng=np.random.default_rng(int(seed))
    A=np.empty((T,D,D));Q=np.empty_like(A); b=np.empty((T,D));w=np.ones(T+1)
    # Orientation changes are known at selection time; no access to random future state.
    for t in range(1,T+1):
        theta=float(rng.normal(0,.12)); phi=float(rng.normal(0,.11))
        if scenario=='frames' and (t in range(22,32) or t in range(60,68)):
            theta+=float(rng.choice([-1,1]))*.88
            phi+=float(rng.choice([-1,1]))*.68
        Ra=rot(0,theta)@rot(1,phi)@rot(2,float(rng.normal(0,.07)))
        Rb=rot(2,float(rng.normal(0,.1)))@rot(1,float(rng.normal(0,.08)))
        alphas=np.array([.79,.87,.94])+rng.uniform(-.045,.045,size=3)
        if scenario=='frames' and t in range(50,56):alphas=np.array([.67,.84,.95])
        A[t-1]=Ra@np.diag(alphas)@Rb
        risk_mult=1.0
        if scenario=='bursts' and (t in range(19,35) or t in range(65,75)):
            risk_mult=8.0
        elif scenario=='frames' and (t in range(22,32) or t in range(60,68)):
            risk_mult=3.0
        Q[t-1]=rot(2,theta)@np.diag([.012,.020,.016])@rot(2,theta).T*risk_mult
        b[t-1]=.025*rng.normal(size=3)
        if scenario=='bursts' and t in range(19,35):w[t]=3.0
        elif scenario=='frames' and t in range(22,32):w[t]=2.4
        elif scenario=='decoys' and (t in range(12,24) or t in range(72,83)):
            w[t]=3.5  # priority without an increase in process noise
        else:w[t]=float(1.0+.2*rng.uniform())
    w[0]=0;w[T]=0
    # Local portal orientation/branch order is noncommutative in general.
    return A,Q,b,w


def make_covariance(A,Q):
    P=[np.eye(D)]
    for t in range(T):
        p=A[t]@P[-1]@A[t].T+Q[t]
        P.append((p+p.T)*.5)
    C=np.empty(((T+1)*D,(T+1)*D),dtype=float)
    for s in range(T+1):
        ss=slice(D*s,D*s+D)
        C[ss,ss]=P[s]
        block=P[s]
        for t in range(s+1,T+1):
            block=block@A[t-1].T
            tt=slice(D*t,D*t+D)
            C[ss,tt]=block;C[tt,ss]=block.T
    return C


def score_weights(w):return np.repeat(w/D/float(np.sum(w)),D)

def all_index(times):
    return np.array([D*t+j for t in sorted(set(list(times)+[T])) for j in range(D)],dtype=int)

def posterior_risk(C,times,w,return_both=False):
    ix=all_index(times)
    G=C[:,ix]
    S=C[np.ix_(ix,ix)]+np.eye(len(ix))*R
    X=np.linalg.solve(S,G.T)  # dimension (27,303)
    lost=np.einsum('ij,ji->i',G,X)
    remaining=np.diag(C)-lost
    weighted=float(score_weights(w)@remaining)
    if return_both:
        ww=np.zeros(T+1);ww[1:T]=1.0
        return weighted,float(score_weights(ww)@remaining)
    return weighted

def posterior_gain(Ccur,t,w):
    ii=np.arange(D*t,D*t+D)
    G=Ccur[:,ii]
    S=Ccur[np.ix_(ii,ii)]+R*np.eye(D)
    H=G.T@(score_weights(w)[:,None]*G)
    return float(np.trace(np.linalg.solve(S,H)))

def covariance_greedy(C,w,K=K):
    # Conventional offline posterior-variance greedy method; no hidden states or noise.
    work=C.copy();chosen=[]
    def condition(t):
        nonlocal work
        ii=np.arange(D*t,D*t+D)
        G=work[:,ii].copy()
        SS=work[np.ix_(ii,ii)]+R*np.eye(D)
        work-=G@np.linalg.solve(SS,G.T)
        work=(work+work.T)*.5
    condition(T)  # common free terminal measurement
    for _ in range(K):
        best=max((t for t in range(1,T) if t not in chosen),key=lambda t:(posterior_gain(work,t,w),-t))
        chosen.append(best);condition(best)
    return sorted(chosen)

def quantile_schedule(mass,K=K):
    z=np.asarray(mass[1:T],float).copy()
    assert z.shape==(T-1,) and np.min(z)>=0
    z=np.maximum(z,1e-12)
    cum=np.cumsum(z); taken=set()
    for j in range(1,K+1):
        target=float(j*cum[-1]/(K+1))
        idx=int(np.searchsorted(cum,target))+1
        if idx in taken:
            idx=min((t for t in range(1,T) if t not in taken),key=lambda t:(abs(t-idx),t))
        taken.add(idx)
    return sorted(taken)

def known_scores(A,Q,w,eta=1.0,gamma=1.0):
    risk=np.array([0]+[float(np.trace(v)) for v in Q])
    risk[T]=0
    comm=np.zeros(T+1)
    for t in range(2,T):
        comm[t]=np.linalg.norm(A[t-1]@A[t-2]-A[t-2]@A[t-1],ord='fro')
    def norm(v):
        out=v.copy(); out[1:T]/=max(1e-12,float(np.mean(out[1:T])))
        return out
    return norm(risk),norm(w),norm(comm) if np.any(comm>0) else comm

def schedules(C,A,Q,w,seed,eta,gamma,K=K,greedy=True):
    risk,priority,comm=known_scores(A,Q,w)
    unif=np.rint(np.linspace(0,T,K+2)[1:-1]).astype(int).tolist()
    rng=np.random.default_rng(seed+500000)
    sched={
        'uniform':sorted(unif),
        'random':sorted(rng.choice(np.arange(1,T),size=K,replace=False).tolist()),
        'priority_only':quantile_schedule(priority,K),
        'risk_only':quantile_schedule(risk,K),
        'srde_hybrid':quantile_schedule(risk+eta*priority+gamma*comm,K),
    }
    if greedy:sched['covariance_greedy']=covariance_greedy(C,w,K)
    for name,sel in sched.items():assert len(sel)==K and len(set(sel))==K and min(sel)>=1 and max(sel)<T,(name,sel)
    return sched

def seeds(which):
    if which=='development':return [(960100+si*12+k,name) for si,name in enumerate(SCENARIOS) for k in range(12)]
    return [(970100+si*40+k,name) for si,name in enumerate(SCENARIOS) for k in range(40)]

def selftest():
    A,Q,b,w=make_geometry(960001,'frames')
    C=make_covariance(A,Q)
    assert C.shape==(303,303)
    assert np.max(np.abs(C-C.T))<1e-12
    assert np.linalg.eigvalsh(C)[0]>0
    zz=schedules(C,A,Q,w,960001,1,1,greedy=True)
    errs={m:posterior_risk(C,s,w) for m,s in zz.items()}
    assert errs['covariance_greedy']<=errs['uniform']+1e-10,errs
    assert all(len(v)==K for v in zz.values())
    a=np.eye(3)*.5; assert np.linalg.norm(a@a-a@a)==0
    print('SELFTEST PASS: SPD, all budgets, posterior trace, greedy vs uniform',json.dumps(errs))

def validate(out):
    assert not (out/'LOCKED_VALIDATION.json').exists()
    start=time.perf_counter();worlds=[]
    for seed,scenario in seeds('development'):
        A,Q,b,w=make_geometry(seed,scenario);C=make_covariance(A,Q)
        scores=[]
        for eta in ETA_GRID:
            for gamma in GAMMA_GRID:
                risk,priority,comm=known_scores(A,Q,w)
                times=quantile_schedule(risk+eta*priority+gamma*comm)
                scores.append({'eta':eta,'gamma':gamma,'risk':posterior_risk(C,times,w)})
        worlds.append({'seed':seed,'scenario':scenario,'scores':scores})
    summaries=[]
    for eta in ETA_GRID:
        for gamma in GAMMA_GRID:
            values=[next(x['risk'] for x in row['scores'] if x['eta']==eta and x['gamma']==gamma) for row in worlds]
            summaries.append({'eta':eta,'gamma':gamma,'risk':float(np.mean(values))})
    choice=min(summaries,key=lambda x:(x['risk'],x['eta'],x['gamma']))
    source=Path(__file__)
    protocol=out/'PREREGISTRATION.md'
    assert protocol.exists()
    lock={'phase':'VALIDATION_LOCKED_TEST_UNOPENED','date':'2026-11-03',
          'source_sha256':sha(source.read_bytes()),'protocol_sha256':sha(protocol.read_bytes()),
          'development_worlds':len(worlds),'selected':{'eta':choice['eta'],'gamma':choice['gamma']},
          'grid':summaries,'development_results':worlds,
          'test_seed_start':970100,'test_worlds':160,'holdout_access':'not evaluated or materialized in validate',
          'elapsed_seconds':time.perf_counter()-start}
    (out/'LOCKED_VALIDATION.json').write_text(json.dumps(lock,indent=2)+'\n')
    print('VALIDATION LOCKED',json.dumps({'selected':lock['selected'],'rows':len(worlds),'time':lock['elapsed_seconds']}))
    return lock

def ci(diff,seed=20261103,n=5000):
    arr=np.asarray(diff,float);rng=np.random.default_rng(seed)
    boot=np.empty(n)
    for i in range(n):boot[i]=np.mean(arr[rng.integers(0,len(arr),len(arr))])
    return [float(v) for v in np.quantile(boot,[.025,.975])]

def empirical_check(C,A,Q,b,w,sched,seed,reps=20):
    # Draw true trajectories and a shared measurement noise bank; no model selection.
    rng=np.random.default_rng(seed+800000)
    mean=np.zeros((T+1,D));
    for t in range(1,T+1):mean[t]=A[t-1]@mean[t-1]+b[t-1]
    mu=mean.ravel();weight=score_weights(w)
    obs=dict();gain=dict();expected=dict()
    for name,sel in sched.items():
        ix=all_index(sel);S=C[np.ix_(ix,ix)]+R*np.eye(len(ix))
        gain[name]=(ix,np.linalg.solve(S,C[ix,:]).T)
        expected[name]=posterior_risk(C,sel,w)
    sq={m:[] for m in sched}
    for _ in range(reps):
        x=np.empty((T+1,D)); x[0]=rng.normal(size=D)
        for t in range(1,T+1):
            x[t]=A[t-1]@x[t-1]+b[t-1]+rng.multivariate_normal(np.zeros(D),Q[t-1])
        z=x+rng.normal(scale=math.sqrt(R),size=(T+1,D));flat=z.ravel()
        for name,(ix,G) in gain.items():
            estimate=mu+G@(flat[ix]-mu[ix]);delta=estimate-x.ravel()
            sq[name].append(float(np.dot(weight,delta**2)))
    return {m:{'analytic_mse':expected[m],'empirical_mean_mse':float(np.mean(sq[m])),
               'replicate_mse':sq[m]} for m in sched}

def evaluate(out):
    assert not (out/'test_world_results.csv').exists(),'Holdout already scored; no overwriting.'
    lock=json.loads((out/'LOCKED_VALIDATION.json').read_text())
    assert sha(Path(__file__).read_bytes())==lock['source_sha256'],'frozen code changed'
    assert sha((out/'PREREGISTRATION.md').read_bytes())==lock['protocol_sha256'],'frozen prereg changed'
    eta,gamma=lock['selected']['eta'],lock['selected']['gamma']
    start=time.perf_counter();rows=[];empirical=[]
    for wi,(seed,scenario) in enumerate(seeds('holdout')):
        A,Q,b,w=make_geometry(seed,scenario);C=make_covariance(A,Q)
        sched=schedules(C,A,Q,w,seed,eta,gamma)
        values={name:posterior_risk(C,sel,w,True) for name,sel in sched.items()}
        row={'seed':seed,'scenario':scenario,'eta':eta,'gamma':gamma,
             'comm_mean':float(np.mean(known_scores(A,Q,w)[2][1:T]))}
        for name in METHODS:
            row[name+'_weighted']=values[name][0]
            row[name+'_unweighted']=values[name][1]
            row[name+'_times']=';'.join(map(str,sched[name]))
        assert row['covariance_greedy_weighted']<=row['uniform_weighted']+1e-10
        rows.append(row)
        if wi in range(12):
            empirical.append({'seed':seed,'scenario':scenario,'results':empirical_check(C,A,Q,b,w,sched,seed)})
        if (wi+1)%40==0:print('HOLDOUT_WORLDS_COMPLETED',wi+1,flush=True)
    # Save frozen outcomes only after every prediction/checkpoint set exists.
    out_csv=out/'test_world_results.csv'
    with out_csv.open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    means={name:{'weighted':float(np.mean([r[name+'_weighted'] for r in rows])),
                 'unweighted':float(np.mean([r[name+'_unweighted'] for r in rows]))} for name in METHODS}
    differences={};baseline='srde_hybrid'
    for name in METHODS:
        if name==baseline:continue
        d=[r[baseline+'_weighted']-r[name+'_weighted'] for r in rows]
        differences[name]={'srde_minus_comparator':float(np.mean(d)),'ci95':ci(d),
                           'fraction_srde_better':float(np.mean(np.array(d)<0))}
    scenarios={s:{name:float(np.mean([r[name+'_weighted'] for r in rows if r['scenario']==s])) for name in METHODS} for s in SCENARIOS}
    # Negative control: swap priorities while preserving model geometry and original scoring weights, first 40 test worlds.
    shuffled=[]
    for row in rows[:40]:
        seed=int(row['seed']);scenario=row['scenario'];A,Q,b,w=make_geometry(seed,scenario);C=make_covariance(A,Q)
        sw=w.copy();rng=np.random.default_rng(seed+110000)
        sw[1:T]=rng.permutation(sw[1:T])
        r0,p0,c0=known_scores(A,Q,w); _,p1,_=known_scores(A,Q,sw)
        t=quantile_schedule(r0+eta*p1+gamma*c0)
        shuffled.append({'seed':seed,'original_weighted_risk':row['srde_hybrid_weighted'],
                         'shuffled_priority_weighted_risk':posterior_risk(C,t,w)})
    result={'title':'SRDE-P6 100-level 3D checkpoint allocation and posterior trajectory reconstruction',
            'status':'SYNTHETIC_MODEL_BASED_RECONSTRUCTION_NOT_NOVEL_THEOREM',
            'date':'2026-11-03','source_sha256':lock['source_sha256'],'protocol_sha256':lock['protocol_sha256'],
            'test_worlds':len(rows),'levels':T,'dimensions':D,'checkpoint_budget':K,
            'free_terminal_measurement':True,'observation_noise_variance':R,
            'selected_development_params':lock['selected'],'policy_mean_expected_mse':means,
            'by_scenario':scenarios,'paired_differences':differences,'shuffled_priority_control':shuffled,
            'empirical_check':empirical,
            'elapsed_seconds':time.perf_counter()-start,
            'limitations':['Fully specified linear Gaussian generator, no human meaning or feeling',
              'All candidates see generated transition covariance including known future portal metadata',
              'The constructed query-priority scores are available to every method',
              'Conventional greedy is a computationally stronger offline planning baseline, not globally optimal',
              'Posterior risk is calculated from the known generative model, not independently calibrated field data',
              'All numerical results are a bounded diagnostic of this specific simulator',
              'Prior art exists for both budgeted checkpoints and sparse-state estimation']}
    (out/'results.json').write_text(json.dumps(result,indent=2)+'\n')
    print('EVALUATION',json.dumps({'means':means,'main':differences['uniform'],
                                    'strong':differences['covariance_greedy'],'elapsed':result['elapsed_seconds']}))
    return result

def main():
    parser=argparse.ArgumentParser();parser.add_argument('stage',choices=['selftest','validate','evaluate']);parser.add_argument('--out',type=Path,required=True)
    a=parser.parse_args();a.out.mkdir(parents=True,exist_ok=True)
    if a.stage=='selftest':selftest()
    elif a.stage=='validate':validate(a.out)
    else:evaluate(a.out)
if __name__=='__main__':main()
