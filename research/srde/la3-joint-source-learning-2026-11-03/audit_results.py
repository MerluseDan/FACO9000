"""Independent direct-summation, action-optimality and chronology audit; imports no runner."""
import csv,gzip,json,hashlib,itertools,math,random
from pathlib import Path
from collections import defaultdict
from functools import lru_cache
R=Path(__file__).parent;D=R/'results';P=json.loads((R/'PROTOCOL.json').read_text());C={x['id']:x for x in P['conditions']}
H=list(itertools.product([0,1],repeat=3))
def read(n):
 with gzip.open(D/(n+'.csv.gz'),'rt',newline='') as f:return list(csv.DictReader(f))
def bern(v,t,a):return a if v==t else 1-a
def il(x,y,l,a):
 u=(x>>2)&1;v=(x>>1)&1;w=x&1
 return bern(u,y,a)*bern(w,y,a)*(int(u==v) if l else bern(v,y,a))
def audit_fit(rows,theta,mode):
 scores=[]
 for a,pi,q in theta:
  ll=0.
  for r in rows:
   ys=[0,1] if r['y_observed']=='' else [int(r['y_observed'])]
   ls=[0,1] if mode=='noaudit' or r['lineage_observed']=='' else [int(r['lineage_observed'])]
   val=sum(.5*(pi if l else 1-pi)*il(int(r['initial']),y,l,a)*(1 if mode=='noaudit' else bern(int(r['audit']),l,q)) for y in ys for l in ls)
   ll+=math.log(val) if val>0 else -math.inf
  scores.append(ll)
 top=max(scores);v=[math.exp(x-top) for x in scores];z=sum(v);return [x/z for x in v]
class AuditPolicy:
 def __init__(self,joint,allow):
  self.j=joint;self.allow=allow
  self.belief=lru_cache(None)(self._belief);self.solve=lru_cache(None)(self._solve)
 def _belief(self,x,fs,z):
  w=[self.j[x][i]*math.prod(bern(f,y,.7) for f in fs)*(1 if z==-1 else int(zz==z)) for i,(y,l,zz) in enumerate(H)]
  z=sum(w);return tuple(v/z for v in w) if z else (0.,)*8
 def terminal(self,x,fs,z):
  w=self.belief(x,fs,z);p=sum(v for v,(y,l,zz) in zip(w,H) if y) if sum(w) else .5
  return min(p*(1-p),.15),p,int(p*(1-p)>.15)
 def _solve(self,x,fs,z,n):
  best=self.terminal(x,fs,z)[0];action='S'
  if n>=3:return best,action
  for a in (['F'] if len(fs)<2 else [])+(['A'] if self.allow and z==-1 else []):
   vals=[]
   for v in [0,1]:
    prob=sum(w*(bern(v,y,.7) if a=='F' else int(zz==v)) for w,(y,l,zz) in zip(self.belief(x,fs,z),H))
    if prob:vals.append(prob*self.solve(x,fs+(v,) if a=='F' else fs,v if a=='A' else z,n+1)[0])
   risk=(.015 if a=='F' else .00375)+sum(vals)
   if risk<best-1e-12:best,action=risk,a
  return best,action
 def check(self,raw,row):
  x=int(raw['initial']);y=int(raw['y']);fs=();z=-1;cost=0.;n=0
  for a in row['trace']:
   assert a==self.solve(x,fs,z,n)[1]
   assert n<3
   if a=='F':assert len(fs)<2;fs+= (int(raw['fresh'+str(len(fs))]),);cost+=.015
   else:assert a=='A' and z==-1 and self.allow;z=int(raw['audit']);cost+=.00375
   n+=1
  assert self.solve(x,fs,z,n)[1]=='S'
  _,prob,abstain=self.terminal(x,fs,z);br=(prob-y)**2;loss=(.15 if abstain else br)+cost
  assert abs(prob-float(row['p']))<1e-11 and abstain==int(row['abstain'])
  assert int(sum(self.belief(x,fs,z))==0)==int(row['zero_model_likelihood'])
  for k,v in [('cost',cost),('brier',br),('loss',loss)]:assert abs(v-float(row[k]))<1e-11
  return loss,br,cost,1-abstain,int('A' in row['trace'])
