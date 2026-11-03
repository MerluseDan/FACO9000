"""LA2: typed delayed calibration, selection bias, and downstream decision cost."""
import csv,gzip,hashlib,itertools,json,math,random,sys,time,platform
from pathlib import Path
from functools import lru_cache
from dataclasses import asdict
import decision_core as core
R=Path(__file__).parent
GRID=[i/100 for i in range(101)];CUTOFF=128;VERIFY_COST=.003
LEARNERS=['LatentBayes','TargetHardCounts','RandomVerifiedCounts','SelectedVerifiedCounts','MixedRandomBayes','MixedSelectedBayes','DoubleCountSelected','SRDETypedRecursive']
METHODS=['FreshOnly','AssumePerfect',*LEARNERS,'KnownAuditQ']
def conditions():
 return [{'id':f'C{i:02d}','q':q,'actual_acc':a,'family':'specified' if a==.8 else 'source_model_error'} for i,(q,a) in enumerate(itertools.product([1.,.8,.5,0.],[.8,.65]))]
def copy_prob(x,y=None):
 m=core.Model(pi=.2);v=[0.,0.]
 for yy in ([0,1] if y is None else [y]):
  for l in [0,1]:v[l]+=(m.pi if l else 1-m.pi)*core.initial_likelihood(x,yy,l,m)
 total=sum(v);return v[1]/total
def agreement(x,y,z):return z==int(copy_prob(x,y)>.5)
def observed_packet(raw,rand_req,sel_req):
 i=raw['issue'];y=raw['y'] if i+5<=CUTOFF else None
 return {'issue':i,'initial':raw['initial'],'audit':raw['audit'],'y_observed':y,'random_requested':int(rand_req),'selected_requested':int(sel_req),'random_lineage':raw['lineage'] if rand_req and i+17<=CUTOFF else None,'selected_lineage':raw['lineage'] if sel_req and i+17<=CUTOFF else None}
def make_calibration(seed,cond):
 rng=random.Random(seed*1000+int(cond['id'][1:]));m=core.Model(pi=.2,q=cond['q'],acc=cond['actual_acc']);raw=[];packets=[];nr=ns=0
 for i in range(128):
  y,l,x,f0,f1,z=core.draw(rng,m);ur,us=rng.random(),rng.random()
  row={'issue':i,'y':y,'lineage':l,'initial':x,'audit':z,'random_u':ur,'selected_u':us};raw.append(row)
  # Requests occur only after the event label arrives. Selection never sees L.
  available=i+5<=CUTOFF
  rr=available and nr<32 and ur<.25
  ss=available and ns<32 and us<(.8 if agreement(x,y,z) else .1)
  nr+=rr;ns+=ss;packets.append(observed_packet(row,rr,ss))
 return raw,packets
def infer(packets,name):
 logs=[0.]*101;used=0
 if name=='SRDETypedRecursive':name='MixedSelectedBayes'
 for row in packets:
  x,z,y=row['initial'],row['audit'],row['y_observed'];factors=[]
  if name in ['RandomVerifiedCounts','SelectedVerifiedCounts']:
   l=row['random_lineage' if name.startswith('Random') else 'selected_lineage']
   if l is None:continue
   factors=[float(l==z)]
  elif name=='TargetHardCounts':
   if y is None:continue
   factors=[float(z==int(copy_prob(x,y)>.5))]
  elif name=='DoubleCountSelected':
   factors=[copy_prob(x,None) if z else 1-copy_prob(x,None)]
   if y is not None:factors.append(copy_prob(x,y) if z else 1-copy_prob(x,y))
   if row['selected_lineage'] is not None:factors.append(float(z==row['selected_lineage']))
  else:
   l=row['random_lineage'] if name=='MixedRandomBayes' else row['selected_lineage'] if name=='MixedSelectedBayes' else None
   # One factor per underlying report: a later, finer observation replaces the earlier marginal factor.
   factors=[float(z==l)] if l is not None else [copy_prob(x,y) if z else 1-copy_prob(x,y)]
  used+=1
  for j,q in enumerate(GRID):
   for t in factors:
    v=q*t+(1-q)*(1-t)
    logs[j]+=math.log(v) if v>0 else -math.inf
 maxlog=max(logs);weights=[math.exp(v-maxlog) for v in logs];total=sum(weights);weights=[v/total for v in weights]
 mean=sum(q*w for q,w in zip(GRID,weights));cdf=0.;lo=hi=None
 for q,w in zip(GRID,weights):
  cdf+=w
  if lo is None and cdf>=.025:lo=q
  if hi is None and cdf>=.975:hi=q
 verify='random' if name in ['RandomVerifiedCounts','MixedRandomBayes'] else 'selected' if name in ['SelectedVerifiedCounts','MixedSelectedBayes','DoubleCountSelected'] else None
 nreq=sum(p[verify+'_requested'] for p in packets) if verify else 0
 nseen=sum(p[verify+'_lineage'] is not None for p in packets) if verify else 0
 return {'q_mean':mean,'q_decision':round(mean+1e-12,2),'q_lower':lo,'q_upper':hi,'factors_used':used,'reference_requested':nreq,'reference_seen':nseen,'target_seen':sum(p['y_observed'] is not None for p in packets),'calibration_cost':128*.00375+nreq*VERIFY_COST},weights
