"""FACO SRDE E30 real HuggingFace GPU inference runner. Colab-friendly.

No remote execution occurs until a person starts a Google Colab runtime.
Do not label output a completed experiment without model_run.json and QA.
"""
import argparse
import hashlib
import json
import os
import platform
import random
import re
import statistics
import sys
import time
from collections import defaultdict
from pathlib import Path
from e30_integrity import (ROOT,REPAIR_ID,MODEL_ID,MODEL_REVISION,atomic_json,file_sha,
    verify_freeze,dependency_versions,preserve_identity,recover_jsonl,append_row,
    validate_rows,require_exact_completion,preflight_passed)

from e30_persistence import persist_and_reload
from e30_core import (MAIN_SEEDS,CONFIRM_SEEDS,METHODS,PROTOCOL_ID,TOKEN_BUDGET,
                     canonical,data,evidence,prompt,sha,save_offline)

MODEL_DEFAULT = 'Qwen/Qwen2.5-1.5B-Instruct'
MAX_NEW_TOKENS = 80

def strictly_grade(raw, ended, gold):
    """No lenient salvage: an invalid or truncated answer is not a success."""
    if not ended:return {'status':'TRUNCATED','answer':None,'correct':False}
    try:
        def unique(pairs):
            d={}
            for k,v in pairs:
                if k in d: raise ValueError('Duplicate JSON key')
                d[k]=v
            return d
        obj=json.loads(raw,object_pairs_hook=unique)
    except (TypeError,ValueError):
        return {'status':'INVALID_JSON','answer':None,'correct':False}
    if not isinstance(obj,dict) or list(obj.keys())!=['answer'] or not isinstance(obj['answer'],str):
        return {'status':'INVALID_SCHEMA','answer':None,'correct':False}
    val=obj['answer']
    if not re.fullmatch(r'(?:[A-Z][A-Z2-9]{7}|UNKNOWN)',val):
        return {'status':'INVALID_VALUE','answer':val,'correct':False}
    return {'status':'CORRECT' if val==gold else 'WRONG','answer':val,'correct':val==gold}

def bootstrap_paired(rows,a='srde_activated',b='graph_state',n=10000):
    """Paired worlds are the resampling unit, not correlated individual tasks."""
    per=defaultdict(dict)
    for r in rows:per[r['world']].setdefault(r['method'],[]).append(int(r['correct']))
    pairs=[]
    for w,item in per.items():
        if a in item and b in item:
            assert len(item[a])==len(item[b])
            pairs.append(statistics.mean(item[a])-statistics.mean(item[b]))
    if not pairs:return {'n_paired_worlds':0,'delta':None,'ci95':None}
    rng=random.Random(3040001)
    samples=sorted(statistics.mean(rng.choices(pairs,k=len(pairs))) for _ in range(n))
    return {'n_paired_worlds':len(pairs),'delta':statistics.mean(pairs),
            'ci95':[samples[int(.025*n)],samples[min(n-1,int(.975*n))]]}

def summarize(rows):
    s={}
    for m in METHODS:
        rs=[r for r in rows if r['method']==m]
        if not rs:continue
        s[m]={'n':len(rs),'correct':sum(bool(x['correct']) for x in rs),
              'accuracy':sum(bool(x['correct']) for x in rs)/len(rs),
              'truncated':sum(x['status']=='TRUNCATED' for x in rs),
              'invalid':sum(x['status'].startswith('INVALID') for x in rs),
              'wrong':sum(x['status']=='WRONG' for x in rs),
              'mean_inference_seconds':statistics.mean(x['seconds'] for x in rs),
              'mean_retrieval_seconds':statistics.mean(x['retrieval_seconds'] for x in rs),
              'mean_state_preprocessing_seconds':statistics.mean(x['state_preprocessing_seconds'] for x in rs),
              'total_state_visible_records':sum(x['state_visible_records'] for x in rs),
              'total_state_validity_checks':sum(x['state_validity_checks'] for x in rs),
              'mean_evidence_tokens':statistics.mean(x['evidence_tokens'] for x in rs),
              'mean_actual_input_tokens':statistics.mean(x['input_tokens'] for x in rs),
              'known_accuracy':(statistics.mean(bool(x['correct']) for x in rs if x['gold']!='UNKNOWN')
                               if any(x['gold']!='UNKNOWN' for x in rs) else None),
              'unknown_accuracy':(statistics.mean(bool(x['correct']) for x in rs if x['gold']=='UNKNOWN')
                                 if any(x['gold']=='UNKNOWN' for x in rs) else None)}
    return {'methods':s,'paired_srde_minus_graph_state':bootstrap_paired(rows),
            'note':'Strict exact JSON. Invalid/truncated counted wrong. Worlds clustered in bootstrap.'}

