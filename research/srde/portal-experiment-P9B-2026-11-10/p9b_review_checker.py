#!/usr/bin/env python3
"""P9B: version-pinned, read-only Git-document revision watcher.

The program verifies the public Git blob SHA, compares source text locations,
and emits a *human review queue*, NOT semantic or legal/scientific verdicts.
Python standard library only; no files are written except explicit output.

Examples:
    python p9b_review_checker.py selftest
    python p9b_review_checker.py scan --out observation.json

Full P9B registry was committed to MerluseDan/FACO9000 at freeze commit
1c8ce661a82aeda96f794fe287c71b340f5c154a.
"""
from __future__ import annotations
import argparse, difflib, hashlib, json, os, sys, time, urllib.request
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent
REGISTRY = ROOT / "registry_mirror.json"
HEADERS={"User-Agent":"SRDE-P9B-read-only-research", "Accept":"application/vnd.github+json"}

def git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()

def fetch(url: str) -> bytes:
    # Network accesses are public, read-only and bounded. No original repo mutation.
    req=urllib.request.Request(url,headers=HEADERS)
    with urllib.request.urlopen(req,timeout=20) as x:
        body=x.read(2_000_001)
        if len(body)>2_000_000: raise ValueError("Public document exceeds 2MB guard")
        return body

def get_head(repo: str) -> str:
    result=json.loads(fetch(f"https://api.github.com/repos/{repo}/commits/main"))
    return result["sha"]

def compare_refs(repo: str, before: str, after: str) -> str:
    v=json.loads(fetch(f"https://api.github.com/repos/{repo}/compare/{before}...{after}"))
    return v.get("status", "unknown")

def get_source(repo: str, ref: str, path: str) -> bytes:
    return fetch(f"https://raw.githubusercontent.com/{repo}/{ref}/{path}")

def inspect(old: str, new: str, line_number: int, before_lines: int=5) -> dict:
    """Compare source exact-line and frozen local-context selectors.

    No semantic interpretation: all alerts mean *review needed*, not 'false'.
    """
    a,b=old.splitlines(),new.splitlines()
    assert 1<=line_number<=len(a) and a[line_number-1].strip()
    target=a[line_number-1]
    old_window=a[max(0,line_number-1-before_lines):line_number]
    matches=[i+1 for i,line in enumerate(b) if line==target]
    window_matches=[i+1 for i in range(len(b)) if
                    b[max(0,i-before_lines):i+1]==old_window]
    exact=bool(matches)
    context=bool(window_matches)
    # Stronger conventional comparator: source-level diff hunk near original
    # line (including insertions that alter scope without touching the quote).
    anchor_i=line_number-1
    close=max(0,anchor_i-before_lines)
    high=anchor_i+before_lines
    altered=[]
    for tag,i1,i2,j1,j2 in difflib.SequenceMatcher(None,a,b,autojunk=False).get_opcodes():
        if tag=='equal':continue
        affected=(close<=i1<=high) if i1==i2 else (i1<=high and i2-1>=close)
        if affected:altered.append({"operation":tag,"baseline_lines":[i1+1,i2],"current_lines":[j1+1,j2]})
    return {"exact_anywhere":exact,"context_preserved":context,
            "diff_context_alert":bool(altered),"diff_context_hunks":altered[:8],
            "exact_match_line_numbers":matches[:15],
            "context_match_line_numbers":window_matches[:15],
            "old_occurrences":sum(line==target for line in a),
            "review_required":not context,
            "reason":("anchor_missing" if not exact else
                      "context_changed_or_moved" if not context else
                      "local_anchor_intact")}

def inspect_document(reg: dict, baseline: bytes, current: bytes, current_ref: str,
                     ancestry: str) -> dict:
    old_sha=git_blob_sha(baseline)
    if old_sha!=reg["baseline_blob"]:
        raise ValueError("Immutable baseline Git blob SHA does not match registry")
    current_blob=git_blob_sha(current)
    result={"doc_id":reg["id"],"repository":reg["repo"],"path":reg["path"],
            "baseline_commit":reg["baseline_ref"],"current_commit":current_ref,
            "baseline_blob":old_sha,"current_blob":current_blob,
            "ancestry_status":ancestry,"source_changed":current_blob!=old_sha,
            "baseline_integrity":"VERIFIED","claims":[],"review_queue":[]}
    if ancestry not in ("ahead","identical"):
        result["status"]="UNCERTAIN_HISTORY";return result
    a,b=baseline.decode("utf-8"),current.decode("utf-8")
    for c in reg["claims"]:
        finding=inspect(a,b,c["line"])
        z={"claim_id":c["id"],"role":c["role"],"registered_claim":c["text"],
           "baseline_line":c["line"],"citation_status":finding,
           "semantic_outcome":"PENDING_INDEPENDENT_REVIEW" if finding["review_required"] else "NOT_ASSESSED"}
        result["claims"].append(z)
        if finding["review_required"]:result["review_queue"].append(c["id"])
    result["status"]="REVIEW_QUEUED" if result["review_queue"] else "NO_ANCHOR_CHANGE"
    return result

