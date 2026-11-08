"""LA4: observational twins, query semantics and abstention. Standard library."""
import math,itertools,json,csv,gzip,random,time,sys,platform
from pathlib import Path
from functools import lru_cache
R=Path(__file__).parent
PI=.2;ALPHA=.9;ABSTAIN=.15;QUERY_COST=.005;HORIZON=128;BUDGET=4
METHODS=['LiteralBits','RobustAbstain','ProvenanceOnly','UniformAnchors','ConfidentAnchors','GreedyDecision','EntropyGreedy','TwoStepTable','TwoStepRecursive','SRDETypedGate','KnownOrientation']
def bern(v,t,a):return a if v==t else 1-a
def likelihood(x,b,l,a):
 u=(x>>2)&1;v=(x>>1)&1;w=x&1
 return .5*(PI if l else 1-PI)*bern(u,b,a)*bern(w,b,a)*(int(u==v) if l else bern(v,b,a))
def conditions():
 return [{'id':f'C{i:02d}','a':a,'reference':ref,'orientation':list(ori),'family':'independent' if ref=='accurate' else 'uninformative' if ref=='random' else 'dependent_echo'} for i,(a,ref,ori) in enumerate(itertools.product([.65,.8],['accurate','random','echo'],itertools.product([0,1],repeat=2)))]
def draw(rng,a):
 b=int(rng.random()<.5);l=int(rng.random()<PI)
 u=b if rng.random()<a else 1-b
 v=u if l else b if rng.random()<a else 1-b
 w=b if rng.random()<a else 1-b
 return b,l,4*u+2*v+w
def pool(seed,c):
 # The same observable pool is coupled across all orientations and reference modes.
 rng=random.Random(seed*100+int(round(c['a']*100)))
 rows=[]
 for i in range(8):
  b,l,x=draw(rng,c['a']);u=rng.random();context=i//4;y=b^c['orientation'][context]
  response=(y if u<(.9 if c['reference']=='accurate' else .5) else 1-y) if c['reference']!='echo' else (x>>2)&1
  rows.append({'index':i,'context':context,'x':x,'proxy_b':b,'lineage':l,'y':y,'anchor_response':response,'reference_u':u})
 return rows
