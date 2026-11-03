#!/usr/bin/env python3
"""Reproducible *synthetic sanity checks* for the SRDE portal hypothesis.

No model of a human brain, no semantic understanding, and no real-world
prediction is claimed. Dependencies: Python 3.10+ standard library only.
"""
import argparse
import json
import math
import random
from datetime import date
from pathlib import Path

DEFAULT_SEED = 20261102


def wilson_interval(successes, n, z=1.959963984540054):
    if n < 1:
        raise ValueError('n must be positive')
    p = successes / n
    denom = 1 + z*z/n
    centre = (p + z*z/(2*n))/denom
    radius = z*math.sqrt(p*(1-p)/n + z*z/(4*n*n))/denom
    return [round(max(0.0, centre-radius), 5), round(min(1.0, centre+radius), 5)]


def theoretical_endpoint_accuracy(q, depth):
    """Symmetric binary flip chain, each edge preserves the state with probability q."""
    return (1.0 + (2*q-1)**depth)/2.0


def binary_portal_test(q, depth, trials, seed):
    rng = random.Random(seed)
    correct_one = correct_majority = 0
    brier = 0.0
    r = theoretical_endpoint_accuracy(q, depth)
    for _ in range(trials):
        root = rng.getrandbits(1)
        terminals = []
        for _ in range(3):
            current = root
            for _ in range(depth):
                if rng.random() > q:
                    current = 1 - current
            terminals.append(current)
        correct_one += terminals[0] == root
        # Independent routes through the synthetic graph. The event here
        # is defined as the MAJORITY of the three endpoint states.
        majority_event = int(sum(terminals) >= 2)
        correct_majority += majority_event == root
        forecast_prob_one = r if root else 1-r
        brier += (forecast_prob_one - terminals[0])**2
    a1, a3 = correct_one/trials, correct_majority/trials
    predicted_majority = 3*r*r - 2*r*r*r
    return {
        'per_edge_preservation_q': q,
        'depth': depth,
        'trials': trials,
        'one_route': {'correct': correct_one, 'accuracy': round(a1, 5),
                      'wilson_95': wilson_interval(correct_one, trials),
                      'theoretical_accuracy': round(r, 5),
                      'oracle_brier': round(brier/trials, 5),
                      'trivial_0_5_brier': 0.25},
        'three_independent_routes_majority': {
            'correct': correct_majority, 'accuracy': round(a3, 5),
            'wilson_95': wilson_interval(correct_majority, trials),
            'theoretical_accuracy': round(predicted_majority, 5)},
        'duplicate_ballots_have_no_new_information': True,
        'directional_note': 'Root to endpoint is generation; endpoint to root is inference under a uniform-root symmetric-channel assumption.'
    }


def reachability_null(width, depth, edges_per_node, worlds, seed):
    """Random, evidence-free portals. Reachability never establishes causality."""
    rng = random.Random(seed)
    steps = [0, 1, 2, 3, 5, 10, 25, 50, 100]
    steps = [s for s in steps if s <= depth]
    sums = {str(d): 0 for d in steps}
    full_endpoints = 0
    for _ in range(worlds):
        reachable = {0}
        for d in range(depth+1):
            if d in steps:
                sums[str(d)] += len(reachable)
            if d == depth:
                if len(reachable) == width:
                    full_endpoints += 1
                break
            # A randomly wired layered DAG, with no semantic or evidence signal.
            adj = {j: rng.sample(range(width), edges_per_node) for j in range(width)}
            reachable = set().union(*(set(adj[i]) for i in reachable))
    return {
        'width': width, 'depth': depth, 'outgoing_edges_per_node': edges_per_node,
        'worlds': worlds,
        'mean_reachable_endpoints_by_depth': {d: round(v/worlds, 3) for d,v in sums.items()},
        'fraction_worlds_all_endpoints_reachable_at_final_depth': round(full_endpoints/worlds, 5),
        'important': 'These are randomly wired noncausal links. Long path existence is a negative control, not discovered meaning.'
    }


def run(depth=100, trials=20000, worlds=100, seed=DEFAULT_SEED):
    assert depth > 0 and trials > 0 and worlds > 0
    rates = [0.995, 0.98, 0.90, 0.50]
    tests = [binary_portal_test(q, depth, trials, seed+i*10009) for i,q in enumerate(rates)]
    null = reachability_null(width=12, depth=depth, edges_per_node=2,
                             worlds=worlds, seed=seed+99999)
    # Sanity checks are independent of the outcome used to write the manuscript.
    for t in tests:
        p=t['one_route']['accuracy']; theo=t['one_route']['theoretical_accuracy']
        margin=5*math.sqrt(0.25/trials)
        assert abs(p-theo)<margin, (p,theo,margin)
    assert abs(tests[-1]['one_route']['accuracy']-0.5)<0.03
    assert tests[0]['three_independent_routes_majority']['accuracy'] > tests[0]['one_route']['accuracy']
    return {
        'title': 'SRDE Portal Depth: 100-level controlled synthetic sanity checks',
        'generated_on': str(date(2026,11,2)),
        'seed': seed,
        'tested_properties': 'Long-path connectivity vs information retention; independent vs duplicate voting',
        'not_tested': ['semantic meaning representation', 'geometric orientation', 'feeling F', 'temporal portal lifetimes',
                       'forecasting actual future events', 'human neuroscience', 'SRDE superiority over alternative algorithms'],
        'binary_chain_experiments': tests,
        'reachability_null_experiment': null,
        'interpretation': 'Random portals connect many endpoints but carry no real information. Signal along long noisy chains rapidly degrades. Independent votes can help only under assumptions about their dependence and accuracy.'
    }


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--out', default='srde_portal_results.json')
    ap.add_argument('--depth',type=int,default=100)
    ap.add_argument('--trials',type=int,default=20000)
    ap.add_argument('--worlds',type=int,default=100)
    ap.add_argument('--seed',type=int,default=DEFAULT_SEED)
    args=ap.parse_args()
    result=run(args.depth,args.trials,args.worlds,args.seed)
    out=Path(args.out)
    out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print('Wrote',out)
    for row in result['binary_chain_experiments']:
        print('q={:.3f}: one={:.4%}; three={:.4%}; theoretical(one)={:.4%}; Brier={:.5f}'.format(
            row['per_edge_preservation_q'],row['one_route']['accuracy'],
            row['three_independent_routes_majority']['accuracy'],
            row['one_route']['theoretical_accuracy'],row['one_route']['oracle_brier']))
    print('Random-portal reachable endpoints per layer:',result['reachability_null_experiment']['mean_reachable_endpoints_by_depth'])

if __name__=='__main__':
    main()
