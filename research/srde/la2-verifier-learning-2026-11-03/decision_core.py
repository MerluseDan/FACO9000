"""SRDE-LA1: exact finite decision problem plus untouched sampled cases. Stdlib only."""
import csv,gzip,hashlib,itertools,json,math,random,sys,time,platform
from pathlib import Path
from functools import lru_cache
from dataclasses import dataclass,asdict
R=Path(__file__).parent
H=3; ABSTAIN=.15; EPS=1e-12
@dataclass(frozen=True)
class Model:
    pi:float=.2
    q:float=1.
    delay:int=0
    ca:float=.00375
    cv:float=.015
    acc:float=.8
    fresh:float=.7
def bern(x,y,r):return r if x==y else 1-r
def bits(k):return ((k>>2)&1,(k>>1)&1,k&1)
def initial_likelihood(x,y,l,m):
    a,b,c=bits(x)
    return bern(a,y,m.acc)*bern(c,y,m.acc)*(int(a==b) if l else bern(b,y,m.acc))
@lru_cache(None)
def belief(s,m):
    t,x,fs,z,pending,requested=s
    w=[]
    for y,l in itertools.product(range(2),repeat=2):
        v=.5*(m.pi if l else 1-m.pi)*initial_likelihood(x,y,l,m)
        for f in fs:v*=bern(f,y,m.fresh)
        if z!=-1:v*=bern(z,l,m.q)
        w.append(v)
    total=sum(w)
    return tuple(v/total for v in w) if total>0 else None
def probability(s,m):
    b=belief(s,m)
    return .5 if b is None else b[2]+b[3]
def terminal(s,m):
    p=probability(s,m);risk=p*(1-p)
    return min(risk,ABSTAIN),p,risk>ABSTAIN
def initial(x):return (0,x,(),-1,-1,False)
def actions(s,allow_audit=True):
    t,x,fs,z,pending,requested=s
    if t>=H:return ()
    a=[]
    if len(fs)<2:a.append('F')
    if allow_audit and not requested:a.append('A')
    if pending!=-1:a.append('W')
    return tuple(a)
def cost(a,m):return m.ca if a=='A' else m.cv if a=='F' else 0.
@lru_cache(None)
def transition(s,a,m):
    t,x,fs,z,pending,requested=s
    nt=t+1
    if a=='A':pending=t+m.delay;requested=True
    deliver=pending!=-1 and pending<=nt
    b=belief(s,m)
    if b is None:return ()
    out=[]
    for f in (range(2) if a=='F' else [-1]):
        for az in (range(2) if deliver else [-1]):
            pr=0.
            for idx,(y,l) in enumerate(itertools.product(range(2),repeat=2)):
                pr+=b[idx]*(bern(f,y,m.fresh) if f!=-1 else 1)*(bern(az,l,m.q) if deliver else 1)
            if pr>0:
                ns=(nt,x,fs+(f,) if f!=-1 else fs,az if deliver else z,-1 if deliver else pending,requested)
                out.append((pr,ns))
    return tuple(out)
class TablePlanner:
    """Conventional reachable-state graph and backward induction."""
    def __init__(self,m,allow_audit=True):
        self.m=m;self.allow=allow_audit;self.table={};seen=set();stack=[initial(x) for x in range(8)]
        while stack:
            s=stack.pop()
            if s in seen or belief(s,m) is None:continue
            seen.add(s)
            for a in actions(s):stack.extend(ns for p,ns in transition(s,a,m))
        for s in sorted(seen,key=lambda s:-s[0]):
            best,_,_=terminal(s,m);choice='S'
            for a in actions(s,allow_audit):
                val=cost(a,m)+sum(p*self.table[ns][0] for p,ns in transition(s,a,m))
                if val<best-EPS:best,choice=val,a
            self.table[s]=(best,choice)
    def choose(self,s):return self.table.get(s,(ABSTAIN,'S'))[1]
class RecursivePlanner:
    """Portal-style recursive expansion of the same finite action graph."""
    def __init__(self,m):
        self.m=m
        @lru_cache(None)
        def solve(s):
            best,_,_=terminal(s,m);choice='S'
            if belief(s,m) is None:return best,choice
            for a in actions(s):
                val=cost(a,m)+sum(p*solve(ns)[0] for p,ns in transition(s,a,m))
                if val<best-EPS:best,choice=val,a
            return best,choice
        self.solve=solve
    def choose(self,s):return self.solve(s)[1]
