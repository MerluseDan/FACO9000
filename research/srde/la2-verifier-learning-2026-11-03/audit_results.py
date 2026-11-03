"""Independent LA2 auditor. No import of either experiment runner."""
import csv,gzip,json,hashlib,math
from pathlib import Path
from collections import defaultdict
R=Path(__file__).parent;D=R/'results'
P=json.loads((R/'PROTOCOL.json').read_text());SC={x['id']:x for x in P['conditions']}
def read(n):
 with gzip.open(D/n,'rt',newline='') as f:return list(csv.DictReader(f))
def post(raw,row,m):
    y=int(raw['y']);l=int(raw['lineage']);x=int(raw['initial']);a=(x>>2)&1;b=(x>>1)&1;c=x&1
    fs=[];z=-1;due=None;requested=False;cost=0.;t=0
    for act in row['trace']:
        assert t<3
        if act=='A':assert not requested;requested=True;due=t+m['delay'];cost+=m['ca']
        elif act=='F':assert len(fs)<2;fs.append(int(raw['fresh'+str(len(fs))]));cost+=m['cv']
        else:assert act=='W' and due is not None
        t+=1
        if due is not None and due<=t:z=int(raw['audit']);due=None
    assert t==int(row['stop_t']) and len(fs)==int(row['fresh_n']) and z==int(row['audit_seen'])
    pr=m['pi']
    if row['method']=='NaiveIndependent':pr=0.
    if row['method']=='OracleLineageDP':pr=float(l)
    def lik(obs,truth,acc):return acc if obs==truth else 1-acc
    w=[]
    for yy in [0,1]:
        for ll in [0,1]:
            v=.5*(pr if ll else 1-pr)*lik(a,yy,m['acc'])*lik(c,yy,m['acc'])
            v*=int(a==b) if ll else lik(b,yy,m['acc'])
            for f in fs:v*=lik(f,yy,m['fresh'])
            if z!=-1:v*=lik(z,ll,m['q'])
            w.append(v)
    total=sum(w);prob=(w[2]+w[3])/total if total else .5
    abstain=int(prob*(1-prob)>.15)
    assert abstain==int(row['abstain']) and int(total==0)==int(row['zero_model_likelihood'])
    assert abs(float(row['p'])-prob)<1e-12
    assert abs(float(row['cost'])-cost)<1e-12
    brier=(prob-y)**2;loss=(.15 if abstain else brier)+cost
    assert abs(float(row['brier'])-brier)<1e-12 and abs(float(row['loss'])-loss)<1e-12
    return brier,loss,cost
def atom_weight(raw,m):
    y=int(raw['y']);l=int(raw['lineage']);x=int(raw['initial']);a=(x>>2)&1;b=(x>>1)&1;c=x&1
    def f(o,t,r):return r if o==t else 1-r
    w=.5*(m['pi'] if l else 1-m['pi'])*f(a,y,m['acc'])*f(c,y,m['acc'])
    w*=int(a==b) if l else f(b,y,m['acc'])
    w*=f(int(raw['fresh0']),y,m['fresh'])*f(int(raw['fresh1']),y,m['fresh'])*f(int(raw['audit']),l,m['q'])
    return w

def cp(x,y):
 a=(x>>2)&1;b=(x>>1)&1;c=x&1;w=[0.,0.]
 for yy in ([0,1] if y is None else [y]):
  for l in [0,1]:
   v=(.2 if l else .8)*(.8 if a==yy else .2)*(.8 if c==yy else .2)
   w[l]+=v*(int(a==b) if l else (.8 if b==yy else .2))
 return w[1]/sum(w)
def posterior(rows,name):
 logw=[0.]*101
 for r in rows:
  x=int(r['initial']);z=int(r['audit']);y=None if r['y_observed']=='' else int(r['y_observed'])
  l=None
  if name in ['RandomVerifiedCounts','MixedRandomBayes']:l=r['random_lineage']
  if name in ['SelectedVerifiedCounts','MixedSelectedBayes','DoubleCountSelected','SRDETypedRecursive']:l=r['selected_lineage']
  if name in ['RandomVerifiedCounts','SelectedVerifiedCounts']:
   if l=='':continue
   factors=[float(int(l)==z)]
  elif name=='TargetHardCounts':
   if y is None:continue
   factors=[float(z==int(cp(x,y)>.5))]
  elif name=='DoubleCountSelected':
   factors=[cp(x,None) if z else 1-cp(x,None)]
   if y is not None:factors.append(cp(x,y) if z else 1-cp(x,y))
   if l!='':factors.append(float(z==int(l)))
  else:factors=[float(z==int(l))] if l not in [None,''] else [cp(x,y) if z else 1-cp(x,y)]
  for j in range(101):
   for f in factors:
    v=(j*f+(100-j)*(1-f))/100
    logw[j]+=math.log(v) if v>0 else -math.inf
 top=max(logw);v=[math.exp(x-top) for x in logw];total=sum(v)
 return [x/total for x in v]
