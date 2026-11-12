#!/usr/bin/env python3
"""SRDE-P10: controlled CPU task navigation benchmark.

This is a synthetic agent-controller microbenchmark, NOT an LLM evaluation.
Stages: selftest, develop, holdout. Preregistration and source hashes must match.
"""
from __future__ import annotations
import argparse, csv, hashlib, json, math, random, statistics, time
from dataclasses import dataclass
from pathlib import Path
from collections import defaultdict

SCENARIOS = ('steady','churn','interrupt','decoy','shift')
POLICIES = ('recency','fullscan','graph_cached','srde','srde_no_evidence')
LAMBDA_GRID = (0.0,0.2,0.6,1.0)
N_PROJECTS=6
STAGES=9
N_TASKS=N_PROJECTS*STAGES
BUDGET=320.0
HORIZON=150
N_DEV=20
N_HOLDOUT=80
BOOT=4000
BASE_DEV=711000
BASE_TEST=911000
BOOT_SEED=20261111

# Cost units are synthetic; costs include tool output verification.
COST={'mechanical':1.5,'tiny':4.5,'large':12.5,'recipe':1.8}
SWITCH=0.7
DIFFICULTY=(0,1,1,2,0,1,2,1,0)

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def seed_list(phase):
    if phase=='dev':return [(BASE_DEV+10000*i+j,s) for i,s in enumerate(SCENARIOS) for j in range(N_DEV)]
    return [(BASE_TEST+10000*i+j,s) for i,s in enumerate(SCENARIOS) for j in range(N_HOLDOUT)]

def deterministic_uniform(*params):
    s='|'.join(map(str,params)).encode()
    return int.from_bytes(hashlib.blake2b(s,digest_size=8).digest(),'big')/(1<<64)

@dataclass(frozen=True)
class Task:
    id:int
    project:int
    stage:int
    deps:tuple[int,...]
    sources:tuple[int,...]
    complexity:int
    arrival:int
    value:float
    x:float
    y:float

@dataclass(frozen=True)
class World:
    seed:int
    scenario:str
    tasks:tuple[Task,...]
    events:dict[int,tuple[int,...]]
    interrupts:tuple[int,...]

