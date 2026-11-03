#!/usr/bin/env python3
"""SRDE-P7 bit-matched portal provenance memory experiment, CPU only.

Stages: selftest, validate (training + selection, no holdout), evaluate (holdout once).
Fixed protocol: PREREGISTRATION.md. No human cognition or novel theorem claimed.
"""
from __future__ import annotations
import argparse, hashlib, json, time, csv, math, struct, platform
from pathlib import Path
import numpy as np
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler

T=100
BUDGETS=(12,20,32,40)
N_TRAIN=5000; N_VAL=1000; N_TEST=3000
SEEDS={'train':714001,'validation':714002,'test':714003}
ALPHAS=(0.1,1.0,10.0,100.0)
G=np.array([[0.,-1.],[1.,0.]])
EYE=np.eye(2)


def rot(theta):
    return np.array([[math.cos(theta),-math.sin(theta)],[math.sin(theta),math.cos(theta)]],float)

A=np.stack([.965*rot(.24), .961*rot(-.33), np.array([[.927,.083],[-.044,.944]])])
b=np.array([[.110,-.052],[-.086,.096],[.036,-.105]])
d=np.array([[.023,-.017],[-.020,.027]])
ADD_QUERIES=np.array([
    [[.085,-.062],[0.,0.]],
    [[0.,0.],[-.076,.088]],
    [[.050,.025],[-.045,.064]],
    [[-.071,.059],[.061,-.053]],
],float)
STRUCT_QUERIES=tuple((k,theta) for k in (0,1,2) for theta in (-.12,.12))
STRESS_QUERY=(0,.45)
QUERY_PROJ=np.array([.6,.8])


def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def worlds(seed,n):
    rng=np.random.default_rng(seed)
    acts=np.empty((n,T),np.uint8);lin=np.empty((n,T),np.uint8)
    acts[:,0]=rng.integers(0,3,size=n)
    lin[:,0]=rng.integers(0,2,size=n)
    for t in range(1,T):
        stay_a=rng.random(n)<.67
        new=rng.integers(0,2,size=n)
        acts[:,t]=np.where(stay_a,acts[:,t-1],(acts[:,t-1]+1+new)%3)
        stay_p=rng.random(n)<.88
        lin[:,t]=np.where(stay_p,lin[:,t-1],1-lin[:,t-1])
    return acts,lin


def trajectory(acts,lin,angle_query=None,derivatives=True):
    n=len(acts);x=np.zeros((n,2),float)
    states=np.empty((n,T,2),float)
    J=np.zeros((n,2,2,2),float) # provenance, output dim, input delta dim
    D=np.zeros((n,3,2),float)   # derivative of x wrt portal type rotation angle
    mats=A.copy()
    if angle_query is not None:
        target,theta=angle_query
        mats[target]=rot(theta)@A[target]
    for t in range(T):
        ac=acts[:,t];p=lin[:,t]
        M=mats[ac];old=x
        if derivatives:
            # Push previous derivatives through the next portal before adding local terms.
            J=np.einsum('nij,nkjl->nkil',M,J,optimize=True)
            J[np.arange(n),p]+=EYE
            D=np.einsum('nij,nkj->nki',M,D,optimize=True)
            # d (R(theta) A x)/dtheta at zero = G A x.
            pulse=np.einsum('ij,nj->ni',G,np.einsum('nij,nj->ni',A[ac],old,optimize=True),optimize=True)
            D[np.arange(n),ac]+=pulse
        x=np.einsum('nij,nj->ni',M,old,optimize=True)+b[ac]+d[p]
        states[:,t]=x
    return x,states,J,D


def reverse_jacobians(acts,lin):
    # Conventional suffix-product identity, algebraically independent of forward J recurrence.
    n=len(acts);suffix=np.broadcast_to(EYE,(n,2,2)).copy();j=np.zeros((n,2,2,2),float)
    for t in range(T-1,-1,-1):
        p=lin[:,t];j[np.arange(n),p]+=suffix
        suffix=np.einsum('nij,njk->nik',suffix,A[acts[:,t]],optimize=True)
    return j


