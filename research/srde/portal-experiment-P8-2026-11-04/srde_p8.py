#!/usr/bin/env python3
"""SRDE-P8: conditional nonlinear curvature vs lossless entropy chronology.
Selftest -> validate (no holdout seeds) -> evaluate once. Fixed protocol 2026-11-04.
Purely authored synthetic paths, not novel mathematics or a cognition model.
"""
from __future__ import annotations
import argparse, csv, hashlib, json, math, platform, sys, time
from pathlib import Path
import numpy as np

T=100
BUDGETS=(20,24,32,40)
METHODS=('terminal','tangent','curvature','conventional_hessian_twin','suffix','entropy','hybrid')
FAMILIES=('add','rotation','joint','stress')
SEED_DEV=880101;SEED_TEST=880202
N_DEV=400;N_TEST=1200 # per scenario
PREC=640
A=np.stack([
    .965*np.array([[math.cos(.24),-math.sin(.24)],[math.sin(.24),math.cos(.24)]]),
    .961*np.array([[math.cos(-.33),-math.sin(-.33)],[math.sin(-.33),math.cos(-.33)]]),
    np.array([[.927,.083],[-.044,.944]])])
b=np.array([[.110,-.052],[-.086,.096],[.036,-.105]])
d=np.array([[.023,-.017],[-.020,.027]])
G=np.array([[0.,-1.],[1.,0.]])
ADD=np.array([[.085,-.062],[-.076,.088]])
# Name, portal angles by type, additive provenance changes
QUERIES=(
 ('add', (0.,0.,0.),ADD),
 ('rotation',(.35,0.,0.),None),
 ('rotation',(0.,-.35,0.),None),
 ('joint',(.35,-.30,0.),None),
 ('joint',(.32,0.,.30),None),
 ('stress',(.85,0.,0.),None),
)
PROJECTION=np.array([.6,.8]);N_BOOT=2000


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def rot(v):
    c,s=np.cos(v),np.sin(v)
    return np.array([[c,-s],[s,c]],dtype=float)

def gen_worlds(seed,n):
    a=[];p=[];m=[]
    for mode in (0,1):
        rng=np.random.default_rng(seed+mode*177)
        aa=np.empty((n,T),np.uint8);pp=np.empty((n,T),np.uint8)
        aa[:,0]=rng.integers(0,3,n);pp[:,0]=rng.integers(0,2,n)
        for t in range(1,T):
            if mode==0:
                stay_a=rng.random(n)<.67;switch=rng.integers(0,2,n)
                aa[:,t]=np.where(stay_a,aa[:,t-1],(aa[:,t-1]+1+switch)%3)
                stay_p=rng.random(n)<.88
                pp[:,t]=np.where(stay_p,pp[:,t-1],1-pp[:,t-1])
            else:
                aa[:,t]=rng.integers(0,3,n)
                pp[:,t]=rng.integers(0,2,n)
        a.append(aa);p.append(pp);m.append(np.full(n,mode,np.uint8))
    return np.concatenate(a),np.concatenate(p),np.concatenate(m)


def trajectory(acts,provs,query=None,deriv=False,save_states=False):
    n=len(acts);x=np.zeros((n,2),dtype=float)
    mats=A.copy();add=np.zeros((2,2))
    if query is not None:
        _,thetas,dd=query
        mats=np.stack([rot(th)@A[k] for k,th in enumerate(thetas)])
        if dd is not None:add=dd
    states=np.zeros((n,T,2),dtype=float) if save_states else None
    if deriv:
        D=np.zeros((n,3,2));H=np.zeros((n,3,3,2))
    for t in range(T):
        a=acts[:,t];p=provs[:,t];M=mats[a]
        old=x
        if deriv:
            dd=np.einsum('nij,nkj->nki',M,D,optimize=True)
            hh=np.einsum('nij,nklj->nkli',M,H,optimize=True)
            for k in range(3):
                idx=a==k
                if not idx.any():continue
                GM=G@A[k]
                dd[idx,k]+=np.einsum('ij,nj->ni',GM,old[idx],optimize=True)
                for l in range(3):
                    hh[idx,k,l]+=np.einsum('ij,nj->ni',GM,D[idx,l],optimize=True)
                    hh[idx,l,k]+=np.einsum('ij,nj->ni',GM,D[idx,l],optimize=True)
                hh[idx,k,k]-=np.einsum('ij,nj->ni',A[k],old[idx],optimize=True)
            D,H=dd,hh
        x=np.einsum('nij,nj->ni',M,x,optimize=True)+b[a]+d[p]+add[p]
        if save_states:states[:,t]=x
    if deriv:return x,states,D,H
    return x,states