def main():
 freeze=json.loads((R/'FREEZE.json').read_text())
 assert all(hashlib.sha256((R/n).read_bytes()).hexdigest()==h for n,h in freeze['sha256'].items())
 raw=read('calibration_raw.csv.gz');pack=read('calibration_packets.csv.gz');byworld=defaultdict(list)
 assert len(raw)==len(pack)==len(SC)*len(P['seeds'])*128
 counters=defaultdict(lambda:[0,0])
 for rr,pk in zip(raw,pack):
  assert rr['world']==pk['world'] and rr['issue']==pk['issue']
  i=int(rr['issue']);x=int(rr['initial']);y=int(rr['y']);z=int(rr['audit']);w=rr['world']
  assert pk['y_observed']==(str(y) if i+5<=128 else '')
  for j,k in enumerate(['random','selected']):
   prob=.25 if j==0 else .8 if z==int(cp(x,y)>.5) else .1
   requested=i+5<=128 and counters[w][j]<32 and float(rr[k+'_u'])<prob
   counters[w][j]+=requested
   assert int(pk[k+'_requested'])==requested
   assert pk[k+'_lineage']==(rr['lineage'] if requested and i+17<=128 else '')
  byworld[w].append(pk)
 posterior_rows=read('posterior_weights.csv.gz');pw=defaultdict(list)
 for r in posterior_rows:pw[r['world'],r['method']].append(float(r['weight']))
 fits=json.loads((D/'fits.json').read_text());fq={};maxerr=0
 for f in fits:
  key=f['world'],f['method'];fq[key]=f
  if key not in pw:continue
  independently=posterior(byworld[f['world']],f['method'])
  error=max(abs(a-b) for a,b in zip(pw[key],independently));maxerr=max(maxerr,error);assert error<1e-10
  mean=sum(i/100*v for i,v in enumerate(independently));assert abs(mean-f['q_mean'])<1e-11
  assert round(mean+1e-12,2)==f['q_decision']
  mode='random' if f['method'] in ['RandomVerifiedCounts','MixedRandomBayes'] else 'selected' if f['method'] in ['SelectedVerifiedCounts','MixedSelectedBayes','DoubleCountSelected','SRDETypedRecursive'] else None
  nr=sum(int(r[mode+'_requested']) for r in byworld[f['world']]) if mode else 0
  assert f['reference_requested']==nr and abs(f['calibration_cost']-(.48+.003*nr))<1e-12
 records={(r['condition'],r['atom']):r for r in read('exact_atoms.csv.gz')}
 mass=defaultdict(float)
 for (cid,atom),r in records.items():
  c=SC[cid];m={'pi':.2,'q':c['q'],'acc':c['actual_acc'],'fresh':.7}
  w=atom_weight(r,m);assert abs(w-float(r['weight']))<1e-14;mass[cid]+=w
 assert len(mass)==8 and all(abs(v-1)<1e-12 for v in mass.values())
 n=0;aggregate={};ties={}
 samples={(r['world'],r['case']):r for r in read('sample_cases.csv.gz')}
 for split,src in [('exact','exact_predictions.csv.gz'),('sample','sample_predictions.csv.gz')]:
  sums=defaultdict(lambda:[0.,0.,0.,0.,0.]);seen=set()
  with gzip.open(D/src,'rt',newline='') as fh:
   for r in csv.DictReader(fh):
    key=(r['world'],r['atom'] if split=='exact' else r['case'],r['method']);assert key not in seen;seen.add(key)
    raw=records[(r['condition'],r['atom'])] if split=='exact' else samples[(r['world'],r['case'])]
    assert raw['y']==r['y']
    m={'pi':.2,'acc':.8,'fresh':.7,'q':float(r['q_decision']),'delay':0,'ca':.00375,'cv':.015}
    brier,loss,cost=post(raw,r,m);w=float(r['weight'])
    assert abs(w-(float(raw['weight']) if split=='exact' else 1.))<1e-14
    a=sums[(r['world'],r['method'])];a[0]+=w;a[1]+=w*loss;a[2]+=w*brier;a[3]+=w*('A' in r['trace']);a[4]+=w*(1-int(r['abstain']))
    if r['method']=='MixedSelectedBayes':ties[(split,key[:2])]=(r['p'],r['trace'],r['abstain'])
    if r['method']=='SRDETypedRecursive':assert ties[(split,key[:2])]==(r['p'],r['trace'],r['abstain'])
    n+=1
  aggregate[split]=sums
 worlds=json.loads((D/'world_metrics.json').read_text())
 for r in worlds:
  k=(r['world'],r['method']);fit=fq[k]
  for split,fields in [('exact',['deployment_loss','brier','audit_rate','coverage']),('sample',['sample_loss','sample_brier'])]:
   sums=aggregate[split][k]
   for i,f in enumerate(fields):
    err=abs(r[f]-sums[i+1]/sums[0]);maxerr=max(maxerr,err);assert err<1e-10
  assert abs(r['total_loss']-r['deployment_loss']-fit['calibration_cost']/r['horizon'])<1e-12
 result={'passed':True,'independent_of_runner_import':True,'frozen_files_verified':len(freeze['sha256']),'calibration_packets_checked':len(pack),'posterior_fits_checked':len(pw),'forecast_rows_checked':n,'max_numeric_error':maxerr,'checks':['delayed labels and references','verification selection and cap','posterior latent summation','reference acquisition cost including pending','exact world probability mass','forecast posterior and chronology','query cost and abstention','all world decision and Brier metrics','recursive and conventional forecast/trace identity','source freeze hashes']}
 (R/'AUDIT_RESULTS.json').write_text(json.dumps(result,indent=2)+chr(10));print(json.dumps(result))
if __name__=='__main__':main()
