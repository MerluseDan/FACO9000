"""CPU research prototype, not native SRDE. See PROTOCOL.json. No network needed."""
import argparse, csv, gzip, hashlib, json, os, platform, time
from pathlib import Path
import numpy as np
import scipy, sklearn
from scipy.special import expit, logit
from scipy.ndimage import rotate
from sklearn.datasets import load_digits
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.svm import SVC
from sklearn.metrics import roc_auc_score, accuracy_score, brier_score_loss, log_loss
from sklearn.metrics.pairwise import euclidean_distances

HERE=Path(__file__).resolve().parent
def dump(path,obj):
    path.write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n')
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def evidence_state(pos,neg): return ('neither','false_only','true_only','both')[2*bool(pos)+bool(neg)]
def fde_not(x): return (x[1],x[0])
def fde_and(x,y): return (x[0]&y[0],x[1]|y[1])
def fde_or(x,y): return (x[0]|y[0],x[1]&y[1])
def decode_recursive(leaf, edges):
    if not edges: return leaf
    return edges[0]*decode_recursive(leaf,edges[1:])
def decoded(e,recursive=False):
    return decode_recursive(e['leaf'],e['edges']) if recursive else e['leaf']*int(np.prod(e['edges']))
def score(case,recursive=False,lineage=True,context=True,temporal=True,pathsign=True):
    seen=set(); total=0.
    for e in case['reports']:
        if not e['active'] or (context and e['context']!=case['context']): continue
        if lineage and e['lineage'] in seen: continue
        seen.add(e['lineage'])
        r=.5+(e['reliability']-.5)*(np.exp(-e['age']/3) if temporal else 1.)
        vote=decoded(e,recursive) if pathsign else e['leaf']
        total+=vote*np.log(r/(1-r))
    return float(expit(total))
def features(case):
    reports=case['reports']; votes=[decoded(e) for e in reports]
    valid=[e for e in reports if e['active'] and e['context']==case['context']]
    unique={e['lineage']:e for e in valid}
    u=list(unique.values()); uv=[decoded(e) for e in u]
    p=sum(v>0 for v in uv); n=sum(v<0 for v in uv)
    scores=[score(case,**kw) for kw in ({},{'lineage':False},{'context':False},{'temporal':False},{'pathsign':False})]
    return [logit(np.clip(s,1e-6,1-1e-6)) for s in scores]+[len(reports),len(valid),len(u),p,n,int(p>0),int(n>0),sum(votes),sum(e['active'] for e in reports),np.mean([e['age'] for e in reports]) if reports else 0]
def generate(seed,split,nworld):
    rng=np.random.default_rng(seed); out=[]
    shifted=split=='shift'
    for w in range(nworld):
        rates=rng.uniform(.65,.9,4)
        for i in range(60):
            y=int(rng.integers(2)); c=int(rng.integers(2)); reports=[]
            f=float(np.clip((.8 if y else .2)+rng.normal(0,.13),0,1))
            if shifted: f=1-f
            for s in range(4):
                if rng.random()<.22: continue
                age=int(rng.choice([0,1,3,8],p=[.6,.2,.15,.05] if not shifted else [.15,.15,.25,.45]))
                rc=c if rng.random()<.8 else 1-c
                ref=y if rc==c else int(rng.integers(2))
                # Independent historical perturbation per lineage; explicitly authored process.
                old=ref^int(rng.random()<.5*(1-np.exp(-age/3)))
                v=2*(old^int(rng.random()>rates[s]))-1
                depth=int(rng.integers(1,4)); edges=rng.choice([-1,1],depth).tolist()
                leaf=v*int(np.prod(edges)); active=bool(rng.random()<.85)
                copies=int(rng.integers(1,5)) if rng.random()<(.25 if not shifted else .75) else 1
                for cp in range(copies): reports.append(dict(lineage=s,copy=cp,age=age,context=rc,reliability=float(rates[s]),leaf=leaf,edges=edges,active=active))
            out.append(dict(id=f'{seed}:{split}:{w}:{i}',world=f'{seed}:{split}:{w}',split=split,y=y,context=c,F=f,reports=reports))
    return out
