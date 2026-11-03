import json,csv,gzip,hashlib,zipfile
from pathlib import Path
from collections import defaultdict,Counter
R=Path(__file__).parent;D=R/'results';checks={}
raw=[json.loads(s) for s in gzip.open(D/'source_cases.jsonl.gz','rt')];gold={c['id']:c for c in raw}
checks['source_count']=len(gold)==56000
checks['source_splits']=dict(Counter(c['split'] for c in raw))=={'train':20000,'calibration':6000,'chronological':10000,'unseen':10000,'shift':10000}
checks['all_past_reports']=all(e['observed_time']<=c['time']<c['target_time'] for c in raw for e in c['reports'])
rows=list(csv.DictReader((D/'predictions.csv').open()));checks['prediction_count']=len(rows)==360000;checks['unique_keys']=len({(r['id'],r['method']) for r in rows})==len(rows)
checks['matching_heldout_gold']=all(int(r['y'])==gold[r['id']]['y'] and r['split']==gold[r['id']]['split'] and r['split'] not in ['train','calibration'] for r in rows)
checks['vote_cap']=all(0<=int(r['decoded_votes'])<=4 for r in rows)
groups=defaultdict(list)
for r in rows:groups[(int(r['seed']),r['split'],r['method'])].append(r)
err=0.
for m in json.loads((D/'metrics.json').read_text()):
 g=groups[(m['seed'],m['split'],m['method'])];b=sum((min(1-1e-7,max(1e-7,float(x['p'])))-int(x['y']))**2 for x in g)/len(g);err=max(err,abs(b-m['brier']))
checks['brier_arithmetic']=err<1e-12
f=json.loads((R/'FREEZE.json').read_text());checks['code_frozen']=hashlib.sha256((R/'run_simulation.py').read_bytes()).hexdigest()==f['code_sha256'];checks['protocol_frozen']=hashlib.sha256((R/'PROTOCOL.json').read_bytes()).hexdigest()==f['protocol_sha256']
checks['local_replay']=json.loads((R/'LOCAL_REPLAY_CHECK.json').read_text())['all_passed'];comp=json.loads((R/'COLAB_COMPARISON.json').read_text());checks['colab_source_identity']=comp['source_cases_decompressed'] and comp['latent_gold_decompressed']
checks['colab_five_methods_exact']=all(d['different']==0 for m,d in comp['by_method'].items() if not m.startswith('GraphHGB4'))
with zipfile.ZipFile(R/'Colab_CPU_Executed_Results.zip') as z:checks['colab_zip_crc']=z.testzip() is None
out=dict(checks=checks,all_integrity_checks_passed=all(checks.values()),max_brier_error=err,cross_platform_all_models_numerical_tolerance_passed=comp['metric_tolerance_1e-6'],limitation='HGB version-sensitive difference retained; no all-model exact cross-platform claim.')
(R/'AUDIT_RESULTS.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2));assert out['all_integrity_checks_passed']
