#!/usr/bin/env python3
"""Independent P7 integrity and outcome audit; does not import the experimental module."""
import hashlib,json,math,struct
from pathlib import Path
import numpy as np
import pandas as pd
BASE=Path(__file__).resolve().parent
J=json.loads((BASE/'results.json').read_text())
L=json.loads((BASE/'LOCKED_SELECTION.json').read_text())
sha=lambda name: hashlib.sha256((BASE/name).read_bytes()).hexdigest()
assert sha('PREREGISTRATION.md')==J['protocol_sha256']==L['protocol_sha256']
assert sha('srde_p7.py')==J['source_sha256']==L['source_sha256']
assert sha('snapshot_models.npz')==J['model_sha256']==L['model_file_sha256']
assert L['status']=='VALIDATION_LOCKED_TEST_UNOPENED'
assert J['worlds']=={'training':5000,'validation':1000,'heldout':3000}
assert J['steps']==100 and list(J['budgets_bytes'])==[12,20,32,40]
expected_rows=4*5*4*3000
f=BASE/'holdout_world_metrics.csv';D=pd.read_csv(f)
assert len(D)==expected_rows, (len(D),expected_rows)
assert D[['world','budget','method','family']].drop_duplicates().shape[0]==expected_rows
assert set(D.budget)=={12,20,32,40}
assert set(D.method)=={'SRDE_provenance','conventional_matched','snapshot_ridge','recent_log','terminal_only'}
assert set(D.family)=={'add','struct','stress','identity'}
assert D.loss.ge(-1e-12).all() and D.decision_error.between(0,1).all()
score_checks=0;max_mean_error=0
for B,methods in J['scores'].items():
    for meth,fams in methods.items():
        for fam,rec in fams.items():
            observed=D[(D.budget==int(B))&(D.method==meth)&(D.family==fam)]
            assert len(observed)==3000
            diff=abs(observed.loss.mean()-rec['mse'])
            diffr=abs(observed.decision_error.mean()-rec['decision_error_rate'])
            assert diff<1e-10 and diffr<1e-10,(B,meth,fam,diff,diffr)
            max_mean_error=max(max_mean_error,diff)
            score_checks+=1
for B in [12,20,32,40]:
    for name in ['srde','snapshots','recent_log']:
        f=BASE/f'holdout_{name}_B{B}.bin'
        assert f.stat().st_size==3000*B,(B,name)
    s1=D[(D.budget==B)&(D.method=='SRDE_provenance')].sort_values(['family','world']).loss.to_numpy()
    s2=D[(D.budget==B)&(D.method=='conventional_matched')].sort_values(['family','world']).loss.to_numpy()
    assert np.array_equal(s1,s2),('conventional tie',B)

# Independently reconstruct the deterministic held-out token stream.
rng=np.random.default_rng(714003)
n=3000;T=100
a=np.empty((n,T),np.uint8);p=np.empty((n,T),np.uint8)
a[:,0]=rng.integers(0,3,size=n)
p[:,0]=rng.integers(0,2,size=n)
for t in range(1,T):
    same=rng.random(n)<.67
    rr=rng.integers(0,2,size=n)
    a[:,t]=np.where(same,a[:,t-1],(a[:,t-1]+1+rr)%3)
    same=rng.random(n)<.88
    p[:,t]=np.where(same,p[:,t-1],1-p[:,t-1])