def pack3(vals):
    b=bytearray((len(vals)*3+7)//8)
    for i,v in enumerate(vals):
        v=int(v);assert 0<=v<=5
        for bit in range(3):
            if v>>bit&1:b[(i*3+bit)//8]|=1<<((i*3+bit)%8)
    return bytes(b)

def unpack3(buf,n):
    ans=[]
    for i in range(n):
        v=0
        for bit in range(3):v|=((buf[(i*3+bit)//8]>>((i*3+bit)%8))&1)<<bit
        if v>5:raise ValueError('invalid token in compressed event log')
        ans.append(v)
    return np.asarray(ans,np.uint8)


def frequencies(mode,prev,k):
    if k=='a':
        if prev is None or mode==1:return (1,1,1)
        return tuple(670 if i==prev else 165 for i in range(3))
    if prev is None or mode==1:return (1,1)
    return tuple(880 if i==prev else 120 for i in range(2))


def bounds(lo,hi,freq,choice):
    d=sum(freq);pre=sum(freq[:choice]);end=pre+freq[choice];width=hi-lo
    return lo+width*pre//d,lo+width*end//d


def coder_full(acts,provs,mode):
    lo=0;hi=1<<PREC;pa=None;pp=None
    for a,p in zip(acts,provs):
        a=int(a);p=int(p)
        lo,hi=bounds(lo,hi,frequencies(mode,pa,'a'),a)
        lo,hi=bounds(lo,hi,frequencies(mode,pp,'p'),p)
        pa=a;pp=p
        assert hi>lo
    for nbyte in range(1,48):
        step=1<<(PREC-8*nbyte);j=(lo+step-1)//step
        if (j+1)*step<=hi:
            return j.to_bytes(nbyte,'big')
    raise AssertionError('coder interval insufficient')


def coder_decode(bits,mode):
    nbyte=len(bits);assert 1<=nbyte<=47
    step=1<<(PREC-8*nbyte)
    point=int.from_bytes(bits,'big')*step+step//2
    lo=0;hi=1<<PREC;a=[];p=[];pa=None;pp=None
    for t in range(T):
        for kind in ('a','p'):
            f=frequencies(mode,pa if kind=='a' else pp,kind)
            found=None
            for v in range(len(f)):
                nl,nh=bounds(lo,hi,f,v)
                if nl<=point<nh:
                    found=v;lo=nl;hi=nh;break
            if found is None:raise AssertionError('undecodable interval')
            if kind=='a':a.append(found);pa=found
            else:p.append(found);pp=found
    return np.asarray(a,np.uint8),np.asarray(p,np.uint8)


def pad(data,B):
    if len(data)>B:raise AssertionError(('over budget',len(data),B))
    return data+bytes(B-len(data))


def encode_suffix(acts,provs,states,B,prefix_len=1):
    k=min(T,(B-prefix_len-4)*8//3)
    assert 0<k<T
    at=states[T-k-1].astype('<f2').tobytes()
    sym=pack3(2*acts[-k:].astype(int)+provs[-k:].astype(int))
    header=bytes([k]) if prefix_len==1 else bytes([0xfd,k])
    return pad(header+at+sym,B)


def encode_entropy(acts,provs,states,mode,B):
    bits=coder_full(acts,provs,mode)
    if len(bits)+2<=B:return pad(bytes([mode*2,len(bits)])+bits,B),True,len(bits)
    k=min(T,(B-6)*8//3)
    chk=states[T-k-1].astype('<f2').tobytes()
    sym=pack3(2*acts[-k:].astype(int)+provs[-k:].astype(int))
    return pad(bytes([1+mode*2,k])+chk+sym,B),False,len(bits)


def decode_history(raw,B,kind):
    if len(raw)!=B:raise AssertionError('wrong byte budget')
    if kind=='suffix':
        k=raw[0];start=np.frombuffer(raw[1:5],dtype='<f2').astype(float)
        tokens=unpack3(raw[5:],k)
        return start,tokens//2,tokens%2,k,False
    mode=raw[0]>>1;tag=raw[0]&1;h=raw[1]
    if not tag:
        a,p=coder_decode(raw[2:2+h],mode)
        return np.zeros(2),a,p,T,True
    k=h;start=np.frombuffer(raw[2:6],dtype='<f2').astype(float)
    tokens=unpack3(raw[6:],k)
    return start,tokens//2,tokens%2,k,False


def jit_layout(x,D,H,B):
    """Fixed deterministic priority x, D0/D1/D2, H00/H11/H22,H01/H02/H12."""
    pieces=list(x)+[float(z) for k in range(3) for z in D[k]]
    pieces += [float(z) for k in range(3) for z in H[k,k]]
    pieces += [float(z) for k,l in ((0,1),(0,2),(1,2)) for z in H[k,l]]
    assert len(pieces)==20
    return pieces[:B//2]


def encode_jet(x,D,H,B,tangent=False):
    if tangent:arr=np.concatenate([x,D.reshape(6)]).astype('<f2')
    else:arr=np.array(jit_layout(x,D,H,B),dtype='<f2')
    return pad(arr.tobytes(),B)


def decode_jet(raw,B,tangent=False):
    if len(raw)!=B:raise AssertionError
    vals=np.frombuffer(raw[:2*(B//2)],dtype='<f2').astype(float)
    x=vals[:2];D=np.zeros((3,2));H=np.zeros((3,3,2))
    D[:]=vals[2:8].reshape(3,2)
    if not tangent:
        ptr=8
        for k in range(3):
            if ptr+2<=len(vals):H[k,k]=vals[ptr:ptr+2];ptr+=2
            else:break
        for k,l in ((0,1),(0,2),(1,2)):
            if ptr+2<=len(vals):H[k,l]=H[l,k]=vals[ptr:ptr+2];ptr+=2
            else:break
    return x,D,H


def jet_prediction(raws,B,tangent=False):
    n=len(raws);x=np.empty((n,2));D=np.empty((n,3,2));H=np.empty((n,3,3,2))
    for i,buf in enumerate(raws):x[i],D[i],H[i]=decode_jet(buf,B,tangent)
    preds=[]
    for family,angles,delta in QUERIES:
        theta=np.asarray(angles)
        y=x+np.einsum('nkj,k->nj',D,theta,optimize=True)
        y=y+.5*np.einsum('nklj,k,l->nj',H,theta,theta,optimize=True)
        # No source-J derivative is allocated in structural-focused codec.
        preds.append(y)
    return np.stack(preds,axis=1)


def history_prediction(raws,B,kind):
    n=len(raws);groups={};stats={'full':0,'suffix':0,'k_suffix':None}
    for i,buf in enumerate(raws):
        start,a,p,k,full=decode_history(buf,B,kind)
        groups.setdefault(k,[]).append((i,start,a,p))
        stats['full' if full else 'suffix']+=1
        if not full:stats['k_suffix']=k
    result=np.empty((n,len(QUERIES),2),float)
    for k,grp in groups.items():
        ix=np.asarray([z[0] for z in grp],int)
        initial=np.stack([z[1] for z in grp]);ac=np.stack([z[2] for z in grp]);pr=np.stack([z[3] for z in grp])
        assert ac.shape==(len(grp),k)
        for qi,(fam,angles,add) in enumerate(QUERIES):
            mats=np.stack([rot(q)@A[j] for j,q in enumerate(angles)])
            addition=np.zeros((2,2)) if add is None else add
            x=initial.copy()
            for t in range(k):
                at=ac[:,t];p=pr[:,t]
                x=np.einsum('nij,nj->ni',mats[at],x,optimize=True)+b[at]+d[p]+addition[p]
            result[ix,qi]=x
    return result,stats


def all_methods(acts,provs,mode,states,x,D,H,B,save_prefix=None):
    N=len(acts)
    tangent=[encode_jet(x[i],D[i],H[i],B,tangent=True) for i in range(N)]
    curvature=[encode_jet(x[i],D[i],H[i],B) for i in range(N)]
    suffix=[encode_suffix(acts[i],provs[i],states[i],B) for i in range(N)]
    fullcode=[];fits=[];lengths=[]
    for i in range(N):
        buf,yes,byte_length=encode_entropy(acts[i],provs[i],states[i],int(mode[i]),B)
        fullcode.append(buf);fits.append(yes);lengths.append(byte_length)
    hybrid=[]
    for i in range(N):
        if fits[i]:hybrid.append(fullcode[i])
        else:hybrid.append(bytes([255])+encode_jet(x[i],D[i],H[i],B-1))
    terminal=[pad(np.asarray(x[i],dtype='<f2').tobytes(),B) for i in range(N)]
    raw={'terminal':terminal,'tangent':tangent,'curvature':curvature,'suffix':suffix,'entropy':fullcode,'hybrid':hybrid}
    if save_prefix:
        for name,values in raw.items():
            path=save_prefix.parent/f'{save_prefix.name}_{name}_B{B}.bin'
            path.write_bytes(b''.join(values))
            assert path.stat().st_size==N*B
    out={}
    out['terminal']=np.repeat(np.stack([np.frombuffer(buf[:4],dtype='<f2').astype(float) for buf in terminal])[:,None,:],len(QUERIES),axis=1)
    out['tangent']=jet_prediction(tangent,B,tangent=True)
    out['curvature']=jet_prediction(curvature,B)
    out['conventional_hessian_twin']=out['curvature'].copy()
    out['suffix'],st_suf=history_prediction(suffix,B,'suffix')
    out['entropy'],st_ent=history_prediction(fullcode,B,'entropy')
    out['hybrid']=np.empty_like(out['curvature'])
    yes=np.flatnonzero(fits);no=np.flatnonzero(np.logical_not(fits))
    if len(yes):
        pr,_=history_prediction([fullcode[i] for i in yes],B,'entropy')
        out['hybrid'][yes]=pr
    if len(no):out['hybrid'][no]=jet_prediction([hybrid[i][1:] for i in no],B-1)
    return out,{'fit_count':len(yes),'fallback_count':len(no),'fit_rate':float(len(yes)/N),'encoded_bytes_length':lengths,'suffix_k':st_suf['k_suffix'],'entropy_fallback_k':st_ent['k_suffix']}


def summarise(truth,forecast,modes):
    metrics={};per={};proj_gold=truth@PROJECTION
    for name,pr in forecast.items():
        errs=((truth-pr)**2).mean(axis=2)
        dec=(proj_gold>0)!=(pr@PROJECTION>0)
        metrics[name]={};per[name]={}
        for mode,tag in [(0,'sticky'),(1,'iid'),(None,'overall')]:
            idx=np.ones(len(truth),bool) if mode is None else modes==mode
            metrics[name][tag]={};per[name][tag]={}
            for family in FAMILIES:
                sel=np.array([i for i,q in enumerate(QUERIES) if q[0]==family],int)
                e=errs[idx][:,sel].mean(axis=1)
                bad=dec[idx][:,sel].mean(axis=1)
                metrics[name][tag][family]={'mse':float(np.mean(e)),'sign_error':float(np.mean(bad))}
                per[name][tag][family]=(e,bad)
            metrics[name][tag]['weighted4']={'mse':float(np.mean([metrics[name][tag][f]['mse'] for f in FAMILIES])),
                'sign_error':float(np.mean([metrics[name][tag][f]['sign_error'] for f in FAMILIES]))}
    return metrics,per


def ci(arr,seed=880303):
    rng=np.random.default_rng(seed)
    a=np.asarray(arr,float)
    picks=rng.integers(0,len(a),(N_BOOT,len(a)))
    draws=a[picks].mean(axis=1)
    return [float(x) for x in np.quantile(draws,[.025,.975])]


def selftest():
    ac,pr,mode=gen_worlds(881001,12)
    x,st,D,H=trajectory(ac,pr,deriv=True,save_states=True)
    for i in range(len(ac)):
        for B in BUDGETS:
            buf,full,nbyte=encode_entropy(ac[i],pr[i],st[i],int(mode[i]),B)
            start,a,p,k,isfull=decode_history(buf,B,'entropy')
            if full:
                assert np.array_equal(a,ac[i]) and np.array_equal(p,pr[i])
            else:
                assert np.array_equal(a,ac[i,-k:]) and np.array_equal(p,pr[i,-k:])
            suffix=encode_suffix(ac[i],pr[i],st[i],B)
            assert len(suffix)==B
            assert len(encode_jet(x[i],D[i],H[i],B))==B
    # Numerical finite differences for the Jacobian, pure and mixed Hessian.
    aa=ac[:5];pp=pr[:5];step=2e-5
    xx=x[:5]
    def fw(th):return trajectory(aa,pp,('rotation',tuple(th),None))[0]
    for j in range(3):
        t=np.zeros(3);t[j]=step
        d_num=(fw(t)-fw(-t))/(2*step)
        h_num=(fw(t)+fw(-t)-2*xx)/(step**2)
        assert np.max(np.abs(d_num-D[:5,j]))<1e-4,(j,'D')
        assert np.max(np.abs(h_num-H[:5,j,j]))<.0005,(j,'H')
    for j,k in [(0,1),(0,2),(1,2)]:
        t=np.zeros(3);t[j]=step;t[k]=step
        t2=np.zeros(3);t2[j]=step;t2[k]=-step
        mixed=(fw(t)-fw(t2)-fw(-t2)+fw(-t))/(4*step**2)
        assert np.max(np.abs(mixed-H[:5,j,k]))<.001,(j,k,'mixed')
    print('SELFTEST PASS: coder exact, suffix byte limits, Jacobian and full Hessian finite differences')


def validate(out):
    assert not (out/'LOCKED_VALIDATION.json').exists()
    ac,pr,mode=gen_worlds(SEED_DEV,N_DEV)
    x,states,D,H=trajectory(ac,pr,deriv=True,save_states=True)
    validation={}
    for B in BUDGETS:
        counts={};nbyte={}
        for group,tag in [(0,'sticky'),(1,'iid')]:
            ids=np.flatnonzero(mode==group)
            lens=[len(coder_full(ac[i],pr[i],int(mode[i]))) for i in ids]
            counts[tag]={'fit':int(sum(v+2<=B for v in lens)),'n':len(ids),'fit_rate':float(np.mean([v+2<=B for v in lens]))}
            nbyte[tag]={'min':min(lens),'median':float(np.median(lens)),'max':max(lens)}
        validation[str(B)]={'fit_counts':counts,'lengths':nbyte}
    lock={'status':'LOCKED_VALIDATION_TEST_UNOPENED','date':'2026-11-04','source_sha256':sha(Path(__file__)),
          'protocol_sha256':sha(out/'PREREGISTRATION.md'),'selection':'fixed methods, no parameter tuning',
          'seed_dev':SEED_DEV,'seed_test':SEED_TEST,'worlds_dev':2*N_DEV,'worlds_holdout':'UNOPENED',
          'budgets':list(BUDGETS),'validation':validation,'numpy_version':np.__version__,'python':platform.python_version()}
    (out/'LOCKED_VALIDATION.json').write_text(json.dumps(lock,indent=2)+'\n')
    print('VALIDATION LOCKED:',json.dumps({'B32_sticky':validation['32']['fit_counts']['sticky'],
       'B32_iid':validation['32']['fit_counts']['iid'],'B40_sticky':validation['40']['fit_counts']['sticky'],
       'B40_iid':validation['40']['fit_counts']['iid']}))


def evaluate(out):
    assert not (out/'test_world_metrics.csv').exists(),'Holdout exists: refuse to overwrite'
    lock=json.loads((out/'LOCKED_VALIDATION.json').read_text())
    assert lock['status']=='LOCKED_VALIDATION_TEST_UNOPENED'
    assert lock['source_sha256']==sha(Path(__file__))
    assert lock['protocol_sha256']==sha(out/'PREREGISTRATION.md')
    t0=time.process_time()
    acts,pr,mode=gen_worlds(SEED_TEST,N_TEST)
    x,states,D,H=trajectory(acts,pr,deriv=True,save_states=True)
    gold=np.stack([trajectory(acts,pr,q)[0] for q in QUERIES],axis=1)
    np.savez_compressed(out/'source_and_truths.npz',actions=acts,provenance=pr,population=mode,
       terminal=x.astype(np.float32),gold=gold.astype(np.float64))
    forecast_store={};counts={};per_rows=[];all_metrics={};paired={}
    for B in BUDGETS:
        outB,comp=all_methods(acts,pr,mode,states,x,D,H,B,save_prefix=out/f'actual_payload')
        counts[str(B)]={tag:{'fit':int(sum(1 for j in range(len(mode)) if mode[j]==q and comp['encoded_bytes_length'][j]+2<=B)),
          'n':int(np.sum(mode==q))} for q,tag in [(0,'sticky'),(1,'iid')]}
        counts[str(B)]['all']={'fit':comp['fit_count'],'n':len(mode),'fallback':comp['fallback_count'],
                              'suffix_k':comp['suffix_k'],'entropy_fallback_k':comp['entropy_fallback_k']}
        assert all(len(p)==len(mode)*B for p in [
            (out/f'actual_payload_{name}_B{B}.bin').read_bytes() for name in ('curvature','entropy','hybrid','suffix')])
        assert np.array_equal(outB['curvature'],outB['conventional_hessian_twin'])
        # Full entropy-coded cases must equal true nonlinear direct replay to finite precision.
        selected=np.asarray([i for i,k in enumerate(comp['encoded_bytes_length']) if k+2<=B])
        if len(selected):assert np.max(np.abs(outB['entropy'][selected]-gold[selected]))<2e-12
        metrics,per=summarise(gold,outB,mode)
        all_metrics[str(B)]=metrics
        for name in METHODS:forecast_store[f'forecast_{B}_{name}']=outB[name].astype(np.float64)
        for name in METHODS:
            err=((gold-outB[name])**2).mean(axis=2)
            dec=(gold@PROJECTION>0)!=(outB[name]@PROJECTION>0)
            for family in FAMILIES:
                qq=[i for i,q in enumerate(QUERIES) if q[0]==family]
                e=err[:,qq].mean(axis=1);de=dec[:,qq].mean(axis=1)
                for j in range(len(e)):
                    per_rows.append([j,'sticky' if mode[j]==0 else 'iid',B,name,family,float(e[j]),float(de[j])])
        # Prespecified hypothesis intervals use independent whole-world resampling within populations.
        sub=mode==1
        def family_error(name,fam):
            qq=[i for i,q in enumerate(QUERIES) if q[0]==fam]
            return ((gold[:,qq]-outB[name][:,qq])**2).mean(axis=(1,2))
        if B==32:
            h2=family_error('curvature','joint')[sub]-family_error('tangent','joint')[sub]
            mid=family_error('curvature','rotation')[sub]
            high=family_error('curvature','stress')[sub]
            # each within-pop balanced means over four query families for primary H3
            err_by_name={name:np.mean(np.stack([family_error(name,fam) for fam in FAMILIES],axis=1),axis=1) for name in METHODS}
            better=min(('entropy','curvature'),key=lambda name:float(err_by_name[name].mean()))
            p=err_by_name['hybrid'];strong=err_by_name[better]
            paired={'H2_iid_curvature_minus_tangent_joint':{'mean_delta':float(h2.mean()),'ci95':ci(h2)},
                    'H4_iid_stress_minus_rotation_curvature':{'mean_delta':float((high-mid).mean()),'ci95':ci(high-mid)},
                    'H3_overall_hybrid_vs_stronger_fixed':{'comparator':better,'hybrid_mean':float(p.mean()),
                       'comparator_mean':float(strong.mean()),'relative_improvement':float((strong.mean()-p.mean())/strong.mean()),
                       'paired_difference':float((p-strong).mean()),'ci95':ci(p-strong)}}
        print('HOLDOUT BUDGET',B,'entropy full',comp['fit_count'],'of',len(mode),'curvature joint MSE',
              metrics['curvature']['overall']['joint']['mse'],'entropy joint MSE',metrics['entropy']['overall']['joint']['mse'],flush=True)
    with (out/'test_world_metrics.csv').open('w',newline='') as fh:
        wr=csv.writer(fh);wr.writerow(['world_id','population','budget_bytes','method','family','mse','sign_error'])
        wr.writerows(per_rows)
    np.savez_compressed(out/'all_forecasts.npz',**forecast_store)
    # Wrong-order/lineage tests: selected 600 worlds each pop to limit output; read-only diagnostics, not scored model selection.
    neg={}
    ix=np.r_[np.arange(600),np.arange(N_TEST,N_TEST+600)]
    rng=np.random.default_rng(880404)
    order=acts[ix].copy();pp=pr[ix].copy()
    for j in range(len(ix)):
        order[j]=order[j,rng.permutation(T)]
        pp[j]=pp[j,rng.permutation(T)]
    wrong_order=trajectory(order,pr[ix],QUERIES[0])[0]
    wrong_line=trajectory(acts[ix],pp,QUERIES[0])[0]
    g=gold[ix,0]
    neg['wrong_action_order_add_MSE']=float(((wrong_order-g)**2).mean())
    neg['wrong_provenance_order_add_MSE']=float(((wrong_line-g)**2).mean())
    neg['n_negative_worlds']=len(ix)
    results={'title':'SRDE-P8 nonlinear portal curvature vs entropy-coded chronology','date':'2026-11-04',
      'status':'COMPLETED_ONE_SYNTHETIC_HOLDOUT','source_sha256':lock['source_sha256'],
      'protocol_sha256':lock['protocol_sha256'],'test_worlds':len(mode),'worlds_by_population':{'sticky':N_TEST,'iid':N_TEST},
      'path_levels':T,'budgets':list(BUDGETS),'queries':[{'family':q[0],'angles':q[1],
         'provenance_additions':None if q[2] is None else q[2].tolist()} for q in QUERIES],
      'method_scores':all_metrics,'entropy_fit_counts':counts,'hypotheses':paired,'negative_controls':neg,
      'clock_cpu_seconds':time.process_time()-t0,'limitations':[
       'Known synthetic generator and exact source coding probability models, not real-world forecasting',
       'Second-order derivatives and arithmetic coding are established conventional techniques',
       'SRDE curvature memory must tie its information-matched conventional Hessian twin exactly',
       'Source dictionaries, initial state and shared codebooks are public and not charged to per-world bytes',
       'No universal mathematical novelty or human cognition evidence',
       'Task family is fixed before encoding and the provenance-query tradeoff is not resolved by structural-only jets',
       'Saturated full-log cases have perfect replay by construction, not an algorithmic breakthrough']}
    (out/'results.json').write_text(json.dumps(results,indent=2)+'\n')
    print('FINAL',json.dumps({'fit_rates_B32':counts['32'],'H2':paired['H2_iid_curvature_minus_tangent_joint'],
          'H3':paired['H3_overall_hybrid_vs_stronger_fixed'],'H4':paired['H4_iid_stress_minus_rotation_curvature']},indent=2))


def main():
    pa=argparse.ArgumentParser();pa.add_argument('stage',choices=('selftest','validate','evaluate'))
    pa.add_argument('--out',type=Path,default=Path('.'))
    a=pa.parse_args();a.out.mkdir(parents=True,exist_ok=True)
    {'selftest':selftest,'validate':lambda:validate(a.out),'evaluate':lambda:evaluate(a.out)}[a.stage]()

if __name__=='__main__':main()
