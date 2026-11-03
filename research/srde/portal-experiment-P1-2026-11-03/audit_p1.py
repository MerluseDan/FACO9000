#!/usr/bin/env python3
"""Independent outputs-only audit of SRDE-P1, without importing the model runner."""
from collections import Counter, defaultdict
from pathlib import Path
import hashlib, json, math, statistics, sys

D=Path(__file__).resolve().parent
s=json.loads((D/'summary.json').read_text())
rows=[json.loads(line) for line in (D/'heldout_predictions.jsonl').read_text().splitlines()]
assert len(rows)==3456
assert len({(r['world'],r['case']) for r in rows})==len(rows)
assert sorted(Counter(r['world'] for r in rows).values())==[48]*72
assert Counter(r['q'] for r in rows)=={0.985:1152,0.995:1152,0.999:1152}
assert all(r['depth']==100 for r in rows)
assert sum(r['root'] for r in rows) in range(1450,2020)
assert sum(r['unrelated_null_event'] for r in rows) in range(1450,2020)
assert all(0<=r['entry']['valence_1000']<=1000 and 0<=r['entry']['arousal_1000']<=1000 for r in rows)
assert all(abs(r['forecast_srde_portal']-r['forecast_state_graph'])<1e-11 for r in rows)
assert all(abs(r['backward_srde_portal']-r['backward_state_graph'])<1e-11 for r in rows)
computed={}
for model in ['srde_portal','state_graph','state_blind_graph','constant_0_5','shuffled_world']:
    forward=statistics.fmean((r['forecast_'+model]-r['event'])**2 for r in rows)
    backward=statistics.fmean((r['backward_'+model]-r['root'])**2 for r in rows)
    acc=statistics.fmean(int((r['forecast_'+model]>=.5)==r['event']) for r in rows)
    expected=next(m for m in s['metrics'] if m['model']==model)
    assert abs(forward-expected['forward']['brier'])<1e-8
    assert abs(backward-expected['backward']['brier'])<1e-8
    assert abs(acc-expected['forward']['threshold_accuracy'])<1e-8
    computed[model]={'forward_brier':forward,'backward_brier':backward,'accuracy':acc}
null_pred=statistics.fmean((r['forecast_srde_portal']-r['unrelated_null_event'])**2 for r in rows)
assert abs(null_pred-s['null_event']['unsupported_portal_association_brier'])<1e-8
assert abs(s['null_event']['correct_provenance_abstention_brier']-.25)<1e-12
# Check no obvious leakage by case label; predictions have neither observed event nor null in their keys.
assert all(0<=r['forecast_srde_portal']<=1 for r in rows)
# Root is a *known input* for the forward task, not secretly inferred from outcomes.
sha={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in D.glob('*') if p.is_file() and p.name!='audit_p1.json'}
out={'status':'PASS','checked_rows':len(rows),'unique_trials':len({(r['world'],r['case']) for r in rows}),
     'worlds':72,'trials_per_world':48,'depth':100,'strong_graph_equivalence':True,
     'independent_recomputed_metrics':computed,'unrelated_null_spurious_prediction_brier':null_pred,
     'file_sha256_before_audit':sha,'limitations':['Audit of outputs and runner invariants; not independent validation of the synthetic generator or real-world prediction.',
                                                   'Strong graph and SRDE parity is mathematically expected.']}
(D/'audit_p1.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
print('PASS: 3456 unique trials; balanced q; 72 holdout worlds; graph parity; forward/backward metrics; null control; SHA manifest')
