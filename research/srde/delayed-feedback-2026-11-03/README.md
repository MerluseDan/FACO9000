# SRDE delayed-feedback experiment — 3 November 2026

Read **SRDE_Delayed_Feedback_Report.pdf** or **RESEARCH_REPORT.md** first. The protocol and source hashes were committed to GitHub before outcome computation. This is a new synthetic simulation, not a retuned version of the preceding study.

## Reproduce

Measured environment: Python 3.14.4. From this directory:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-lock.txt
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 .venv/bin/python run_delayed.py --out replay
.venv/bin/python test_delayed.py
.venv/bin/python audit_results.py
```

The audit reads the bundled original results; compare replay output with those files to check a new run. FREEZE.json guards the runner, reused helper and protocol. The simulation uses no external data/network after dependency installation. Gzip metadata can differ; compare decompressed data. Metric/alarm/control/fit/bootstrap JSON and decompressed source/gold/prediction files matched in the second complete process, as recorded in REPLAY_CHECK.json.

## Data and evidence

- results/source_cases.jsonl.gz: all 76,000 training/calibration/deployment source cases.
- results/latent_gold.json.gz: generation/grading-only states, rates and regime times. Never supplied to learners.
- results/predictions.csv.gz: 350,000 individual predictions for seven policies over the same 50,000 deployment cases; probabilities, phases, votes and feedback availability.
- results/metrics.json, alarms.json, controls.json, fit_parameters.json, paired_bootstrap.json, environment.json: complete computed results.
- run_delayed.py and source_common.py: frozen source; test_delayed.py: twelve checks; audit_results.py: independent arithmetic/coverage audit.
- PROTOCOL.json and FREEZE.json: pre-outcome public protocol/source identities. TEST_HARNESS_NOTE.md preserves the corrected chronology in two initial test-harness failures; no frozen scientific code changed.
- RESEARCH_REGISTER.jsonl: retained questions and limitations; metrics summary, chart, PDF and Markdown report: readable results.
- SHA256SUMS.txt: verify with `sha256sum -c SHA256SUMS.txt`.

Feedback becomes available eight issue steps later. Online updates use consumed votes only. Changed worlds have an unannounced drift and return; unchanged worlds expose false alarms. ResetPortal and ResetSequential are exact conventional/recursive counterparts. No GPU, paid resource or Colab execution is claimed for this round.

The tested reset policy detected changes but raised many false alarms and lost overall. Exponential forgetting helped changed worlds but lost on the full mix. These conditional/negative outcomes are preserved without post-outcome tuning. They do not establish real-world forecasting or human cognitive theory.

GitHub: https://github.com/MerluseDan/FACO9000/tree/main/research/srde/delayed-feedback-2026-11-03

Canonical Drive: https://drive.google.com/drive/folders/15315BGmLeDl4vq1XdsKbk5tudAGKip8r
