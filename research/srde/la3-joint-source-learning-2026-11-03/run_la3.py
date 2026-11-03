"""Frozen LA3 finite Bayesian calibration and budgeted decisions; standard library."""
import itertools,json,math,random,csv,gzip,time,sys,platform
from pathlib import Path
from functools import lru_cache
import decision_core as core
R=Path(__file__).parent
THETA=list(itertools.product([.55,.65,.8,.95],[.1,.2,.5,.8],[0.,.25,.5,.75,.8,1.]))
HIDDEN=list(itertools.product([0,1],repeat=3)) # event Y, copy state L, potential audit Z
METHODS=['FixedFresh','QOnlyFull','JointMAPFull','JointMeanFull','JointBMAFull','JointBMAFresh','NoAuditTrainFresh','SRDERecursive','KnownAll']
def conditions():
 c=[{'a':a,'pi':pi,'q':q,'family':'on_grid'} for a,pi,q in itertools.product([.65,.8],[.2,.8],[1.,.5])]
 c += [{'a':.7,'pi':.35,'q':.8,'family':'off_grid'},{'a':.9,'pi':.65,'q':.2,'family':'off_grid'}]
 return [{'id':f'C{i:02d}',**x} for i,x in enumerate(c)]
def initial_lik(x,y,l,a):
 u,v,w=core.bits(x)
 return core.bern(u,y,a)*core.bern(w,y,a)*(int(u==v) if l else core.bern(v,y,a))
def reference_agrees(x,y,z):
 v=[(.2 if l else .8)*initial_lik(x,y,l,.8) for l in [0,1]]
 return z==int(v[1]>v[0])
def calibration(seed,c):
 rng=random.Random(seed*1000+int(c['id'][1:]));m=core.Model(pi=c['pi'],q=c['q'],acc=c['a']);raw=[];pack=[];nr=0
 for i in range(128):
  y,l,x,f0,f1,z=core.draw(rng,m);u=rng.random()
  req=i+5<=128 and nr<32 and u<(.8 if reference_agrees(x,y,z) else .1);nr+=req
  raw.append({'issue':i,'y':y,'lineage':l,'initial':x,'audit':z,'selection_u':u})
  pack.append({'issue':i,'initial':x,'audit':z,'y_observed':y if i+5<=128 else None,'reference_requested':int(req),'lineage_observed':l if req and i+17<=128 else None})
 return raw,pack
def fit(packets,mode):
 theta=[(.8,.2,q) for q in [0.,.25,.5,.75,.8,1.]] if mode=='qonly' else THETA
 logs=[]
 for a,pi,q in theta:
  logp=0.
  for r in packets:
   xs=r['initial'];ys=[0,1] if r['y_observed'] is None else [r['y_observed']]
   ls=[0,1] if mode=='noaudit' or r['lineage_observed'] is None else [r['lineage_observed']]
   v=0.
   for y in ys:
    for l in ls:
     v+=.5*(pi if l else 1-pi)*initial_lik(xs,y,l,a)*(1 if mode=='noaudit' else core.bern(r['audit'],l,q))
   logp+=math.log(v) if v>0 else -math.inf
  logs.append(logp)
 top=max(logs);weights=[math.exp(x-top) for x in logs];total=sum(weights)
 return [(a,pi,q,w/total) for (a,pi,q),w in zip(theta,weights)]
def predictive(weighted):
 # Integrate global parameter uncertainty before conditioning on the new case.
 return tuple(tuple(sum(w*.5*(pi if l else 1-pi)*initial_lik(x,y,l,a)*core.bern(z,l,q) for a,pi,q,w in weighted) for y,l,z in HIDDEN) for x in range(8))
