"""Matched three-stage E30 campaign; every stage keeps a separate receipt."""
import argparse
import json
import os
from pathlib import Path
import time
import zipfile
from e30_integrity import append_row, atomic_json, file_sha, ROOT
from e30_run_model import load_backend, run, MODEL_DEFAULT

def checkpoint_export(root,stage,completed,require_download_ack=False):
    root=Path(root)
    dest=root.parent/f'{root.name}_{stage}_{completed:03d}_{time.time_ns()}_checkpoint.zip'
    tmp=dest.with_suffix('.zip.tmp')
    with zipfile.ZipFile(tmp,'w',zipfile.ZIP_DEFLATED) as z:
        for p in sorted(root.rglob('*')):
            if p.is_file():z.write(p,str(p.relative_to(root.parent)))
    with tmp.open('rb') as f:os.fsync(f.fileno())
    os.replace(tmp,dest)
    print('CHECKPOINT_EXPORT',dest,file_sha(dest),flush=True)
    if require_download_ack:
        from google.colab import files
        files.download(str(dest))
        # The operator checks the actual browser download before acknowledging.
        answer=input('Verify the checkpoint ZIP is saved outside this Colab runtime, then type SAVED: ')
        if answer.strip()!='SAVED':raise RuntimeError('Off-runtime checkpoint download not acknowledged; stopped')
        append_row(root/'durability_receipts.jsonl',{'stage':stage,'completed':completed,
            'export_sha256':file_sha(dest),'operator_ack':'SAVED',
            'utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())})
    return dest

def campaign(root,platform_name,download_ack=False):
    root=Path(root);root.mkdir(parents=True,exist_ok=True)
    started=time.perf_counter()
    backend=load_backend(MODEL_DEFAULT)
    atomic_json(root/'startup_cost.json',{'backend_load_seconds':time.perf_counter()-started})
    for mode,folder in [('preflight','preflight'),('standard','main'),('confirmation','confirmation')]:
        def cb(out,completed):
            if completed%80==0:checkpoint_export(root,folder,completed,download_ack)
        try:
            report=run(root/folder,mode,preflight=root/'preflight' if mode!='preflight' else None,
                platform_name=platform_name,backend=backend,checkpoint_callback=cb)
            checkpoint_export(root,folder,report['completed_calls'],download_ack)
        except Exception as e:
            append_row(root/'failures.jsonl',{'stage':mode,'error':str(e),'type':type(e).__name__})
            checkpoint_export(root,folder,0,download_ack)
            raise
    return root

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',required=True)
    p.add_argument('--platform',choices=['local','colab'],required=True);p.add_argument('--download-ack',action='store_true')
    a=p.parse_args();campaign(a.out,a.platform,a.download_ack)
