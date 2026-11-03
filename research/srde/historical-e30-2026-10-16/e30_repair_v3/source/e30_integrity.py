"""E30 v2 immutable identity, atomic receipts and lossless checkpoint recovery."""
import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
from e30_core import canonical, sha

ROOT = Path(__file__).resolve().parents[1]
REPAIR_ID = 'FACO-SRDE-E30-REPAIR-v3-FP32-2026-10-16'
MODEL_ID = 'Qwen/Qwen2.5-1.5B-Instruct'
MODEL_REVISION = '989aa7980e4cf806f80c7fef2b1adb7bc71aa306'

def file_sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda:f.read(8*1024*1024),b''): h.update(chunk)
    return h.hexdigest()

def atomic_json(path, value):
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_name(path.name+'.tmp')
    with tmp.open('w') as f:
        f.write(json.dumps(value,indent=2,sort_keys=True)+'\n'); f.flush(); os.fsync(f.fileno())
    os.replace(tmp,path)
    fd=os.open(path.parent,os.O_RDONLY)
    try: os.fsync(fd)
    finally: os.close(fd)

def source_manifest():
    files=(sorted((ROOT/'source').glob('*.py'))+sorted((ROOT/'tests').glob('*.py'))+
           sorted((ROOT/'corpora').glob('*.json'))+
           [ROOT/'PROTOCOL_v3.md',ROOT/'dependencies.lock.json',ROOT/'MODEL_FILES.json'])
    return {str(p.relative_to(ROOT)):file_sha(p) for p in files}

def verify_freeze():
    frozen=json.loads((ROOT/'FREEZE.json').read_text())
    if frozen['files']!=source_manifest(): raise RuntimeError('Frozen code/protocol/dependency manifest changed')
    return frozen

def dependency_versions():
    lock=json.loads((ROOT/'dependencies.lock.json').read_text())
    import platform
    if '.'.join(platform.python_version_tuple()[:2])!=lock['python']:
        raise RuntimeError('Python minor version differs from frozen dependency lock')
    actual={n:importlib.metadata.version(n) for n in lock['packages']}
    if actual!=lock['packages']: raise RuntimeError('Dependency versions differ from frozen lock')
    return actual

def preserve_identity(out, identity):
    """Never rewrite original metadata. A different identity requires a new directory."""
    path=Path(out)/'run_metadata.json'
    if path.exists():
        old=json.loads(path.read_text())
        if old!=identity: raise RuntimeError('Resume refused: complete runtime/study identity changed')
    else: atomic_json(path,identity)

def recover_jsonl(path):
    """Quarantine only an unterminated final append; all earlier corruption fails.

    Original bytes are retained once under their content hash. A valid record
    without its newline is also an uncommitted append and is rerun.
    """
    path=Path(path)
    if not path.exists(): return []
    raw=path.read_bytes(); lines=raw.splitlines(keepends=True)
    if lines and not lines[-1].endswith(b'\n'):
        backup=path.with_name(path.name+'.interrupted-'+hashlib.sha256(raw).hexdigest()+'.bak')
        if not backup.exists():
            with backup.open('xb') as f: f.write(raw); f.flush(); os.fsync(f.fileno())
        tail=lines.pop()
        atomic_json(path.with_name(path.name+'.recovery-'+hashlib.sha256(raw).hexdigest()+'.json'),
                    {'original_sha256':hashlib.sha256(raw).hexdigest(),'backup':backup.name,
                     'discarded_uncommitted_tail_hex':tail.hex(),'retained_records':len(lines)})
        tmp=path.with_name(path.name+'.recovering')
        with tmp.open('wb') as f: f.write(b''.join(lines)); f.flush(); os.fsync(f.fileno())
        os.replace(tmp,path)
    rows=[]
    for i,line in enumerate(lines,1):
        try: row=json.loads(line)
        except (ValueError,UnicodeError) as e: raise RuntimeError(f'Corrupt committed checkpoint line {i}') from e
        if not isinstance(row,dict): raise RuntimeError(f'Invalid checkpoint object line {i}')
        rows.append(row)
    return rows

def append_row(path,row):
    with Path(path).open('a') as f:
        f.write(canonical(row)+'\n'); f.flush(); os.fsync(f.fileno())

def validate_rows(rows,expected,grade):
    known=set()
    for row in rows:
        key=(row.get('task_id'),row.get('method'))
        if key not in expected: raise RuntimeError(f'Unexpected checkpoint key: {key}')
        if key in known: raise RuntimeError(f'Duplicate checkpoint key: {key}')
        exp=expected[key]
        for field in ('world','scenario','gold','prompt_sha256','evidence_tokens','input_prompt_sha256'):
            if row.get(field)!=exp[field]: raise RuntimeError(f'Checkpoint {field} changed for {key}')
        if row.get('evidence_text')!=exp['ev']['text']: raise RuntimeError(f'Checkpoint evidence changed for {key}')
        if type(row.get('ended')) is not bool or not isinstance(row.get('model_output'),str):
            raise RuntimeError('Missing termination/output evidence')
        recomputed=grade(row['model_output'],row['ended'],exp['gold'])
        for field in ('status','answer','correct'):
            if type(row.get(field)) is not type(recomputed[field]) or row.get(field)!=recomputed[field]:
                raise RuntimeError(f'Checkpoint grade mismatch: {key} {field}')
        for field in ('seconds','retrieval_seconds','state_preprocessing_seconds'):
            if not isinstance(row.get(field),(float,int)) or not math.isfinite(row[field]) or row[field]<0:
                raise RuntimeError(f'Invalid measured cost {field}')
        known.add(key)
    return known

def require_exact_completion(known,expected):
    if known!=set(expected): raise RuntimeError('Incomplete/extra completion keyset')

def preflight_passed(rows,expected):
    require_exact_completion({(r['task_id'],r['method']) for r in rows},expected)
    # Accuracy is deliberately excluded. WRONG is structurally valid.
    return len(rows)==4 and all(r['status'] in ('CORRECT','WRONG') for r in rows)