class Planner:
 def __init__(self,joint,allow=True):
  self.joint=joint;self.allow=allow
  self.belief=lru_cache(None)(self._belief);self.edges=lru_cache(None)(self._edges)
  self.recursive=lru_cache(None)(self._recursive)
  seen=set();stack=[self.start(x) for x in range(8)]
  while stack:
   s=stack.pop()
   if s in seen:continue
   seen.add(s)
   for action in self.actions(s):stack.extend(ns for p,ns in self.edges(s,action))
  self.table={}
  for s in sorted(seen,key=lambda x:-x[0]):
   best=self.terminal(s)[0];choice='S'
   for action in self.actions(s):
    risk=self.cost(action)+sum(p*self.table[ns][0] for p,ns in self.edges(s,action))
    if risk<best-1e-12:best,choice=risk,action
   self.table[s]=(best,choice)
 @staticmethod
 def start(x):return (0,x,(),-1)
 @staticmethod
 def cost(action):return .015 if action=='F' else .00375
 def _belief(self,s):
  t,x,fs,az=s
  w=[v*(int(z==az) if az!=-1 else 1)*math.prod(core.bern(f,y,.7) for f in fs) for v,(y,l,z) in zip(self.joint[x],HIDDEN)]
  total=sum(w);return tuple(v/total for v in w) if total else (0.,)*8
 def prob(self,s):
  b=self.belief(s);return sum(w for w,(y,l,z) in zip(b,HIDDEN) if y) if sum(b)>0 else .5
 def terminal(self,s):
  p=self.prob(s);return min(p*(1-p),.15),p,int(p*(1-p)>.15)
 def actions(self,s):
  t,x,fs,z=s
  if t>=3:return []
  return (['F'] if len(fs)<2 else [])+(['A'] if self.allow and z==-1 else [])
 def _edges(self,s,action):
  t,x,fs,az=s;out=[]
  for v in [0,1]:
   p=sum(w*(core.bern(v,y,.7) if action=='F' else int(z==v)) for w,(y,l,z) in zip(self.belief(s),HIDDEN))
   if p>0:out.append((p,(t+1,x,fs+(v,) if action=='F' else fs,v if action=='A' else az)))
  return tuple(out)
 def _recursive(self,s):
  best=self.terminal(s)[0];choice='S'
  for action in self.actions(s):
   v=self.cost(action)+sum(p*self.recursive(ns)[0] for p,ns in self.edges(s,action))
   if v<best-1e-12:best,choice=v,action
  return best,choice
 def run(self,case,recursive=False):
  y,l,x,f0,f1,z=case;s=self.start(x);trace='';cost=0.
  while s[0]<3:
   action=(self.recursive(s) if recursive else self.table[s])[1]
   if action=='S':break
   t,x,fs,az=s;trace+=action;cost+=self.cost(action)
   s=(t+1,x,fs+((f0,f1)[len(fs)],) if action=='F' else fs,z if action=='A' else az)
  risk,p,abstain=self.terminal(s);brier=(p-y)**2
  return {'p':p,'abstain':abstain,'zero_model_likelihood':int(sum(self.belief(s))==0),'trace':trace,'cost':cost,'brier':brier,'loss':(.15 if abstain else brier)+cost}
