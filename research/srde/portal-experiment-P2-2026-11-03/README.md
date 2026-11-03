# Blackbird Intelligence / SRDE-P2: Real-Observation Portal Forecasting

**2026-11-03 | Concept: Dan Merluse | AI-assisted implementation and audit**

### Outcome

On retrospective Mauna Loa CO₂ forecasts, state-conditioned portal inference learned the seasonal signal but **did not outperform** the strongest nonlinear conventional predictors on the held-out final seven years. Full metrics and caveats are in `REPORT.md` and `SRDE_P2_Research_Report.pdf`. A public hypothesis is not evidence of causality or validated neuroscience.

### Data and task

- Fixed archival public dataset: `statsmodels.datasets.co2` (1958–2001; original CSV snapshot preserved in this archive).
- Input at issue week `t`: only CO₂ readings from `t` or earlier, annual sine/cosine, and historical differences.
- Future event: `1[CO2(t+4) > CO2(t)]` for four measured weekly intervals ahead.
- Chronology: train through 1988; selection 1989–1994; final 1995–2001.
- Missing past or future readings are dropped; none are imputed.

### Replicate

Run from this folder using Python 3.11+ and pinned package versions in `locked_selection.json`:

```bash
python -m pip install numpy==2.3.5 pandas==2.2.3 scipy==1.17.0 scikit-learn==1.8.0 statsmodels==0.14.6 matplotlib reportlab
python test_srde_p2.py
```

To repeat the full evaluation, **use a fresh output directory containing a copy of `PREREGISTRATION.md`** and place `srde_p2.py` in the same source working directory. Run:

```bash
python srde_p2.py --stage validate --output-dir .
python srde_p2.py --stage evaluate --output-dir .
python audit_p2.py
```

The evaluator explicitly refuses to overwrite an existing `test_predictions.csv`; use a new directory for fresh runs. `make_report.py` generates figures and PDF report after audit.

### Artifacts

- `PREREGISTRATION.md` — fixed protocol publicly committed before final test evaluation.
- `srde_p2.py` — original model implementation and pre-registered comparison.
- `test_srde_p2.py` — nonholdout tests of causal feature alignment and recursion.
- `locked_selection.json` — validation search results and selected parameters, including protocol and source hashes.
- `source_statsmodels_co2.csv` — archived observational source snapshot.
- `test_predictions.csv` — 361 time-stamped test events, their measured outcomes and each method's probability.
- `results.json` — all scores, descriptive year-block uncertainty, shuffled-label control and reverse Bayes diagnostic.
- `audit_p2.py` / `audit.json` — independent score/date/source verification.
- `REPORT.md` and `SRDE_P2_Research_Report.pdf` — full report with limitations.
- `manifest.json` — SHA-256 checksums for the final archive entries.

### Do not misinterpret

'100-level portals' is a maximum permitted hierarchy depth. The fitted real-data model actually used **3 levels**. Its architecture resembles a conventional probabilistic model tree. The study does not include the proposed emotional valence coordinate; no human feelings were sampled. All predictions were retrospective rather than conducted live.

Related public hypothesis: https://github.com/MerluseDan/FACO9000/blob/main/research/srde/portal-hypothesis-2026-11-02/README.md