def gpu_guard():
    """Refuse active unrelated compute; never stop another process."""
    import subprocess
    r=subprocess.run(['nvidia-smi','pmon','-c','2','-s','um'],capture_output=True,text=True,timeout=15)
    if r.returncode: raise RuntimeError('Cannot inspect GPU occupancy: '+r.stderr.strip())
    for line in r.stdout.splitlines():
        cols=line.split()
        if len(cols)>5 and cols[0].isdigit() and 'C' in cols[2] and cols[1]!=str(os.getpid()):
            # Idle resident services may have '-' or zero SM. Never kill them.
            if cols[3].isdigit() and int(cols[3])>0:
                raise RuntimeError('Unrelated GPU compute active; checkpoint retained: '+line.strip())
    return r.stdout

def load_backend(model_id,allow_cpu=False):
    if allow_cpu: raise RuntimeError('Repaired protocol forbids CPU substitution')
    if model_id!=MODEL_ID: raise RuntimeError('Frozen model ID changed')
    deps=dependency_versions()
    os.environ.setdefault('CUBLAS_WORKSPACE_CONFIG',':4096:8')
    import torch,transformers
    lock=json.loads((ROOT/'dependencies.lock.json').read_text())
    if torch.__version__!=lock['torch_build']:raise RuntimeError('Torch CUDA build differs from frozen lock')
    from transformers import AutoModelForCausalLM,AutoTokenizer
    from huggingface_hub import snapshot_download
    if not torch.cuda.is_available(): raise RuntimeError('CUDA GPU unavailable; no CPU substitution')
    occupancy=gpu_guard()
    snap=Path(snapshot_download(model_id,revision=MODEL_REVISION,
        allow_patterns=['*.json','*.txt','*.safetensors','LICENSE'],
        cache_dir=os.environ.get('E30_MODEL_CACHE')))
    model_files=json.loads((ROOT/'MODEL_FILES.json').read_text())
    for name,digest in model_files['files'].items():
        if file_sha(snap/name)!=digest: raise RuntimeError('Pinned model file hash mismatch: '+name)
    torch.manual_seed(3040001); torch.cuda.manual_seed_all(3040001)
    torch.use_deterministic_algorithms(True)
    torch.backends.cuda.matmul.allow_tf32=False; torch.backends.cudnn.allow_tf32=False
    tok=AutoTokenizer.from_pretrained(str(snap),trust_remote_code=False,local_files_only=True)
    model=AutoModelForCausalLM.from_pretrained(str(snap),device_map={'':'cuda:0'},
        torch_dtype=torch.float32,attn_implementation='eager',trust_remote_code=False,local_files_only=True)
    model.eval()
    devices=sorted({str(p.device) for p in model.parameters()})
    dtypes=sorted({str(p.dtype) for p in model.parameters() if p.is_floating_point()})
    if devices!=['cuda:0'] or dtypes!=['torch.float32']:
        raise RuntimeError('Model did not fully load on CUDA in frozen float32 dtype')
    eos=model.generation_config.eos_token_id
    eos_set=set(eos if isinstance(eos,(list,tuple)) else [eos]); eos_set.discard(None)
    def chat(task,ctx):
        p=prompt(task,ctx)
        return tok.apply_chat_template([{'role':'system','content':p['system']},
            {'role':'user','content':p['user']}],tokenize=True,add_generation_prompt=True,return_tensors='pt')
    def count(text): return len(tok.encode(text,add_special_tokens=False))
    count.chat_hash=lambda task,ctx:sha(chat(task,ctx)[0].tolist())
    def infer(task,ctx):
        inp=chat(task,ctx).to('cuda:0'); input_count=inp.shape[1]
        torch.cuda.synchronize(); torch.cuda.reset_peak_memory_stats()
        t0=time.perf_counter()
        with torch.inference_mode():
            out=model.generate(inp,max_new_tokens=MAX_NEW_TOKENS,do_sample=False,
                pad_token_id=tok.pad_token_id if tok.pad_token_id is not None else tok.eos_token_id)
        torch.cuda.synchronize(); elapsed=time.perf_counter()-t0
        generated=out[0,input_count:].tolist()
        # Only an observed configured EOS/EOT is a valid termination.
        return {'raw':tok.decode(generated,skip_special_tokens=True).strip(),
            'ended':bool(generated and generated[-1] in eos_set),'seconds':elapsed,
            'input_tokens':int(input_count),'output_tokens':len(generated),
            'generated_token_ids':generated,'peak_allocated_bytes':torch.cuda.max_memory_allocated(),
            'peak_reserved_bytes':torch.cuda.max_memory_reserved()}
    import subprocess
    smi=subprocess.run(['nvidia-smi','--query-gpu=uuid,name,driver_version,memory.total',
        '--format=csv,noheader'],capture_output=True,text=True,check=True).stdout.strip()
    runtime={'python':platform.python_version(),'dependencies':deps,'torch_build':torch.__version__,
        'cuda_build':torch.version.cuda,'gpu':smi,'device_map':{k:str(v) for k,v in model.hf_device_map.items()},
        'parameter_devices':devices,'parameter_dtypes':dtypes,'attention':'eager',
        'deterministic_algorithms':True,'tf32':False,'seed':3040001,
        'model_revision':MODEL_REVISION,'tokenizer_revision':MODEL_REVISION,
        'model_files_sha256':sha(model_files),'generation_config':model.generation_config.to_dict(),
        'tokenizer_class':type(tok).__name__,'chat_template_sha256':sha(tok.chat_template),
        'gpu_occupancy_before_load':occupancy}
    # Occupancy varies between invocations and is not part of resume identity.
    infer.runtime_observation={'gpu_occupancy_before_load':runtime.pop('gpu_occupancy_before_load')}
    infer.real_backend=True
    return count,infer,runtime

