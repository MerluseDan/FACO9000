"""Independent LA4 likelihood-ratio/selection/forecast/twin audit. No runner import."""
import csv,gzip,json,math,itertools,hashlib,gc
from pathlib import Path
from collections import defaultdict
from functools import lru_cache
R=Path(__file__).parent;D=R/'results';P=json.loads((R/'PROTOCOL.json').read_text());C={r['id']:r for r in P['conditions']}
def rows(n):
 with gzip.open(D/(n+'.csv.gz'),'rt',newline='') as f:return list(csv.DictReader(f))
def il(x,b,l,a):
 u=(x>>2)&1;v=(x>>1)&1;w=x&1
 return .5*(.2 if l else .8)*(a if u==b else 1-a)*(a if w==b else 1-a)*(int(u==v) if l else a if v==b else 1-a)
class Check:
 def __init__(self,xs,a):
  self.xs=xs;self.a=a
  self.evidence=lru_cache(None)(self._evidence);self.post=lru_cache(None)(self._post)
  self.risk=lru_cache(None)(self._risk);self.solve=lru_cache(None)(self._solve)
  self.mass=[sum(il(x,b,l,a) for b,l in itertools.product([0,1],repeat=2)) for x in range(8)]
  self.bp=[sum(il(x,1,l,a) for l in [0,1])/self.mass[x] for x in range(8)]
 def _evidence(self,s,g):
  w=[]
  for r in [0,1]:
   value=1.
   for i in range(4*g,4*g+4):
    anchor,lineage=s[2*i:2*i+2]
    v=0.
    for b,l in itertools.product([0,1],repeat=2):
     q=il(self.xs[i],b,l,self.a)
     if anchor!=-1:q*=.9 if anchor==(b^r) else .1
     if lineage!=-1:q*=int(lineage==l)
     v+=q
    value*=v
   w.append(value)
  return tuple(w)
 def _post(self,s):
  return tuple((w:=self.evidence(s,g))[1]/sum(w) for g in [0,1])
 def _risk(self,s):
  rr=self.post(s);total=0.
  for g,x in itertools.product([0,1],range(8)):
   p=(1-rr[g])*self.bp[x]+rr[g]*(1-self.bp[x]);total+=.5*self.mass[x]*min(p*(1-p),.15)
  return total
 @staticmethod
 def change(s,a,v):return s[:a]+(v,)+s[a+1:]
 def outcomes(self,s,a):
  g=a//8;z=sum(self.evidence(s,g))
  out=[]
  for v in [0,1]:
   ss=self.change(s,a,v);prob=sum(self.evidence(ss,g))/z
   if prob>1e-15:out.append((prob,ss))
  return out
 def _solve(self,s,d):
  best=self.risk(s);act=-1
  if d==0:return best,act
  for a,v in enumerate(s):
   if v!=-1:continue
   value=.005/128+sum(prob*self.solve(ss,d-1)[0] for prob,ss in self.outcomes(s,a))
   if value<best-1e-12:best,act=value,a
  return best,act
 def choose(self,s,name,used):
  if name in ['LiteralBits','RobustAbstain','KnownOrientation']:return -1
  if name in ['UniformAnchors','ProvenanceOnly']:return (used%2)*8+(used//2)*2+int(name=='ProvenanceOnly')
  if name in ['GreedyDecision','TwoStepTable','TwoStepRecursive']:return self.solve(s,1 if name=='GreedyDecision' else min(2,4-used))[1]
  if name=='EntropyGreedy':
   def entropy(st):
    return sum(-v*math.log2(v)-(1-v)*math.log2(1-v) if 0<v<1 else 0 for v in self.post(st))
   best=entropy(s);act=-1
   for a,v in enumerate(s):
    if v!=-1:continue
    value=sum(prob*entropy(ss) for prob,ss in self.outcomes(s,a))
    if value<best-1e-12:best,act=value,a
   return act
  if name=='ConfidentAnchors':g=used%2
  else:
   assert name=='SRDETypedGate';rr=self.post(s)
   avail=[g for g in [0,1] if max(rr[g],1-rr[g])<.95 and any(s[2*i]==-1 for i in range(4*g,4*g+4))]
   if not avail:return -1
   g=min(avail,key=lambda g:(abs(rr[g]-.5),g))
  candidates=[2*i for i in range(g*4,g*4+4) if s[2*i]==-1]
  return min(candidates,key=lambda a:(-abs(self.bp[self.xs[a//2]]-.5),a))
def main():
 freeze=json.loads((R/'FREEZE.json').read_text())
 for n,h in freeze['sha256'].items():assert hashlib.sha256((R/n).read_bytes()).hexdigest()==h
 raw=rows('calibration_raw');observed=rows('calibration_observed');byworld=defaultdict(list);twins={};maxerr=0.
 assert len(raw)==len(observed)==288*8
 for a,b in zip(raw,observed):
  assert set(b)=={'world','index','context','x'}
  for k in b:assert b[k]==a[k]
  c=C[a['condition']];g=int(a['context']);y=int(a['proxy_b'])^c['orientation'][g];assert y==int(a['y'])
  u=float(a['reference_u']);expected=(y if u<(.9 if c['reference']=='accurate' else .5) else 1-y) if c['reference']!='echo' else (int(a['x'])>>2)&1
  assert expected==int(a['anchor_response'])
  key=c['a'],a['seed'],a['index'];v=tuple(a[k] for k in ['context','x','proxy_b','lineage','reference_u'])
  if key in twins:assert twins[key]==v
  else:twins[key]=v
  byworld[a['world']].append(a)
 receipts=defaultdict(list)
 for r in rows('query_receipts'):receipts[r['world'],r['method']].append(r)
 fitrows=rows('fits');fits={(r['world'],r['method']):r for r in fitrows};assert len(fits)==288*len(P['methods'])
 checkedquery=0
 for world,rr in byworld.items():
  c=C[world.split('-')[0]];checker=Check([int(r['x']) for r in rr],c['a'])
  for name in P['methods']:
   s=(-1,)*16;qq=receipts[world,name];assert len(qq)<=4
   for j,q in enumerate(qq):
    action=int(q['action']);assert int(q['step'])==j and s[action]==-1
    expected_action=checker.choose(s,name,j)
    if expected_action!=action and name=='SRDETypedGate':
     rrpost=checker.post(s);g=action//8
     available=[gg for gg in [0,1] if max(rrpost[gg],1-rrpost[gg])<.95 and any(s[2*i]==-1 for i in range(4*gg,4*gg+4))]
     assert g in available
     assert abs(rrpost[g]-.5)<=min(abs(rrpost[gg]-.5) for gg in available)+1e-12
     alternatives=[2*i for i in range(4*g,4*g+4) if s[2*i]==-1]
     assert action in alternatives and abs(checker.bp[checker.xs[action//2]]-.5)>=max(abs(checker.bp[checker.xs[aa//2]]-.5) for aa in alternatives)-1e-12
    else:assert expected_action==action,(world,name,j,'selection')
    response=int(rr[action//2]['anchor_response' if action%2==0 else 'lineage'])
    assert response==int(q['response']) and int(q['index'])==action//2
    assert q['type']==('event_anchor' if action%2==0 else 'lineage')
    s=checker.change(s,action,response)
    for g,k in enumerate(['r0','r1']):
     err=abs(checker.post(s)[g]-float(q[k]));maxerr=max(maxerr,err);assert err<1e-10
    checkedquery+=1
   if len(qq)<4:assert checker.choose(s,name,len(qq))==-1
   fit=fits[world,name];assert tuple(json.loads(fit['state']))==s;assert int(fit['queries'])==len(qq)
   assert int(fit['anchors'])==sum(q['type']=='event_anchor' for q in qq)
   assert int(fit['lineage_queries'])==sum(q['type']=='lineage' for q in qq)
   for g,k in enumerate(['r0','r1']):assert abs(checker.post(s)[g]-float(fit[k]))<1e-10
   if name=='ProvenanceOnly':assert checker.post(s)==(.5,.5)
  # Discard per-world planning caches; they are not forecast evidence.
  del checker;gc.collect()
 # In echo worlds even acquired pseudo-anchor transcripts cannot distinguish orientation.
 echo_transcripts={}
 for world in byworld:
  c=C[world.split('-')[0]]
  if c['reference']!='echo':continue
  for name in P['methods']:
   if name=='KnownOrientation':continue
   key=c['a'],world.split('-')[1],name
   transcript=tuple((q['action'],q['response']) for q in receipts[world,name])
   if key in echo_transcripts:assert echo_transcripts[key]==transcript
   else:echo_transcripts[key]=transcript
 atoms=rows('exact_atoms');amap={(r['condition'],r['atom']):r for r in atoms};mass=defaultdict(float);dist=defaultdict(lambda:defaultdict(float))
 for r in atoms:
  c=C[r['condition']];b,l,x,g=map(int,[r['proxy_b'],r['lineage'],r['x'],r['context']]);w=.5*il(x,b,l,c['a'])
  assert abs(w-float(r['weight']))<1e-14;assert int(r['y'])==b^c['orientation'][g];mass[c['id']]+=w
  dist[c['id']][g,x,l]+=w
 assert all(abs(w-1)<1e-12 for w in mass.values())
 for c in C.values():
  variants=[d for d in C.values() if d['a']==c['a']]
  for d in variants:
   for k,w in dist[c['id']].items():assert abs(w-dist[d['id']][k])<1e-14
 smap={(r['world'],r['case']):r for r in rows('sample_cases')};observables={}
 for (world,case),r in smap.items():
  c=C[world.split('-')[0]];key=c['a'],world.split('-')[1],case
  v=tuple(r[k] for k in ['proxy_b','lineage','x','context'])
  if key in observables:assert observables[key]==v
  else:observables[key]=v
  assert int(r['y'])==int(r['proxy_b'])^c['orientation'][int(r['context'])]
 sums={};forecast_count=0;ties={};literal={}
 for split in ['exact','sample']:
  agg=defaultdict(lambda:[0.]*5);bins=defaultdict(lambda:[[0.,0.] for _ in range(10)]);seen=set()
  with gzip.open(D/(split+'_predictions.csv.gz'),'rt') as f:
   for r in csv.DictReader(f):
    world,name=r['world'],r['method'];key=world,name;uid=world,name,r['case'];assert uid not in seen;seen.add(uid)
    c=C[r['condition']];src=amap[c['id'],r['case']] if split=='exact' else smap[world,r['case']]
    x,g,y=map(int,[src['x'],src['context'],src['y']]);assert r['x']==src['x'] and r['context']==src['context'] and r['y']==src['y']
    denom=sum(il(x,b,l,c['a']) for b,l in itertools.product([0,1],repeat=2));pb=sum(il(x,1,l,c['a']) for l in [0,1])/denom
    ori=0. if name=='LiteralBits' else c['orientation'][g] if name=='KnownOrientation' else float(fits[key]['r'+str(g)])
    prob=pb*(1-ori)+(1-pb)*ori;ab=int(prob*(1-prob)>.15);br=(prob-y)**2;loss=.15 if ab else br;cover=1-ab;wrong=int(not ab and int(prob>=.5)!=y)
    for k,val in [('p',prob),('brier',br),('decision_loss',loss),('coverage',cover),('wrong_accepted',wrong)]:
     err=abs(val-float(r[k]));maxerr=max(maxerr,err);assert err<1e-10
    assert ab==int(r['abstain']);w=float(r['weight']);assert abs(w-(float(src['weight']) if split=='exact' else 1))<1e-14
    vals=[br,loss,cover,wrong];agg[key][0]+=w
    for i,v in enumerate(vals):agg[key][i+1]+=w*v
    b=bins[key][min(int(prob*10),9)];b[0]+=w*prob;b[1]+=w*y
    tk=split,world,r['case']
    if name=='TwoStepTable':ties[tk]=(r['p'],r['abstain'])
    if name=='TwoStepRecursive':assert ties[tk]==(r['p'],r['abstain'])
    if name in ['RobustAbstain','ProvenanceOnly']:assert prob==.5 and ab==1
    forecast_count+=1
  sums[split]=(agg,bins)
 for r in rows('world_metrics'):
  key=r['world'],r['method'];agg,bins=sums[r['split']];v=agg[key]
  for i,k in enumerate(['brier','decision_loss','coverage','wrong_accepted']):
   err=abs(v[i+1]/v[0]-float(r[k]));maxerr=max(maxerr,err);assert err<1e-10
  ece=sum(abs(b[0]-b[1]) for b in bins[key])/v[0];assert abs(ece-float(r['ece10']))<1e-10
  nq=int(fits[key]['queries']);assert abs(float(r['queries'])-nq)<1e-14
  assert abs(float(r['total_loss'])-(float(r['decision_loss'])+.005*nq/128))<1e-12
 result={'passed':True,'runner_imported':False,'frozen_files':len(freeze['sha256']),'independent_calibration_pools':len(twins)//8,'counterfactual_evaluation_worlds':len(byworld),'calibration_observations_checked':len(observed),'query_receipts_checked':checkedquery,'posterior_fits_checked':len(fits),'forecasts_checked':forecast_count,'max_numeric_error':maxerr,'checks':['hidden values excluded from observed packets','counterfactual coupling','anchor mechanism and lineage response','all acquired-query choices via separate evidence-ratio planner; heuristic context ties accepted within1e-12','no repeated queries and cap4','full transcript posterior','all exact distribution weights','exact provenance-only orientation invariance','all forecast probabilities/abstention/Brier/decision loss','ECE and all world metrics','query expenses','recursive/table forecasts identical','observable-world marginal equivalence','echo-reference complete transcript invariance across target orientations']}
 (R/'AUDIT_RESULTS.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
