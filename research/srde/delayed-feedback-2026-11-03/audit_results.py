import json,csv,gzip,hashlib
from pathlib import Path
from collections import Counter,defaultdict
R=Path(__file__).parent;D=R/'results';gold={};counts=Counter();causal=True
hidden=json.loads(gzip.decompress((D/'latent_gold.json.gz').read_bytes()))
for line in gzip.open(D/'source_cases.jsonl.gz','rt'):
 c=json.loads(line);gold[c['id']]=(c['y'],c['time'],c['target_time']);counts[c.get('time')<120 and 'train' or c['time']<160 and 'calibration' or 'deployment']+=1
 assert c['y']==hidden[c['id'].split(':')[0]][str(c['world_index'])]['latent_states'][c['target_time']][c['context']]
 causal=causal and all(e['observed_time']<=c['time']<c['target_time'] for e in c['reports'])
checks=dict(source_count=len(gold)==76000,source_splits=dict(counts)=={'train':20000,'calibration':6000,'deployment':50000},causal_reports=causal)
keys=set();groups=defaultdict(lambda:[0.,0]);latest_ok=True;cap=True;predcount=0;equivalent={}
for x in csv.DictReader(gzip.open(D/'predictions.csv.gz','rt')):
 predcount+=1;key=(x['id'],x['method']);assert key not in keys;keys.add(key);y,t,target=gold[x['id']];assert y==int(x['y']) and t==int(x['time']) and target==t+1
 p=min(1-1e-7,max(1e-7,float(x['p'])));err=(p-y)**2
 for part in ['all',x['phase'],'changed_worlds' if x['changed']=='True' else 'unchanged_worlds']:
  a=groups[(x['method'],part)];a[0]+=err;a[1]+=1
 latest_ok=latest_ok and int(x['latest_feedback_available_time'])<=t;cap=cap and 0<=int(x['decoded_votes'])<=4
 if x['method']=='ResetPortal':equivalent[x['id']]=(x['p'],x['decoded_votes'])
 if x['method']=='ResetSequential':assert equivalent[x['id']]==(x['p'],x['decoded_votes'])
errors=[]
for m in json.loads((D/'metrics.json').read_text()):
 s,n=groups[(m['method'],m['subset'])];errors.append(abs(s/n-m['brier']));assert n==m['n']
f=json.loads((R/'FREEZE.json').read_text());checks.update(prediction_count=predcount==350000,unique_keys=len(keys)==350000,feedback_not_from_future=latest_ok,vote_cap=cap,brier_arithmetic=max(errors)<1e-12,frozen_identities=all(hashlib.sha256((R/n).read_bytes()).hexdigest()==h for n,h in f['sha256'].items()),exact_local_replay=json.loads((R/'REPLAY_CHECK.json').read_text())['all_passed'],recursive_sequential_equal=True)
out=dict(checks=checks,all_passed=all(checks.values()),max_brier_error=max(errors));(R/'AUDIT_RESULTS.json').write_text(json.dumps(out,indent=2)+'\n');print(out);assert out['all_passed']