def selected_tasks(corpus,mode):
    tasks=[]
    for w in corpus['worlds']:
        for t in w['tasks']:
            if mode=='quick' and t['scenario'] not in ('current_route','linked_policy','poisoned_policy','conflicting_override'):continue
            if mode=='preflight' and (w is not corpus['worlds'][0] or t['scenario']!='current_route'):continue
            tasks.append((w,t))
    items=[(w,t,m) for w,t in tasks for m in METHODS]
    random.Random(987123).shuffle(items)
    return items

def prepare_expected(work,count):
    expected={}
    for world,task,method in work:
        start=time.perf_counter(); ev=evidence(world,task,method,TOKEN_BUDGET,count)
        elapsed=time.perf_counter()-start
        if count(ev['text'])>TOKEN_BUDGET:raise RuntimeError('Actual evidence token cap exceeded')
        key=(task['id'],method)
        if key in expected:raise RuntimeError('Duplicate frozen work key')
        expected[key]={'world':world['world'],'scenario':task['scenario'],'gold':task['gold'],
            'prompt_sha256':sha(prompt(task,ev['text'])),
            'input_prompt_sha256':count.chat_hash(task,ev['text']),
            'evidence_tokens':ev['tokens'],'ev':ev,'retrieval_seconds':elapsed,'task':task}
    return expected