def structural_targets(acts,lin):
    return np.stack([trajectory(acts,lin,(k,theta),False)[0] for k,theta in STRUCT_QUERIES],axis=1)


def stress_targets(acts,lin):
    return trajectory(acts,lin,STRESS_QUERY,False)[0]


def append_to_budget(data,B):
    if len(data)>B:raise AssertionError((len(data),B))
    return data + bytes(B-len(data))


def encode_sketch(x,J,D,B):
    flat=np.concatenate([x.ravel(),J.ravel(),D.ravel() if B>=32 else []])
    if B==12:
        values=np.clip(flat[:10]/np.array([8.,8.]+[48.]*8),-1.,1.)
        codes=np.rint(values*127).astype(np.int8)
        data=codes.tobytes()
    else:
        data=flat.astype('<f2').tobytes()
    return append_to_budget(data,B)


def decode_sketch(raw,B):
    if len(raw)!=B:raise AssertionError('budget mismatch')
    if B==12:
        codes=np.frombuffer(raw[:10],dtype=np.int8).astype(float)
        flat=codes/127*np.array([8.,8.]+[48.]*8)
    else:
        nn=16 if B>=32 else 10
        flat=np.frombuffer(raw[:nn*2],dtype='<f2').astype(float)
    x=flat[:2];j=flat[2:10].reshape(2,2,2)
    dd=flat[10:].reshape(3,2) if B>=32 else np.zeros((3,2))
    return x,j,dd


