#!/usr/bin/env python3
"""Independent P8 audit: no import of srde_p8 code or scoring functions.
Read locked hashes, exact payloads, all saved forecasts and full 268800-row output.
"""
from __future__ import annotations
import csv,hashlib,json,math,os
from pathlib import Path
import numpy as np

DIR=Path(__file__).resolve().parent
record=json.loads((DIR/'results.json').read_text())
lock=json.loads((DIR/'LOCKED_VALIDATION.json').read_text())
hash_file=lambda p:hashlib.sha256((DIR/p).read_bytes()).hexdigest()
assert hash_file('srde_p8.py')==record['source_sha256']==lock['source_sha256']
assert hash_file('PREREGISTRATION.md')==record['protocol_sha256']==lock['protocol_sha256']
assert lock['worlds_holdout']=='UNOPENED' and record['test_worlds']==2400
s=np.load(DIR/'source_and_truths.npz',allow_pickle=False)
a=s['actions'];p=s['provenance'];pop=s['population'];truth=s['gold']
assert a.shape==(2400,100) and p.shape==a.shape and truth.shape==(2400,6,2)
assert set(np.unique(pop))=={0,1} and np.sum(pop==0)==np.sum(pop==1)==1200
fore_npz=np.load(DIR/'all_forecasts.npz',allow_pickle=False)
fore={key:fore_npz[key] for key in fore_npz.files}
fore_npz.close()
methods=('terminal','tangent','curvature','conventional_hessian_twin','suffix','entropy','hybrid')
families={'add':[0],'rotation':[1,2],'joint':[3,4],'stress':[5]}
proj=np.array([.6,.8]);tested=0;max_error=0.
per_group={};data={}
for B in (20,24,32,40):
    data[B]={}
    for method in methods:
        key=f'forecast_{B}_{method}'
        pp=fore[key];assert pp.shape==truth.shape and np.isfinite(pp).all()
        values={}
        for label,mask in [('sticky',pop==0),('iid',pop==1),('overall',np.ones(len(pop),bool))]:
            values[label]={}
            for fam,ids in families.items():
                q=pp[mask][:,ids];gold=truth[mask][:,ids]
                mse=float(np.mean((gold-q)**2))
                dec=float(np.mean(((gold@proj)>0)!=((q@proj)>0)))
                listed=record['method_scores'][str(B)][method][label][fam]
                assert abs(mse-listed['mse'])<1e-10,(B,method,label,fam,'mse')
                assert abs(dec-listed['sign_error'])<1e-10,(B,method,label,fam,'sign')
                max_error=max(max_error,abs(mse-listed['mse']))
                tested+=1
                values[label][fam]=mse
            assert abs(np.mean(list(values[label].values()))-record['method_scores'][str(B)][method][label]['weighted4']['mse'])<1e-10
        data[B][method]=values
        if method=='curvature':assert np.array_equal(pp,fore[f'forecast_{B}_conventional_hessian_twin'])
    # Verify every byte exactly accounted for, plus mode tags and saturation.
    for method in methods:
        if method=='conventional_hessian_twin':continue
        payload=DIR/f'actual_payload_{method}_B{B}.bin'
        assert payload.stat().st_size==2400*B, (method,B)
        raw=payload.read_bytes()
        if method=='entropy':
            full=np.frombuffer(raw,dtype=np.uint8).reshape(2400,B)[:,0]
            assert set(np.unique(full)).issubset({0,1,2,3})
            for q in (0,1):
                matching=np.flatnonzero(pop==q)
                got=int(np.sum(full[matching]==(2*q)))
                assert got==record['entropy_fit_counts'][str(B)][('sticky','iid')[q]]['fit']
        if method=='hybrid':
            tags=np.frombuffer(raw,dtype=np.uint8).reshape(2400,B)[:,0]
            assert set(np.unique(tags)).issubset({0,2,255})
            assert int(np.sum(tags==255))==record['entropy_fit_counts'][str(B)]['all']['fallback']