class Agent:
 def __init__(self,xs,a):
  self.xs=tuple(xs);self.a=a
  self.marginal=tuple(sum(likelihood(x,b,l,a) for b,l in itertools.product([0,1],repeat=2)) for x in range(8))
  self.bp=tuple(sum(likelihood(x,1,l,a) for l in [0,1])/self.marginal[x] for x in range(8))
  self.weights=lru_cache(None)(self._weights)
  self.orientation=lru_cache(None)(self._orientation)
  self.risk=lru_cache(None)(self._risk)
  self.outcomes=lru_cache(None)(self._outcomes)
  self.greedy=lru_cache(None)(self._greedy)
  self.recursive=lru_cache(None)(self._recursive)
  self.table2=lru_cache(None)(self._table2)
 @staticmethod
 def initial():return (-1,)*16 # (anchor, lineage) for each of eight cases
 def _weights(self,i,r,anchor,lineage):
  x=self.xs[i]
  return tuple(likelihood(x,b,l,self.a)*(bern(anchor,b^r,ALPHA) if anchor!=-1 else 1)*(int(lineage==l) if lineage!=-1 else 1) for b,l in itertools.product([0,1],repeat=2))
 def _orientation(self,state):
  result=[]
  for context in [0,1]:
   values=[]
   for r in [0,1]:
    values.append(math.prod(sum(self.weights(i,r,state[2*i],state[2*i+1])) for i in range(context*4,context*4+4)))
   total=sum(values);result.append(values[1]/total if total else .5)
  return tuple(result)
 def _risk(self,state):
  rr=self.orientation(state)
  return sum(.5*mass*min((p:=self.bp[x]*(1-rr[g])+(1-self.bp[x])*rr[g])*(1-p),ABSTAIN) for g in [0,1] for x,mass in enumerate(self.marginal))
 @staticmethod
 def actions(state):return tuple(i for i in range(16) if state[i]==-1)
 @staticmethod
 def update(state,action,value):
  s=list(state);s[action]=value;return tuple(s)
 def _outcomes(self,state,action):
  i=action//2;g=i//4;rr=self.orientation(state)[g];prob1=0.
  for r,pr in [(0,1-rr),(1,rr)]:
   w=self.weights(i,r,state[2*i],state[2*i+1]);total=sum(w)
   if not total:continue
   prob1+=pr*sum(v*(bern(1,b^r,ALPHA) if action%2==0 else l) for v,(b,l) in zip(w,itertools.product([0,1],repeat=2)))/total
  return tuple((p,self.update(state,action,v)) for v,p in [(0,1-prob1),(1,prob1)] if p>1e-15)
 def _greedy(self,state):
  best=self.risk(state);chosen=-1
  for action in self.actions(state):
   val=QUERY_COST/HORIZON+sum(p*self.risk(ns) for p,ns in self.outcomes(state,action))
   if val<best-1e-12:best,chosen=val,action
  return best,chosen
 def _recursive(self,state,depth):
  if depth==0:return self.risk(state),-1
  best=self.risk(state);chosen=-1
  for action in self.actions(state):
   val=QUERY_COST/HORIZON+sum(p*self.recursive(ns,depth-1)[0] for p,ns in self.outcomes(state,action))
   if val<best-1e-12:best,chosen=val,action
  return best,chosen
 def _table2(self,state):
  # Explicit two-layer backward calculation, separate from recursive solver.
  level1={ns for action in self.actions(state) for p,ns in self.outcomes(state,action)}
  values={ns:self.greedy(ns)[0] for ns in level1}
  best=self.risk(state);chosen=-1
  for action in self.actions(state):
   v=QUERY_COST/HORIZON+sum(p*values[ns] for p,ns in self.outcomes(state,action))
   if v<best-1e-12:best,chosen=v,action
  return best,chosen
 def choose(self,state,name,used):
  if name in ['LiteralBits','RobustAbstain','KnownOrientation']:return -1
  if name=='ProvenanceOnly':return (used%2)*8+(used//2)*2+1
  if name=='UniformAnchors':return (used%2)*8+(used//2)*2
  if name=='ConfidentAnchors':
   g=used%2
   return min([2*i for i in range(g*4,g*4+4) if state[2*i]==-1],key=lambda j:(-abs(self.bp[self.xs[j//2]]-.5),j))
  if name=='GreedyDecision':return self.greedy(state)[1]
  if name=='EntropyGreedy':
   def entropy(ss):
    return sum(-v*math.log2(v)-(1-v)*math.log2(1-v) if 0<v<1 else 0. for v in self.orientation(ss))
   best=entropy(state);chosen=-1
   for action in self.actions(state):
    val=sum(p*entropy(ns) for p,ns in self.outcomes(state,action))
    if val<best-1e-12:best,chosen=val,action
   return chosen
  if name=='TwoStepTable':return self.table2(state)[1] if BUDGET-used>=2 else self.greedy(state)[1]
  if name=='TwoStepRecursive':return self.recursive(state,min(2,BUDGET-used))[1]
  if name=='SRDETypedGate':
   rr=self.orientation(state);available=[g for g in [0,1] if max(rr[g],1-rr[g])<.95 and any(state[2*i]==-1 for i in range(g*4,g*4+4))]
   if not available:return -1
   g=min(available,key=lambda g:(abs(rr[g]-.5),g))
   return min([2*i for i in range(g*4,g*4+4) if state[2*i]==-1],key=lambda j:(-abs(self.bp[self.xs[j//2]]-.5),j))
  raise ValueError(name)
 def run(self,responder,name):
  state=self.initial();trace=[]
  for used in range(BUDGET):
   action=self.choose(state,name,used)
   if action==-1:break
   assert state[action]==-1
   response=responder(action)
   state=self.update(state,action,response)
   trace.append({'step':used,'action':action,'type':'event_anchor' if action%2==0 else 'lineage','index':action//2,'response':response,'r0':self.orientation(state)[0],'r1':self.orientation(state)[1]})
  return state,trace
 def forecast(self,state,name,x,g,c):
  r=0. if name=='LiteralBits' else float(c['orientation'][g]) if name=='KnownOrientation' else self.orientation(state)[g]
  p=self.bp[x]*(1-r)+(1-self.bp[x])*r
  return p,int(p*(1-p)>ABSTAIN)
def dump(path,rows):
 with gzip.open(path,'wt',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def summarize(rows,query_count):
 mass=sum(r['weight'] for r in rows);bb=[[0.,0.,0.] for _ in range(10)]
 d={k:sum(r['weight']*r[k] for r in rows)/mass for k in ['brier','decision_loss','coverage','wrong_accepted']}
 for r in rows:
  b=bb[min(int(r['p']*10),9)];b[0]+=r['weight'];b[1]+=r['weight']*r['p'];b[2]+=r['weight']*r['y']
 d['ece10']=sum(abs(b[1]-b[2]) for b in bb)/mass
 d['queries']=query_count;d['query_cost']=QUERY_COST*query_count;d['total_loss']=d['decision_loss']+QUERY_COST*query_count/HORIZON
 return d
def main(out):
 start=time.perf_counter();P=json.loads((R/'PROTOCOL.json').read_text());assert conditions()==P['conditions'];out.mkdir(parents=True,exist_ok=True)
 rawrows=[];observed=[];queries=[];fits=[];exact=[];samples=[];samplecases=[];atoms=[];metrics=[]
 for c in P['conditions']:
  aa=[(b,l,x,g,.5*likelihood(x,b,l,c['a'])) for b,l,x,g in itertools.product([0,1],[0,1],range(8),[0,1]) if likelihood(x,b,l,c['a'])>0]
  atoms.extend({'condition':c['id'],'atom':i,'proxy_b':b,'lineage':l,'x':x,'context':g,'y':b^c['orientation'][g],'weight':w} for i,(b,l,x,g,w) in enumerate(aa))
  for seed in P['seeds']:
   world=f"{c['id']}-{seed}";raw=pool(seed,c);agent=Agent([r['x'] for r in raw],c['a'])
   rawrows.extend({'world':world,'condition':c['id'],'seed':seed,**r} for r in raw)
   observed.extend({'world':world,'index':r['index'],'context':r['context'],'x':r['x']} for r in raw)
   rng=random.Random(seed*100+int(round(c['a']*100))+30000000);held=[(*draw(rng,c['a']),i%2) for i in range(128)]
   samplecases.extend({'world':world,'case':i,'proxy_b':b,'lineage':l,'x':x,'context':g,'y':b^c['orientation'][g]} for i,(b,l,x,g) in enumerate(held))
   for name in METHODS:
    state,trace=agent.run(lambda action:raw[action//2]['anchor_response' if action%2==0 else 'lineage'],name)
    queries.extend({'world':world,'condition':c['id'],'method':name,**t} for t in trace)
    fits.append({'world':world,'method':name,'state':json.dumps(state),'r0':agent.orientation(state)[0],'r1':agent.orientation(state)[1],'queries':len(trace),'anchors':sum(t['type']=='event_anchor' for t in trace),'lineage_queries':sum(t['type']=='lineage' for t in trace)})
    for split,cc,container in [('exact',aa,exact),('sample',[(*v,1.) for v in held],samples)]:
     rr=[]
     for i,(b,l,x,g,w) in enumerate(cc):
      y=b^c['orientation'][g];p,ab=agent.forecast(state,name,x,g,c);br=(p-y)**2
      r={'world':world,'condition':c['id'],'method':name,'case':i,'context':g,'x':x,'y':y,'weight':w,'p':p,'abstain':ab,'brier':br,'decision_loss':ABSTAIN if ab else br,'coverage':1-ab,'wrong_accepted':int(not ab and int(p>=.5)!=y)}
      rr.append(r);container.append(r)
     metrics.append({'world':world,'condition':c['id'],'seed':seed,'a':c['a'],'family':c['family'],'method':name,'split':split,**summarize(rr,len(trace))})
 for n,rows in [('calibration_raw',rawrows),('calibration_observed',observed),('query_receipts',queries),('fits',fits),('exact_atoms',atoms),('sample_cases',samplecases),('exact_predictions',exact),('sample_predictions',samples),('world_metrics',metrics)]:dump(out/(n+'.csv.gz'),rows)
 agg=[]
 for fam in ['all','independent','uninformative','dependent_echo']:
  for split,name in itertools.product(['exact','sample'],METHODS):
   rr=[r for r in metrics if r['split']==split and r['method']==name and (fam=='all' or r['family']==fam)]
   agg.append({'family':fam,'split':split,'method':name,'evaluation_worlds':len(rr),**{k:sum(r[k] for r in rr)/len(rr) for k in ['brier','decision_loss','coverage','wrong_accepted','ece10','queries','query_cost','total_loss']}})
 (out/'metrics.json').write_text(json.dumps(agg,indent=2,sort_keys=True)+'\n')
 boot=[]
 for fam in ['independent','uninformative','dependent_echo','all']:
  for base in ['GreedyDecision','EntropyGreedy','ConfidentAnchors','SRDETypedGate','RobustAbstain']:
   groups=[]
   for a in [.65,.8]:
    vals=[]
    for seed in P['seeds']:
     aa=[r['total_loss'] for r in metrics if r['method']=='TwoStepTable' and r['split']=='exact' and r['seed']==seed and r['a']==a and (fam=='all' or r['family']==fam)]
     bb=[r['total_loss'] for r in metrics if r['method']==base and r['split']=='exact' and r['seed']==seed and r['a']==a and (fam=='all' or r['family']==fam)]
     vals.append(sum(aa)/len(aa)-sum(bb)/len(bb))
    groups.append(vals)
   rng=random.Random(99101);v=sorted(sum(sum(g[rng.randrange(len(g))] for i in g) for g in groups)/sum(map(len,groups)) for _ in range(1000))
   boot.append({'family':fam,'baseline':base,'delta':sum(map(sum,groups))/sum(map(len,groups)),'lower':v[25],'upper':v[974],'independent_pool_clusters':sum(map(len,groups)),'bootstrap_draws':1000})
 (out/'bootstrap.json').write_text(json.dumps(boot,indent=2,sort_keys=True)+'\n')
 (out/'environment.json').write_text(json.dumps({'python':sys.version,'platform':platform.platform(),'runtime_seconds':time.perf_counter()-start,'independent_calibration_pools':2*len(P['seeds']),'evaluation_worlds':len(P['conditions'])*len(P['seeds']),'raw_counterfactual_calibration_rows':len(rawrows),'sample_case_rows_including_counterfactual_twins':len(samplecases),'exact_forecasts':len(exact),'sample_forecasts':len(samples)},indent=2)+'\n')
 print((out/'environment.json').read_text())
if __name__=='__main__':main(Path(sys.argv[1]) if len(sys.argv)>1 else R/'results')