def metrics(y,p):
    y=np.asarray(y); p=np.clip(p,1e-7,1-1e-7); pred=p>=.5; keep=np.maximum(p,1-p)>=.8
    ece=sum(np.mean(m)*abs(float(y[m].mean()-p[m].mean())) for lo in np.arange(0,1,.1) if np.any(m:=(p>=lo)&(p<lo+.1)))
    return dict(n=len(y),auc=float(roc_auc_score(y,p)) if len(set(y))>1 else None,accuracy=float(accuracy_score(y,pred)),brier=float(brier_score_loss(y,p)),logloss=float(log_loss(y,p,labels=[0,1])),ece10=float(ece),coverage80=float(keep.mean()),risk80=float((pred[keep]!=y[keep]).mean()) if keep.any() else None,assertions80=int(keep.sum()))
def calibrator(p,y):
    m=LogisticRegression(C=1e3,max_iter=1000).fit(logit(np.clip(p,1e-6,1-1e-6)).reshape(-1,1),y)
    return lambda q:m.predict_proba(logit(np.clip(q,1e-6,1-1e-6)).reshape(-1,1))[:,1]
def summarize(rows):
    out=[]
    for seed,split,method in sorted(set((r['seed'],r['split'],r['method']) for r in rows)):
        a=[r for r in rows if (r['seed'],r['split'],r['method'])==(seed,split,method)]
        out.append(dict(seed=seed,split=split,method=method,**metrics([r['y'] for r in a],[r['p'] for r in a])))
        h=[r for r in a if r.get('hard_negative')]
        if h: out[-1]['hard_negative_n']=len(h); out[-1]['hard_negative_false_positive_rate']=float(np.mean([r['p']>=.5 for r in h]))
    return out
def write_csv(path,rows):
    keys=list(dict.fromkeys(k for r in rows for k in r))
    with path.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=keys); w.writeheader(); w.writerows(rows)
