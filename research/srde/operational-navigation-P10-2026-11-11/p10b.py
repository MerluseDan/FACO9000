#!/usr/bin/env python3
"""P10B independent future seed set: strong conventional project-locality challenger.
Imports frozen P10 simulator *without modifying it*; geometric policy locked at lambda=1.
"""
from __future__ import annotations
import argparse,csv,hashlib,json,random,statistics
from pathlib import Path
import p10
GRID=(0.31,0.6,0.9,1.2,1.5)
DEV=1111000
CONF=1311000
DEV_N=20
CONF_N=80
BOOT=4000
BOOT_SEED=20261112

def sha(fn):return hashlib.sha256(Path(fn).read_bytes()).hexdigest()
def worlds(baseseed,n):
    return [(baseseed+i*10000+j,s) for i,s in enumerate(p10.SCENARIOS) for j in range(n)]

class TunedGraph(p10.State):
    def __init__(self,world,bonus):
        super().__init__(world,'graph_cached',0)
        self.bonus=bonus
    def choose(self,ready):
        def score(t):
            v=t.value+0.20*(p10.STAGES-t.stage)
            if t.project==self.last_project:v+=self.bonus
            if t.stage in self.recipe:v+=0.08
            return(v,-t.id)
        return max(ready,key=score)

def challenge_one(world,bonus):
    z=TunedGraph(world,bonus)
    for tick in range(p10.HORIZON):
        if tick in world.events:z.revision(world.events[tick])
        if tick in world.interrupts:
            z.last_project=None;z.last_xy=None;z.interrupt_count+=1
        affordable=[t for t in z.ready(tick) if z.budget>=z.expected_cost(t)]
        if affordable:z.execute(tick,z.choose(affordable))
    final=z.valid_all();count=sum(final.values())
    return {'seed':world.seed,'scenario':world.scenario,'method':'tuned_conventional_graph','bonus':bonus,
           'valid_tasks':count,'valid_weighted':round(sum(t.value for t in world.tasks if final[t.id]),10),
           'effort_units':round(p10.BUDGET-z.budget,7),'unsafe_attempts':z.unsafe,
           'context_switches':z.switches,'small_model_calls':z.small,'large_model_calls':z.large,
           'recipe_reuses':z.recipes,'all_tasks_valid':count==p10.N_TASKS}

def srde_one(world):
    raw=p10.run_one(world,'srde',1.0)
    return {'seed':raw['seed'],'scenario':raw['scenario'],'method':'srde_frozen_lambda_1',
            'bonus':None,'valid_tasks':raw['valid_tasks'],'valid_weighted':raw['valid_weighted'],
            'effort_units':raw['effort_units'],'unsafe_attempts':raw['unsafe_attempts'],
            'context_switches':raw['context_switches'],'small_model_calls':raw['small_model_calls'],
            'large_model_calls':raw['large_model_calls'],'recipe_reuses':raw['recipe_reuses'],
            'all_tasks_valid':raw['all_tasks_valid']}

def prereg_hashes(dir):
    return {'p10_original_sha256':sha(dir/'p10.py'),'p10b_code_sha256':sha(dir/'p10b.py'),
            'p10b_prereg_sha256':sha(dir/'P10B_PREREGISTRATION.md')}

def develop(dir):
    lock=dir/'P10B_DEVELOPMENT_LOCK.json';assert not lock.exists()
    assert len(set(seed for seed,s in worlds(DEV,DEV_N)))==100
    assert {seed for seed,s in worlds(DEV,DEV_N)}.isdisjoint({seed for seed,s in worlds(CONF,CONF_N)})
    results=[]
    for bonus in GRID:
        rows=[challenge_one(p10.make_world(seed,s),bonus) for seed,s in worlds(DEV,DEV_N)]
        results.append({'bonus':bonus,'mean_valid_weighted':statistics.fmean(r['valid_weighted'] for r in rows),
                        'mean_effort_units':statistics.fmean(r['effort_units'] for r in rows)})
    selected=sorted(results,key=lambda x:(-x['mean_valid_weighted'],x['bonus']))[0]
    rec={'status':'DEVELOPMENT_LOCKED_CONFIRMATION_UNOPENED','dev_worlds':100,'confirm_worlds':400,
         'grid':results,'selected_bonus':selected['bonus'],'hashes':prereg_hashes(dir),
         'selection':'max development validated weighted value; tie lower bonus',
         'confirmation_access':'No confirmation world was instantiated in this function.'}
    lock.write_text(json.dumps(rec,indent=2)+'\n')
    print('P10B DEVELOPMENT LOCK',json.dumps({'selected':selected,'grid':results},indent=2))

