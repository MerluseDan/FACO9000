# Blackbird SRDE-P8 — Evidence Change-Impact Research Demo

**Status: audited research prototype, not a native FACO integration or production document monitor.** Built November 8, 2026, entirely CPU-only, standard-library Python.

## What it actually does

Takes seven **archived, real SRDE research reports** and 20 **manually authored, line-anchored claim cards**. It can show which research conclusions remain backed by intact cited passages, and simulate revoking one piece of evidence to see which dependent conclusions lose support. It understands alternate proof paths and prevents two passages from the **same report** from being counted as distinct document roots. Its output is a *text-support/review indicator*, not factual truth verification or legal advice.

## Quick start (from the complete ZIP)

```bash
python3 srde_p8_repaired.py selftest --project .
python3 srde_p8_repaired.py inspect --project .
python3 srde_p8_repaired.py simulate --project . --evidence E_P1_main
python3 srde_p8_repaired.py simulate --project . --evidence E_P7_add
python3 audit_independent.py --project .
```

`inspect`, `simulate`, and `selftest` **do not modify source files**. `simulate` is a virtual counterfactual: it does not change Google Drive, GitHub, or the seven bundled reports. If a source line is corrected or disappears in a **copied** research workspace, the program's manual claim graph can identify support changes; the research evaluation used 240 such controlled edits.

The completed evidence is in `results/FINAL_RESULTS.json`, `results/event_trace.csv`, `results/review_queue_examples.json`, and `results/AUDIT_INDEPENDENT.json`. Running the benchmark a second time in the original project folder is intentionally blocked; to reproduce, extract the complete ZIP into a *fresh directory* and run:

```bash
python3 srde_p8_repaired.py evaluate --project .
python3 audit_independent.py --project .
```

## Debian install (research demo)

The all-architecture `.deb` installs only a read-only shell command and packaged demo files; no services or background surveillance:

```bash
sudo apt install ./srde-evidence-impact_0.8.0~research1_all.deb
srde-evidence-impact selftest
srde-evidence-impact simulate --evidence E_P7_add
srde-evidence-impact inspect
```

The installed files are under `/usr/share/srde-p8` and read-only. To perform `evaluate`, use an extracted full ZIP in a writable directory; the packaged demo is not an autonomous watcher or generic arbitrary-document engine.

## Observed P8 results

- Seven actual previously authored SRDE reports, 15 exact-line evidence anchors, 20 explicit claims, 240 controlled correction/restore/no-op edits on **copies**.
- All 4,800 claim-status comparisons exactly matched full rescanning; every one of the 210 status changes was identified with no false alerts by the indexed method.
- Naive document-level impact flagged 1,429 claim-event pairs, of which **1,219 were unnecessary** under the explicit proof rules. Those are false *status-change* alerts, not the set of potentially interesting proof-path edits.
- Full rescans took 109.88 milliseconds total versus 18.57 milliseconds for the in-memory index over 240 edits (about **5.9x** faster in this tiny corpus). SQL's reported 13.65 milliseconds measured **dependency propagation only**, excluding the document read and thus is NOT directly comparable to the other end-to-end times.
- A **synthetic 300-workspace replication** tested 6,000 claim nodes, 4,500 anchor nodes, and 240 toggles: full graph 1,440,000 claim checks vs 839 indexed checks; timed 13.42s vs 0.451s for indexed and 0.453s for SQLite. These are artificially replicated workspaces, **not 300 different real-world corpora**.
- Conventional reverse dependency and SQLite methods have the same correctness and closely related computational method: the result validates **operational utility** under this scenario, not scientific novelty for recursive portals.

## Integrity and limitations

The preregistration was publicly committed before evaluation. The original frozen runner failed **before scoring** due to exhausting candidate removal events; `ENGINEERING_REPAIR.md`, `evaluation_failure_pre_score.log`, and the original source are preserved. `srde_p8_repaired.py` was separately published and hash-frozen **before** the one successful 240-event run. `FROZEN_INPUTS.json` still ties the scientific input to the original source; see the transparent engineering amendment.

Citation IDs are exact full-line strings. Non-anchor context edits or erroneous citation maps are not detected; scientific statements remain unverified even if a citation exists. Independent reporting groups are document file roots, not rigorously independent experiments. No automatic research-paper extraction, LLM reasoning, live remote sync, third-party tracking, or native FACO integration is claimed.

## Provenance

- [Public P8 protocol and source record](https://github.com/MerluseDan/FACO9000/tree/main/research/srde/portal-experiment-P8-2026-11-08)
- [Blackbird P8 Drive folder](https://drive.google.com/drive/folders/1WIZSE2JhAZ4_sKaP9xbpqlnvxNrE8JOe)
- Full source snapshots and exact SHA digests in `SOURCE_MANIFEST.json` and `FROZEN_INPUTS.json`.

**Decision:** P8 meets the predefined practical workflow test; future experiments need live change feeds, independently authored claim maps, and human review of correctness to determine field usefulness.
