# SRDE binary semantics research — executed 3 November 2026

Start with **SRDE_Binary_Semantics_Report.pdf** or **RESEARCH_REPORT.md**. These are bounded CPU research prototypes, not a native SRDE installation. No GPU or paid resource was launched.

## Reproduce the new experiments

The measured environment was Python 3.14.4. From this extracted directory:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-lock.txt
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 .venv/bin/python run_experiment.py --out replay
.venv/bin/python test_experiment.py
.venv/bin/python run_semantic_probes.py
```

The test suite reads the bundled original results/digits_splits.json; compare replay/digits_splits.json to that file when reproducing. FREEZE.json enforces exact experiment-code identity. Do not edit the frozen script in place to test a new hypothesis; make a separately versioned follow-up and freeze it before scoring. Model fitting and data loading need no network once dependencies are installed: the public handwritten-digit source is bundled in scikit-learn, with the exact consumed 360 rows also preserved in results/digits_source.npz. The script loads the bundled library version, not the exported NPZ; compare exported data arrays if changing libraries.

Synthetic replay uses deterministic source generation from the frozen seeds. Compare prediction CSVs and result JSON byte-for-byte. Gzip/NPZ timestamps and performance measurements may vary; compare decompressed JSONL and array values. REPRODUCTION_CHECK.json records the successful second local execution. Reproduction does not supply independent authorship or a new empirical dataset.

## Reproduce the previous public graph pilot offline

Requires Node 20+. Set SRDE_DATA_DIR to the **absolute path** of sources/grail in this package, then run:

```bash
node sources/prior_unseen/run_real_inductive.mjs
```

The script writes real_inductive_rerun.json in the current working directory and checks the four original Git blob identities. If SRDE_DATA_DIR is omitted it downloads the same public files. The reference rerun result is in sources/prior_unseen/real_inductive_rerun.json. It is the original 20-negative pilot, not a modern graph-neural or hard-negative replication.

## Contents and verification

- PROTOCOL.json and FREEZE.json: pre-run local protocol, code hash and digit splits.
- run_experiment.py: frozen experiment. test_experiment.py: 18 focused tests.
- run_semantic_probes.py and results/semantic_probes.json: exhaustive finite logic/codebook probes.
- results/synthetic_source.jsonl.gz: all 27,000 generated source cases with full reports, lineage, context, age, activation and gold.
- results/synthetic_predictions.csv: 336,000 individual method predictions, including raw and calibrated arms, on 12,000 held-out cases.
- results/digits_source.npz, digits_splits.json, digits_predictions.csv: all consumed image data, original IDs, splits and 10,800 prediction rows including contextual controls. Seeds reuse one image corpus.
- results/*metrics.json, paired_bootstrap.json, integrity.json, timings.csv and environment.json: complete metrics, controls and resource scope.
- sources/: retrieved November 2 proposal, November 3 full prior archive, public graph data, exact rerun code/results, and archived E30 report/continuation summary.
- SOURCES.json and RESEARCH_REGISTER.jsonl: provenance, research questions, inference points and unresolved source gaps.
- METRICS_SUMMARY.csv, evidence_states.png, RESEARCH_REPORT.md and PDF: readable deliverables.
- SHA256SUMS.txt: payload hashes. Verify with `sha256sum -c SHA256SUMS.txt` from this directory.

The ZIP checksum and final authenticated Drive readback receipt are separate siblings of the ZIP, avoiding a self-referential hash. The receipt states exactly which files were uploaded and downloaded for hash comparison. Google Tasks uses the existing [Faco] SRDV rollout list; only this round's new completed steps are closed. Historical E30/platform tasks remain as found.

Main finding: richer evidence representations help in the designed stress test; binary storage itself is not defective; the tested recursion offers no unique advantage over its conventional equivalent. This does not validate human cognitive theory, open-ended semantics or real-event forecasting.