def scan(output: Path):
    start=time.perf_counter();registered=json.loads(REGISTRY.read_text())
    result={"study":"SRDE-P9B","status":"UNSCORED_PROSPECTIVE_DOCUMENT_OBSERVATION",
            "time_utc":datetime.now(timezone.utc).isoformat(),
            "registry_freeze_commit":registered["frozen_registry_github_commit"],
            "sources":[],"errors":[],"requests_note":"2 raw source reads/doc + 1 head/ref check per repo",
            "scientific_boundary":"Do not score semantic accuracy without independent review."}
    heads={}
    for reg in registered["sources"]:
        try:
            repo=reg["repo"]
            if repo not in heads:heads[repo]=get_head(repo)
            status=compare_refs(repo,reg["baseline_ref"],heads[repo])
            x=get_source(repo,reg["baseline_ref"],reg["path"])
            y=get_source(repo,heads[repo],reg["path"])
            result["sources"].append(inspect_document(reg,x,y,heads[repo],status))
        except Exception as e:
            result["errors"].append({"document":reg["id"],"error_class":type(e).__name__,
                                      "error":str(e)[:350]})
    result["duration_seconds"]=round(time.perf_counter()-start,4)
    result["changed_documents"]=sum(s.get("source_changed",False) for s in result["sources"])
    result["review_queue_size"]=sum(len(s.get("review_queue",[])) for s in result["sources"])
    if result["errors"]:result["status"]="INCOMPLETE_CHECK"
    output.parent.mkdir(parents=True,exist_ok=True)
    if output.exists():raise FileExistsError("Never overwrite a prior observation")
    output.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps({k:result[k] for k in ("status","time_utc","changed_documents","review_queue_size","errors","duration_seconds")},indent=2))
    return 0 if not result["errors"] else 2

def selftest():
    old="header\nsection A\nintro\nproduct guard old\nclaim text\nend\nother section\nclaim text\nfooter\nfar filler 1\nfar filler 2\nfar filler 3\nfar filler 4\nfar filler 5\nfar filler 6"
    # True change hidden by a second occurrence; original quote survives elsewhere.
    new="header\nsection A\nintro\nproduct guard NEW\nclaim text\nend\nother section\nclaim text\nfooter"
    a=inspect(old,new,5)
    assert a["exact_anywhere"] and not a["context_preserved"] and a["review_required"] and a["diff_context_alert"]
    # Entire document changed elsewhere; local anchor remains intact.
    new2=old+"\nan unrelated appendix"
    b=inspect(old,new2,5)
    assert b["exact_anywhere"] and b["context_preserved"] and not b["review_required"] and not b["diff_context_alert"]
    # Anchor line removed, but an identical sentence is still present elsewhere.
    new3="header\nsection A\nintro\nproduct guard old\nCORRECTED\nend\nother section\nclaim text\nfooter"
    c=inspect(old,new3,5)
    assert c["exact_anywhere"] and not c["context_preserved"] and c["review_required"] and c["diff_context_alert"]
    # Anchor completely removed.
    new4=old.replace("claim text","updated",2)
    d=inspect(old,new4,5)
    assert not d["exact_anywhere"] and d["review_required"] and d["diff_context_alert"]
    # Control lines stable and no alert.
    e=inspect(old,old,5)
    assert e["context_preserved"] and not e["review_required"]
    print("P9B PREFLIGHT PASS: 5 deterministic offline fixture controls; no future real revisions scored")
    return 0

def main():
    p=argparse.ArgumentParser()
    p.add_argument("command",choices=("selftest","scan"))
    p.add_argument("--out",type=Path,default=None)
    opts=p.parse_args()
    if opts.command=="selftest":return selftest()
    if opts.out is None: raise SystemExit("scan requires --out to avoid accidental overwrites")
    return scan(opts.out)

if __name__=="__main__":sys.exit(main())
