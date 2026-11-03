# SRDE Recursive Portal Prediction Research — 03 November 2026

**Outcome:** No demonstrated predictive advantage over a strong conventional graph baseline. These artifacts preserve an actual public-inductive-data *pilot* and a separately executed synthetic stress test; neither ran the installed native SRDE application.

## Start here

- `SRDE_Recursive_Portals_Unseen_Data_Report_2026-11-03.pdf`: reviewed four-page technical report.
- `RESEARCH_REPORT.md`: full text report and external references.
- `real_inductive_results.json`: observed public GraIL V1 result receipt, file paths, Git hashes, metrics, confidence intervals, limitations.
- `run_real_inductive.mjs`: standalone Node 18+ reproduction; it fetches the 4 source TXT files from the public `kkteru/grail` repository (or uses `SRDE_DATA_DIR` containing the corresponding public files). It validates expected source Git blob SHA1 hashes and reruns the methods. In this work, the actual public-data run occurred through a GitHub-connected JS execution; this source file was syntax and mock-fixture tested locally, but a second full offline Node run was **not** performed.
- `FROZEN_PROTOCOL.json`, `run_synthetic.py`, `synthetic_results.json`, `synthetic_metrics.csv`, `synthetic_test_cases.csv`: executed synthetic stress test and its records.
- `real_auc.png`, `synthetic_auc.png`, `build_report.py`: chart and report reproduction files.
- `SHA256SUMS.txt`: full SHA256 integrity manifest; verify with `sha256sum -c SHA256SUMS.txt` from the unpacked directory.

## Reproduce synthetic test

Python 3.10+ with `numpy`, `pandas`, `scikit-learn` is sufficient:

```
python run_synthetic.py
```

It uses disjoint fixed world seeds, writes per-case and aggregate data. A repeated run in the research session exactly reproduced all numerical metrics and world-bootstrap confidence intervals (excluding variable runtime).

## Real public benchmark qualification

GraIL FB15k-237 V1. Source `https://github.com/kkteru/grail`, original training edges 4245; inductive graph edges 1993, validation 206, test 205. Source entity overlap 0. Test compares each positive with 20 sampled negatives (not official all-entity filtered GraIL scoring). A fixed-size 2–3-hop path-rule predictor and equal-path-evidence conventional alternatives are compared, one dataset and one evaluation seed. No modern pretrained graph neural network is included. A structural portal *analogue* does not implement full SRDE recursive workers, temporal activation, cognition or emotion models.

## License/attribution

This package does not redistribute the GraIL source dataset. Reproduce it using the original source repository and comply with the source project's terms. The original SRDE concept is credited to Dan A. Merluse; the reports and prototype computations are AI-assisted. It is a research record, not a peer-reviewed paper or verified production integration.

## Evidence provenance

The real dataset was fetched from GitHub through an authorized connector, parsed and evaluated in an isolated JS execution. The synthetic test was run locally and its independent repeat was verified. Files here are original generated receipts/scripts, not claims about deployment to the user's machine.
