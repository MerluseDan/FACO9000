"""Independent arithmetic/chronology auditor; deliberately does not import runner."""
import csv,gzip,json,hashlib,math
from pathlib import Path
from collections import defaultdict
R=Path(__file__).parent;D=R/'results'
P=json.loads((R/'PROTOCOL.json').read_text());SC={x['id']:x for x in P['scenarios']}
def read(n):
    with gzip.open(D/n,'rt',newline='') as f:return list(csv.DictReader(f))
def post(raw,row,m):
    y=int(raw['y']);l=int(raw['lineage']);x=int(raw['initial']);a=(x>>2)&1;b=(x>>1)&1;c=x&1
    fs=[];z=-1;due=None;requested=False;cost=0.;t=0
    for act in row['trace']:
        assert t<3
        if act=='A':assert not requested;requested=True;due=t+m['delay'];cost+=m['ca']
        elif act=='F':assert len(fs)<2;fs.append(int(raw['fresh'+str(len(fs))]));cost+=m['cv']
        else:assert act=='W' and due is not None
        t+=1
        if due is not None and due<=t:z=int(raw['audit']);due=None
    assert t==int(row['stop_t']) and len(fs)==int(row['fresh_n']) and z==int(row['audit_seen'])
    pr=m['pi']
    if row['method']=='NaiveIndependent':pr=0.
    if row['method']=='OracleLineageDP':pr=float(l)
    def lik(obs,truth,acc):return acc if obs==truth else 1-acc
    w=[]
    for yy in [0,1]:
        for ll in [0,1]:
            v=.5*(pr if ll else 1-pr)*lik(a,yy,m['acc'])*lik(c,yy,m['acc'])
            v*=int(a==b) if ll else lik(b,yy,m['acc'])
            for f in fs:v*=lik(f,yy,m['fresh'])
            if z!=-1:v*=lik(z,ll,m['q'])
            w.append(v)
    total=sum(w);prob=(w[2]+w[3])/total if total else .5
    abstain=int(prob*(1-prob)>.15)
    assert abstain==int(row['abstain']) and int(total==0)==int(row['zero_model_likelihood'])
    assert abs(float(row['p'])-prob)<1e-12
    assert abs(float(row['cost'])-cost)<1e-12
    brier=(prob-y)**2;loss=(.15 if abstain else brier)+cost
    assert abs(float(row['brier'])-brier)<1e-12 and abs(float(row['loss'])-loss)<1e-12
    return brier,loss,cost
def atom_weight(raw,m):
    y=int(raw['y']);l=int(raw['lineage']);x=int(raw['initial']);a=(x>>2)&1;b=(x>>1)&1;c=x&1
    def f(o,t,r):return r if o==t else 1-r
    w=.5*(m['pi'] if l else 1-m['pi'])*f(a,y,m['acc'])*f(c,y,m['acc'])
    w*=int(a==b) if l else f(b,y,m['acc'])
    w*=f(int(raw['fresh0']),y,m['fresh'])*f(int(raw['fresh1']),y,m['fresh'])*f(int(raw['audit']),l,m['q'])
    return w
def main():
    freeze=json.loads((R/'FREEZE.json').read_text())
    assert all(hashlib.sha256((R/n).read_bytes()).hexdigest()==h for n,h in freeze['sha256'].items())
    checked=0;aggregates={};maxerr=0.;seenexact=0
    for split,src,pred in [('exact','exact_atoms.csv.gz','exact_predictions.csv.gz'),('sample','source_cases.csv.gz','sample_predictions.csv.gz')]:
        source=read(src)
        def key(r):return (r['condition'],r['atom']) if split=='exact' else r['case_id']
        records={key(r):r for r in source};assert len(records)==len(source)
        if split=='sample':assert len(source)==42*5*100
        mass=defaultdict(float)
        if split=='exact':
            for raw in source:
                w=atom_weight(raw,SC[raw['condition']]['actual']);assert abs(w-float(raw['weight']))<1e-14;mass[raw['condition']]+=w
            assert all(abs(v-1)<1e-12 for v in mass.values());seenexact=len(source)
        sums=defaultdict(lambda:[0.,0.,0.,0.]);keys=set();pairs={}
        for r in read(pred):
            k=key(r);raw=records[k];assert raw['y']==r['y'];sk=(k,r['method']);assert sk not in keys;keys.add(sk)
            v=post(raw,r,SC[r['condition']]['assumed']);w=float(r['weight'])
            assert abs(w-(float(raw['weight']) if split=='exact' else 1))<1e-14
            for subset in ['all',SC[r['condition']]['family']]:
                z=sums[(subset,r['method'])];z[0]+=w
                for i in range(3):z[i+1]+=w*v[i]
            if r['method']=='GraphFullDP':pairs[k]=(r['p'],r['trace'],r['abstain'])
            if r['method']=='PortalFullDP':assert pairs[k]==(r['p'],r['trace'],r['abstain'])
            if SC[r['condition']]['family']=='specified' and r['method'] in ['GraphFullDP','PortalFullDP']:
                m=SC[r['condition']]['assumed']
                if m['q']==.5 or m['delay']==4:assert 'A' not in r['trace']
            checked+=1
        assert len(keys)==len(source)*9
        metrics=json.loads((D/'metrics.json').read_text())
        for (subset,name),v in sums.items():
            m=next(x for x in metrics if x['split']==split and x['subset']==subset and x['method']==name)
            for i,field in enumerate(['brier','loss','cost']):
                err=abs(v[i+1]/v[0]-m[field]);maxerr=max(maxerr,err);assert err<1e-10
        aggregates[split]={'source_rows':len(source),'prediction_rows':len(keys)}
    result={'passed':True,'predictions_checked':checked,'split_counts':aggregates,'max_metric_recalculation_error':maxerr,'frozen_files_verified':len(freeze['sha256']),'independent_of_runner_import':True,'checks':['latent observation likelihood','exact probability mass','all posterior probabilities','query costs','abstention','squared-error/decision loss','no premature audit response','slot/query limits','all recursive/conventional forecasts and traces','uninformative/late audit controls','counts and uniqueness','frozen identities']}
    (R/'AUDIT_RESULTS.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
