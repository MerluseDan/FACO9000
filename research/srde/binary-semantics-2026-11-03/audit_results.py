"""Independent arithmetic/coverage audit of saved outputs; no model inference."""
import csv,gzip,json,hashlib
from pathlib import Path
from collections import defaultdict
R=Path(__file__).parent;D=R/'results';checks={}
raw=[json.loads(s) for s in gzip.open(D/'synthetic_source.jsonl.gz','rt')]
gold={c['id']:c for c in raw};checks['source_count']=len(gold)==27000
checks['source_splits']={s:sum(c['split']==s for c in raw) for s in ['train','calibration','test','shift']}=={'train':12000,'calibration':3000,'test':6000,'shift':6000}
rows=list(csv.DictReader((D/'synthetic_predictions.csv').open()));checks['prediction_count']=len(rows)==336000
checks['unique_prediction_keys']=len({(r['seed'],r['id'],r['method']) for r in rows})==len(rows)
groups=defaultdict(list)
for r in rows:groups[(int(r['seed']),r['split'],r['method'])].append(r)
checks['only_heldout_gold']=all(r['split'] in ['test','shift'] and int(r['y'])==gold[r['id']]['y'] and r['split']==gold[r['id']]['split'] for r in rows)
checks['all_predictions_bounded']=all(0<=float(r['p'])<=1 for r in rows)
maxerr=0
for m in json.loads((D/'synthetic_metrics.json').read_text()):
 g=groups[(m['seed'],m['split'],m['method'])]
 # The benchmark clips all metric inputs at 1e-7, including deterministic raw arms.
 b=sum((min(1-1e-7,max(1e-7,float(x['p'])))-int(x['y']))**2 for x in g)/len(g)
 maxerr=max(maxerr,abs(b-m['brier']))
checks['brier_recomputed_from_raw']=maxerr<1e-12
f=json.loads((R/'FREEZE.json').read_text());checks['frozen_code_identity']=hashlib.sha256((R/'run_experiment.py').read_bytes()).hexdigest()==f['code_sha256'];checks['frozen_protocol_identity']=hashlib.sha256((R/'PROTOCOL.json').read_bytes()).hexdigest()==f['protocol_sha256']
checks['digit_split_identity']=json.loads((D/'digits_splits.json').read_text())==f['digits_splits']
checks['repeat_reproduction']=json.loads((R/'REPRODUCTION_CHECK.json').read_text())['all_passed']
checks['all_passed']=all(checks.values());checks['max_arithmetic_brier_error']=maxerr
(R/'AUDIT_RESULTS.json').write_text(json.dumps(checks,indent=2)+'\n');print(json.dumps(checks,indent=2));assert checks['all_passed']
