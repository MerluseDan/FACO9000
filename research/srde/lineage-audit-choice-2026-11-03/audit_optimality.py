"""Independent finite-world policy optimization: partition weighted atoms, not runner beliefs."""
import csv,gzip,json
from pathlib import Path
from functools import lru_cache
R=Path(__file__).parent;D=R/'results'
with gzip.open(D/'exact_atoms.csv.gz','rt') as f:raw=list(csv.DictReader(f))
scenarios=json.loads((R/'PROTOCOL.json').read_text())['scenarios']
metrics=json.loads((D/'condition_metrics.json').read_text())
checks=[]
for sc in scenarios:
    if sc['family']!='specified':continue
    data=[r for r in raw if r['condition']==sc['id']];m=sc['actual']
    weights=[float(r['weight']) for r in data]
    @lru_cache(None)
    def solve(indices,t,nfresh,requested,due,seen):
        mass=sum(weights[i] for i in indices);py=sum(weights[i]*int(data[i]['y']) for i in indices)/mass
        best=mass*min(py*(1-py),.15)
        if t==3:return best
        actions=[]
        if nfresh<2:actions.append('F')
        if not requested:actions.append('A')
        if due!=-1:actions.append('W')
        for a in actions:
            ndue=t+m['delay'] if a=='A' else due
            reveal=ndue!=-1 and ndue<=t+1
            groups={}
            for i in indices:
                key=(int(data[i]['fresh'+str(nfresh)]) if a=='F' else -1,int(data[i]['audit']) if reveal else -1)
                groups.setdefault(key,[]).append(i)
            val=mass*(m['cv'] if a=='F' else m['ca'] if a=='A' else 0.)
            for (fv,z),group in groups.items():val+=solve(tuple(group),t+1,nfresh+(a=='F'),requested or a=='A',-1 if reveal else ndue,seen or reveal)
            best=min(best,val)
        return best
    total=0.
    for x in range(8):
        group=tuple(i for i,r in enumerate(data) if int(r['initial'])==x)
        if group:total+=solve(group,0,0,False,-1,False)
    reported=next(r['loss'] for r in metrics if r['condition']==sc['id'] and r['method']=='GraphFullDP')
    assert abs(total-reported)<1e-12,(sc['id'],total,reported)
    checks.append({'condition':sc['id'],'independent_optimum':total,'reported':reported,'absolute_error':abs(total-reported),'states_evaluated':solve.cache_info().currsize})
out={'passed':True,'conditions_checked':len(checks),'max_error':max(r['absolute_error'] for r in checks),'method':'Independent weighted-world partition search, no runner import or posterior-transition helpers','checks':checks}
(R/'OPTIMALITY_AUDIT.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
print(json.dumps({k:v for k,v in out.items() if k!='checks'}))
