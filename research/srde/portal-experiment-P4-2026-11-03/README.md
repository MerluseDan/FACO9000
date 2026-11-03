# Blackbird Intelligence: SRDE-P4 (2026-11-03)

Retrospective 3-month NOAA Niño 3.4 anomaly-change forecasting study, with strict chronological splitting, state-conditioned recursive portals, conventional baselines and within-calendar-month shuffles.

**Main finding:** State-dependent portals outperformed seasonal-only portals and five within-month shuffled-assignment controls under preregistered exploratory thresholds. They narrowly lost to direct supervised nearest-neighbor retrieval. This does not establish causal discovery, psychological meaning, or general predictive superiority.

## Contents

- `PREREGISTRATION.md`: original protocol publicly committed before the held-out evaluation.
- `P4_PREHOLDOUT_FROZEN.zip`: exact model/source/selection snapshot uploaded to Google Drive before final scoring.
- `source_noaa_nino34_1950_2025.txt`: NOAA 1950-2025 anomaly source, byte-identical to pre-evaluation GitHub blob `1baa53c6c65a9ce6f02e6f11dd3673d051c42963`; current data footer labels ERSST V6.
- `srde_p4.py`: immutable P4 scientific source (includes unit self-tests, validation and evaluation stages).
- `locked_selection.json`, `validation_grid.json`, `validation_stdout.log`: selection stage and audit trail.
- `test_predictions.csv`: 141 original holdout forecasts, including 5 shuffled controls and ablations.
- `all_feature_records.csv`: all features, split boundaries and reconstruction fields.
- `results.json`: final metrics and predeclared contrasts.
- `audit_p4.py`, `audit_independent.json`, `audit_stdout.log`: standalone score/date/hash verification without refitting.
- `REPORT.md`, `SRDE_P4_Research_Report.pdf`: plain-text and formatted interpretation.
- `build_report.py`: creates figures and PDF from already saved forecasts.
- Figures: `holdout_model_comparison.png`, `yearwise_comparison.png`.

## Reproduction

Requirements: Python 3.10+, numpy, pandas, scipy, scikit-learn, matplotlib, reportlab. All experiment computations are CPU-only. Install packages in an independent environment if needed; `locked_selection.json` records observed versions.

**For a fresh reproduction only:** copy `PREREGISTRATION.md`, `source_noaa_nino34_1950_2025.txt`, and `srde_p4.py` to a new empty directory. Then execute:

```sh
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
python srde_p4.py --stage selftest --out .
python srde_p4.py --stage validate --out .
python srde_p4.py --stage evaluate --out .
```

The supplied complete archive already contains the one-shot evaluation. Do not run evaluate in the archived directory: it rejects scoring an existing holdout. For the shipped observations, run `python audit_p4.py` in the original directory instead to verify scores independently. The audit regenerates `audit_independent.json` but does not alter forecasts.

## Important caveats

This is a historical snapshot, not a genuine real-time prospective forecast. The source is related to P3's earlier ocean dataset, although the test years and series are different. A forecast of +0.5 °C Niño 3.4 anomaly change in three months is *not* NOAA's official El Niño episode definition. There are only 12 year-block clusters, overlapping targets, 128 stochastic particles per forecast and no human or emotional-state measurements. Method selection is locked but this architecture was conceived after examining P3's failures. Independent replication in unrelated domains remains necessary.