# Check source stream not silently changed by coding. Independent integer interval decoder.
A=np.stack([
  .965*np.array([[math.cos(.24),-math.sin(.24)],[math.sin(.24),math.cos(.24)]]),
  .961*np.array([[math.cos(-.33),-math.sin(-.33)],[math.sin(-.33),math.cos(-.33)]]),
  np.array([[.927,.083],[-.044,.944]])])
trans=np.array([[.110,-.052],[-.086,.096],[.036,-.105]])
prov_offsets=np.array([[.023,-.017],[-.020,.027]])
# Stream weights, independent of the experimental codec implementation.
def probs(mode,former,kind):
    if kind==3:
        return [1,1,1] if mode or former is None else [670 if v==former else 165 for v in range(3)]
    return [1,1] if mode or former is None else [880 if v==former else 120 for v in range(2)]
def interval_decode(bits,mode):
    N=len(bits);scale=1<<(640-8*N)
    probe=int.from_bytes(bits,'big')*scale+scale//2
    low=0;high=1<<640;act=[];line=[];aprev=None;lprev=None
    for t in range(100):
        for ncat in (3,2):
            fs=probs(mode,aprev if ncat==3 else lprev,ncat)
            curr=low;width=high-low;den=sum(fs);value=None
            for k,freq in enumerate(fs):
                b0=low+width*sum(fs[:k])//den
                b1=low+width*sum(fs[:k+1])//den
                if b0<=probe<b1:curr=b0;high=b1;low=curr;value=k;break
            if value is None:raise AssertionError('invalid arithmetic code')
            if ncat==3:act.append(value);aprev=value
            else:line.append(value);lprev=value
    return np.array(act,np.uint8),np.array(line,np.uint8)

# Independent float64 full chain; verify encoded checkpoint values in all suffix cases.
worlds=len(a);sstate=np.zeros((worlds,2),float)
checkpoints=np.zeros((worlds,100,2),float)
for t in range(100):
    for k in range(3):
        ids=a[:,t]==k
        sstate[ids]=sstate[ids]@A[k].T+trans[k]+prov_offsets[p[ids,t]]
    checkpoints[:,t]=sstate