@lru_cache(None)
def planners(q):return core.build(core.Model(pi=.2,q=q))
@lru_cache(None)
def evaluate_exact(cond_id,q,mode):
 cond=next(x for x in conditions() if x['id']==cond_id)
 actual=core.Model(pi=.2,q=cond['q'],acc=cond['actual_acc']);assumed=core.Model(pi=.2,q=q)
 pl=planners(q);rows=[]
 for atom,(case,weight) in enumerate(core.atoms(actual)):
  r=core.rollout(case,mode,assumed,pl);rows.append({'atom':atom,'weight':weight,'y':case[0],**r})
 summary=core.summarize(rows)
 return summary,rows
def dump(path,rows):
 with gzip.open(path,'wt',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def main(out):
 start=time.perf_counter();out.mkdir(exist_ok=True);proto=json.loads((R/'PROTOCOL.json').read_text());assert conditions()==proto['conditions']
 rawrows=[];packetrows=[];fits=[];posteriors=[];exactrows=[];samplecases=[];samplerows=[];worldrows=[]
 exactatoms=[]
 for cond in proto['conditions']:
  for atom,(c,w) in enumerate(core.atoms(core.Model(pi=.2,q=cond['q'],acc=cond['actual_acc']))):
   exactatoms.append({'condition':cond['id'],'atom':atom,'weight':w,'y':c[0],'lineage':c[1],'initial':c[2],'fresh0':c[3],'fresh1':c[4],'audit':c[5]})
 for cond in proto['conditions']:
  for seed in proto['seeds']:
   world=f"{cond['id']}-{seed}";raw,packets=make_calibration(seed,cond)
   rawrows.extend({'world':world,'condition':cond['id'],'seed':seed,**r} for r in raw)
   packetrows.extend({'world':world,**p} for p in packets)
   rng=random.Random(seed*1000+int(cond['id'][1:])+10000000)
   actual=core.Model(pi=.2,q=cond['q'],acc=cond['actual_acc']);testcases=[core.draw(rng,actual) for _ in range(128)]
   samplecases.extend({'world':world,'case':i,'y':c[0],'lineage':c[1],'initial':c[2],'fresh0':c[3],'fresh1':c[4],'audit':c[5]} for i,c in enumerate(testcases))
   for name in METHODS:
    if name in LEARNERS:
     fit,weights=infer(packets,name);posteriors.extend({'world':world,'method':name,'q':q,'weight':w} for q,w in zip(GRID,weights))
    else:
     q=1. if name=='AssumePerfect' else cond['q'] if name=='KnownAuditQ' else .5
     fit={'q_mean':q,'q_decision':q,'q_lower':q,'q_upper':q,'factors_used':0,'reference_requested':0,'reference_seen':0,'target_seen':0,'calibration_cost':0.}
    fit={'world':world,'condition':cond['id'],'family':cond['family'],'seed':seed,'method':name,'true_q':cond['q'],'actual_acc':cond['actual_acc'],**fit}
    fits.append(fit);q=fit['q_decision'];mode='FreshOnlyDP' if name=='FreshOnly' else 'PortalFullDP' if name=='SRDETypedRecursive' else 'GraphFullDP'
    summary,rows=evaluate_exact(cond['id'],q,mode)
    exactrows.extend({'world':world,'condition':cond['id'],'method':name,'q_decision':q,**r} for r in rows)
    pl=planners(q);assumed=core.Model(pi=.2,q=q)
    srows=[]
    for i,case in enumerate(testcases):
     rr={'world':world,'condition':cond['id'],'case':i,'method':name,'q_decision':q,'weight':1.,'y':case[0],**core.rollout(case,mode,assumed,pl)};samplerows.append(rr);srows.append(rr)
    sample=core.summarize(srows)
    for horizon in proto['amortization_horizons']:
     worldrows.append({'world':world,'condition':cond['id'],'family':cond['family'],'seed':seed,'method':name,'horizon':horizon,'q_error':abs(fit['q_mean']-cond['q']),'interval_contains_q':int(fit['q_lower']<=cond['q']<=fit['q_upper']),'calibration_cost':fit['calibration_cost'],'deployment_loss':summary['loss'],'total_loss':summary['loss']+fit['calibration_cost']/horizon,'brier':summary['brier'],'audit_rate':summary['audit_rate'],'coverage':summary['coverage'],'sample_loss':sample['loss'],'sample_brier':sample['brier']})
 for name,rows in [('exact_atoms.csv.gz',exactatoms),('calibration_raw.csv.gz',rawrows),('calibration_packets.csv.gz',packetrows),('posterior_weights.csv.gz',posteriors),('exact_predictions.csv.gz',exactrows),('sample_cases.csv.gz',samplecases),('sample_predictions.csv.gz',samplerows)]:dump(out/name,rows)
 for name,rows in [('fits.json',fits),('world_metrics.json',worldrows)]: (out/name).write_text(json.dumps(rows,indent=2,sort_keys=True)+'\n')
 aggregate=[]
 for family in ['all','specified','source_model_error']:
  for horizon in proto['amortization_horizons']:
   for name in METHODS:
    a=[r for r in worldrows if r['method']==name and r['horizon']==horizon and (family=='all' or r['family']==family)]
    aggregate.append({'family':family,'horizon':horizon,'method':name,'worlds':len(a),**{k:sum(r[k] for r in a)/len(a) for k in ['q_error','interval_contains_q','calibration_cost','deployment_loss','total_loss','brier','audit_rate','coverage','sample_loss','sample_brier']}})
 (out/'metrics.json').write_text(json.dumps(aggregate,indent=2,sort_keys=True)+'\n')
 # Stratified world bootstrap: resample independent calibration worlds within each fixed condition.
 bootstrap=[]
 for family in ['all','specified','source_model_error']:
  for baseline in ['SelectedVerifiedCounts','RandomVerifiedCounts','FreshOnly','DoubleCountSelected']:
   delta=[];groups=[]
   for cond in proto['conditions']:
    if family!='all' and cond['family']!=family:continue
    a={r['world']:r for r in worldrows if r['condition']==cond['id'] and r['horizon']==512 and r['method']=='MixedSelectedBayes'}
    b={r['world']:r for r in worldrows if r['condition']==cond['id'] and r['horizon']==512 and r['method']==baseline}
    v=[a[k]['total_loss']-b[k]['total_loss'] for k in sorted(a)];groups.append(v);delta.extend(v)
   rng=random.Random(61621);means=[]
   for _ in range(1000):means.append(sum(sum(g[rng.randrange(len(g))] for j in range(len(g))) for g in groups)/len(delta))
   means.sort();bootstrap.append({'family':family,'baseline':baseline,'horizon':512,'delta':sum(delta)/len(delta),'lower':means[25],'upper':means[974],'worlds':len(delta),'draws':1000})
 (out/'bootstrap.json').write_text(json.dumps(bootstrap,indent=2,sort_keys=True)+'\n')
 elapsed=time.perf_counter()-start
 (out/'environment.json').write_text(json.dumps({'python':sys.version,'platform':platform.platform(),'runtime_seconds':elapsed,'worlds':len(proto['conditions'])*len(proto['seeds']),'calibration_cases':len(rawrows),'holdout_cases':len(samplecases),'exact_prediction_rows':len(exactrows),'sample_prediction_rows':len(samplerows)},indent=2)+'\n')
 print((out/'environment.json').read_text())
if __name__=='__main__':main(Path(sys.argv[1]) if len(sys.argv)>1 else R/'results')