def main():
 freeze=json.loads((R/'FREEZE.json').read_text())
 for n,h in freeze['sha256'].items():assert hashlib.sha256((R/n).read_bytes()).hexdigest()==h
 raw=read('calibration_raw');pack=read('calibration_packets');byworld=defaultdict(list);nr=defaultdict(int)
 assert len(pack)==len(raw)==120*128
 for a,b in zip(raw,pack):
  i=int(a['issue']);world=a['world'];y=int(a['y']);x=int(a['initial']);z=int(a['audit'])
  assert (world,a['issue'])==(b['world'],b['issue'])
  assert b['y_observed']==(a['y'] if i+5<=128 else '')
  ww=[(.2 if l else .8)*il(x,y,l,.8) for l in [0,1]]
  prob=.8 if z==int(ww[1]>ww[0]) else .1
  req=i+5<=128 and nr[world]<32 and float(a['selection_u'])<prob;nr[world]+=req
  assert int(b['reference_requested'])==req
  assert b['lineage_observed']==(a['lineage'] if req and i+17<=128 else '')
  byworld[world].append(b)
 post=read('parameter_posteriors');wp=defaultdict(list);maxerr=0
 for r in post:wp[r['world'],r['fit']].append(tuple(float(r[k]) for k in ['a','pi','q','weight']))
 for (world,mode),rr in wp.items():
  theta=[x[:3] for x in rr];weights=audit_fit(byworld[world],theta,mode)
  for x,w in zip(rr,weights):maxerr=max(maxerr,abs(x[3]-w));assert abs(x[3]-w)<1e-10
 jointrows=read('predictive_joints');joint=defaultdict(lambda:[[0.]*8 for _ in range(8)])
 for r in jointrows:joint[r['world'],r['method']][int(r['initial'])][H.index(tuple(int(r[k]) for k in ['y','lineage','audit']))]=float(r['mass'])
 fits=read('fits');fitmap={(f['world'],f['method']):f for f in fits}
 for (world,name),j in joint.items():
  c=C[world.split('-')[0]]
  if name=='FixedFresh':theta=[(.8,.2,1.,1.)]
  elif name=='KnownAll':theta=[(c['a'],c['pi'],c['q'],1.)]
  elif name=='QOnlyFull':theta=wp[world,'qonly']
  elif name=='NoAuditTrainFresh':theta=wp[world,'noaudit']
  elif name=='JointMAPFull':theta=[max(wp[world,'joint'],key=lambda x:x[3])[:3]+(1.,)]
  elif name=='JointMeanFull':theta=[tuple(sum(x[i]*x[3] for x in wp[world,'joint']) for i in range(3))+(1.,)]
  else:theta=wp[world,'joint']
  for x,vv in enumerate(j):
   for i,(y,l,z) in enumerate(H):
    val=sum(w*.5*(pi if l else 1-pi)*il(x,y,l,a)*bern(z,l,q) for a,pi,q,w in theta)
    maxerr=max(maxerr,abs(val-vv[i]));assert abs(val-vv[i])<1e-11
  assert abs(sum(map(sum,j))-1)<1e-11
  cost=0 if name in ['FixedFresh','KnownAll','NoAuditTrainFresh'] else .48+.003*nr[world]
  assert abs(float(fitmap[world,name]['calibration_cost'])-cost)<1e-12
 atomrows=read('exact_atoms');atoms={(r['condition'],r['atom']):r for r in atomrows};mass=defaultdict(float)
 for r in atomrows:
  c=C[r['condition']];x=int(r['initial']);y=int(r['y']);l=int(r['lineage']);z=int(r['audit'])
  w=.5*(c['pi'] if l else 1-c['pi'])*il(x,y,l,c['a'])*bern(z,l,c['q'])*bern(int(r['fresh0']),y,.7)*bern(int(r['fresh1']),y,.7)
  assert abs(w-float(r['weight']))<1e-14;mass[c['id']]+=w
 assert len(mass)==10 and all(abs(x-1)<1e-12 for x in mass.values())
 samples={(r['world'],r['case']):r for r in read('sample_cases')}
 sums={};count=0;policies={};ties={}
 for split in ['exact','sample']:
  ag=defaultdict(lambda:[0.]*6);seen=set()
  with gzip.open(D/(split+'_predictions.csv.gz'),'rt') as f:
   for r in csv.DictReader(f):
    world,name=r['world'],r['method'];k=world,name
    if k not in policies:policies[k]=AuditPolicy(joint[k],name not in ['FixedFresh','JointBMAFresh','NoAuditTrainFresh'])
    src=atoms[r['condition'],r['case']] if split=='exact' else samples[world,r['case']]
    key=world,r['case'],name;assert key not in seen;seen.add(key)
    assert r['y']==src['y'];values=policies[k].check(src,r);w=float(r['weight'])
    assert abs(w-(float(src['weight']) if split=='exact' else 1))<1e-14
    ag[k][0]+=w
    for i,v in enumerate(values):ag[k][i+1]+=w*v
    tk=split,world,r['case']
    if name=='JointBMAFull':ties[tk]=(r['p'],r['trace'],r['abstain'])
    if name=='SRDERecursive':assert ties[tk]==(r['p'],r['trace'],r['abstain'])
    count+=1
  sums[split]=ag
 metrics=read('world_metrics')
 for r in metrics:
  k=r['world'],r['method'];v=sums[r['split']][k]
  for i,key in enumerate(['loss','brier','cost','coverage','audit_rate']):
   err=abs(float(r[key])-v[i+1]/v[0]);maxerr=max(maxerr,err);assert err<1e-10
  assert abs(float(r['total_loss'])-float(r['loss'])-float(r['calibration_cost'])/int(r['horizon']))<1e-12
 result={'passed':True,'runner_imported':False,'calibration_rows':len(pack),'posterior_fits':len(wp),'predictive_joint_models':len(joint),'forecast_rows':count,'max_numeric_error':maxerr,'frozen_files':len(freeze['sha256']),'checks':['typed delayed feedback','selection probabilities and request caps','all parameter posterior masses','parameter mixing before x conditioning','calibration query costs incl pending','all exact atom weights','every forecast probability and loss','all actions independently optimal under supplied posterior predictive','three-slot budgets and audit chronology','all world metrics','recursive/conventional trace identity']}
 (R/'AUDIT_RESULTS.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
