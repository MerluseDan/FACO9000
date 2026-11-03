import os
os.environ.setdefault('OMP_NUM_THREADS','1');os.environ.setdefault('OPENBLAS_NUM_THREADS','1');os.environ.setdefault('MKL_NUM_THREADS','1')
import json,time,platform,csv,gzip,hashlib,argparse
from pathlib import Path
from collections import defaultdict
import numpy as np
import scipy,sklearn
from scipy.special import expit,logit
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score,log_loss
ROOT=Path(__file__).parent
AGES=[0,1,3,8]
def dump(p,x):p.write_text(json.dumps(x,indent=2,sort_keys=True)+'\n')
def hashfile(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def decode(e):return int(e['leaf']*np.prod(e['edges']))
def eligible(c):
 d={}
 for e in c['reports']:
  if e['active'] and e['context']==c['context']:d.setdefault(e['source'],e)
 return list(d.values())
def generate(seed,proto):
 rng=np.random.default_rng(seed);out=defaultdict(list);truth={}
 for world in range(proto['worlds']+proto['unseen_worlds']):
  unseen=world>=proto['worlds'];rates=rng.uniform(.55,.9,8);rates[-2:]=rng.uniform(.2,.4,2)
  states=np.zeros((282,2),int);states[0]=rng.integers(2,size=2)
  for t in range(1,282):states[t]=states[t-1]^(rng.random(2)<(.2 if t>=230 and not unseen else .08))
  truth[str(world)]=dict(hidden_rates=rates.tolist(),latent_states=states.tolist())
  for t in range(20,280):
   split=next((s for s,(lo,hi) in proto['splits'].items() if s!='unseen' and lo<=t<hi),None)
   if unseen:split='unseen' if 170<=t<270 else None
   if split is None:continue
   for context in range(2):
    reports=[]
    for source in range(8):
     if rng.random()<.15:continue
     age=int(rng.choice(AGES));rc=context if rng.random()<.8 else 1-context
     r=1-rates[source] if t>=230 and not unseen and source<4 else rates[source]
     vote=2*(int(states[t-age,rc])^int(rng.random()>r))-1
     edges=rng.choice([-1,1],int(rng.integers(1,4))).tolist();leaf=vote*int(np.prod(edges));active=bool(rng.random()<.9)
     for cp in range(int(rng.integers(1,4))):reports.append(dict(source=source,copy=cp,age=age,observed_time=t-age,context=rc,active=active,leaf=leaf,edges=edges))
    c=dict(id=f'{seed}:{world}:{t}:{context}',world=f'{seed}:{world}',time=t,target_time=t+1,context=context,split=split,y=int(states[t+1,context]),reports=reports)
    out[split].append(c)
 return out,truth
def fit_weights(cases):
 yes=np.full((8,4),2.);total=np.full((8,4),4.)
 for c in cases:
  for e in eligible(c):
   k=AGES.index(e['age']);yes[e['source'],k]+=int((decode(e)>0)==c['y']);total[e['source'],k]+=1
 rates=yes/total
 return np.log(rates/(1-rates)),rates
def ordered(c,weights):return sorted(eligible(c),key=lambda e:(-abs(weights[e['source'],AGES.index(e['age'])]),e['source']))[:4]
def vote_weight(e,w):return decode(e)*w[e['source'],AGES.index(e['age'])]
def walk_recursive(es,w,i=0,total=0.):
 if i>=len(es) or (i>=2 and abs(total)>=logit(.85)):return float(expit(total)),i
 return walk_recursive(es,w,i+1,total+vote_weight(es[i],w))
def walk_iterative(es,w):
 total=0.;n=0
 for e in es:
  total+=vote_weight(e,w);n+=1
  if n>=2 and abs(total)>=logit(.85):break
 return float(expit(total)),n
def vector(c,w):
 es=ordered(c,w);v=np.zeros(41)
 for e in es:
  s=e['source'];k=AGES.index(e['age']);v[s*4+k]=decode(e);v[32+s]=1
 v[40]=sum(vote_weight(e,w) for e in es)
 return v
def metric(y,p):
 y=np.array(y);p=np.clip(p,1e-7,1-1e-7);pr=p>=.5;keep=np.maximum(p,1-p)>=.8
 ece=0.
 for j in range(10):
  mask=np.minimum((p*10).astype(int),9)==j
  if mask.any():ece+=mask.mean()*abs(y[mask].mean()-p[mask].mean())
 return dict(n=len(y),auc=float(roc_auc_score(y,p)),brier=float(np.mean((p-y)**2)),accuracy=float(np.mean(pr==y)),logloss=float(log_loss(y,p,labels=[0,1])),ece10=float(ece),coverage80=float(keep.mean()),risk80=float(np.mean(pr[keep]!=y[keep])) if keep.any() else None)
def csvwrite(p,rows):
 with p.open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def run(out):
 out.mkdir(parents=True,exist_ok=True);proto=json.loads((ROOT/'PROTOCOL.json').read_text());t0=time.perf_counter()
 freeze=ROOT/'FREEZE.json'
 if not freeze.exists():dump(freeze,dict(utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),code_sha256=hashfile(Path(__file__)),protocol_sha256=hashfile(ROOT/'PROTOCOL.json')))
 assert json.loads(freeze.read_text())['code_sha256']==hashfile(Path(__file__))
 preds=[];measure=[];controls=[];parameters=[];allraw=[];hidden={};times=[]
 for seed in proto['seeds']:
  sets,worldtruth=generate(seed,proto);hidden[str(seed)]=worldtruth
  for a in sets.values():allraw.extend(a)
  tr=sets['train'];ca=sets['calibration'];w,r=fit_weights(tr);parameters.append(dict(seed=seed,learned_accuracy=r.tolist(),log_likelihood=w.tolist()))
  trainx=np.array([vector(c,w) for c in tr]);trainy=np.array([c['y'] for c in tr])
  models={}
  for name,m in [('GraphLogistic4',LogisticRegression(C=1,max_iter=1000)),('GraphHGB4',HistGradientBoostingClassifier(max_iter=100,max_leaf_nodes=15,l2_regularization=1,random_state=seed))]:
   start=time.perf_counter();m.fit(trainx,trainy);times.append(dict(seed=seed,method=name,phase='fit',seconds=time.perf_counter()-start));models[name]=m
  def predict(cases,name):
   if name in models:return models[name].predict_proba(np.array([vector(c,w) for c in cases]))[:,1],np.array([len(ordered(c,w)) for c in cases])
   a=[];ns=[]
   for c in cases:
    es=ordered(c,w)
    if name=='Majority4':p=float(expit(sum(decode(e) for e in es)));n=len(es)
    elif name=='LearnedGraph4':p=float(expit(sum(vote_weight(e,w) for e in es)));n=len(es)
    elif name=='AdaptivePortal':p,n=walk_recursive(es,w)
    elif name=='GraphSequential':p,n=walk_iterative(es,w)
    a.append(p);ns.append(n)
   return np.array(a),np.array(ns)
  for name in proto['methods']:
   cp,_=predict(ca,name);cal=LogisticRegression(C=1000,max_iter=1000).fit(logit(np.clip(cp,1e-6,1-1e-6)).reshape(-1,1),[c['y'] for c in ca])
   for split in ['chronological','unseen','shift']:
    cases=sets[split];start=time.perf_counter();p,ns=predict(cases,name);seconds=time.perf_counter()-start;q=cal.predict_proba(logit(np.clip(p,1e-6,1-1e-6)).reshape(-1,1))[:,1]
    times.append(dict(seed=seed,method=name,phase=split,seconds=seconds))
    ys=[c['y'] for c in cases]
    for suffix,pr in [('',q),('_raw',p)]:
     met=dict(seed=seed,split=split,method=name+suffix,**metric(ys,pr),mean_decoded_votes=float(ns.mean()),mean_report_headers=float(np.mean([len(c['reports']) for c in cases])))
     hard=[i for i,c in enumerate(cases) if c['y']==0 and any(decode(e)>0 for e in eligible(c))]
     met.update(hard_negative_n=len(hard),hard_negative_fpr=float(np.mean(pr[hard]>=.5)));measure.append(met)
     for c,z,n in zip(cases,pr,ns):preds.append(dict(seed=seed,id=c['id'],world=c['world'],time=c['time'],split=split,method=name+suffix,y=c['y'],p=float(z),decoded_votes=int(n)))
  evalcases=sets['chronological']+sets['unseen']+sets['shift'];pa,na=predict(evalcases,'AdaptivePortal');pg,ng=predict(evalcases,'GraphSequential')
  labels=np.array([c['y'] for c in evalcases]);null=np.random.default_rng(seed+71).permutation(labels)
  controls.append(dict(seed=seed,source_cases=sum(map(len,sets.values())),chronological_future_exclusion=all(e['observed_time']<=c['time']<c['target_time'] for a in sets.values() for c in a for e in c['reports']),max_votes=int(max(na)),recursive_sequential_max_difference=float(max(abs(pa-pg))),vote_counts_equal=bool(np.array_equal(na,ng)),shuffled_auc=float(roc_auc_score(null,pa)),unseen_world_disjoint=not bool(set(c['world'] for c in sets['train'])&set(c['world'] for c in sets['unseen']))))
  print('seed',seed,'complete',flush=True)
 with gzip.open(out/'source_cases.jsonl.gz','wt') as f:
  for c in allraw:f.write(json.dumps(c,separators=(',',':'))+'\n')
 with gzip.open(out/'latent_gold.json.gz','wt') as f:json.dump(hidden,f,separators=(',',':'))
 csvwrite(out/'predictions.csv',preds);dump(out/'metrics.json',measure);dump(out/'learned_parameters.json',parameters);dump(out/'controls.json',controls);dump(out/'timings.json',times)
 # Cluster all cases from a world together, including serially dependent time points.
 diffs={}
 for split in ['chronological','unseen','shift']:
  base={r['id']:r for r in preds if r['method']=='AdaptivePortal' and r['split']==split}
  for method in ['Majority4','LearnedGraph4','GraphSequential','GraphLogistic4','GraphHGB4']:
   clusters=defaultdict(list)
   for r in preds:
    if r['method']==method and r['split']==split:
     b=base[r['id']];clusters[r['world']].append((b['p']-b['y'])**2-(r['p']-r['y'])**2)
   a=np.array([np.mean(v) for v in clusters.values()]);rng=np.random.default_rng(817);draws=np.mean(rng.choice(a,(1000,len(a))),axis=1)
   diffs[split+':AdaptivePortal-'+method]=dict(delta=float(a.mean()),ci95=np.quantile(draws,[.025,.975]).tolist(),world_clusters=len(a))
 dump(out/'paired_bootstrap.json',diffs)
 dump(out/'environment.json',dict(python=platform.python_version(),numpy=np.__version__,scipy=scipy.__version__,sklearn=sklearn.__version__,platform=platform.platform(),elapsed_seconds=time.perf_counter()-t0,accelerator='CPU; no CUDA calls',threads={k:os.environ.get(k) for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']}))
 print('COMPLETE',json.dumps(dict(cases=len(allraw),prediction_rows=len(preds),elapsed=time.perf_counter()-t0)),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,default=ROOT/'results');args=p.parse_args();run(args.out)
