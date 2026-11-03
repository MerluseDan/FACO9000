#!/usr/bin/env python3
"""SRDE-P1 preregistered 100-depth blind-world synthetic portal prediction benchmark.

CPU only, Python 3.10+ standard library. Do not confuse synthetic state/valence
with real feelings, and do not confuse structural reachability with causation.
Methods include an exact, equally informed two-state factor-graph baseline.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import platform
import random
import statistics
import sys
import time
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

DEPTH = 100
N_WORLDS = 72
TRIALS_PER_WORLD = 48
Q_VALUES = (0.985, 0.995, 0.999)
EVENT_FLIP = 0.04
WORLD_SEED = 2026110301
DEVELOPMENT_SEED = 2026110300
BOOTSTRAP_SEED = 2026110399
BOOTSTRAP_REPS = 5000
PREDICTORS = ("srde_portal", "state_graph", "state_blind_graph", "constant_0_5", "shuffled_world")


def stable_seed(*integers: int) -> int:
    s = ':'.join(str(x) for x in integers).encode()
    return int.from_bytes(hashlib.sha256(s).digest()[:8], 'big')


@dataclass(frozen=True)
class World:
    index: int
    q: float
    gates: tuple[tuple[tuple[int, ...], ...], ...]  # 3 branches × 100 levels


@dataclass(frozen=True)
class Entry:
    x: int
    y: int
    z: int
    orientation: int
    valence_1000: int
    arousal_1000: int
    context: int


def generate_world(idx: int, seed: int = WORLD_SEED) -> World:
    q = Q_VALUES[idx // 24]
    rng = random.Random(stable_seed(seed, idx, 109))
    gates = tuple(tuple(tuple(rng.randrange(31) for _ in range(8))
                        for _ in range(DEPTH)) for _ in range(3))
    return World(idx, q, gates)


def gate_bit(g: tuple[int, ...], s: Entry) -> int:
    """Which portal branch applies in this local frame, given state and valence."""
    return ((g[0] * s.x + g[1] * s.y + g[2] * s.z
             + g[3] * s.orientation + g[4] * (s.valence_1000 >= 500)
             + g[5] * (s.arousal_1000 >= 600) + g[6] * s.context
             + g[7]) & 1)


def advance(g: tuple[int, ...], s: Entry) -> Entry:
    """Change local coordinate frame; the recursion level is separate from z."""
    return Entry(
        (s.x + 2*s.y + g[1] + 3*s.orientation + s.valence_1000//100) % 31,
        (s.y + 3*s.z + g[2] + s.x + s.arousal_1000//125) % 31,
        (s.z + s.x + 2*s.y + g[3] + s.context) % 31,
        (s.orientation + g[4] + 1) % 4,
        (s.valence_1000 + g[5]*13 + (s.x*7) % 103) % 1001,
        (s.arousal_1000 + g[6]*17 + (s.z*11) % 89) % 1001,
        (s.context + g[7] + s.orientation) % 8,
    )


def branch_portal(bit: int, entry: Entry, gates: tuple, q: float) -> float:
    """Scalar probability recursion in the appropriate local semantic frame."""
    p = float(bit)
    s = entry
    for g in gates:
        if gate_bit(g, s):
            p = 1.0 - p
        p = (1.0 - q) + (2.0*q - 1.0)*p
        s = advance(g, s)
    return p


def branch_graph(bit: int, entry: Entry, gates: tuple, q: float) -> float:
    """Equally informed exact factor-graph sum-product, explicit 2-state table."""
    p0, p1 = float(1-bit), float(bit)
    s = entry
    for g in gates:
        if gate_bit(g, s):
            p0, p1 = p1, p0
        n0 = q*p0 + (1-q)*p1
        n1 = (1-q)*p0 + q*p1
        p0, p1 = n0, n1
        s = advance(g, s)
    return p1


def event_prob_three(branch_probs: list[float]) -> float:
    a, b, c = branch_probs
    majority = a*b + a*c + b*c - 2*a*b*c
    return EVENT_FLIP + (1 - 2*EVENT_FLIP)*majority


def forecast(method: str, world: World, root: int, entry: Entry) -> float:
    if method == "constant_0_5":
        return 0.5
    if method == "state_blind_graph":
        # No state-dependent offsets. Exact two-state channel composition.
        p = (1 + (2*world.q - 1)**DEPTH)/2
        p_terminal = p if root == 1 else 1-p
        return event_prob_three([p_terminal]*3)
    fn = branch_portal if method in ("srde_portal", "shuffled_world") else branch_graph
    vals = [fn(root, entry, branch_gates, world.q) for branch_gates in world.gates]
    return event_prob_three(vals)


def simulate(world: World, root: int, entry: Entry, rng: random.Random) -> int:
    terminals = []
    for gates in world.gates:
        s = entry
        bit = root
        for g in gates:
            bit ^= gate_bit(g, s)
            if rng.random() > world.q:
                bit ^= 1
            s = advance(g, s)
        terminals.append(bit)
    event = int(sum(terminals) >= 2)
    if rng.random() < EVENT_FLIP:
        event ^= 1
    return event


def posterior_root(e: int, p_e1_given_root0: float, p_e1_given_root1: float) -> float:
    l0 = p_e1_given_root0 if e else 1-p_e1_given_root0
    l1 = p_e1_given_root1 if e else 1-p_e1_given_root1
    return l1/(l0+l1)


def metrics(trials: list[dict], model: str, target: str = "event") -> dict:
    pred_key = "forecast_"+model if target == "event" else "backward_"+model
    ys = [r[target] if target == "event" else r["root"] for r in trials]
    ps = [r[pred_key] for r in trials]
    brier = statistics.fmean((p-y)**2 for p,y in zip(ps,ys))
    logloss = statistics.fmean(-(y*math.log(max(p,1e-15))+(1-y)*math.log(max(1-p,1e-15))) for p,y in zip(ps,ys))
    acc = statistics.fmean(int((p>=.5)==y) for p,y in zip(ps,ys))
    bins=[]; ece=0
    for i in range(5):
        a=i/5; b=(i+1)/5
        indices=[j for j,p in enumerate(ps) if a<=p<(b if i<4 else b+1e-12)]
        if not indices: continue
        pc=statistics.fmean(ps[j] for j in indices)
        oc=statistics.fmean(ys[j] for j in indices)
        ece+=len(indices)/len(ps)*abs(pc-oc)
        bins.append(dict(lo=a,hi=b,n=len(indices),forecast=round(pc,5),observed=round(oc,5)))
    return {'n':len(trials),'brier':round(brier,8),'log_loss':round(logloss,8),'threshold_accuracy':round(acc,8),
            'brier_skill_vs_0_25':round(1-brier/.25,8),'ece_5bin':round(ece,8),'reliability_bins':bins}


def bootstrap_world_diff(trials: list[dict], a: str, b: str, reps: int=BOOTSTRAP_REPS) -> dict:
    by_world=defaultdict(list)
    for row in trials:
        by_world[row['world']].append(row)
    world_diffs=[]
    for group in by_world.values():
        world_diffs.append(statistics.fmean((r['forecast_'+a]-r['event'])**2-
                                           (r['forecast_'+b]-r['event'])**2 for r in group))
    obs=statistics.fmean(world_diffs)
    rng=random.Random(stable_seed(BOOTSTRAP_SEED, len(world_diffs), len(a), len(b)))
    n=len(world_diffs)
    dist=[statistics.fmean(world_diffs[rng.randrange(n)] for _ in range(n)) for _ in range(reps)]
    dist.sort()
    return {'a':a,'b':b,'worlds':n,'paired_mean_brier_delta_a_minus_b':round(obs,8),
            'world_bootstrap_ci95':[round(dist[int(.025*reps)],8),round(dist[int(.975*reps)-1],8)],
            'bootstrap_reps':reps,'bootstrap_seed':BOOTSTRAP_SEED,
            'negative_favors_a':True}


def selftest():
    # Smoke test on disjoint seed. No holdout-world labels are generated here.
    w=generate_world(48,DEVELOPMENT_SEED)
    e=Entry(7,20,9,2,123,746,5)
    assert gate_bit((0,0,0,0,0,0,0,0),e)==0
    assert gate_bit((0,0,0,0,0,0,0,1),e)==1
    for root in (0,1):
        p=forecast("srde_portal",w,root,e)
        g=forecast("state_graph",w,root,e)
        assert abs(p-g)<1e-12,(p,g)
        assert 0<p<1
        other=forecast("state_blind_graph",w,root,e)
        assert 0<other<1
    assert abs(posterior_root(1,.2,.8)-.8)<1e-12
    assert abs(posterior_root(0,.2,.8)-.2)<1e-12
    vals=[.1,.2,.3]
    assert abs(event_prob_three(vals)-(.04+.92*(.1*.2+.1*.3+.2*.3-2*.1*.2*.3)))<1e-12
    assert 0<=advance(w.gates[0][0],e).valence_1000<=1000
    return {'smoke_seed':DEVELOPMENT_SEED,'exact_graph_portal_invariant':True,'bayes_invariant':True,
            'gate_and_frame_invariants':True,'outcomes_observed':False}


def run(outdir: Path):
    outdir.mkdir(exist_ok=True,parents=True)
    smoke=selftest()
    worlds=[generate_world(i) for i in range(N_WORLDS)]
    results=[]; runtime_ns=defaultdict(list); sensitivity=[]; nulls=[]
    for i,world in enumerate(worlds):
        partner=worlds[(i//24)*24+(i+1)%24]
        for case in range(TRIALS_PER_WORLD):
            rng=random.Random(stable_seed(WORLD_SEED, i, case, 771))
            entry=Entry(rng.randrange(31),rng.randrange(31),rng.randrange(31),rng.randrange(4),
                        rng.randrange(1001),rng.randrange(1001),rng.randrange(8))
            root=rng.randrange(2)
            event=simulate(world,root,entry,rng)
            unrelated=rng.randrange(2)
            row={'world':i,'case':case,'q':world.q,'depth':DEPTH,'root':root,'event':event,
                 'unrelated_null_event':unrelated,'entry':entry.__dict__}
            for method in PREDICTORS:
                model_world=partner if method=='shuffled_world' else world
                start=time.perf_counter_ns()
                p0=forecast(method,model_world,0,entry)
                p1=forecast(method,model_world,1,entry)
                runtime_ns[method].append(time.perf_counter_ns()-start)
                row['forecast_'+method]=p1 if root else p0
                row['backward_'+method]=posterior_root(event,p0,p1)
            assert abs(row['forecast_srde_portal']-row['forecast_state_graph']) < 1e-11
            assert abs(row['backward_srde_portal']-row['backward_state_graph']) < 1e-11
            # State sensitivity, explicitly a synthetic input intervention, not human emotion.
            if case == 0:
                low=Entry(entry.x,entry.y,entry.z,entry.orientation,0,entry.arousal_1000,entry.context)
                high=Entry(entry.x,entry.y,entry.z,entry.orientation,1000,entry.arousal_1000,entry.context)
                sensitivity.append(abs(forecast('srde_portal',world,root,low)-
                                       forecast('srde_portal',world,root,high)))
            # Negative control: prove that predictions on unrelated events are not evidential.
            nulls.append(((row['forecast_srde_portal']-unrelated)**2,(0.5-unrelated)**2))
            results.append(row)
    observed=[]
    for method in PREDICTORS:
        observed.append({'model':method,'forward':metrics(results,method,'event'),
                         'backward':metrics(results,method,'root'),
                         'runtime_cpu_ns_median_per_two_root_queries':round(statistics.median(runtime_ns[method]),2),
                         'runtime_cpu_ns_mean_per_two_root_queries':round(statistics.fmean(runtime_ns[method]),2)})
    delta_h1=bootstrap_world_diff(results,'srde_portal','state_graph')
    delta_h2=bootstrap_world_diff(results,'srde_portal','state_blind_graph')
    delta_h4=bootstrap_world_diff(results,'srde_portal','shuffled_world')
    q_group=[]
    for q in Q_VALUES:
        subset=[r for r in results if r['q']==q]
        q_group.append({'q':q,'worlds':len(set(r['world'] for r in subset)),'n':len(subset),
                        'portal_brier':metrics(subset,'srde_portal')['brier'],
                        'state_graph_brier':metrics(subset,'state_graph')['brier'],
                        'blind_brier':metrics(subset,'state_blind_graph')['brier'],
                        'uninformed_brier':metrics(subset,'constant_0_5')['brier']})
    summary={'name':'SRDE-P1 blind-world 100-level portal forecasting / backward inference',
             'run_utc':datetime.now(timezone.utc).isoformat(),
             'pre_registration_file':'PREREGISTRATION.md',
             'method_status':'CPU synthetic experiment; no observed real-world future events',
             'seed':WORLD_SEED,'worlds':N_WORLDS,'trials_per_world':TRIALS_PER_WORLD,
             'total_test_queries':len(results),'levels':DEPTH,'branches':3,
             'q_values':Q_VALUES,'event_flip':EVENT_FLIP,
             'development_smoke':smoke,'metrics':observed,
             'world_clustered_bootstrap':{'H1_portal_vs_strong_graph':delta_h1,
                                          'H2_portal_vs_state_blind':delta_h2,
                                          'H4_portal_vs_mismatched_rules':delta_h4},
             'by_q':q_group,
             'null_event':{'n':len(nulls),'unsupported_portal_association_brier':round(statistics.fmean(x[0] for x in nulls),8),
                           'correct_provenance_abstention_brier':round(statistics.fmean(x[1] for x in nulls),8),
                           'note':'Independent synthetic null: a portal path does not establish an event link.'},
             'synthetic_valence_sensitivity':{'pairs':len(sensitivity),'mean_absolute_forecast_change_F0_vs_F1':round(statistics.fmean(sensitivity),8),
                                            'nonzero_world_fraction':round(sum(v>1e-10 for v in sensitivity)/len(sensitivity),8),
                                            'meaning':'Conditional-input sanity check only; not human emotion'},
             'environment':{'python':sys.version.split()[0],'platform':platform.platform(),
                            'cpu':platform.processor() or platform.machine(),'pid':os.getpid(),
                            'gpu_used':False},
             'limitations':['The generator and predictors share known causal mechanisms; prediction is in-simulator only.',
                            'No actual natural-language meaning embeddings or human cognition.',
                            'No external observational data, timestamps or intervention validation.',
                            'The strong graph baseline is information-equivalent to portal recursion.',
                            'CPU timings are for unoptimized Python prototypes, not a compute-efficiency proof.'],
             'primary_interpretation':'A nonnegative H1 point estimate does not favor SRDE over the strong graph baseline.'}
    (outdir/'heldout_predictions.jsonl').write_text(''.join(json.dumps(r,sort_keys=True)+'\n' for r in results),encoding='utf-8')
    (outdir/'summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print('WORLDS',N_WORLDS,'CASES',len(results),'DEPTH',DEPTH)
    for row in observed:
        print(row['model'],'Brier=',row['forward']['brier'],'Backward=',row['backward']['brier'],
              'accuracy=',row['forward']['threshold_accuracy'])
    for k,v in summary['world_clustered_bootstrap'].items():
        print(k,'delta=',v['paired_mean_brier_delta_a_minus_b'],'CI=',v['world_bootstrap_ci95'])
    print('NULL',summary['null_event'])
    print('F_SENSITIVITY',summary['synthetic_valence_sensitivity'])
    print('Saved in',outdir)
    return summary


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--selftest',action='store_true')
    ap.add_argument('--outdir',default='.')
    args=ap.parse_args()
    if args.selftest:
        print(json.dumps(selftest(),indent=2));return
    run(Path(args.outdir))


if __name__=='__main__':
    main()