def dump(path,rows):
 with gzip.open(path,'wt',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def summary(rows):
 mass=sum(r['weight'] for r in rows)
 v={k:sum(r['weight']*r[k] for r in rows)/mass for k in ['loss','brier','cost']}
 v['coverage']=sum(r['weight']*(1-r['abstain']) for r in rows)/mass
 v['audit_rate']=sum(r['weight']*('A' in r['trace']) for r in rows)/mass
 bb=[[0.,0.,0.] for _ in range(10)]
 for r in rows:
  b=bb[min(int(r['p']*10),9)];w=r['weight'];b[0]+=w;b[1]+=w*r['p'];b[2]+=w*r['y']
 v['ece10']=sum(abs(b[1]-b[2]) for b in bb)/mass
 return v
def main(out):
 start=time.perf_counter();P=json.loads((R/'PROTOCOL.json').read_text());assert conditions()==P['conditions']
 out.mkdir(parents=True,exist_ok=True)
 rawrows=[];packets=[];post=[];joints=[];exact=[];sample=[];sources=[];atoms=[];metrics=[];fits=[]
 for c in P['conditions']:
  m=core.Model(pi=c['pi'],q=c['q'],acc=c['a']);aa=list(core.atoms(m))
  atoms.extend({'condition':c['id'],'atom':i,'weight':w,'y':v[0],'lineage':v[1],'initial':v[2],'fresh0':v[3],'fresh1':v[4],'audit':v[5]} for i,(v,w) in enumerate(aa))
  for seed in P['seeds']:
   world=f"{c['id']}-{seed}";raw,pack=calibration(seed,c)
   rawrows.extend({'world':world,**r} for r in raw);packets.extend({'world':world,**r} for r in pack)
   trained={k:fit(pack,k) for k in ['joint','qonly','noaudit']}
   for k,weighted in trained.items():post.extend({'world':world,'fit':k,'a':a,'pi':pi,'q':q,'weight':w} for a,pi,q,w in weighted)
   rng=random.Random(seed*1000+int(c['id'][1:])+20000000);cases=[core.draw(rng,m) for _ in range(128)]
   sources.extend({'world':world,'case':i,'y':v[0],'lineage':v[1],'initial':v[2],'fresh0':v[3],'fresh1':v[4],'audit':v[5]} for i,v in enumerate(cases))
   cal_cost=.48+.003*sum(p['reference_requested'] for p in pack)
   planners={}
   for name in METHODS:
    if name=='FixedFresh':weighted=[(.8,.2,1.,1.)]
    elif name=='KnownAll':weighted=[(c['a'],c['pi'],c['q'],1.)]
    elif name=='QOnlyFull':weighted=trained['qonly']
    elif name=='NoAuditTrainFresh':weighted=trained['noaudit']
    elif name=='JointMAPFull':
     a,pi,q,w=max(trained['joint'],key=lambda x:x[3]);weighted=[(a,pi,q,1.)]
    elif name=='JointMeanFull':
     weighted=[tuple(sum(v[j]*v[3] for v in trained['joint']) for j in range(3))+(1.,)]
    else:weighted=trained['joint']
    j=predictive(weighted);allow=name not in ['FixedFresh','JointBMAFresh','NoAuditTrainFresh']
    cachekey=(j,allow)
    if cachekey not in planners:planners[cachekey]=Planner(j,allow)
    planner=planners[cachekey]
    joints.extend({'world':world,'method':name,'initial':x,'y':y,'lineage':l,'audit':z,'mass':v} for x,vv in enumerate(j) for v,(y,l,z) in zip(vv,HIDDEN))
    fits.append({'world':world,'condition':c['id'],'method':name,'a_mean':sum(a*w for a,pi,q,w in weighted),'pi_mean':sum(pi*w for a,pi,q,w in weighted),'q_mean':sum(q*w for a,pi,q,w in weighted),'calibration_cost':0. if name in ['FixedFresh','KnownAll','NoAuditTrainFresh'] else cal_cost})
    for split,cc,container in [('exact',aa,exact),('sample',[(v,1.) for v in cases],sample)]:
     rr=[]
     for i,(case,w) in enumerate(cc):
      r={'world':world,'condition':c['id'],'method':name,'case':i,'y':case[0],'weight':w,**planner.run(case,name=='SRDERecursive')}
      rr.append(r);container.append(r)
     s=summary(rr)
     for h in P['amortization_horizons']:
      cost=0. if name in ['FixedFresh','KnownAll','NoAuditTrainFresh'] else cal_cost
      metrics.append({'world':world,'condition':c['id'],'family':c['family'],'method':name,'split':split,'horizon':h,**s,'calibration_cost':cost,'total_loss':s['loss']+cost/h})
 for n,rows in [('calibration_raw',rawrows),('calibration_packets',packets),('parameter_posteriors',post),('predictive_joints',joints),('exact_atoms',atoms),('sample_cases',sources),('exact_predictions',exact),('sample_predictions',sample),('world_metrics',metrics),('fits',fits)]:dump(out/(n+'.csv.gz'),rows)
 agg=[]
 for fam in ['all','on_grid','off_grid']:
  for split,h,name in itertools.product(['exact','sample'],P['amortization_horizons'],METHODS):
   rr=[r for r in metrics if r['split']==split and r['method']==name and r['horizon']==h and (fam=='all' or r['family']==fam)]
   agg.append({'family':fam,'split':split,'horizon':h,'method':name,'worlds':len(rr),**{k:sum(r[k] for r in rr)/len(rr) for k in ['loss','brier','cost','coverage','audit_rate','ece10','calibration_cost','total_loss']}})
 (out/'metrics.json').write_text(json.dumps(agg,indent=2,sort_keys=True)+'\n')
 boot=[]
 for fam in ['all','on_grid','off_grid']:
  for baseline in ['QOnlyFull','JointBMAFresh','NoAuditTrainFresh','JointMAPFull','JointMeanFull']:
   groups=[]
   for c in P['conditions']:
    if fam!='all' and c['family']!=fam:continue
    a={r['world']:r['total_loss'] for r in metrics if r['condition']==c['id'] and r['method']=='JointBMAFull' and r['split']=='exact' and r['horizon']==512}
    b={r['world']:r['total_loss'] for r in metrics if r['condition']==c['id'] and r['method']==baseline and r['split']=='exact' and r['horizon']==512}
    groups.append([a[k]-b[k] for k in sorted(a)])
   rng=random.Random(88321);vals=[]
   for _ in range(1000):vals.append(sum(sum(g[rng.randrange(len(g))] for i in g) for g in groups)/sum(map(len,groups)))
   vals.sort();boot.append({'family':fam,'baseline':baseline,'horizon':512,'delta':sum(map(sum,groups))/sum(map(len,groups)),'lower':vals[25],'upper':vals[974]})
 (out/'bootstrap.json').write_text(json.dumps(boot,indent=2,sort_keys=True)+'\n')
 (out/'environment.json').write_text(json.dumps({'python':sys.version,'platform':platform.platform(),'runtime_seconds':time.perf_counter()-start,'worlds':len(P['conditions'])*len(P['seeds']),'calibration_cases':len(rawrows),'sample_cases':len(sources),'exact_forecasts':len(exact),'sample_forecasts':len(sample)},indent=2)+'\n')
 print((out/'environment.json').read_text())
if __name__=='__main__':main(Path(sys.argv[1]) if len(sys.argv)>1 else R/'results')