def scenarios():
    out=[]
    for pi,q,d,ratio in itertools.product([.2,.8],[.5,.8,1.],[0,2,4],[.25,4.]):
        m=Model(pi,q,d,.015*ratio)
        out.append({'id':f'C{len(out):02d}','family':'specified','assumed':asdict(m),'actual':asdict(m)})
    for actual_q in [.5,0.]:
        for pi in [.2,.8]:
            m=Model(pi,1.,0,.00375);a=Model(pi,actual_q,0,.00375)
            out.append({'id':f'Q{len(out):02d}','family':'audit_shift','assumed':asdict(m),'actual':asdict(a)})
    for actual_pi in [.1,.9]:
        m=Model(.5,1.,0,.00375);a=Model(actual_pi,1.,0,.00375)
        out.append({'id':f'P{len(out):02d}','family':'prior_shift','assumed':asdict(m),'actual':asdict(a)})
    return out
METHODS=['StopBayes','NaiveIndependent','FreshOnlyDP','AuditFirst','GreedyVOI','SRDE_AuditRule','GraphFullDP','PortalFullDP','OracleLineageDP']
def build(m):
    full=TablePlanner(m);fresh=TablePlanner(m,False);rec=RecursivePlanner(m)
    oracle=[TablePlanner(Model(**{**asdict(m),'pi':float(l)}),False) for l in range(2)]
    return full,fresh,rec,oracle
def select(s,name,m,planners):
    full,fresh,rec,oracle=planners
    if belief(s,m) is None:return 'S'
    if name in ['StopBayes','NaiveIndependent']:return 'S'
    if name=='GraphFullDP':return full.choose(s)
    if name=='PortalFullDP':return rec.choose(s)
    if name=='FreshOnlyDP':return fresh.choose(s)
    if name=='AuditFirst':return 'A' if s[0]==0 else fresh.choose(s)
    if name=='SRDE_AuditRule':
        t,x,fs,z,pending,requested=s;a,b,c=bits(x)
        if not requested and a==b and c!=a and m.q>=.8 and m.ca<=m.cv and t+m.delay<=H:return 'A'
        if pending!=-1 and pending<=H and len(fs)>=2:return 'W'
        return fresh.choose(s)
    if name=='GreedyVOI':
        best=terminal(s,m)[0];choice='S'
        for a in actions(s):
            val=cost(a,m)+sum(p*terminal(ns,m)[0] for p,ns in transition(s,a,m))
            if val<best-EPS:best,choice=val,a
        return choice
    raise ValueError(name)
def rollout(case,name,m,planners):
    y,l,x,f0,f1,z=case;s=initial(x);spent=0.;trace=[]
    if name=='NaiveIndependent':m=Model(**{**asdict(m),'pi':0.})
    if name=='OracleLineageDP':
        m=Model(**{**asdict(m),'pi':float(l)});oracle=planners[3][l]
    while s[0]<H:
        a=oracle.choose(s) if name=='OracleLineageDP' else select(s,name,m,planners)
        if a=='S':break
        assert a in actions(s,name!='FreshOnlyDP')
        t,x,fs,az,pending,requested=s
        spent+=cost(a,m);trace.append(a)
        if a=='A':pending=t+m.delay;requested=True
        if a=='F':fs=fs+((f0,f1)[len(fs)],)
        nt=t+1
        if pending!=-1 and pending<=nt:az=z;pending=-1
        s=(nt,x,fs,az,pending,requested)
    _,p,abstain=terminal(s,m)
    return {'p':p,'abstain':int(abstain),'cost':spent,'trace':''.join(trace),'stop_t':s[0],'fresh_n':len(s[2]),'audit_seen':s[3],'zero_model_likelihood':int(belief(s,m) is None),'brier':(p-y)**2,'loss':(ABSTAIN if abstain else (p-y)**2)+spent}
def atoms(m):
    for y,l,x,f0,f1,z in itertools.product(range(2),range(2),range(8),range(2),range(2),range(2)):
        pr=.5*(m.pi if l else 1-m.pi)*initial_likelihood(x,y,l,m)*bern(f0,y,m.fresh)*bern(f1,y,m.fresh)*bern(z,l,m.q)
        if pr>0:yield (y,l,x,f0,f1,z),pr
def draw(rng,m):
    y=rng.randrange(2);l=int(rng.random()<m.pi)
    a=y if rng.random()<m.acc else 1-y
    b=a if l else (y if rng.random()<m.acc else 1-y)
    c=y if rng.random()<m.acc else 1-y
    f=[y if rng.random()<m.fresh else 1-y for _ in range(2)]
    z=l if rng.random()<m.q else 1-l
    return (y,l,4*a+2*b+c,*f,z)