def make_world(seed:int, scenario:str)->World:
    assert scenario in SCENARIOS
    rng=random.Random(seed)
    tasks=[]
    for p in range(N_PROJECTS):
        for st in range(STAGES):
            ident=p*STAGES+st
            deps=[]
            if st>0:deps.append(ident-1)
            if st>=4 and st%3==0:deps.append(ident-3)
            if p>0 and st in (3,7):deps.append((p-1)*STAGES+min(st-1,6))
            docs=[(p+st//3)%10]
            if st in (1,5):docs.append((p+st+3)%10)
            # One evidence source per task minimum; two for selected cross-stage tasks.
            value=1.0+0.06*(STAGES-1-st)+0.12*p+0.07*rng.random()
            # Spatial coordinates preserve project + task type but are NOT authoritative dependencies.
            if scenario=='decoy':
                x=(p%2)*0.4+(st%3)*0.11 # unrelated projects deliberately near
                y=(p%3)*0.25+(st//3)*0.06
            else:
                x=(p%3)*1.4+0.12*(st%3)
                y=(p//3)*1.6+0.11*(st//3)
            tasks.append(Task(ident,p,st,tuple(dict.fromkeys(deps)),tuple(dict.fromkeys(docs)),
                       DIFFICULTY[st],p*4+st*2,value,x,y))
    events={}
    if scenario=='churn':ticks=(30,50,71,91,111,132)
    elif scenario=='interrupt':ticks=(41,103)
    elif scenario=='decoy':ticks=(34,75,115)
    elif scenario=='shift':ticks=(44,88,120)
    else:ticks=(95,)
    for k,tick in enumerate(ticks):events[tick]=(rng.randrange(10),)
    interrupts={'steady':(89,), 'churn':(65,124), 'interrupt':(22,45,69,92,116,138),
                'decoy':(75,), 'shift':(77,122)}[scenario]
    return World(seed,scenario,tuple(tasks),events,interrupts)

class State:
    def __init__(self,world:World,policy:str,lam:float):
        self.w=world;self.policy=policy;self.lam=lam
        self.docs=[0]*10
        self.done={} # task id -> (versioned source stamp, dep generation stamp, result generation)
        self.flag=set() # weaker controls remember a completed bit but not enough provenance
        self.recipe=set()
        self.failures=defaultdict(int)
        self.serial=0
        self.budget=BUDGET
        self.last_project=None
        self.last_xy=None
        self.small=0;self.large=0;self.mechanical=0;self.recipes=0
        self.unsafe=0;self.fail=0;self.attempts=0;self.validated=0;self.repaired=0
        self.switches=0;self.interrupt_count=0;self.revisions=0;self.actions=[]
    def check(self,taskid:int, cache:dict|None=None, truth=True)->bool:
        if cache is None:cache={}
        if taskid in cache:return cache[taskid]
        record=self.done.get(taskid)
        if record is None:cache[taskid]=False;return False
        ev,dependencies,_=record
        t=self.w.tasks[taskid]
        if truth or self.policy!='srde_no_evidence':
            if ev!=tuple(self.docs[d] for d in t.sources):cache[taskid]=False;return False
        for dep,gen in zip(t.deps,dependencies):
            if not self.check(dep,cache,truth=truth) or self.done[dep][2]!=gen:
                cache[taskid]=False;return False
        cache[taskid]=True;return True
    def perceived_done(self,taskid:int,cache:dict)->bool:
        return taskid in self.flag if self.policy=='recency' else self.check(taskid,cache,truth=False)
    def valid_all(self):
        cache={}
        return {t.id:self.check(t.id,cache,truth=True) for t in self.w.tasks}
    def revision(self,docs):
        self.revisions+=len(docs)
        for i in docs:self.docs[i]+=1
        if self.policy=='recency':
            # A recency window remembers tasks touched very recently, not the whole provenance map.
            # Deliberately weak control; this must not be used as a strong comparator.
            for tid in list(self.flag):
                if (self.w.tasks[tid].sources and any(d in docs for d in self.w.tasks[tid].sources) and
                    (self.serial-self.done.get(tid,((),(),-100))[2])<=8):
                    self.flag.remove(tid)
    def ready(self,tick:int)->list[Task]:
        cache={}
        out=[]
        for t in self.w.tasks:
            if tick<t.arrival or self.perceived_done(t.id,cache):continue
            if all(self.perceived_done(d,cache) for d in t.deps):out.append(t)
        return out
    def choose(self,ready:list[Task])->Task:
        if self.policy=='recency':return min(ready,key=lambda t:(t.arrival,t.id))
        if self.policy=='fullscan':return max(ready,key=lambda t:(t.value+0.13*(STAGES-t.stage)-0.02*(t.project!=self.last_project),-t.id))
        def score(t):
            # Shared conventional graph priority: importance plus prerequisite-unblocking and project reuse.
            base=t.value+0.20*(STAGES-t.stage)
            base+=0.31 if self.last_project==t.project else 0
            base+=0.08 if t.stage in self.recipe else 0
            if self.policy=='srde' or self.policy=='srde_no_evidence':
                if self.last_xy is not None:
                    dist=math.hypot(t.x-self.last_xy[0],t.y-self.last_xy[1])
                    base+=self.lam/(1.0+dist)
            return(base,-t.id)
        return max(ready,key=score)
    def expected_cost(self,t:Task):
        complex=t.complexity
        can_recipe=(self.policy not in ('recency','fullscan') and complex>0 and t.stage in self.recipe)
        key=(t.id,tuple(self.docs[d] for d in t.sources),
             tuple(self.done[d][2] if d in self.done else -1 for d in t.deps))
        num=self.failures[key]
        tier=('mechanical' if complex==0 else ('recipe' if can_recipe and num==0 else ('tiny' if complex==1 and num==0 else 'large')))
        switch=self.last_project is not None and self.last_project!=t.project
        return COST[tier]+(SWITCH if switch else 0)
    def execute(self,tick:int,t:Task):
        switch=self.last_project is not None and self.last_project!=t.project
        complex=t.complexity
        # Do not change the executor by method. Only fullscan lacks the validated recipe cache.
        can_recipe=(self.policy not in ('recency','fullscan') and complex>0 and t.stage in self.recipe)
        key=(t.id,tuple(self.docs[d] for d in t.sources),
             tuple(self.done[d][2] if d in self.done else -1 for d in t.deps))
        num=self.failures[key]
        if complex==0: tier='mechanical'
        elif can_recipe and num==0:tier='recipe'
        elif complex==1 and num==0:tier='tiny'
        else:tier='large'
        price=COST[tier]+(SWITCH if switch else 0)
        if self.budget<price:return False
        self.budget-=price
        if switch:self.switches+=1
        self.last_project=t.project;self.last_xy=(t.x,t.y)
        self.attempts+=1
        setattr(self,{'tiny':'small','large':'large','recipe':'recipes','mechanical':'mechanical'}[tier],
                getattr(self,{'tiny':'small','large':'large','recipe':'recipes','mechanical':'mechanical'}[tier])+1)
        deps_current={i:self.check(i,truth=True) for i in t.deps}
        if not all(deps_current.values()):
            self.unsafe+=1;self.failures[key]+=1;self.fail+=1
            self.actions.append((tick,t.id,tier,False,'stale_deps'))
            return True
        # Synthetic success probabilities do NOT represent any actual LLM's real performance.
        success_p={'mechanical':1.0,'tiny':0.78,'large':0.94,'recipe':0.92}[tier]
        if self.w.scenario=='shift' and tick>=82 and tier=='recipe':success_p=0.57
        outcome=deterministic_uniform(self.w.seed,t.id,tuple(self.docs[d] for d in t.sources),num,tier)
        ok=outcome<success_p
        self.actions.append((tick,t.id,tier,ok,'tested'))
        if not ok:
            self.fail+=1;self.failures[key]+=1
            return True
        previous=t.id in self.done
        self.serial+=1
        self.done[t.id]=(tuple(self.docs[d] for d in t.sources),tuple(self.done[d][2] for d in t.deps),self.serial)
        self.flag.add(t.id)
        self.validated+=1
        if previous:self.repaired+=1
        if tier in ('tiny','large','recipe'):
            self.recipe.add(t.stage)
        return True

def run_one(world:World,policy:str,lam:float)->dict:
    z=State(world,policy,lam)
    for tick in range(HORIZON):
        if tick in world.events:z.revision(world.events[tick])
        if tick in world.interrupts:
            z.last_project=None;z.last_xy=None;z.interrupt_count+=1
        ready=[t for t in z.ready(tick) if z.budget>=z.expected_cost(t)]
        if not ready:continue
        task=z.choose(ready)
        z.execute(tick,task)
    final=z.valid_all();n=sum(final.values())
    weighted=sum(t.value for t in world.tasks if final[t.id])
    output={
        'seed':world.seed,'scenario':world.scenario,'method':policy,'lambda':lam,'valid_tasks':n,
        'valid_weighted':round(weighted,10),'unsafe_attempts':z.unsafe,'failures':z.fail,
        'small_model_calls':z.small,'large_model_calls':z.large,'recipe_reuses':z.recipes,
        'mechanical_calls':z.mechanical,'total_attempts':z.attempts,'successes_verified_at_action':z.validated,
        'repaired_tasks':z.repaired,'final_stale_records':sum(x in z.done and not final[x] for x in range(N_TASKS)),
        'effort_units':round(BUDGET-z.budget,7),'context_switches':z.switches,
        'interruptions':z.interrupt_count,'source_revisions':z.revisions,
        'per_valid_task_effort':round((BUDGET-z.budget)/n,6) if n else None,
        'ever_done':len(z.done),'all_tasks_valid':n==N_TASKS}
    return output

def simple_stats(rows:list[dict],key:str)->dict:
    vals=[float(x[key]) for x in rows]
    return{'mean':statistics.fmean(vals),'min':min(vals),'max':max(vals)}

def paired_ci(da:list[float], seed=BOOT_SEED):
    rng=random.Random(seed); n=len(da)
    draws=[statistics.fmean(da[rng.randrange(n)] for _ in range(n)) for _ in range(BOOT)]
    draws.sort()
    return [draws[int(.025*BOOT)],draws[int(.975*BOOT)-1]]

def dev(out):
    lock=out/'DEVELOPMENT_LOCK.json'
    assert not lock.exists(),'Do not overwrite frozen validation.'
    sources=hashes(out)
    result=[]
    for lam in LAMBDA_GRID:
        rows=[]
        for seed,s in seed_list('dev'):
            w=make_world(seed,s)
            rows.append(run_one(w,'srde',lam))
        result.append({'lambda':lam,'mean_valid_weighted':statistics.fmean(r['valid_weighted'] for r in rows),
                       'mean_effort':statistics.fmean(r['effort_units'] for r in rows),
                       'worlds':len(rows)})
    selected=sorted(result,key=lambda q:(-q['mean_valid_weighted'],q['lambda']))[0]
    lockobj={'study':'SRDE-P10','phase':'DEVELOPMENT_LOCKED_HOLDOUT_UNOPENED',
             'frozen_source_sha256':sources['p10.py'],'frozen_protocol_sha256':sources['PREREGISTRATION.md'],
             'development_worlds':len(seed_list('dev')),'holdout_worlds_planned':len(seed_list('holdout')),
             'lambda_grid':result,'selected_lambda':selected['lambda'],'selection_rule':'max dev weighted correctly valid work; tie lower lambda',
             'holdout_access':'No holdout world generated or scored during development.'}
    lock.write_text(json.dumps(lockobj,indent=2)+'\n')
    print('DEVELOPMENT LOCK:',json.dumps({'lambda':selected['lambda'],'scores':result},indent=2))

def hashes(out):return {f:sha(out/f) for f in ('p10.py','PREREGISTRATION.md')}

def holdout(out):
    path=out/'RAW_HOLDOUT.csv';assert not path.exists(),'Holdout is one-time; use a fresh extraction for replays.'
    lock=json.loads((out/'DEVELOPMENT_LOCK.json').read_text())
    assert lock['phase']=='DEVELOPMENT_LOCKED_HOLDOUT_UNOPENED'
    assert hashes(out)=={'p10.py':lock['frozen_source_sha256'],'PREREGISTRATION.md':lock['frozen_protocol_sha256']},'Frozen source changed.'
    lam=float(lock['selected_lambda'])
    rows=[]
    for i,(seed,scenario) in enumerate(seed_list('holdout')):
        w=make_world(seed,scenario)
        for method in POLICIES:
            rows.append(run_one(w,method,lam))
        if (i+1)%80==0:print('HOLDOUT WORLDS FINISHED',i+1,flush=True)
    with path.open('w',newline='') as fp:
        writer=csv.DictWriter(fp,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    result={'study':'SRDE-P10','status':'SYNTHETIC_CONTROLLER_MICROBENCHMARK_NOT_REAL_AI',
            'world_count':len(seed_list('holdout')),'method_count':len(POLICIES),'total_score_rows':len(rows),
            'selected_lambda':lam,'limits':['No actual LLM inference, tokens, GPU, or human tasks',
            'Synthetic known graph and evidence revisions','Shared worker proxy probabilities are not empirical model statistics',
            'Exact graph with identical information is the primary competitor',
            'This experiment cannot establish novel mathematical or general AI improvement'],
            'means':{},'comparisons':{},'by_scenario':{}}
    for p in POLICIES:
        subset=[r for r in rows if r['method']==p]
        result['means'][p]={k:statistics.fmean(float(r[k]) for r in subset) for k in
        ('valid_tasks','valid_weighted','unsafe_attempts','failures','small_model_calls','large_model_calls','recipe_reuses','effort_units','context_switches','all_tasks_valid')}
    by={(r['seed'],r['method']):r for r in rows}
    for comparator in ('graph_cached','fullscan','recency'):
        diff=[by[(s,'srde')]['valid_weighted']-by[(s,comparator)]['valid_weighted'] for s,_ in seed_list('holdout')]
        result['comparisons'][comparator]={'srde_minus_comparator_mean':statistics.fmean(diff),
           'paired_world_CI95':paired_ci(diff),'fraction_srde_better':sum(v>0 for v in diff)/len(diff),
           'fraction_equal':sum(v==0 for v in diff)/len(diff)}
    for scenario in SCENARIOS:
        result['by_scenario'][scenario]={p:statistics.fmean(r['valid_weighted'] for r in rows if r['scenario']==scenario and r['method']==p) for p in POLICIES}
    # Deliberately strict: no claim of geometry benefit without positive CI and no unsafe-action/cost worsening.
    comp=result['comparisons']['graph_cached']
    result['geometry_advantage_confirmed']=(comp['paired_world_CI95'][0]>0 and
        result['means']['srde']['unsafe_attempts']<=result['means']['graph_cached']['unsafe_attempts'] and
        result['means']['srde']['effort_units']<=result['means']['graph_cached']['effort_units'])
    result['null_policy_must_match_exactly_if_zero_lambda']=(lam!=0 or all(by[(s,'srde')]==dict(by[(s,'graph_cached')],method='srde') for s,_ in seed_list('holdout')))
    if lam==0:assert result['null_policy_must_match_exactly_if_zero_lambda'],'Zero lambda should exactly tie graph.'
    (out/'RESULTS.json').write_text(json.dumps(result,indent=2)+'\n')
    print('HOLDOUT RESULTS:',json.dumps({'lambda':lam,'means':result['means'],'strong':comp,'confirmed':result['geometry_advantage_confirmed']},indent=2))

def selftest():
    w=make_world(7,'churn')
    assert len(w.tasks)==N_TASKS and all(d<t.id for t in w.tasks for d in t.deps)
    assert len(w.events)>=2
    z=State(w,'graph_cached',0)
    t=w.tasks[0]
    assert z.execute(t.arrival,t) and z.check(t.id)
    source=t.sources[0];z.revision((source,))
    assert not z.check(t.id,truth=True),'Source revision must invalidate a completed task.'
    # No false-valid descendant after parent revision.
    u=State(w,'graph_cached',0)
    for tt in w.tasks[:3]:
        u.serial+=1
        u.done[tt.id]=(tuple(u.docs[d] for d in tt.sources),tuple(u.done[d][2] for d in tt.deps),u.serial)
    assert u.check(2)
    u.revision((w.tasks[0].sources[0],))
    assert not u.check(2,truth=True)
    # Coordinate lambda=0 is the identical conventional scheduling policy.
    for s in SCENARIOS:
        ww=make_world(99,s)
        a=run_one(ww,'graph_cached',0);b=run_one(ww,'srde',0)
        bb=dict(b,method='graph_cached')
        assert a==bb,(s,'exact policy parity failure',a,b)
    for n in ('dev','holdout'):
        sets=seed_list(n)
        assert len(sets)==len(SCENARIOS)*(N_DEV if n=='dev' else N_HOLDOUT)
    assert {x for x,_ in seed_list('dev')}.isdisjoint({x for x,_ in seed_list('holdout')})
    print('SELFTEST PASS: dependency DAG, source invalidation, cascading staleness, exact zero-lambda parity, split isolation')

def main():
    ap=argparse.ArgumentParser();ap.add_argument('stage',choices=('selftest','develop','holdout'))
    ap.add_argument('--out',type=Path,required=True)
    args=ap.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    if args.stage=='selftest':selftest()
    elif args.stage=='develop':dev(args.out)
    else:holdout(args.out)

if __name__=='__main__':main()