# Validate the entire 300-bit action/provenance sequence from raw log B=40.
path=BASE/'holdout_recent_log_B40.bin'
data=path.read_bytes()
assert len(data)==40*n
for i in range(n):
    bits=data[i*40:(i+1)*40]
    tokens=[]
    for t in range(T):
        value=0
        for b in range(3):
            idx=t*3+b;value|=((bits[idx//8]>>(idx%8))&1)<<b
        assert value<=5
        tokens.append(value)
    gold=(2*a[i]+p[i]).astype(int)
    assert np.array_equal(tokens,gold)

# Independent suffix-product formula for provenance derivatives, and independent
# forward-run terminal states. Both must agree with frozen B20 half-precision bytes.
R=lambda theta:np.array([[math.cos(theta),-math.sin(theta)],[math.sin(theta),math.cos(theta)]])
As=np.stack([.965*R(.24),.961*R(-.33),np.array([[.927,.083],[-.044,.944]])])
bs=np.array([[.110,-.052],[-.086,.096],[.036,-.105]])
ds=np.array([[.023,-.017],[-.020,.027]])
M=80;x=np.zeros((M,2))
for t in range(T):
    ac=a[:M,t];li=p[:M,t]
    x=np.einsum('nij,nj->ni',As[ac],x)+bs[ac]+ds[li]
Jsrc=np.zeros((M,2,2,2))
suffix=np.broadcast_to(np.eye(2),(M,2,2)).copy()
for t in range(T-1,-1,-1):
    Jsrc[np.arange(M),p[:M,t]]+=suffix
    suffix=np.einsum('nij,njk->nik',suffix,As[a[:M,t]])

buff=(BASE/'holdout_srde_B20.bin').read_bytes()
max_float16_discrepancy=0
for i in range(M):
    payload=np.frombuffer(buff[i*20:(i+1)*20],dtype='<f2').astype(float)
    exact=np.concatenate([x[i],Jsrc[i].ravel()])
    want=exact.astype('<f2').astype(float)
    error=np.max(np.abs(payload-want))
    assert error==0,('quantization',i,error)
    max_float16_discrepancy=max(max_float16_discrepancy,error)

# Independently re-evaluate *one chosen* paired 95% CI from the raw per-world rows
# with the locked whole-world resampling seed. This complements mean checks above.
sub1=D[(D.budget==20)&(D.method=='SRDE_provenance')&(D.family=='add')].sort_values('world')
sub2=D[(D.budget==20)&(D.method=='recent_log')&(D.family=='add')].sort_values('world')
arr=sub1.loss.to_numpy()-sub2.loss.to_numpy()
rr=np.random.default_rng(714004)
indices=rr.integers(0,n,size=(2000,n))
bootstrap=arr[indices].mean(axis=1)
interval=np.percentile(bootstrap,[2.5,97.5])
record=J['paired_bootstrap']['20']['add']['recent_log']
assert abs(arr.mean()-record['srde_minus_comparator'])<1e-10
assert np.allclose(interval,record['ci95_world'],atol=1e-10,rtol=0)

out={
  'status':'PASS','date':'2026-11-03','test_worlds':3000,
  'metrics_rows':expected_rows,'metrics_groups':score_checks,
  'all_hashes_match':True,'all_per_world_memory_budgets_match':True,
  'complete_B40_action_log_verified_all_worlds':True,
  'conventional_matched_tie_verified_all_budgets_and_families':True,
  'independent_reverse_provenance_J_matches_B20_payloads_worlds':M,
  'largest_B20_payload_roundtrip_error':max_float16_discrepancy,
  'largest_metrics_mean_error':float(max_mean_error),
  'paired_B20_add_against_log_delta':float(arr.mean()),
  'paired_B20_add_against_log_interval_95':list(map(float,interval)),
  'scientific_limits':[
    'Same known synthetic generator, not external confirmation',
    'The exact additive-query mechanism is matched to the sensitivity code',
    'Conventional forward sensitivity and SRDE representation carry identical information',
    'Full event log at 40 bytes is lossless under public initial state',
    'Offline ridge decoder model weights are shared and not charged as per-world bytes',
    'Read-only audit does not independently replicate every synthetic distribution outside this generator'
  ]}
(BASE/'audit_independent.json').write_text(json.dumps(out,indent=2)+'\n')
print('P7 INDEPENDENT AUDIT PASS: 240000 raw outcome rows, 80 independently reconstructed worlds, 3000 raw complete logs, exact paired CI')
