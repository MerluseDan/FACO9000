"""FACO SRDE Experiment 30. Standard-library-only controlled corpus + retrieval.

Synthetic engineering-memory worlds; no executable model inference is claimed here.
Gold labels are generated from independent scenario declarations, not from retriever outputs.
Deterministic and designed to support separately measured hosted Qwen inference.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import random
import re
import statistics
import time
import contextvars
from collections import Counter, defaultdict
from pathlib import Path

PROTOCOL_ID = 'FACO-SRDE-E30-COLAB-2026-10-15-PRIMARY-v1'
MAIN_SEEDS = (401, 409, 419, 421, 431, 433, 439, 443)
CONFIRM_SEEDS = (509, 521, 523, 541)
METHODS = ('lexical', 'temporal_graph', 'graph_state', 'srde_activated')
KINDS = ('route','policy','receipt','gate','override','parent')
SCENARIOS = ('current_route','historical_route','linked_policy','linked_receipt','poisoned_policy',
             'unreliable_gate','conflicting_override','dependent_receipt','stable_gate','expired_route')
TOKEN_BUDGET = 320
_STATE_COST = contextvars.ContextVar('state_cost', default=None)

def canonical(data):
    return json.dumps(data,sort_keys=True,separators=(',',':'),ensure_ascii=False)

def sha(obj):
    return hashlib.sha256(canonical(obj).encode()).hexdigest()

def code(rng, prefix='V'):
    return prefix+''.join(rng.choice('ABCDEFGHJKLMNPQRSTUVWXYZ23456789') for _ in range(7))

def rec(i, ent, kind, value, start, *, end=1000, root='official', authority='signed', dependencies=(),
        invalid=False, weight=3, relation='', role=''):
    return dict(id=f'D{i:04}',entity=ent,kind=kind,value=value,start=start,end=end,root=root,
                authority=authority,dependencies=list(dependencies),invalid=bool(invalid),
                weight=weight,relation=relation,role=role)

def generate_world(seed):
    rng=random.Random(seed)
    realm=f'W{seed}'
    components=[f'{realm}-C{i:02}' for i in range(24)]
    docs=[]
    def add(ent,kind,value,t,**kw):
        d=rec(len(docs),ent,kind,value,t,**kw)
        docs.append(d)
        return d
    # Distractors: many identifiers, dates, and mutually related records.
    for i, entity in enumerate(components):
        parent=components[(i+7)%len(components)]
        add(entity,'parent',parent,100,root=f'owner-{i}',relation='depends-on')
        for kind in ('route','policy','receipt','gate','override'):
            root=f'catalog-{i}-{kind}'
            add(entity,kind,code(rng,kind[0].upper()),100,root=root)
            if i%3==0:
                # Updating a claim closes the preceding revision.
                for d in docs:
                    if d['entity']==entity and d['kind']==kind and d['end']==1000:
                        d['end']=200
                add(entity,kind,code(rng,kind[0].upper()),200,root=f'fresh-{i}-{kind}')
    A,B,C,D,E,F,G,H=components[:8]
    parentA=components[7]
    # Poisoned copies: apparent agreement from one defective root.
    for old in docs:
        if old['entity']==B and old['kind']=='policy':old['end']=260
    poisoned=add(B,'policy',code(rng,'P'),260,root='root-compromised',authority='signed')
    add(B,'policy',poisoned['value'],261,root='root-compromised',authority='forwarded',weight=1)
    add(B,'policy',poisoned['value'],262,root='root-compromised',authority='forwarded',weight=1)
    verified=add(B,'policy',code(rng,'P'),263,root='independent-audit',authority='independent-audit')
    # A visible root revocation event; no hidden truth is supplied to retrieval.
    add('root-compromised','revocation','REVOKED',265,root='audit-event',authority='signed')
    # C has no active non-revoked gate evidence.
    for old in docs:
        if old['entity']==C and old['kind']=='gate':old['end']=260
    add(C,'gate',code(rng,'G'),260,root='root-compromised',authority='forwarded')
    # D has equal-priority independent contradictory receipts for override.
    for old in docs:
        if old['entity']==D and old['kind']=='override':old['end']=260
    add(D,'override',code(rng,'O'),260,root='auditor-left',authority='independent-audit',weight=3)
    add(D,'override',code(rng,'O'),260,root='auditor-right',authority='independent-audit',weight=3)
    # E has a derived receipt depending on a revoked upstream evidence claim.
    for old in docs:
        if old['entity']==E and old['kind']=='receipt':old['end']=260
    base=add(E,'receipt',code(rng,'R'),260,root='root-compromised')
    add(E,'receipt',base['value'],266,root='derived-engine',dependencies=(base['id'],),role='derived')
    # H's most recent route expires; its past value also expires before now.
    for old in docs:
        if old['entity']==H and old['kind']=='route':old['end']=200
    add(H,'route',code(rng,'R'),200,end=280,root='time-limited',authority='signed')

    def latest(ent,kind,t):
        ds=[d for d in docs if d['entity']==ent and d['kind']==kind and d['start']<=t<d['end']]
        return max(ds,key=lambda d:d['start']) if ds else None
    pa=latest(A,'parent',300)['value']
    # Scenario truth is declared using constructing facts, not inferred via a search algorithm.
    task_defs=[
      ('current_route',A,'route',300,latest(A,'route',300)['value'],
       f'What is the current route marker for {A} at tick 300?', (latest(A,'route',300)['id'],)),
      ('historical_route',A,'route',150,latest(A,'route',150)['value'],
       f'What was the route marker for {A} at tick 150?', (latest(A,'route',150)['id'],)),
      ('linked_policy',A,'policy',300,latest(pa,'policy',300)['value'],
       f'At tick 300, what policy code belongs to the parent that {A} depends on?',
       (latest(A,'parent',300)['id'], latest(pa,'policy',300)['id'])),
      ('linked_receipt',A,'receipt',300,latest(pa,'receipt',300)['value'],
       f'At tick 300, what receipt code belongs to the parent dependency of {A}?',
       (latest(A,'parent',300)['id'], latest(pa,'receipt',300)['id'])),
      ('poisoned_policy',B,'policy',300,verified['value'],
       f'At tick 300, what supported policy code applies to {B} after reference-source revocations?',
       (verified['id'],next(x['id'] for x in docs if x['entity']=='root-compromised' and x['kind']=='revocation'))),
      ('unreliable_gate',C,'gate',300,'UNKNOWN',
       f'At tick 300, what supported gate code applies to {C} after source revocations?',
       (next(x['id'] for x in docs if x['entity']==C and x['kind']=='gate' and x['start']==260),)),
      ('conflicting_override',D,'override',300,'UNKNOWN',
       f'At tick 300, what override code is established for {D} by independent auditors?',
       tuple(x['id'] for x in docs if x['entity']==D and x['kind']=='override' and x['start']==260)),
      ('dependent_receipt',E,'receipt',300,'UNKNOWN',
       f'At tick 300, what verified receipt code applies to {E} when upstream evidence is revoked?',
       tuple(x['id'] for x in docs if x['entity']==E and x['kind']=='receipt' and x['start']>=260)),
      ('stable_gate',G,'gate',300,latest(G,'gate',300)['value'],
       f'What is the gate code for {G} at tick 300?', (latest(G,'gate',300)['id'],)),
      ('expired_route',H,'route',300,'UNKNOWN',
       f'What valid route code remains for {H} at tick 300, after expirations?',
       tuple(x['id'] for x in docs if x['entity']==H and x['kind']=='route')),
    ]
    tasks=[]
    for i,(scenario,entity,kind,t,gold,q,proof) in enumerate(task_defs):
        tasks.append(dict(id=f'{realm}-Q{i:02}',world=realm,scenario=scenario,
                          entity=entity,kind=kind,tick=t,question=q,gold=gold,
                          proof=list(proof)))
    return dict(seed=seed,world=realm,docs=docs,tasks=tasks)

def data(seeds=MAIN_SEEDS):
    worlds=[generate_world(s) for s in seeds]
    return {'protocol':PROTOCOL_ID, 'worlds':worlds,
            'sha256':sha(worlds)}

def format_doc(d):
    deps=','.join(d['dependencies']) or '-'
    return f"[{d['id']}] {d['entity']} {d['kind']}={d['value']} valid=[{d['start']},{d['end']}) origin={d['root']} verification={d['authority']} inherits={deps}"

def tokens(text):
    return set(re.findall(r'[a-z0-9]+',text.lower()))

def candidate_pool(world,task):
    """Graph expansion built strictly from observable corpus edges."""
    docs=world['docs']; ent=task['entity']; t=task['tick']
    parent_ids=[x['value'] for x in docs if x['entity']==ent and x['kind']=='parent' and x['start']<=t<x['end']]
    target_kinds={task['kind'], 'revocation','parent'}
    return [d for d in docs if (d['entity']==ent or d['entity'] in parent_ids or d['kind']=='revocation')
            and (d['kind'] in target_kinds or (d['entity'] in parent_ids and d['kind']==task['kind']))]

def score_doc(d,task, mode, parent):
    query=tokens(task['question']); obj=tokens(f"{d['entity']} {d['kind']} {d['value']} {d['root']} {d['relation']}")
    lexical=len(query&obj)/(1+len(query|obj)**.5)
    if mode=='lexical':return lexical + (0.0001*d['start'])
    s=5.0*(d['entity']==task['entity'])+4*(d['kind']==task['kind'])+3*(d['entity']==parent)
    if d['kind']=='revocation': s+=7
    if d['kind']=='parent': s+=4
    if d['start']<=task['tick']<d['end']:s+=2
    s+=lexical+(d['start']*.001)
    return s

def bad_roots(world,tick):
    return {d['entity'] for d in world['docs'] if d['kind']=='revocation'
            and d['start']<=tick<d['end'] and d['value']=='REVOKED'}

def is_valid(d, doc_by_id, revoked,tick,visited=None):
    meter = _STATE_COST.get()
    if meter is not None: meter['validity_checks'] += 1
    if d['start']>tick or d['end']<=tick or d['invalid'] or d['root'] in revoked:
        return False
    visited=set() if visited is None else visited
    if d['id'] in visited: return False
    visited.add(d['id'])
    return all((dep in doc_by_id and is_valid(doc_by_id[dep],doc_by_id,revoked,tick,visited.copy()))
               for dep in d['dependencies'])

def materialized_state(world,task, distinct_origin=True):
    """Conventional event-state resolver; same for graph_state and SRDE.

    This deliberately leaves novelty to selection/activation, not an oracle.
    """
    docs=world['docs']; by_id={d['id']:d for d in docs}; revoked=bad_roots(world,task['tick'])
    pool=candidate_pool(world,task)
    parent=max((x for x in pool if x['entity']==task['entity'] and x['kind']=='parent' and
                is_valid(x,by_id,revoked,task['tick'])),key=lambda x:x['start'],default=None)
    ent=parent['value'] if task['scenario'] in ('linked_policy','linked_receipt') and parent else task['entity']
    vals=[d for d in docs if d['entity']==ent and d['kind']==task['kind']
          and is_valid(d,by_id,revoked,task['tick'])]
    if vals:
        mx=max(d['start'] for d in vals); vals=[d for d in vals if d['start']==mx]
    roots=defaultdict(list)
    for d in vals:roots[d['root']].append(d)
    uniques=[max(sub,key=lambda x:x['weight']) for sub in roots.values()] if distinct_origin else vals
    values={d['value'] for d in uniques}
    result=next(iter(values)) if len(values)==1 else 'UNKNOWN'
    return dict(value=result,root_count=len(roots),support=[d['id'] for d in uniques],
                considered=ent,revoked=sorted(revoked),ambiguous=len(values)>1,
                valid_count=len(vals))

def _truncate(lines, budget, token_count):
    used=0; out=[]
    for line in lines:
        n=token_count(line+'\n')
        if used+n>budget: continue
        out.append(line);used+=n
    return '\n'.join(out),used

def evidence(world, task, method, budget=TOKEN_BUDGET, token_count=None):
    """Measured token-budgeted retrieval. model tokenizer provided at inference time.

    No prompt has access to task.gold or task.proof.
    """
    if method not in METHODS: raise ValueError(method)
    token_count=token_count or (lambda s: max(1,(len(s)+3)//4))
    all_docs=world['docs'];pool=candidate_pool(world,task)
    p=next((d['value'] for d in pool if d['entity']==task['entity'] and d['kind']=='parent'),None)
    if method=='lexical':
        chosen=sorted(all_docs,key=lambda d:(-score_doc(d,task,'lexical',p),d['id']))
        lines=[format_doc(d) for d in chosen]
    elif method=='temporal_graph':
        chosen=sorted(pool,key=lambda d:(-score_doc(d,task,method,p),d['id']))
        lines=[format_doc(d) for d in chosen]
    else:
        # The resolver sees the full visible world BEFORE evidence truncation.
        # Measure the same resolver separately for both state methods.
        meter={'visible_records':len(all_docs),'validity_checks':0}
        handle=_STATE_COST.set(meter)
        state_start=time.perf_counter()
        try: state=materialized_state(world,task,distinct_origin=True)
        finally:
            state_seconds=time.perf_counter()-state_start
            _STATE_COST.reset(handle)
        chosen=sorted(pool,key=lambda d:(-score_doc(d,task,'temporal_graph',p),d['id']))
        # Both state-based methods use same conventional event resolver. SRDE
        # adds activation and provenance-aware prioritization, not hidden gold.
        state_line=(f"EVENT-STATE time={task['tick']} entity={state['considered']} kind={task['kind']} "
                    f"eligible_record_ids={','.join(state['support']) or "-"} independent_roots={state['root_count']} "
                    f"conflicting_sources={str(state['ambiguous']).lower()} revoked_roots={','.join(state['revoked']) or '-'}")
        if method=='graph_state':
            lines=[state_line]+[format_doc(d) for d in chosen]
        else:
            priority=set(state['support'])
            # Even if no valid claims survive, emit suspicious/corroborating records.
            chosen.sort(key=lambda d:(-int(d['id'] in priority),
                    -int(d['root'] in state['revoked']),
                    -score_doc(d,task,'temporal_graph',p),d['id']))
            lines=[state_line]+[format_doc(d) for d in chosen]
    ctx,used=_truncate(lines,budget,token_count)
    # Tokenization is not perfectly additive across line boundaries. Recheck
    # the actual combined evidence string with the real model tokenizer.
    fragments=ctx.split('\n') if ctx else []
    while fragments and token_count('\n'.join(fragments))>budget:
        fragments.pop()
    ctx='\n'.join(fragments)
    used=token_count(ctx) if ctx else 0
    selected=re.findall(r'\[(D\d+)\]',ctx)
    return dict(text=ctx,tokens=used,selected=selected,proof_hit=sum(i in selected for i in task['proof']),
                proof_count=len(task['proof']),
                state_preprocessing_seconds=state_seconds if method in ('graph_state','srde_activated') else 0.,
                state_visible_records=meter['visible_records'] if method in ('graph_state','srde_activated') else 0,
                state_validity_checks=meter['validity_checks'] if method in ('graph_state','srde_activated') else 0)

def prompt(task,ctx):
    # Equal for every method and independent of gold.
    instruction=('You are answering a project-memory question. Use only the provided records. '
      'An EVENT-STATE line is computed from the full visible world before evidence truncation; '
      'its supporting records may be omitted from this evidence window. '
      'A revoked origin or its derived evidence is not reliable. Duplicate copies with one origin are not independent. '
      'If independent current claims conflict, or no reliable current claim survives, answer UNKNOWN. '
      'A record valid=[start,end) applies when start <= tick < end. '
      'Return exactly one JSON object with the sole field "answer", holding an exact code or "UNKNOWN". '
      'No explanations, no markdown.')
    return {'system':instruction,'user':f"EVIDENCE:\n{ctx}\n\nQUESTION:\n{task['question']}"}

def offline_report(corpus,budget=TOKEN_BUDGET):
    out=[]
    for w in corpus['worlds']:
        for t in w['tasks']:
            for m in METHODS:
                ev=evidence(w,t,m,budget)
                out.append({'world':w['world'],'scenario':t['scenario'],'method':m,'task':t['id'],
                            'proof_hits':ev['proof_hit'],'proof_count':ev['proof_count'],
                            'retrieved_tokens_est':ev['tokens'],
                            'gold_visible':t['gold'] in ev['text'] if t['gold']!='UNKNOWN' else None})
    return out

def save_offline(outdir,corpus):
    dest=Path(outdir);dest.mkdir(parents=True,exist_ok=True)
    (dest/'corpus.json').write_text(json.dumps(corpus,indent=2)+'\n')
    rows=offline_report(corpus)
    with (dest/'offline.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    s={m:{'proof_recall':round(sum(x['proof_hits'] for x in rows if x['method']==m)/
                                max(1,sum(x['proof_count'] for x in rows if x['method']==m)),4),
             'gold_visible_rate_non_unknown':round(sum(bool(x['gold_visible']) for x in rows if x['method']==m and x['gold_visible'] is not None)/
                   max(1,sum(x['gold_visible'] is not None for x in rows if x['method']==m)),4)}
       for m in METHODS}
    (dest/'offline_summary.json').write_text(json.dumps({'status':'OFFLINE_RETRIEVAL_ONLY_NOT_REAL_LLM','corpus_sha256':corpus['sha256'],
                                                          'n_worlds':len(corpus['worlds']),'n_tasks':sum(len(w['tasks']) for w in corpus['worlds']),
                                                          'summary':s},indent=2)+'\n')
    return s

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',default='e30_offline');p.add_argument('--confirmation',action='store_true')
    args=p.parse_args(); d=data(CONFIRM_SEEDS if args.confirmation else MAIN_SEEDS)
    summary=save_offline(args.out,d)
    print(json.dumps({'corpus_hash':d['sha256'],'summary':summary},indent=2))