def synth(root,protocol):
    allpred=[]; allraw=[]; times=[]; integrity=[]
    for seed in protocol['seeds']:
        sets={s:generate(seed*100+j,s,n) for j,(s,n) in enumerate(protocol['synthetic']['worlds'].items())}
        for a in sets.values(): allraw.extend(a)
        tr=sets['train']; ca=sets['calibration']; y=np.array([c['y'] for c in tr]); yc=np.array([c['y'] for c in ca])
        x=np.array([features(c) for c in tr]); xc=np.array([features(c) for c in ca])
        fs={s:np.array([features(c) for c in a]) for s,a in sets.items()}
        sf={s:np.column_stack([fs[s],[c['F'] for c in a]]) for s,a in sets.items()}
        methods={
          'Boolean':lambda a:np.array([float(any(decoded(e)>0 for e in c['reports'])) for c in a]),
          'ActivationOnly':lambda a:np.array([float(any(e['active'] for e in c['reports'])) for c in a]),
          'SignedVotes':lambda a:expit(np.array([sum(decoded(e) for e in c['reports']) for c in a])),
          'FourState':lambda a:np.array([.8 if z[10] and not z[11] else .2 if z[11] and not z[10] else .5 for z in map(features,a)]),
          'GraphBayes':lambda a:np.array([score(c) for c in a]),
          'PortalProb':lambda a:np.array([score(c,recursive=True) for c in a]),
          'NoLineage':lambda a:np.array([score(c,lineage=False) for c in a]),
          'NoContext':lambda a:np.array([score(c,context=False) for c in a]),
          'NoTime':lambda a:np.array([score(c,temporal=False) for c in a]),
          'NoPathSign':lambda a:np.array([score(c,pathsign=False) for c in a]),
          'AffectOnly':lambda a:np.array([c['F'] for c in a])}
        model_specs={'GraphLogistic':(LogisticRegression(C=1,max_iter=1000),False),'GraphHGB':(HistGradientBoostingClassifier(max_iter=100,max_leaf_nodes=15,l2_regularization=1,random_state=seed),False),'GraphHGB_F':(HistGradientBoostingClassifier(max_iter=100,max_leaf_nodes=15,l2_regularization=1,random_state=seed),True)}
        for name,(model,usef) in model_specs.items():
            start=time.perf_counter(); model.fit(sf['train'] if usef else x,y)
            times.append(dict(seed=seed,method=name,phase='fit',seconds=time.perf_counter()-start,n=len(tr)))
            # all case vectors supplied in this closure share one known split.
            methods[name]=lambda a,m=model,f=usef:m.predict_proba(np.array([features(c)+([c['F']] if f else []) for c in a]))[:,1]
        for name,fn in methods.items():
            cp=fn(ca); cal=calibrator(cp,yc)
            for split in ['test','shift']:
                a=sets[split]; start=time.perf_counter(); p=fn(a); seconds=time.perf_counter()-start; q=cal(p)
                times.append(dict(seed=seed,method=name,phase=split,seconds=seconds,n=len(a)))
                for c,raw,prob in zip(a,p,q):
                    hard=c['y']==0 and any(decoded(e)>0 for e in c['reports'])
                    for suffix,v in [('_raw',raw),('',prob)]:
                        allpred.append(dict(seed=seed,id=c['id'],world=c['world'],split=split,method=name+suffix,y=c['y'],p=float(v),hard_negative=hard))
        p=np.array([score(c) for c in sets['test']]); ys=np.array([c['y'] for c in sets['test']]); shuffled=np.random.default_rng(seed+9).permutation(ys)
        integrity.append(dict(seed=seed,recursive_iterative_max_abs=float(np.max(abs(p-np.array([score(c,recursive=True) for c in sets['test']])))),shuffled_label_auc=float(roc_auc_score(shuffled,p)),max_edge_occurrences=max(sum(len(e['edges']) for e in c['reports']) for a in sets.values() for c in a),split_worlds_disjoint=len(set(c['world'] for a in sets.values() for c in a))==90))
        print('synthetic seed',seed,'done',flush=True)
    with gzip.open(root/'synthetic_source.jsonl.gz','wt') as f:
        for c in allraw:f.write(json.dumps(c,separators=(',',':'))+'\n')
    write_csv(root/'synthetic_predictions.csv',allpred); write_csv(root/'timings.csv',times)
    dump(root/'synthetic_metrics.json',summarize(allpred)); dump(root/'integrity.json',integrity)
    # Paired bootstrap over worlds, not correlated cases; no tuning against this result.
    diffs={}
    for split in ['test','shift']:
      base={r['id']:r for r in allpred if r['method']=='GraphBayes' and r['split']==split}
      for name in ['PortalProb','Boolean','FourState','GraphHGB','GraphLogistic','NoLineage','NoContext','NoTime','GraphHGB_F']:
        worlds={}
        for r in allpred:
          if r['method']!=name or r['split']!=split:continue
          b=base[r['id']]; worlds.setdefault(r['world'],[]).append((r['p']-r['y'])**2-(b['p']-b['y'])**2)
        v=np.array([np.mean(z) for z in worlds.values()]); rng=np.random.default_rng(991); bs=np.mean(rng.choice(v,(1000,len(v))),axis=1)
        diffs[split+':'+name+'-GraphBayes']=dict(brier_delta=float(v.mean()),ci95=np.quantile(bs,[.025,.975]).tolist(),worlds=len(v))
    dump(root/'paired_bootstrap.json',diffs)

def graph_probs(xtr,ytr,xquery,depth):
    # Query only attaches to train graph. No test/calibration labels or query-query edges.
    def weights(a,b,selfgraph=False):
        d=euclidean_distances(a,b,squared=True)
        if selfgraph:np.fill_diagonal(d,np.inf)
        ix=np.argsort(d,axis=1)[:,:10]; v=np.exp(-np.take_along_axis(d,ix,axis=1)/4)
        v/=v.sum(axis=1,keepdims=True); w=np.zeros_like(d); np.put_along_axis(w,ix,v,axis=1)
        return w
    w=weights(xquery,xtr); f=ytr.astype(float)
    if depth>1:
        t=weights(xtr,xtr,True)
        for _ in range(depth-1):f=.5*ytr+.5*t@f
    return np.clip(w@f,1e-5,1-1e-5)
