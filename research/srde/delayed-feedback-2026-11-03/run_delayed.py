import os
os.environ.setdefault('OMP_NUM_THREADS','1');os.environ.setdefault('OPENBLAS_NUM_THREADS','1');os.environ.setdefault('MKL_NUM_THREADS','1')
import json,time,gzip,csv,hashlib,platform,argparse
from pathlib import Path
from collections import defaultdict,deque
import numpy as np,sklearn
from scipy.special import expit,logit
from sklearn.linear_model import LogisticRegression
from source_common import eligible,decode,fit_weights,metric,AGES,walk_recursive,walk_iterative
ROOT=Path(__file__).parent
def dump(p,x):p.write_text(json.dumps(x,indent=2,sort_keys=True)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def generate(seed,proto):
 rng=np.random.default_rng(seed);sets=defaultdict(list);gold={}
 for world in range(proto['worlds']):
  changed=world<10;tau=int(rng.integers(230,251));ret=int(rng.integers(330,351));rates=rng.uniform(.55,.9,8);rates[-2:]=rng.uniform(.2,.4,2)
  states=np.zeros((422,2),int);states[0]=rng.integers(2,size=2)
  for t in range(1,422):states[t]=states[t-1]^(rng.random(2)<(.2 if changed and tau<=t<ret else .08))
  gold[str(world)]=dict(changed=changed,change=tau,return_time=ret,hidden_rates=rates.tolist(),latent_states=states.tolist())
  for t in list(range(20,120))+list(range(130,160))+list(range(170,420)):
   split='train' if t<120 else 'calibration' if t<160 else 'deployment'
   for context in range(2):
    reports=[]
    for source in range(8):
     if rng.random()<.15:continue
     age=int(rng.choice(AGES));rc=context if rng.random()<.8 else 1-context
     rr=1-rates[source] if changed and tau<=t<ret and source<4 else rates[source]
     v=2*(int(states[t-age,rc])^int(rng.random()>rr))-1;edges=rng.choice([-1,1],int(rng.integers(1,4))).tolist();active=bool(rng.random()<.9)
     for cp in range(int(rng.integers(1,4))):reports.append(dict(source=source,copy=cp,age=age,observed_time=t-age,context=rc,active=active,leaf=v*int(np.prod(edges)),edges=edges))
    sets[split].append(dict(id=f'{seed}:{world}:{t}:{context}',world=f'{seed}:{world}',world_index=world,time=t,target_time=t+1,context=context,y=int(states[t+1,context]),reports=reports))
 return sets,gold
def select(c,w):return sorted(eligible(c),key=lambda e:(-abs(w[e['source'],AGES.index(e['age'])]),e['source']))[:4]
def raw_predict(c,w,adaptive=False,recursive=False):
 assert 'y' not in c,'Gold must be stripped before prediction'
 es=select(c,w)
 if adaptive:
  p,n=(walk_recursive(es,w) if recursive else walk_iterative(es,w))
 else:p=float(expit(sum(decode(e)*w[e['source'],AGES.index(e['age'])] for e in es)));n=len(es)
 return p,[(e['source'],AGES.index(e['age']),decode(e)) for e in es[:n]]
def fit_cal(p,y,C=1000):
 m=LogisticRegression(C=C,max_iter=100).fit(logit(np.clip(p,1e-6,1-1e-6)).reshape(-1,1),y)
 return float(m.coef_[0,0]),float(m.intercept_[0])
def calibrated(p,cal):return float(expit(cal[0]*logit(np.clip(p,1e-6,1-1e-6))+cal[1]))
class Learner:
 def __init__(self,name,rates,cal,threshold):
  self.name=name;self.initial_s=rates*32-2;self.initial_f=(1-rates)*32-2;self.s=self.initial_s.copy();self.f=self.initial_f.copy();self.window=deque();self.losses=deque(maxlen=32);self.cal=cal;self.threshold=threshold;self.n=0;self.last_alarm=-100000;self.epoch=-1;self.ready=32;self.alarms=[];self.caldata=deque(maxlen=128);self.cal_fits=0;self.max_available=-1;self.max_prediction_time=-1
 def weights(self):
  if self.name=='Window128Graph4':
   factor=max(0.,1-self.n/128);s=self.s-self.initial_s+factor*self.initial_s;f=self.f-self.initial_f+factor*self.initial_f
  else:s=self.s;f=self.f
  r=(2+s)/(4+s+f);return np.log(np.clip(r,1e-6,1-1e-6)/np.clip(1-r,1e-6,1))
 def predict(self,c,now):
  assert 'y' not in c and self.max_available<=now
  self.max_prediction_time=now;adaptive=self.name in ['ResetPortal','ResetSequential']
  p,es=raw_predict(c,self.weights(),adaptive,self.name=='ResetPortal')
  unknown=self.name.startswith('Reset') and self.ready<32
  q=.5 if unknown else calibrated(p,self.cal)
  return dict(raw_p=p,p=q,evidence=es,issue_time=now)
 def feedback(self,event,now):
  assert event['available_time']<=now,'Future label accessed'
  self.max_available=max(self.max_available,event['available_time']);self.n+=1
  y=event['y'];pred=event['forecast'];self.losses.append((pred['p']-y)**2);self.caldata.append((pred['raw_p'],y))
  if self.name=='FrozenRollingCal' and self.n>=64 and self.n%32==0 and len({z[1] for z in self.caldata})>1:
   self.cal=fit_cal(np.array([z[0] for z in self.caldata]),np.array([z[1] for z in self.caldata]),C=10);self.cal_fits+=1
  if self.name in ['FrozenGraph4','FrozenRollingCal']:return
  if self.name.startswith('Reset'):
   if len(self.losses)==32 and self.n-self.last_alarm>=64 and np.mean(self.losses)>self.threshold:
    self.s[:]=0;self.f[:]=0;self.epoch=now;self.ready=0;self.last_alarm=self.n;self.alarms.append(now);self.losses.clear();return
   if pred['issue_time']<self.epoch:return
   self.ready+=1
  if self.name=='ExpDecayGraph4':self.s*=.98;self.f*=.98
  contributions=[]
  for source,k,v in pred['evidence']:
   correct=int((v>0)==y);self.s[source,k]+=correct;self.f[source,k]+=1-correct;contributions.append((source,k,correct))
  if self.name=='Window128Graph4':
   self.window.append(contributions)
   if len(self.window)>128:
    for source,k,correct in self.window.popleft():self.s[source,k]-=correct;self.f[source,k]-=1-correct
def phase(t,g):
 if not g['changed']:return 'unchanged'
 if t<g['change']:return 'before_change'
 if t<g['change']+32:return 'early_drift'
 if t<g['return_time']:return 'late_drift'
 if t<g['return_time']+32:return 'early_return'
 return 'late_return'
def run(out):
 out.mkdir(parents=True,exist_ok=True);proto=json.loads((ROOT/'PROTOCOL.json').read_text());freeze=ROOT/'FREEZE.json'
 identities={n:sha(ROOT/n) for n in ['run_delayed.py','source_common.py','PROTOCOL.json']}
 if not freeze.exists():dump(freeze,dict(utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),sha256=identities))
 assert json.loads(freeze.read_text())['sha256']==identities
 start=time.perf_counter();predictions=[];raw=[];hidden={};alarms=[];controls=[];fitparams=[]
 for seed in proto['seeds']:
  sets,gold=generate(seed,proto);hidden[str(seed)]=gold
  for a in sets.values():raw.extend(a)
  w,r=fit_weights(sets['train']);calibrators={};thresholds={}
  for adaptive in [False,True]:
   p=np.array([raw_predict({k:v for k,v in c.items() if k!='y'},w,adaptive,False)[0] for c in sets['calibration']]);y=np.array([c['y'] for c in sets['calibration']]);cal=fit_cal(p,y);calibrators[adaptive]=cal;thresholds[adaptive]=float(np.mean((np.array([calibrated(z,cal) for z in p])-y)**2)+.10)
  fitparams.append(dict(seed=seed,learned_accuracy=r.tolist(),calibrators={str(k):v for k,v in calibrators.items()},thresholds={str(k):v for k,v in thresholds.items()}))
  recseq_max=0.;maxvotes=0;future_ok=True
  byworld=defaultdict(list)
  for c in sets['deployment']:byworld[c['world_index']].append(c)
  for wi,cases in byworld.items():
   learners={name:Learner(name,r,calibrators[name in ['ResetPortal','ResetSequential']],thresholds[name in ['ResetPortal','ResetSequential']]) for name in proto['methods']};pending=defaultdict(list)
   for c in cases:
    now=c['time']
    # Two contexts share time. Popping makes each matured case delivered once before either new prediction.
    for event in pending.pop(now,[]):
     for name,learner in learners.items():learner.feedback(dict(available_time=event['available_time'],y=event['y'],forecast=event['forecasts'][name]),now)
    forecasts={};safe={k:v for k,v in c.items() if k!='y'}
    for name,learner in learners.items():
     f=learner.predict(safe,now);forecasts[name]=f;maxvotes=max(maxvotes,len(f['evidence']));future_ok=future_ok and learner.max_available<=now
     predictions.append(dict(seed=seed,id=c['id'],world=c['world'],time=now,method=name,phase=phase(now,gold[str(wi)]),changed=gold[str(wi)]['changed'],y=c['y'],p=f['p'],raw_p=f['raw_p'],decoded_votes=len(f['evidence']),latest_feedback_available_time=learner.max_available))
    recseq_max=max(recseq_max,abs(forecasts['ResetPortal']['p']-forecasts['ResetSequential']['p']))
    pending[c['target_time']+7].append(dict(available_time=c['target_time']+7,y=c['y'],forecasts=forecasts))
   for name,l in learners.items():alarms.append(dict(seed=seed,world=f'{seed}:{wi}',method=name,changed=gold[str(wi)]['changed'],change=gold[str(wi)]['change'],return_time=gold[str(wi)]['return_time'],alarm_times=l.alarms,revealed_labels=l.n,online_calibration_fits=l.cal_fits))
  controls.append(dict(seed=seed,future_feedback_excluded=future_ok,recursive_sequential_max_abs=recseq_max,max_votes=maxvotes,source_cases=sum(map(len,sets.values()))))
  print('seed',seed,'completed',flush=True)
 with gzip.open(out/'source_cases.jsonl.gz','wt') as f:
  for c in raw:f.write(json.dumps(c,separators=(',',':'))+'\n')
 with gzip.open(out/'latent_gold.json.gz','wt') as f:json.dump(hidden,f,separators=(',',':'))
 with gzip.open(out/'predictions.csv.gz','wt',newline='') as f:
  writer=csv.DictWriter(f,fieldnames=list(predictions[0]));writer.writeheader();writer.writerows(predictions)
 groups=defaultdict(list)
 for p in predictions:
  groups[(p['method'],'all')].append(p);groups[(p['method'],p['phase'])].append(p);groups[(p['method'],'changed_worlds' if p['changed'] else 'unchanged_worlds')].append(p)
 metrics=[]
 for (name,part),rs in sorted(groups.items()):metrics.append(dict(method=name,subset=part,**metric([x['y'] for x in rs],[x['p'] for x in rs]),mean_votes=float(np.mean([x['decoded_votes'] for x in rs]))))
 differences={}
 for subset in ['all','changed_worlds','unchanged_worlds']:
  base={x['id']:x for x in groups[('FrozenGraph4',subset)]}
  for name in proto['methods'][1:]:
   ws=defaultdict(list)
   for x in groups[(name,subset)]:
    b=base[x['id']];ws[x['world']].append((x['p']-x['y'])**2-(b['p']-b['y'])**2)
   a=np.array([np.mean(v) for v in ws.values()]);rng=np.random.default_rng(939);z=np.mean(rng.choice(a,(1000,len(a))),axis=1);differences[subset+':'+name+'-FrozenGraph4']=dict(brier_delta=float(a.mean()),ci95=np.quantile(z,[.025,.975]).tolist(),world_clusters=len(a))
 dump(out/'metrics.json',metrics);dump(out/'alarms.json',alarms);dump(out/'controls.json',controls);dump(out/'fit_parameters.json',fitparams);dump(out/'paired_bootstrap.json',differences)
 dump(out/'environment.json',dict(python=platform.python_version(),numpy=np.__version__,sklearn=sklearn.__version__,elapsed_seconds=time.perf_counter()-start,accelerator='CPU',source_cases=len(raw),predictions=len(predictions)))
 print('COMPLETE',len(raw),len(predictions),time.perf_counter()-start,flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,default=ROOT/'results');a=p.parse_args();run(a.out)
