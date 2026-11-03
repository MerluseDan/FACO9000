# SRDE learned temporal evidence — executed 3 November 2026

Read SRDE_Learned_Temporal_Report.pdf or RESEARCH_REPORT.md first. The next simulation learns effective source/age forecast weights from training outcomes, then tests later stable times, unseen worlds and deliberately shifted source/dynamics conditions. This is authored synthetic next-step forecasting, not empirical real-event prediction or native SRDE integration.

## Reproduce locally

Measured local environment: Python 3.14.4. From this extracted directory:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-local-lock.txt
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 .venv/bin/python run_simulation.py --out replay
.venv/bin/python test_simulation.py
```

The exact code is guarded by FREEZE.json. Change no scientific code in place to test a new hypothesis; version and freeze a follow-up first. The run uses no external data or network after dependencies are installed. The bundled source cases, latent gold and learned parameters preserve the complete input/output chain. Latent gold is for generation/grading and is not available to fitting or prediction functions.

## Google Colab

Open SRDE_Learned_Reliability_Chronological_2026-11-03.ipynb in Colab and run its study cell with a CPU runtime. The notebook embeds the exact frozen source/protocol/receipt. GPU acceleration is unnecessary for this small experiment. No GPU, paid upgrade, new Drive authorization or Drive mount was used.

The executed notebook is at https://colab.research.google.com/drive/1oKsGyW5g8tHRCiZe49hvB0ri5z-aESKL . Colab_CPU_Executed_Results.zip is the full recovered cloud output, not a placeholder or a local result renamed as cloud. Its archive SHA-256 is b33d8e6ff30c21f8b3221be7a53b88b73f13541657513a3e7a0b9690d21eaf5c.

Colab used Python 3.13.18, NumPy 2.4.6, SciPy 1.16.3, scikit-learn 1.6.1; local versions differ. Five of six methods reproduce predictions exactly across platforms. HGB is version-sensitive; COLAB_COMPARISON.json retains the failed overall numerical-tolerance check and per-method differences. Do not claim exact full cross-platform reproduction. Both complete local executions match exactly in the recorded local environment.

Standard browser download failed. The archive was recovered from its visible notebook output, decoded and verified against the output's SHA-256 and ZIP CRC. Large notebook output is stored by Colab separately; the standalone archive preserves all cloud files in this deliverable.

## Contents

- PROTOCOL.json, FREEZE.json: pre-run protocol, exact code hash and UTC receipt.
- run_simulation.py: frozen computation. test_simulation.py and tests.log: twelve focused checks.
- results/source_cases.jsonl.gz: all 56,000 source cases; results/latent_gold.json.gz: generation/grading-only latent states.
- results/predictions.csv: 360,000 raw/calibrated method predictions over the same 30,000 held-out cases.
- results/learned_parameters.json: all source/age weights fitted only on training data.
- results/metrics.json, paired_bootstrap.json, controls.json, timings.json, environment.json: complete local results.
- Colab_CPU_Executed_Results.zip: complete cloud source and output; Colab_Execution_Proof.png: actual notebook summary.
- COLAB_COMPARISON.json and LOCAL_REPLAY_CHECK.json: cross-environment comparison and exact local replay.
- AUDIT_RESULTS.json: independent arithmetic, counts and frozen-code checks.
- RESEARCH_REGISTER.jsonl: bounded findings and source-linked next questions.
- SHA256SUMS.txt: verify with `sha256sum -c SHA256SUMS.txt`.

The outer ZIP hash and authenticated Drive delivery receipt are separate sibling files to avoid self-referential checksums. Cross-platform runs use the same data and do not increase the independent scientific sample size. The measured vote reduction is not a monetary, wall-time or GPU-saving claim.