def digits(root,protocol):
    data=load_digits(); mask=data.target<2; ids=np.where(mask)[0]; x=data.data[mask]/16; y=data.target[mask]
    np.savez_compressed(root/'digits_source.npz',x=x,y=y,original_ids=ids)
    pred=[]; splits=[]; times=[]
    for seed in protocol['seeds']:
        tr,rest=train_test_split(np.arange(len(y)),test_size=.4,stratify=y,random_state=seed)
        ca,te=train_test_split(rest,test_size=.5,stratify=y[rest],random_state=seed)
        splits.append(dict(seed=seed,train=ids[tr].tolist(),calibration=ids[ca].tolist(),test=ids[te].tolist()))
        rng=np.random.default_rng(seed); shift=np.clip(rotate(x[te].reshape(-1,8,8),20,axes=(1,2),reshape=False,order=1).reshape(-1,64)+rng.normal(0,.12,(len(te),64)),0,1)
        models={'PixelLogistic':(LogisticRegression(C=1,max_iter=1000),False),'PixelRBF':(SVC(C=10,gamma='scale'),False),'BitRBF':(SVC(C=10,gamma='scale'),True)}
        methods={}
        for name,(m,bits) in models.items():
            start=time.perf_counter(); m.fit((x[tr]>.5).astype(float) if bits else x[tr],y[tr]); times.append(dict(seed=seed,method=name,fit_seconds=time.perf_counter()-start))
            methods[name]=lambda q,m=m,b=bits:expit(m.decision_function((q>.5).astype(float) if b else q))
        methods['GraphKNN']=lambda q:graph_probs(x[tr],y[tr],q,1)
        methods['PortalDiffusion3']=lambda q:graph_probs(x[tr],y[tr],q,3)
        for name,fn in methods.items():
            cal=calibrator(fn(x[ca]),y[ca])
            for split,qx in [('test',x[te]),('shift',shift)]:
                start=time.perf_counter(); raw=fn(qx); p=cal(raw); times.append(dict(seed=seed,method=name,split=split,infer_seconds=time.perf_counter()-start))
                for j,pr in zip(te,p):pred.append(dict(seed=seed,id=int(ids[j]),split=split,method=name,y=int(y[j]),p=float(pr)))
                # Context 1 reverses assertion semantics, so probability must complement.
                for j,pr in zip(te,p):
                    pred.append(dict(seed=seed,id=int(ids[j]),split=split+'_reversed_ungrounded',method=name,y=int(1-y[j]),p=float(pr)))
                    pred.append(dict(seed=seed,id=int(ids[j]),split=split+'_reversed_grounded',method=name,y=int(1-y[j]),p=float(1-pr)))
        print('digits seed',seed,'done',flush=True)
    write_csv(root/'digits_predictions.csv',pred);dump(root/'digits_metrics.json',summarize(pred));dump(root/'digits_splits.json',splits);dump(root/'digits_timings.json',times)
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--out',type=Path,default=HERE/'results');args=parser.parse_args();root=args.out;root.mkdir(parents=True,exist_ok=True)
    proto=json.loads((HERE/'PROTOCOL.json').read_text()); freeze=HERE/'FREEZE.json'
    if not freeze.exists():
        # Freeze code/protocol and independent dataset row splits BEFORE any model fit.
        data=load_digits(); ids=np.where(data.target<2)[0]; y=data.target[ids]; splits=[]
        for seed in proto['seeds']:
            tr,r=train_test_split(np.arange(len(y)),test_size=.4,stratify=y,random_state=seed);ca,te=train_test_split(r,test_size=.5,stratify=y[r],random_state=seed)
            splits.append(dict(seed=seed,train=ids[tr].tolist(),calibration=ids[ca].tolist(),test=ids[te].tolist()))
        dump(freeze,dict(utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),protocol_sha256=sha(HERE/'PROTOCOL.json'),code_sha256=sha(Path(__file__)),digits_splits=splits))
    assert json.loads(freeze.read_text())['code_sha256']==sha(Path(__file__)), 'Code changed after freeze'
    start=time.perf_counter();synth(root,proto);digits(root,proto)
    dump(root/'environment.json',dict(python=platform.python_version(),numpy=np.__version__,scipy=scipy.__version__,sklearn=sklearn.__version__,platform=platform.platform(),elapsed_seconds=time.perf_counter()-start,cpu_threads={k:os.environ.get(k) for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']}))
if __name__=='__main__':main()