def interval(x):
    rng=random.Random(BOOT_SEED);n=len(x)
    data=[sum(x[rng.randrange(n)] for _ in range(n))/n for i in range(BOOT)]
    data.sort();return[data[100],data[3899]]

def confirm(dir):
    path=dir/'P10B_CONFIRMATION.csv';assert not path.exists(),'Do not retest an already-scored confirmation.'
    lock=json.loads((dir/'P10B_DEVELOPMENT_LOCK.json').read_text())
    assert lock['status']=='DEVELOPMENT_LOCKED_CONFIRMATION_UNOPENED'
    assert lock['hashes']==prereg_hashes(dir),'Frozen pre-confirmation source changed'
    bonus=float(lock['selected_bonus'])
    raw=[]
    for i,(seed,s) in enumerate(worlds(CONF,CONF_N)):
        world=p10.make_world(seed,s)
        raw.append(challenge_one(world,bonus))
        raw.append(srde_one(world))
        if (i+1)%80==0:print('P10B CONFIRMATION WORLDS',i+1,flush=True)
    with path.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(raw[0]));w.writeheader();w.writerows(raw)
    by={(int(r['seed']),r['method']):r for r in raw}
    diffs=[by[(seed,'srde_frozen_lambda_1')]['valid_weighted']-by[(seed,'tuned_conventional_graph')]['valid_weighted'] for seed,_ in worlds(CONF,CONF_N)]
    means={method:{key:statistics.fmean(float(r[key]) for r in raw if r['method']==method)
          for key in ('valid_tasks','valid_weighted','effort_units','unsafe_attempts','context_switches','small_model_calls','large_model_calls','recipe_reuses','all_tasks_valid')}
          for method in ('srde_frozen_lambda_1','tuned_conventional_graph')}
    comparisons={s:{m:statistics.fmean(r['valid_weighted'] for r in raw if r['scenario']==s and r['method']==m)
                   for m in means} for s in p10.SCENARIOS}
    ci=interval(diffs);correct=(ci[0]>0 and
        means['srde_frozen_lambda_1']['unsafe_attempts']<=means['tuned_conventional_graph']['unsafe_attempts'] and
        means['srde_frozen_lambda_1']['effort_units']<=means['tuned_conventional_graph']['effort_units'])
    report={'status':'P10B_NEW_SEED_COMPARATOR_CHALLENGE_NOT_REAL_AI',
            'selected_bonus':bonus,'worlds':400,'rows':len(raw),'means':means,
            'srde_minus_conventional':statistics.fmean(diffs),'paired_CI95':ci,
            'fraction_srde_better':sum(v>0 for v in diffs)/400,
            'fraction_srde_equal':sum(v==0 for v in diffs)/400,
            'by_scenario':comparisons,'distinct_spatial_advantage_confirmed':correct,
            'limitations':['Follows positive P10; distinct test seeds but same synthetic simulator and rules',
            'Conventional graph bonus is tuned with new separate development worlds, spatial lambda inherited from P10',
            'Neither method runs a real AI, website, or actual concurrent FACO projects',
            'Conventional heuristic may still have alternatives beyond one project coefficient']}
    (dir/'P10B_RESULTS.json').write_text(json.dumps(report,indent=2)+'\n')
    print('P10B CONFIRMATION RESULTS',json.dumps(report,indent=2))

def selftest():
    for s in p10.SCENARIOS:
        w=p10.make_world(889900,s)
        r=challenge_one(w,0.31)
        b=p10.run_one(w,'graph_cached',0)
        for key in ('valid_tasks','valid_weighted','effort_units','unsafe_attempts','context_switches',
                    'small_model_calls','large_model_calls','recipe_reuses','all_tasks_valid'):
            assert r[key]==b[key],(s,key,r[key],b[key])
    assert {seed for seed,s in worlds(DEV,DEV_N)}.isdisjoint({seed for seed,s in worlds(CONF,CONF_N)})
    assert {seed for seed,s in worlds(CONF,CONF_N)}.isdisjoint({seed for seed,s in p10.seed_list('holdout')})
    print('P10B SELFTEST PASS: conventional coefficient=0.31 matches frozen graph, seed sets isolated.')

def main():
    a=argparse.ArgumentParser();a.add_argument('stage',choices=['selftest','develop','confirm']);a.add_argument('--out',type=Path,required=True)
    opt=a.parse_args();opt.out.mkdir(parents=True,exist_ok=True)
    {'selftest':lambda:selftest(),'develop':lambda:develop(opt.out),'confirm':lambda:confirm(opt.out)}[opt.stage]()
if __name__=='__main__':main()