def checked_preflight(path,base_identity,count):
    path=Path(path)
    meta=json.loads((path/'run_metadata.json').read_text())
    if meta['base_identity']!=base_identity or meta['mode']!='preflight':
        raise RuntimeError('Preflight identity differs from measured run')
    expected=prepare_expected(selected_tasks(data(),'preflight'),count)
    rows=recover_jsonl(path/'model_rows.jsonl')
    validate_rows(rows,expected,strictly_grade)
    if not preflight_passed(rows,expected):raise RuntimeError('Preflight structurally failed; main blocked (accuracy does not gate)')
    report=json.loads((path/'model_run.json').read_text())
    if report.get('status')!='PREFLIGHT_STRUCTURAL_PASS' or report.get('completed_calls')!=4:
        raise RuntimeError('Preflight receipt missing/not passed')
    return file_sha(path/'model_rows.jsonl')

def run(outdir,mode,model_id=MODEL_DEFAULT,allow_cpu=False,preflight=None,platform_name='local',backend=None,checkpoint_callback=None):
    if mode not in ('preflight','quick','standard','confirmation'):raise ValueError(mode)
    if mode!='preflight' and preflight is None:raise RuntimeError('A completed structural preflight is required')
    frozen=verify_freeze()
    corpus=data(CONFIRM_SEEDS if mode=='confirmation' else MAIN_SEEDS)
    expected_hash=frozen['corpora']['confirmation' if mode=='confirmation' else 'main']
    if corpus['sha256']!=expected_hash:raise RuntimeError('Frozen corpus changed')
    out=Path(outdir);out.mkdir(parents=True,exist_ok=True)
    count,infer,runtime=backend if backend else load_backend(model_id,allow_cpu)
    real_backend=bool(getattr(infer,'real_backend',False))
    base_identity={'repair':REPAIR_ID,'freeze_sha256':sha(frozen),'model_id':model_id,
        'model_revision':MODEL_REVISION,'tokenizer_revision':MODEL_REVISION,
        'methods':list(METHODS),'evidence_token_budget':TOKEN_BUDGET,'max_new_tokens':MAX_NEW_TOKENS,
        'platform':platform_name,'runtime':runtime,'synthetic':True,
        'state_preprocessing':'Both state methods resolve full visible world before truncation; measured per call'}
    validation_start=time.perf_counter()
    preflight_hash=checked_preflight(preflight,base_identity,count) if mode!='preflight' else None
    identity={'base_identity':base_identity,'mode':mode,'corpus_sha256':corpus['sha256'],
        'preflight_rows_sha256':preflight_hash,
        'confirmation_label':'independent-seed same-generator confirmation' if mode=='confirmation' else None}
    preserve_identity(out,identity)
    observations=getattr(infer,'runtime_observation',{})
    append_row(out/'runtime_invocations.jsonl',{'timestamp_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
        'observations':observations})
    cp=out/'corpus.json'
    if cp.exists() and json.loads(cp.read_text())!=corpus:raise RuntimeError('Persisted corpus changed')
    if not cp.exists():atomic_json(cp,corpus)
    corpus=persist_and_reload(corpus,out/'evidence_memory.sqlite')
    work=selected_tasks(corpus,mode); expected=prepare_expected(work,count)
    atomic_json(out/'expected_keys.json',sorted([list(k) for k in expected]))
    checkpoint=out/'model_rows.jsonl';rows=recover_jsonl(checkpoint)
    known=validate_rows(rows,expected,strictly_grade)
    append_row(out/'validation_invocations.jsonl',{'seconds':time.perf_counter()-validation_start,
        'note':'Preflight revalidation, persistence reopen, expected-prompt construction and checkpoint validation; excluded from per-call retrieval/inference timing',
        'expected_prompt_state_cost_by_method':{m:{
            'state_seconds':sum(x['ev']['state_preprocessing_seconds'] for k,x in expected.items() if k[1]==m),
            'visible_records':sum(x['ev']['state_visible_records'] for k,x in expected.items() if k[1]==m),
            'validity_checks':sum(x['ev']['state_validity_checks'] for k,x in expected.items() if k[1]==m)} for m in METHODS}})
    # Any old completion marker is trusted only after the rows are revalidated.
    print(f'{mode}: {len(known)}/{len(work)} valid saved calls',flush=True)
    for i,(world,task,method) in enumerate(work,1):
        key=(task['id'],method)
        if key in known:continue
        guard_start=time.perf_counter()
        if real_backend:gpu_guard()
        guard_seconds=time.perf_counter()-guard_start
        # Retrieval is measured for THIS call; resume validation costs are separate overhead.
        t0=time.perf_counter();ev=evidence(world,task,method,TOKEN_BUDGET,count)
        retrieval_seconds=time.perf_counter()-t0
        exp=expected[key]
        if sha(prompt(task,ev['text']))!=exp['prompt_sha256']:raise RuntimeError('Prompt nondeterminism')
        rr=infer(task,ev['text']); grade=strictly_grade(rr['raw'],rr['ended'],task['gold'])
        item={k:exp[k] for k in ('world','scenario','gold','prompt_sha256','input_prompt_sha256','evidence_tokens')}
        item.update(task_id=task['id'],method=method,model_output=rr['raw'],ended=rr['ended'],
            seconds=rr['seconds'],retrieval_seconds=retrieval_seconds,guard_seconds=guard_seconds,
            input_tokens=rr['input_tokens'],output_tokens=rr['output_tokens'],
            generated_token_ids=rr.get('generated_token_ids'),peak_allocated_bytes=rr.get('peak_allocated_bytes'),
            peak_reserved_bytes=rr.get('peak_reserved_bytes'),proof_hits=ev['proof_hit'],proof_count=ev['proof_count'],
            evidence_text=ev['text'],state_preprocessing_seconds=ev['state_preprocessing_seconds'],
            state_visible_records=ev['state_visible_records'],state_validity_checks=ev['state_validity_checks'],**grade)
        append_row(checkpoint,item);rows.append(item);known.add(key)
        print(f'[{i}/{len(work)}] {task["id"]} {method}: {grade["status"]} ({rr["seconds"]:.3f}s)',flush=True)
        if checkpoint_callback is not None and len(known)%20==0:checkpoint_callback(out,len(known))
    known=validate_rows(rows,expected,strictly_grade);require_exact_completion(known,expected)
    structural=preflight_passed(rows,expected) if mode=='preflight' else None
    status=('PREFLIGHT_STRUCTURAL_PASS' if structural else 'PREFLIGHT_STRUCTURAL_FAIL') if mode=='preflight' else 'REAL_LLM_COMPLETED'
    if not real_backend:status='MOCK_'+status
    report={'status':status,'full_run':mode in ('standard','confirmation') and real_backend,
        'protocol':identity,'total_calls':len(work),'completed_calls':len(known),
        'checkpoint_sha256':file_sha(checkpoint),'summary':summarize(rows)}
    atomic_json(out/'model_run.json',report)
    if mode=='preflight' and not structural:raise RuntimeError('Malformed/truncated preflight; main blocked')
    return report

def main():
    p=argparse.ArgumentParser();p.add_argument('--mode',choices=['offline','preflight','quick','standard','confirmation'],default='preflight')
    p.add_argument('--model',default=MODEL_DEFAULT);p.add_argument('--out',default='e30_result')
    p.add_argument('--preflight');p.add_argument('--platform',choices=['local','colab'],default='local')
    args=p.parse_args()
    if args.mode=='offline':print(json.dumps(save_offline(args.out,data()),indent=2));return
    try:
        report=run(args.out,args.mode,args.model,preflight=args.preflight,platform_name=args.platform)
        print(json.dumps(report,indent=2))
    except Exception as e:
        out=Path(args.out);out.mkdir(parents=True,exist_ok=True)
        append_row(out/'failures.jsonl',{'timestamp_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
            'mode':args.mode,'type':type(e).__name__,'error':str(e)})
        raise

if __name__=='__main__':main()

