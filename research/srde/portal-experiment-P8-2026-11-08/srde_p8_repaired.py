#!/usr/bin/env python3
"""SRDE-P8: evidence change-impact research engine (standard library, CPU only).

Proof paths are explicit and manuscript-based; this program does not infer truth,
read private files, or publish/modify original source documents.
"""
from __future__ import annotations
import argparse
from collections import defaultdict, deque
import csv, hashlib, itertools, json, random, shutil, sqlite3, statistics, tempfile, time
from pathlib import Path

SEED_REAL=20261108
SEED_SCALE=20261109
REAL_EVENTS=240
SCALE_WORKSPACES=300
SCALE_EVENTS=240


def jload(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def index_corpus(project):
    """Load original physical markdown documents but do not change them."""
    project=Path(project)
    cards=jload(project/'evidence_cards.json')
    manifest=jload(project/'SOURCE_MANIFEST.json')
    docs={key:project/'corpus'/src['filename'] for key,src in manifest['sources'].items()}
    assert len(docs)==7 and len(cards['evidence'])==15 and len(cards['claims'])==20
    for src in manifest['sources'].values():
        assert digest(project/'corpus'/src['filename'])==src['sha256']
    return cards,docs


def initial_active(anchors,docs):
    text={k:set(p.read_text(encoding='utf-8').splitlines()) for k,p in docs.items()}
    return {a['id']:a['full_line'] in text[a['document']] for a in anchors}


def topo_claims(claims):
    by_id={c['id']:c for c in claims}
    children=defaultdict(set); indeg={i:0 for i in by_id}
    for claim in claims:
        refs={s for path in claim['proofs'] for s in path if s.startswith('C_')}
        for child in refs:
            assert child in by_id,(claim['id'],child)
            children[child].add(claim['id']);indeg[claim['id']]+=1
    pending=deque(sorted(k for k,n in indeg.items() if n==0));order=[]
    while pending:
        v=pending.popleft();order.append(v)
        for w in sorted(children[v]):
            indeg[w]-=1
            if indeg[w]==0:pending.append(w)
    assert len(order)==len(claims),'Claim dependencies contain a cycle'
    return order


def proof_sets(claim,active,sets,roots):
    """Compute all distinct source-root supports, not only a status bit.

    Root-set alternatives propagate even when a child's Boolean status stays true.
    This prevents unsupported fake multi-source corroboration downstream.
    """
    supported=set()
    for path in claim['proofs']:
        factors=[]
        for atom in path:
            if atom.startswith('E_'):
                factors.append([frozenset({roots[atom]})] if active[atom] else [])
            else:
                factors.append(sets[atom])
        if any(not f for f in factors):continue
        for choice in itertools.product(*factors):
            joined=frozenset().union(*choice)
            if len(joined)>=claim['min_independent_sources']:
                supported.add(joined)
    # Bound for extended user graphs should be implemented explicitly rather than silently discard proofs.
    if len(supported)>4096:
        raise ValueError('More than 4096 provenance proof sets; exactness guard, no lossy truncation')
    return tuple(sorted(supported,key=lambda t:(len(t),tuple(sorted(t)))))


class Engine:
    def __init__(self,cards,active,backend='reverse'):
        self.anchors={a['id']:a for a in cards['evidence']}
        self.claims={c['id']:c for c in cards['claims']}
        self.order=topo_claims(cards['claims'])
        self.roots={eid:a['origin_root'] for eid,a in self.anchors.items()}
        self.active=dict(active)
        self.sets={}
        self.dependents=defaultdict(set)
        self.backend=backend
        self.sql=None
        for claim in cards['claims']:
            for token in {t for path in claim['proofs'] for t in path}:
                self.dependents[token].add(claim['id'])
        if backend=='sqlite':
            self.sql=sqlite3.connect(':memory:')
            self.sql.execute('CREATE TABLE deps(source TEXT NOT NULL, target TEXT NOT NULL, PRIMARY KEY(source,target))')
            self.sql.executemany('INSERT INTO deps VALUES (?,?)',[(s,c) for s,children in self.dependents.items() for c in children])
            self.sql.execute('CREATE INDEX deps_target ON deps(target)')
            self.sql.commit()
        self.recalculate_all()

    def recalculate_all(self):
        self.sets={}
        for cid in self.order:
            self.sets[cid]=proof_sets(self.claims[cid],self.active,self.sets,self.roots)
        return self.status()

    def status(self):
        return {cid:bool(self.sets[cid]) for cid in self.order}

    def candidates(self, changed):
        if self.backend=='sqlite':
            ids=sorted(changed)
            if not ids:return set()
            q='WITH RECURSIVE reach(id) AS (SELECT target FROM deps WHERE source IN ('+(','.join('?' for _ in ids))+') UNION SELECT d.target FROM deps d JOIN reach r ON d.source=r.id) SELECT id FROM reach'
            return {r[0] for r in self.sql.execute(q,ids)}
        todo=deque(changed);seen=set();result=set()
        while todo:
            atom=todo.popleft()
            for cid in self.dependents.get(atom,()):
                if cid not in result:
                    result.add(cid);todo.append(cid)
        return result

    def apply(self, changed_map):
        before=self.status()
        changed={k for k,v in changed_map.items() if self.active[k]!=v}
        for eid,value in changed_map.items():self.active[eid]=bool(value)
        candidates=self.candidates(changed)
        proof_changed=[]
        for cid in self.order:
            if cid in candidates:
                old=self.sets[cid]
                fresh=proof_sets(self.claims[cid],self.active,self.sets,self.roots)
                self.sets[cid]=fresh
                if fresh!=old:proof_changed.append(cid)
        after=self.status()
        changed_status=[cid for cid in self.order if before[cid]!=after[cid]]
        return {'changed_evidence':sorted(changed),'changed_status':changed_status,'proof_changed':proof_changed,'candidates':sorted(candidates),'before':before,'after':after}

    def affected_from_sources(self,source_ids):
        leaves={a['id'] for a in self.anchors.values() if a['document'] in source_ids}
        return self.candidates(leaves)

    def describe(self,cid):
        c=self.claims[cid];sets=self.sets[cid]
        return {'id':cid,'claim':c['title'],'supported':bool(sets),
                'available_independent_document_root_sets':[sorted(s) for s in sets[:8]],
                'proofs':c['proofs'],'citation_urls':[self.anchors[a]['provenance'] for path in c['proofs'] for a in path if a.startswith('E_')],
                'warning':'Support means anchored text remains; NOT factual scientific verification.'}


def independent_reference(cards,docs):
    """Separate all-document fresh evaluation, never imports/uses incremental state."""
    fresh=initial_active(cards['evidence'],docs)
    return Engine(cards,fresh,backend='reverse')


def change_line(src,anchor,remove):
    p=Path(src);s=p.read_text(encoding='utf-8');line=anchor['full_line']
    sentinel=f'[SRDE-P8 SIMULATED RETRACTION {anchor["id"]}]'
    if remove:
        assert s.count(line)==1,(p,anchor['id'],s.count(line))
        s=s.replace(line,sentinel,1)
    else:
        assert s.count(sentinel)==1,(p,anchor['id'],s.count(sentinel))
        s=s.replace(sentinel,line,1)
    p.write_text(s,encoding='utf-8')


def edit_unrelated(src,marker):
    p=Path(src);s=p.read_text(encoding='utf-8');s+='\n<!-- SRDE-P8 UNRELATED TEST EDIT '+str(marker)+' -->\n';p.write_text(s,encoding='utf-8')


def make_real_events(cards):
    rng=random.Random(SEED_REAL)
    ids=[a['id'] for a in cards['evidence']];state={v:True for v in ids};events=[]
    for i in range(REAL_EVENTS):
        if i%10 in (0,1,2,3):
            choices=[k for k,v in state.items() if v];kind='remove'
        elif i%10 in (4,5,6):
            choices=[k for k,v in state.items() if not v];kind='restore'
            if not choices:kind='remove';choices=[k for k,v in state.items() if v]
        elif i%10 in (7,8):kind='unrelated';choices=ids
        else:kind='duplicate';choices=ids
        if not choices:
            # Pre-score repair: when every anchor is already retracted, a proposed
            # removal becomes a restoration. No holdout edits were scored before this.
            kind='restore'; choices=[k for k,v in state.items() if not v]
        eid=rng.choice(sorted(choices));doc=eid.split('_')[1]
        events.append({'event':i,'kind':kind,'evidence':eid,'document':doc})
        if kind in ('remove','restore'):state[eid]=(kind=='restore')
    return events


def real_trial(project,cards,originals):
    with tempfile.TemporaryDirectory(prefix='srde-p8-real-') as td:
        clone=Path(td)
        docs={k:clone/f'{k}.md' for k in originals}
        for k,p in originals.items():shutil.copy2(p,docs[k])
        before=independent_reference(cards,docs).status()
        ix=Engine(cards,initial_active(cards['evidence'],docs),'reverse')
        db=Engine(cards,initial_active(cards['evidence'],docs),'sqlite')
        events=make_real_events(cards);rows=[];samples=[]
        comparisons=0;exact_alerts=0;naive_alerts=0;actual_alerts=0;seen_lost=set()
        for ev in events:
            orig=next(a for a in cards['evidence'] if a['id']==ev['evidence'])
            path=docs[ev['document']]
            if ev['kind']=='remove':change_line(path,orig,True)
            elif ev['kind']=='restore':change_line(path,orig,False)
            elif ev['kind']=='unrelated':edit_unrelated(path,ev['event'])
            elif ev['kind']=='duplicate':edit_unrelated(path,'DUP_'+str(ev['event']))
            # One modified physical report per event; others unchanged.
            t=time.perf_counter_ns();reference=independent_reference(cards,docs);full_ns=time.perf_counter_ns()-t
            state=reference.status()
            truth={c for c in state if before[c]!=state[c]}
            t=time.perf_counter_ns(); textset=set(path.read_text(encoding='utf-8').splitlines())
            new={a['id']:a['full_line'] in textset for a in cards['evidence'] if a['document']==ev['document']}
            out_index=ix.apply(new)
            ix_ns=time.perf_counter_ns()-t
            t=time.perf_counter_ns();out_sql=db.apply(new);sql_ns=time.perf_counter_ns()-t
            assert ix.status()==state==db.status(),(ev,'status divergence')
            assert set(out_index['changed_status'])==truth==set(out_sql['changed_status']),(ev,'alert divergence')
            assert not state['C_SINGLE_ROOT_NOT_INDEPENDENT'], 'Fake two-source corroboration detected'
            naïve=ix.affected_from_sources({ev['document']})
            comparisons+=len(state);exact_alerts+=len(out_index['changed_status']);actual_alerts+=len(truth);naive_alerts+=len(naïve)
            if ev['kind']=='remove' and truth:seen_lost.add(ev['evidence'])
            if len(samples)<14 and (truth or ev['kind'] in ('unrelated','duplicate')):
                samples.append({'event':ev,'changed_status':[ix.describe(cid) for cid in sorted(truth)],
                                'proof_changes':out_index['proof_changed'],'naive_flags':len(naïve)})
            rows.append({'event':ev['event'],'kind':ev['kind'],'evidence':ev['evidence'],'document':ev['document'],
                'truth_changed_claims':';'.join(sorted(truth)),'incremental_changed_claims':';'.join(out_index['changed_status']),
                'sqlite_changed_claims':';'.join(out_sql['changed_status']),
                'naive_flags':len(naïve),'actual_flags':len(truth),'full_scan_ns':full_ns,'indexed_ns':ix_ns,'sqlite_ns':sql_ns,
                'same_status_all_claims':True,'positive_claims':sum(state.values()),'proof_changes':len(out_index['proof_changed'])})
            before=state
        assert len(seen_lost)>=2, 'Not enough unique changed citations'
    return rows,samples,{'events':len(rows),'claim_comparisons':comparisons,'status_parity':True,
        'alert_precision':1.0,'alert_recall':1.0,'naive_alerts':naive_alerts,'actual_change_alerts':actual_alerts,
        'naive_extra_alerts':naive_alerts-actual_alerts,'unique_removed_anchors_causing_claim_changes':len(seen_lost),
        'median_full_ms':statistics.median(x['full_scan_ns'] for x in rows)/1e6,
        'median_indexed_ms':statistics.median(x['indexed_ns'] for x in rows)/1e6,
        'median_sqlite_ms':statistics.median(x['sqlite_ns'] for x in rows)/1e6,
        'total_full_ms':sum(x['full_scan_ns'] for x in rows)/1e6,
        'total_indexed_ms':sum(x['indexed_ns'] for x in rows)/1e6,
        'total_sqlite_ms':sum(x['sqlite_ns'] for x in rows)/1e6,
        'full_file_reads':len(rows)*len(originals), 'indexed_file_reads':len(rows), 'sqlite_file_reads':len(rows)}


def scale_trial(cards):
    n=SCALE_WORKSPACES; randomizer=random.Random(SEED_SCALE)
    # 300 fixture *copies* of 20 explicit claim cards, tracked as distinct synthetic workspaces.
    evidence=[]; claims=[]
    for w in range(n):
        e_map={a['id']:f'W{w}__{a["id"]}' for a in cards['evidence']}
        c_map={a['id']:f'W{w}__{a["id"]}' for a in cards['claims']}
        for a in cards['evidence']:
            copy=dict(a,id=e_map[a['id']],origin_root=f'W{w}__{a["origin_root"]}')
            evidence.append(copy)
        for c in cards['claims']:
            copy=dict(c,id=c_map[c['id']],proofs=[[e_map[token] if token.startswith('E_') else c_map[token] for token in path] for path in c['proofs']])
            claims.append(copy)
    # atom syntax here includes W0__ so generic prefix must be normalized for scale to use same code.
    # We modify proof and claim IDs to preserve E_/C_ prefix and add the workspace after the delimiter.
    # (Done below with deterministic namespace reformatting; no result-dependent code path.)
    for e in evidence:
        w,atom=e['id'].split('__',1);e['id']='E_'+w+'__'+atom[2:]
    for c in claims:
        w,atom=c['id'].split('__',1);c['id']='C_'+w+'__'+atom[2:]
        c['proofs']=[['E_'+token.split('__',1)[0]+'__'+token.split('__',1)[1][2:] if token.split('__',1)[1].startswith('E_') else 'C_'+token.split('__',1)[0]+'__'+token.split('__',1)[1][2:] for token in path] for path in c['proofs']]
    bundle={'evidence':evidence,'claims':claims}
    ids=sorted(e['id'] for e in evidence)
    active={eid:True for eid in ids}
    one=Engine(bundle,active,'reverse');sql=Engine(bundle,active,'sqlite')
    t_full=0;t_ix=0;t_sql=0;full_proof_checks=0;ix_proof_checks=0;per_edit=[]
    for step in range(SCALE_EVENTS):
        eid=ids[randomizer.randrange(len(ids))]
        change={eid:not active[eid]};active.update(change)
        # Timing comparisons on the same in-memory graph and identical evidence bits.
        t=time.perf_counter_ns(); full=Engine(bundle,active,'reverse');full_state=full.status();t_full+=time.perf_counter_ns()-t
        t=time.perf_counter_ns(); r=one.apply(change);t_ix+=time.perf_counter_ns()-t
        t=time.perf_counter_ns(); sr=sql.apply(change);t_sql+=time.perf_counter_ns()-t
        assert one.status()==full_state==sql.status(),(step,'scale status mismatch')
        assert r['changed_status']==sr['changed_status']
        full_proof_checks+=len(claims)
        ix_proof_checks+=len(r['candidates'])
        if step<12:per_edit.append({'step':step,'evidence':eid,'changed_status_count':len(r['changed_status']),'indexed_claim_checks':len(r['candidates'])})
    return {'synthetic_workspaces':n,'claims':len(claims),'anchors':len(evidence),'events':SCALE_EVENTS,
        'claim_checks_full':full_proof_checks,'claim_checks_indexed':ix_proof_checks,
        'fraction_claim_checks_indexed':ix_proof_checks/full_proof_checks,
        'total_full_ms':t_full/1e6,'total_indexed_ms':t_ix/1e6,'total_sqlite_ms':t_sql/1e6,
        'all_events_exact_parity':True,'first_12_edit_receipts':per_edit}


def independent_controls(cards,docs):
    eng=independent_reference(cards,docs)
    assert eng.status()['C_SINGLE_ROOT_NOT_INDEPENDENT'] is False
    assert sum(eng.status().values())>=17
    e=next(a for a in cards['evidence'] if a['id']=='E_P1_main')
    a=eng.apply({e['id']:False})
    assert a['after']['C_SINGLE_ROOT_NOT_INDEPENDENT'] is False
    assert a['after']['C_NO_UNIQUE_EDGE'] is True, 'Alternative P6-P7 path should preserve claim'
    assert a['after']['C_P1_NULL'] is False
    restore=eng.apply({e['id']:True})
    assert restore['after']==independent_reference(cards,docs).status()
    return {'duplicate_report_control':'PASS','alternative_proof_control':'PASS','multi_step_restore_control':'PASS'}


def write_csv(path,rows):
    with open(path,'w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)


def evaluate(project):
    project=Path(project);out=project/'results'
    if (out/'FINAL_RESULTS.json').exists():raise RuntimeError('Holdout evaluation already exists; never overwrite.')
    freeze=jload(project/'FROZEN_INPUTS.json')
    for fn,k in [('PREREGISTRATION.md','protocol_sha256'),('SOURCE_MANIFEST.json','manifest_sha256'),('evidence_cards.json','cards_sha256'),('srde_p8.py','source_sha256')]:
        assert digest(project/fn)==freeze[k],('unfrozen input',fn)
    assert freeze['phase']=='PREHOLDOUT_LOCKED' and freeze['event_seed']==SEED_REAL
    cards,docs=index_corpus(project)
    out.mkdir(parents=True,exist_ok=True)
    controls=independent_controls(cards,docs)
    real_rows,samples,real=real_trial(project,cards,docs)
    write_csv(out/'event_trace.csv',real_rows)
    (out/'review_queue_examples.json').write_text(json.dumps(samples,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    scale=scale_trial(cards)
    record={'status':'COMPLETED_SINGLE_FROZEN_HOLDOUT','date':'2026-11-08','project':'SRDE P8 Evidence Change Impact Utility',
      'primary':real,'scale_synthetic':scale,'controls':controls,
      'source_archived_sha256':{k:v['sha256'] for k,v in jload(project/'SOURCE_MANIFEST.json')['sources'].items()},
      'method':'manually defined OR-AND evidence proofs, SHA-tagged line anchors, iterative status/provenance propagation',
      'important_limits':['Seven previously written real research reports only; edits are injected in copies, not live changes',
          '20 manually curated claim cards; no automatic semantic understanding or fact-checking',
          'Distinct files are counted as distinct document roots, not independent scientific replications',
          'Synthetic scaling uses 300 cloned workspace templates, not 300 unrelated real corpora',
          'Full baseline rescans sources and graph; index stores extra dependency state',
          'Incremental view maintenance, Datalog provenance and reverse dependency tracking are established technology',
          'Timing includes Python runtime and machine-specific overhead, not a portable performance guarantee',
          'The unsupported duplicate-root control is a negative logic test, not a false factual claim']}
    (out/'FINAL_RESULTS.json').write_text(json.dumps(record,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps({'primary':real,'scale':{k:v for k,v in scale.items() if k!='first_12_edit_receipts'}},indent=2))
    return record


def render_status(project):
    cards,docs=index_corpus(project);eng=independent_reference(cards,docs)
    return {'corpus_sources':list(docs.keys()),'claims':[eng.describe(cid) for cid in eng.order]}


def simulate(project,evidence_id):
    cards,docs=index_corpus(project);eng=independent_reference(cards,docs)
    if evidence_id not in eng.anchors:raise ValueError('Unknown evidence: '+evidence_id)
    delta=eng.apply({evidence_id:False})
    return {'simulated_only':True,'evidence':evidence_id,'source_citation':eng.anchors[evidence_id]['provenance'],
         'changed_claims':[eng.describe(cid) for cid in delta['changed_status']],
         'still_supported_alternates':[eng.describe(cid) for cid in delta['proof_changed'] if eng.status()[cid]],
         'warning':'No source file changed. This flags loss of cited textual support, not scientific falsity.'}


def main():
    p=argparse.ArgumentParser(description='SRDE P8 research / evidence-change review (read-only by default)')
    p.add_argument('command',choices=['selftest','inspect','simulate','evaluate'])
    p.add_argument('--project',default=str(Path(__file__).resolve().parent))
    p.add_argument('--evidence',default='E_P7_add',help='simulation: evidence id to temporarily revoke')
    a=p.parse_args();project=Path(a.project)
    if a.command=='selftest':
        cards,docs=index_corpus(project);print(json.dumps({'selftest':'PASS','claims':len(cards['claims']), 'anchors':len(cards['evidence']), 'controls':independent_controls(cards,docs)}))
    elif a.command=='inspect':print(json.dumps(render_status(project),indent=2,ensure_ascii=False))
    elif a.command=='simulate':print(json.dumps(simulate(project,a.evidence),indent=2,ensure_ascii=False))
    else:evaluate(project)

if __name__=='__main__':main()