assert np.max(np.abs(checkpoints[:,-1]-s['terminal']))<2e-6
full_count_by_budget={};full_reconstructed=0;suffix_verified=0
for B in (20,24,32,40):
    packet=(DIR/f'actual_payload_entropy_B{B}.bin').read_bytes()
    nfull=0
    for i in range(worlds):
        buf=packet[i*B:(i+1)*B];kind=buf[0]&1;mode=buf[0]>>1
        assert mode==int(pop[i])
        if kind==0:
            n=buf[1];assert 1<=n<=B-2
            recovered_a,recovered_p=interval_decode(buf[2:2+n],mode)
            assert np.array_equal(recovered_a,a[i]) and np.array_equal(recovered_p,p[i])
            assert np.array_equal(buf[2+n:],bytes(B-2-n))
            nfull+=1;full_reconstructed+=1
        else:
            k=buf[1];assert 1<=k<100
            est=np.frombuffer(buf[2:6],dtype='<f2').astype(float)
            want=checkpoints[i,100-k-1].astype('<f2').astype(float)
            assert np.array_equal(est,want)
            tokens=[]
            for j in range(k):
                bit=j*3;t=0
                for h in range(3):t|=((buf[6+(bit+h)//8]>>((bit+h)%8))&1)<<h
                assert t<=5;tokens.append(t)
            recovered=np.array(tokens,np.uint8)
            actual=(2*a[i,-k:]+p[i,-k:]).astype(np.uint8)
            assert np.array_equal(recovered,actual)
            suffix_verified+=1
    assert nfull==record['entropy_fit_counts'][str(B)]['all']['fit']
    full_count_by_budget[str(B)]=nfull
# Every per-world record, method/family/budget and same exact forecast scores.
seen=set();rowcount=0;rowmax=0.
with (DIR/'test_world_metrics.csv').open(newline='') as h:
    rd=csv.DictReader(h)
    for row in rd:
        n=int(row['world_id']);B=int(row['budget_bytes']);method=row['method'];fam=row['family']
        key=(n,B,method,fam)
        if key in seen:raise AssertionError('duplicate saved result')
        seen.add(key);rowcount+=1
        assert row['population']==('sticky' if pop[n]==0 else 'iid')
        ids=families[fam]
        target=truth[n,ids];pred=fore[f'forecast_{B}_{method}'][n,ids]
        mse=float(np.mean((pred-target)**2))
        dec=float(np.mean(((target@proj)>0)!=((pred@proj)>0)))
        d_mse=abs(mse-float(row['mse']))
        assert d_mse<1e-8 and abs(dec-float(row['sign_error']))<1e-12
        rowmax=max(rowmax,d_mse)
assert rowcount==2400*4*7*4 and len(seen)==rowcount
# Independently bootstrap primary deltas from archived forecasts.
B=32;mask=pop==1
get=lambda method,ids:((fore[f'forecast_{B}_{method}'][mask][:,ids]-truth[mask][:,ids])**2).mean(axis=(1,2))
h2=get('curvature',[3,4])-get('tangent',[3,4]);h4=get('curvature',[5])-get('curvature',[1,2]);
all_family=lambda method:np.mean(np.stack([((fore[f'forecast_{B}_{method}'][:,ids]-truth[:,ids])**2).mean(axis=(1,2)) for ids in families.values()],axis=1),axis=1)
ref=record['hypotheses']['H3_overall_hybrid_vs_stronger_fixed']
h3=all_family('hybrid')-all_family(ref['comparator'])
def independent_ci(xx):
    rng=np.random.default_rng(880303);x=np.asarray(xx,float)
    sampled=np.empty(2000)
    for k in range(2000):
        selected=rng.integers(0,len(x),size=len(x))
        sampled[k]=x[selected].mean()
    return list(map(float,np.quantile(sampled,[.025,.975])))
for key,vals in [('H2_iid_curvature_minus_tangent_joint',h2),('H4_iid_stress_minus_rotation_curvature',h4),('H3_overall_hybrid_vs_stronger_fixed',h3)]:
    item=record['hypotheses'][key]
    assert abs(vals.mean()-(item.get('mean_delta',item.get('paired_difference'))))<1e-9
    assert np.allclose(independent_ci(vals),item['ci95'],atol=1e-9,rtol=0)
report={
 'status':'PASS','date':'2026-11-04','heldout_worlds':2400,'heldout_per_world_scores':rowcount,
 'source_and_protocol_locked_sha256_valid':True,'every_budget_byte_count_valid':True,
 'all_saved_scores_independently_reconstructed':True,'max_group_MSE_absolute_difference':max_error,
 'max_raw_per_world_MSE_discrepancy':rowmax,
 'all_conventional_hessian_twins_exact':True,'lossless_arithmetic_paths_decoded_and_verified':full_reconstructed,
 'entropy_full_counts_by_budget':full_count_by_budget,'entropy_fallback_suffixes_verified':suffix_verified,
 'all_prespecified_primary_bootstraps_independently_reproduced':True,
 'scientific_limits':["The experiment's known synthetic generator matches the coder probability models exactly",
   'Curve-sketch and conventional Hessian use identical mathematics',
   'Saved full-log decoder validation confirms source information, not original scientific novelty',
   'Zero error for full logs is a mathematical consequence of exact source recovery'],
}
(DIR/'audit_independent.json').write_text(json.dumps(report,indent=2)+'\n')
print('INDEPENDENT AUDIT PASS',json.dumps({k:report[k] for k in ('heldout_worlds','heldout_per_world_scores','lossless_arithmetic_paths_decoded_and_verified','entropy_fallback_suffixes_verified','max_raw_per_world_MSE_discrepancy')},indent=2))