def summarize(rows):
    weight=sum(r['weight'] for r in rows)
    out={'mass':weight}
    for k in ['brier','loss','cost','abstain','fresh_n','zero_model_likelihood']:out[k]=sum(r['weight']*r[k] for r in rows)/weight
    accepted=[r for r in rows if not r['abstain']];aw=sum(r['weight'] for r in accepted)
    out['coverage']=aw/weight;out['accepted_error']=sum(r['weight']*(int(r['p']>=.5)!=r['y']) for r in accepted)/aw if aw else None
    out['audit_rate']=sum(r['weight']*('A' in r['trace']) for r in rows)/weight
    out['ece10']=0.
    for b in range(10):
        group=[r for r in rows if min(9,int(r['p']*10))==b];bw=sum(r['weight'] for r in group)
        if bw:out['ece10']+=abs(sum(r['weight']*(r['p']-r['y']) for r in group))/weight
    return out
def main(out):
    start=time.perf_counter();out.mkdir(exist_ok=True)
    protocol=json.loads((R/'PROTOCOL.json').read_text());assert scenarios()==protocol['scenarios']
    exact=[];exactraw=[];sample=[];raw=[];statechecks=[]
    for sc in protocol['scenarios']:
        m=Model(**sc['assumed']);actual=Model(**sc['actual']);pl=build(m)
        for s,(v,a) in pl[0].table.items():
            rv,ra=pl[2].solve(s);assert abs(v-rv)<1e-12 and a==ra
        statechecks.append({'condition':sc['id'],'states':len(pl[0].table),'equivalence':True})
        for atom_id,(case,pr) in enumerate(atoms(actual)):
            exactraw.append({'condition':sc['id'],'atom':atom_id,'weight':pr,'y':case[0],'lineage':case[1],'initial':case[2],'fresh0':case[3],'fresh1':case[4],'audit':case[5]})
            for name in METHODS:
                rr=rollout(case,name,m,pl)
                exact.append({'condition':sc['id'],'family':sc['family'],'atom':atom_id,'method':name,'weight':pr,'y':case[0],**rr})
        for seed in protocol['seeds']:
            rng=random.Random(seed*1000+protocol['scenarios'].index(sc))
            for i in range(protocol['cases_per_seed_condition']):
                case=draw(rng,actual);uid=f"{sc['id']}-{seed}-{i}"
                raw.append({'case_id':uid,'condition':sc['id'],'seed':seed,'y':case[0],'lineage':case[1],'initial':case[2],'fresh0':case[3],'fresh1':case[4],'audit':case[5]})
                for name in METHODS:sample.append({'case_id':uid,'condition':sc['id'],'family':sc['family'],'seed':seed,'method':name,'weight':1.,'y':case[0],**rollout(case,name,m,pl)})
        belief.cache_clear();transition.cache_clear()
    def write(name,rows):
        with gzip.open(out/name,'wt',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    write('exact_predictions.csv.gz',exact);write('exact_atoms.csv.gz',exactraw);write('sample_predictions.csv.gz',sample);write('source_cases.csv.gz',raw)
    summaries=[]
    for split,rows in [('exact',exact),('sample',sample)]:
        for subset in ['all','specified','audit_shift','prior_shift']:
            for name in METHODS:
                group=[r for r in rows if r['method']==name and (subset=='all' or r['family']==subset)]
                summaries.append({'split':split,'subset':subset,'method':name,**summarize(group)})
    conditions=[]
    for sc in protocol['scenarios']:
        for name in METHODS:conditions.append({'condition':sc['id'],'family':sc['family'],'method':name,**summarize([r for r in exact if r['condition']==sc['id'] and r['method']==name])})
    for name,obj in [('metrics.json',summaries),('condition_metrics.json',conditions),('state_checks.json',statechecks)]:
        (out/name).write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n')
    # Paired case bootstrap by condition; worlds are independent here, not a time series.
    diffs={r['case_id']:r['loss'] for r in sample if r['method']=='GraphFullDP'}
    paired={}
    for base in ['FreshOnlyDP','SRDE_AuditRule','GreedyVOI']:
        arr=[diffs[r['case_id']]-r['loss'] for r in sample if r['method']==base and r['family']=='specified']
        rng=random.Random(9291);n=len(arr);means=[]
        for _ in range(400):means.append(sum(arr[rng.randrange(n)] for j in range(n))/n)
        means.sort();paired[base]={'delta':sum(arr)/n,'lower':means[10],'upper':means[389],'cases':n,'draws':400}
    (out/'bootstrap.json').write_text(json.dumps(paired,indent=2,sort_keys=True)+'\n')
    elapsed=time.perf_counter()-start
    (out/'environment.json').write_text(json.dumps({'python':sys.version,'platform':platform.platform(),'runtime_seconds':elapsed,'source_cases':len(raw),'exact_rows':len(exact),'sample_rows':len(sample)},indent=2)+'\n')
    print(json.dumps({'runtime_seconds':elapsed,'source_cases':len(raw),'exact_rows':len(exact),'sample_rows':len(sample)}))
if __name__=='__main__':main(Path(sys.argv[1]) if len(sys.argv)>1 else R/'results')