def pack_symbols(sym):
    result=bytearray((len(sym)*3+7)//8)
    for i,value in enumerate(sym):
        v=int(value);assert 0<=v<=5
        for bit in range(3):
            if v&(1<<bit):
                slot=3*i+bit;result[slot//8]|=(1<<(slot%8))
    return bytes(result)


def unpack_symbols(data,k):
    out=np.empty(k,dtype=np.uint8)
    for i in range(k):
        value=0
        for bit in range(3):
            pos=3*i+bit
            if data[pos//8]&(1<<(pos%8)):value|=1<<bit
        assert value<=5
        out[i]=value
    return out


def encode_suffix(a,p,states,B):
    if B>=38:
        sym=(a.astype(int)*2+p.astype(int)).astype(np.uint8)
        return append_to_budget(pack_symbols(sym),B),T
    k=(8*B-32)//3
    state=np.asarray(states[T-k-1],dtype='<f2').tobytes() if k<T else np.zeros(2,dtype='<f2').tobytes()
    sym=(a[-k:].astype(int)*2+p[-k:].astype(int)).astype(np.uint8)
    return append_to_budget(state+pack_symbols(sym),B),k


def decode_suffix(raw,B,qtype,query=None):
    if B>=38:
        k=T;x=np.zeros(2,float);symbols=unpack_symbols(raw[:38],T)
    else:
        k=(8*B-32)//3
        x=np.frombuffer(raw[:4],dtype='<f2').astype(float).copy()
        symbols=unpack_symbols(raw[4:],k)
    for z in symbols:
        ac=int(z)//2;p=int(z)%2;M=A[ac]
        if qtype=='struct' and query is not None and ac==query[0]:M=rot(query[1])@M
        addon=ADD_QUERIES[int(query),p] if qtype=='add' else np.zeros(2)
        x=M@x+b[ac]+d[p]+addon
    return x


def decode_suffix_batch(payloads,B,qtype,query=None):
    """Vectorized replay from *decoded* real B-byte payloads; exact same algorithm as decode_suffix."""
    n=len(payloads)
    k=T if B>=38 else (8*B-32)//3
    tokens=np.stack([unpack_symbols(blob[:38] if B>=38 else blob[4:],k) for blob in payloads])
    x=np.zeros((n,2),float) if B>=38 else np.stack([np.frombuffer(blob[:4],dtype='<f2').astype(float) for blob in payloads])
    if qtype=='add':addon=ADD_QUERIES[int(query)]
    for t in range(k):
        ac=tokens[:,t]//2;pr=tokens[:,t]%2
        mats=A[ac].copy()
        if qtype=='struct' and query is not None:
            mask=(ac==query[0]);mats[mask]=rot(query[1])@A[int(query[0])]
        x=np.einsum('nij,nj->ni',mats,x,optimize=True)+b[ac]+d[pr]
        if qtype=='add':x+=addon[pr]
    return x


def snapshot_times(B):
    return np.rint(np.linspace(1,T,B//4)).astype(int) # 1-based, includes T


def encode_snapshots(states,B):
    return append_to_budget(states[snapshot_times(B)-1].astype('<f2').tobytes(),B)


def snapshots_for_model(states,B):
    return states[:,snapshot_times(B)-1,:].astype('<f2').astype(float).reshape(len(states),-1)


def trained_targets(acts,lin,x,J,D):
    st=structural_targets(acts,lin)
    # J 8 values, D 6 values, exact differences 6 queries x 2 axes
    return np.column_stack([J.reshape(len(acts),-1),D.reshape(len(acts),-1),(st-x[:,None,:]).reshape(len(acts),-1)])


def train_snapshot_predictors(train_data,val_data):
    (xt,stt,Jt,Dt,at,pt)=train_data
    (xv,stv,Jv,Dv,av,pv)=val_data
    Y=trained_targets(at,pt,xt,Jt,Dt)
    # Validation query responses generated entirely from validation worlds.
    target_val=trained_targets(av,pv,xv,Jv,Dv)
    models={};grid=[]
    for B in BUDGETS:
        Xtr=snapshots_for_model(stt,B);Xv=snapshots_for_model(stv,B)
        scaler=StandardScaler().fit(Xtr)
        Ztr=scaler.transform(Xtr);Zv=scaler.transform(Xv)
        rows=[];choices=[]
        for alpha in ALPHAS:
            mdl=Ridge(alpha=alpha,fit_intercept=True).fit(Ztr,Y)
            out=mdl.predict(Zv)
            xv_quant=stv[:,snapshot_times(B)[-1]-1,:].astype('<f2').astype(float)
            e_add=[]
            jj=out[:,:8].reshape(len(av),2,2,2)
            for dd in ADD_QUERIES:
                pred=xv_quant+np.einsum('npij,pj->ni',jj,dd,optimize=True)
                actual=xv+np.einsum('npij,pj->ni',Jv,dd,optimize=True)
                e_add.append(np.mean((pred-actual)**2))
            e_struct=[]
            for i in range(6):
                pred=xv_quant+out[:,14+2*i:14+2*i+2]
                actual=xv+target_val[:,14+2*i:14+2*i+2]
                e_struct.append(np.mean((pred-actual)**2))
            dev_loss=(float(np.mean(e_add))+float(np.mean(e_struct)))/2
            rows.append({'alpha':alpha,'validation_add_mse':float(np.mean(e_add)),
                         'validation_struct_mse':float(np.mean(e_struct)),'selection_loss':dev_loss})
            choices.append((dev_loss,alpha,mdl))
        _,chosen,m=min(choices,key=lambda x:(x[0],x[1]))
        models[B]={'mean':scaler.mean_,'scale':scaler.scale_,'weights':m.coef_,'intercept':m.intercept_,'alpha':float(chosen)}
        grid.append({'budget_bytes':B,'selected_alpha':float(chosen),'candidates':rows})
    return models,grid


def predict_snapshot(fields,states,B,mode,query):
    X=snapshots_for_model(states,B)
    z=(X-fields['mean'])/fields['scale'];out=z@fields['weights'].T+fields['intercept']
    end=states[:,snapshot_times(B)[-1]-1,:].astype('<f2').astype(float)
    if mode=='add':
        JJ=out[:,:8].reshape(len(states),2,2,2)
        return end+np.einsum('npij,pj->ni',JJ,ADD_QUERIES[int(query)],optimize=True)
    if mode=='struct':
        idx=STRUCT_QUERIES.index(query)
        return end+out[:,14+2*idx:14+2*idx+2]
    if mode=='stress':
        D=out[:,8:14].reshape(len(states),3,2)
        return end+STRESS_QUERY[1]*D[:,STRESS_QUERY[0]]
    return end


def score(gold,pred):
    assert gold.shape==pred.shape and gold.shape[1]==2
    e=((gold-pred)**2).mean(axis=1)
    dec=((gold@QUERY_PROJ>0)!=(pred@QUERY_PROJ>0)).astype(float)
    return e,dec


def validate(out):
    assert not (out/'LOCKED_SELECTION.json').exists(),'Validation already locked'
    ac,pr=worlds(SEEDS['train'],N_TRAIN)
    x,states,J,D=trajectory(ac,pr)
    av,pv=worlds(SEEDS['validation'],N_VAL)
    xv,sv,Jv,Dv=trajectory(av,pv)
    models,grid=train_snapshot_predictors((x,states,J,D,ac,pr),(xv,sv,Jv,Dv,av,pv))
    np.savez_compressed(out/'snapshot_models.npz',**{
        f'{B}_{k}':v for B,info in models.items() for k,v in info.items() if k!='alpha'})
    c=(out/'snapshot_models.npz').read_bytes()
    lock={'experiment':'SRDE-P7', 'status':'VALIDATION_LOCKED_TEST_UNOPENED',
          'date':'2026-11-03', 'protocol_sha256':digest(out/'PREREGISTRATION.md'),
          'source_sha256':digest(Path(__file__)), 'model_file_sha256':hashlib.sha256(c).hexdigest(),
          'train_worlds':N_TRAIN,'validation_worlds':N_VAL,'holdout_worlds':'UNOPENED',
          'seeds_exclusive':SEEDS,'budget_bytes':BUDGETS, 'ridge_grid':grid,
          'quantization':{'B12':'int8 10 terms and zero-pad to 12 bytes','B20':'float16 x+2 source Jacobians','B32_B40':'float16 x+2 source Jacobians+3 action rotation derivatives'},
          'software':{'python':platform.python_version(),'numpy':np.__version__},
          'anti_leakage':'No holdout seed sampled or targets materialized in validate.'}
    (out/'LOCKED_SELECTION.json').write_text(json.dumps(lock,indent=2,default=list)+'\n')
    print('VALIDATION LOCKED: '+json.dumps({'selected_ridge_alpha':{r['budget_bytes']:r['selected_alpha'] for r in grid},'holdout':'unopened'}))
    return lock


def evaluate(out):
    assert not (out/'holdout_world_metrics.csv').exists(),'Holdout already scored; no overwrite'
    lock=json.loads((out/'LOCKED_SELECTION.json').read_text())
    assert lock['source_sha256']==digest(Path(__file__))
    assert lock['protocol_sha256']==digest(out/'PREREGISTRATION.md')
    assert lock['model_file_sha256']==digest(out/'snapshot_models.npz')
    m=np.load(out/'snapshot_models.npz',allow_pickle=False)
    models={B:{k:m[f'{B}_{k}'] for k in ('mean','scale','weights','intercept')} for B in BUDGETS}
    ah,ph=worlds(SEEDS['test'],N_TEST)
    x,states,J,D=trajectory(ah,ph)
    Jcv=reverse_jacobians(ah,ph)
    err_j=np.max(np.abs(J-Jcv));assert err_j<1e-10,err_j
    truths_add=[x+np.einsum('npij,pj->ni',J,q,optimize=True) for q in ADD_QUERIES]
    # Verify the J formula against independently rerunning the first 30 portal paths after additive interventions.
    def replay_add_subset(shift):
        xx=np.zeros((30,2),float)
        for t in range(T):
            ac=ah[:30,t];pp=ph[:30,t]
            xx=np.einsum('nij,nj->ni',A[ac],xx,optimize=True)+b[ac]+d[pp]+shift[pp]
        return xx
    assert all(np.max(np.abs(replay_add_subset(q)-truths_add[i][:30]))<1e-10 for i,q in enumerate(ADD_QUERIES))
    truths_struct=structural_targets(ah,ph)
    truths_stress=stress_targets(ah,ph)
    n=N_TEST
    row_records=[];scores={};bytes_verified={};negative_scores={}
    # Precompute negative control source labels once, never change true canonical x.
    rng=np.random.default_rng(714005)
    pshuf=ph.copy()
    for i in range(n):pshuf[i]=rng.permutation(pshuf[i])
    Jshuf=reverse_jacobians(ah,pshuf)
    areorder=ah.copy();preorder=ph.copy()
    for i in range(n):
        perm=np.random.default_rng(714006+i).permutation(T)
        areorder[i]=ah[i,perm];preorder[i]=ph[i,perm]
    Jorder=reverse_jacobians(areorder,preorder)
    # Budget-by-budget frozen evaluation.
    for B in BUDGETS:
        bs=[];snap=[];raw=[];negp=[];nego=[]
        for i in range(n):
            bs.append(encode_sketch(x[i],J[i],D[i],B))
            snap.append(encode_snapshots(states[i],B))
            p,k=encode_suffix(ah[i],ph[i],states[i],B);raw.append(p)
            negp.append(encode_sketch(x[i],Jshuf[i],D[i],B))
            nego.append(encode_sketch(x[i],Jorder[i],D[i],B))
        for bbb in (bs,snap,raw,negp,nego):assert all(len(v)==B for v in bbb)
        bytes_verified[str(B)]={'per_world_bytes':B,'worlds':n,'verified_payload_bytes':n*B,'recent_log_symbols':k,'complete_log':k==T}
        (out/f'holdout_srde_B{B}.bin').write_bytes(b''.join(bs))
        (out/f'holdout_snapshots_B{B}.bin').write_bytes(b''.join(snap))
        (out/f'holdout_recent_log_B{B}.bin').write_bytes(b''.join(raw))
        Xmem=np.stack([decode_sketch(s,B)[0] for s in bs]);Jmem=np.stack([decode_sketch(s,B)[1] for s in bs]);Dmem=np.stack([decode_sketch(s,B)[2] for s in bs])
        Jwrong=np.stack([decode_sketch(s,B)[1] for s in negp]);Jorderwrong=np.stack([decode_sketch(s,B)[1] for s in nego])
        methods=('SRDE_provenance','conventional_matched','snapshot_ridge','recent_log','terminal_only')
        # Store one per-world mean for each query family. Full individual query scores appear in metrics JSON.
        arrays={key:{typ:[] for typ in ('add','struct','stress','identity')} for key in methods}
        wrong={'wrong_lineage':[],'wrong_order':[]}
        for qid,q in enumerate(ADD_QUERIES):
            truth=truths_add[qid]
            pred_s=Xmem+np.einsum('npij,pj->ni',Jmem,q,optimize=True)
            # Matched convention uses independently constructed Jacobians and *same* byte codec.
            conv=np.stack([decode_sketch(encode_sketch(x[i],Jcv[i],D[i],B),B)[0] for i in range(n)])+np.einsum('npij,pj->ni',Jmem,q,optimize=True)
            assert np.max(np.abs(pred_s-conv))<1e-10
            pp={
                'SRDE_provenance':pred_s,'conventional_matched':conv,
                'snapshot_ridge':predict_snapshot(models[B],states,B,'add',qid),
                'recent_log':decode_suffix_batch(raw,B,'add',qid),
                'terminal_only':np.stack([decode_sketch(encode_sketch(x[i],np.zeros((2,2,2)),np.zeros((3,2)),B),B)[0] for i in range(n)])
            }
            for name,pred in pp.items():arrays[name]['add'].append(score(truth,pred))
            wrong['wrong_lineage'].append(score(truth,Xmem+np.einsum('npij,pj->ni',Jwrong,q,optimize=True)))
            wrong['wrong_order'].append(score(truth,Xmem+np.einsum('npij,pj->ni',Jorderwrong,q,optimize=True)))
        for qid,q in enumerate(STRUCT_QUERIES):
            truth=truths_struct[:,qid,:]
            pred_s=Xmem+q[1]*Dmem[:,q[0]]
            pp={'SRDE_provenance':pred_s,'conventional_matched':pred_s.copy(),
                'snapshot_ridge':predict_snapshot(models[B],states,B,'struct',q),
                'recent_log':decode_suffix_batch(raw,B,'struct',q),
                'terminal_only':Xmem.copy()}
            for name,pred in pp.items():arrays[name]['struct'].append(score(truth,pred))
        for typ,truth,query in [('stress',truths_stress,STRESS_QUERY),('identity',x,None)]:
            if typ=='stress':
                ps=Xmem+STRESS_QUERY[1]*Dmem[:,STRESS_QUERY[0]]
                pred={'SRDE_provenance':ps,'conventional_matched':ps.copy(),
                      'snapshot_ridge':predict_snapshot(models[B],states,B,'stress',None),
                      'recent_log':decode_suffix_batch(raw,B,'struct',query),
                      'terminal_only':Xmem.copy()}
            else:
                pred={'SRDE_provenance':Xmem,'conventional_matched':Xmem.copy(),
                      'snapshot_ridge':predict_snapshot(models[B],states,B,'identity',None),
                      'recent_log':decode_suffix_batch(raw,B,'identity',None),
                      'terminal_only':Xmem.copy()}
            for name,p in pred.items():arrays[name][typ].append(score(truth,p))
        # Query-averaged world-level losses per policy.
        for name in methods:
            scores.setdefault(str(B),{})[name]={}
            rec={'budget':B,'method':name}
            for fam,values in arrays[name].items():
                loss=np.mean([v[0] for v in values],axis=0)
                disc=np.mean([v[1] for v in values],axis=0)
                rec[f'{fam}_mse']=float(np.mean(loss));rec[f'{fam}_decision_error']=float(np.mean(disc))
                scores[str(B)][name][fam]={'mse':rec[f'{fam}_mse'],'decision_error_rate':rec[f'{fam}_decision_error']}
                for i in range(n):
                    row_records.append({'world':i,'budget':B,'method':name,'family':fam,'loss':float(loss[i]),'decision_error':float(disc[i])})
        for key,values in wrong.items():
            loss=np.mean([v[0] for v in values],axis=0)
            negative_scores.setdefault(str(B),{})[key]={'additive_mse':float(np.mean(loss))}
        print('BUDGET',B,'add_mse',json.dumps({name:round(scores[str(B)][name]['add']['mse'],8) for name in methods}),flush=True)
    # Whole-world bootstrap, fixed seed, per family, prechosen comparisons.
    differences={};rngboot=np.random.default_rng(714004)
    rec_group={}
    for row in row_records:
        rec_group[(row['budget'],row['method'],row['family'],row['world'])]=row['loss']
    draws=rngboot.integers(0,n,size=(2000,n))  # a single frozen world bootstrap index bank
    for B in BUDGETS:
        differences[str(B)]={}
        for fam in ('add','struct','stress','identity'):
            differences[str(B)][fam]={}
            a=np.array([rec_group[(B,'SRDE_provenance',fam,i)] for i in range(n)])
            for comp in ('snapshot_ridge','recent_log','conventional_matched'):
                z=np.array([rec_group[(B,comp,fam,i)] for i in range(n)])
                delta=a-z
                # Independent world bootstrap; same resamples per comparison.
                boot=delta[draws].mean(axis=1)
                differences[str(B)][fam][comp]={'srde_minus_comparator':float(delta.mean()),
                    'ci95_world':list(map(float,np.percentile(boot,[2.5,97.5]))),
                    'fraction_worlds_SRDE_better':float(np.mean(delta<0))}
    import pandas as pd
    pd.DataFrame(row_records).to_csv(out/'holdout_world_metrics.csv',index=False,float_format='%.12g')
    results={'title':'SRDE-P7 compressed ordered-portal and provenance replay',
       'date':'2026-11-03','status':'SYNTHETIC_FIXED_BIT_TASK_CONDITIONAL_EVIDENCE',
       'worlds':{'training':N_TRAIN,'validation':N_VAL,'heldout':N_TEST},
       'steps':T,'budgets_bytes':BUDGETS,'protocol_sha256':lock['protocol_sha256'],
       'source_sha256':lock['source_sha256'],'model_sha256':lock['model_file_sha256'],
       'description':'Provenance source additive counterfactuals and structural portal edits after history compressed; source matrices and neural operator are public; not a novel mathematical theorem',
       'quantized_payloads':bytes_verified,'validation':lock['ridge_grid'],
       'scores':scores,'paired_bootstrap':differences,'negative_controls':negative_scores,
       'independent_reverse_jacobian_max_abs_diff':float(err_j),
       'limits':['Known synthetic world generation and allowed queries','All encoders share portal dictionaries and public x0',
       'A learned offline snapshot decoder has unmetered shared training weights, only per-world bytes matched',
       'The conventional Jacobian/sensitivity twin must tie the SRDE sketch',
       'Additive perturbations are exactly in the sensitivity family; finite rotation edit is out of family',
       'Fixed per-world byte capacity not full computing energy/latency budget','No human affect, consciousness, universal semantics, or externally validated prediction']}
    (out/'results.json').write_text(json.dumps(results,indent=2,default=list)+'\n')
    return results


def selftest():
    rng=np.random.default_rng(17)
    ac,pr=worlds(16,4)
    x,states,J,D=trajectory(ac,pr)
    assert x.shape==(4,2) and states.shape==(4,T,2)
    jj=reverse_jacobians(ac,pr);assert np.max(np.abs(J-jj))<1e-10
    for B in BUDGETS:
        for i in range(4):
            v=encode_sketch(x[i],J[i],D[i],B)
            assert len(v)==B
            s=encode_snapshots(states[i],B);assert len(s)==B
            r,k=encode_suffix(ac[i],pr[i],states[i],B)
            assert len(r)==B
            if B>=38:
                assert np.max(np.abs(decode_suffix(r,B,'identity')-x[i]))<1e-10
            else:
                assert k<T
    # structural first-order derivative finite difference on tiny perturbation
    z=trajectory(ac,pr,(0,1e-5),False)[0]
    assert np.max(np.abs((z-x)/1e-5-D[:,0]))<.001
    # source Jacobian additive replay reference
    delta=ADD_QUERIES[0]
    val=x+np.einsum('npij,pj->ni',J,delta)
    xx=np.zeros((4,2))
    for t in range(T):
        a=ac[:,t];p=pr[:,t]
        xx=np.einsum('nij,nj->ni',A[a],xx)+b[a]+d[p]+delta[p]
    assert np.max(np.abs(xx-val))<1e-10
    print('SELFTEST PASS: encoding sizes, sufficiency, derivative checks, recent log')


def main():
    pa=argparse.ArgumentParser();pa.add_argument('stage',choices=['selftest','validate','evaluate'])
    pa.add_argument('--out',type=Path,required=True)
    args=pa.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    {'selftest':lambda:selftest(),'validate':lambda:validate(args.out),'evaluate':lambda:evaluate(args.out)}[args.stage]()

if __name__=='__main__':main()
