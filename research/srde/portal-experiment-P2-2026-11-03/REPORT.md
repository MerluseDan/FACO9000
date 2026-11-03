# SRDE-P2 — Real-Observation Portal Forecasting: Completed Research Report

**Proto Alpha / Blackbird Intelligence — November 3, 2026**  
**Research concept:** Dan Merluse  
**Formalization, implementation, auditing:** ChatGPT-assisted  
**Status:** Single-domain, historical, independently audited, preregistered proof-of-concept. **Negative superiority result.**

## Executive result

On **361 real future-event labels withheld from training and model selection** (1995–2001), the portal model scored **0.061502** Brier, compared with **0.059726** for random forest and **0.060037** for gradient boosting. **The SRDE prototype did not win.** It outperformed logistic regression (Brier **0.069725**) but not stronger nonlinear competitors. The earlier 1989–1994 validation advantage of SRDE (Brier **0.03707**) did **not** generalize to 1995–2001. Higher AUC is not proof of better calibration; both are recorded.

This is a useful null/negative finding: conditional local subspaces alone do not establish a better forecast architecture. The *hypothesis remains falsifiable and unproven.* No claims of human neuroscience, feelings, universal meaning mapping, or general prediction follow from this test.

## Data, target, and chronology

- Fixed, public historical observations: `statsmodels.datasets.co2` from Mauna Loa Observatory, Hawaii, **1958-03-29 to 2001-12-29**, supplied by installed statsmodels **0.14.6** (origination: NOAA/Scripps observational series); this is an archival snapshot rather than an operational real-time feed.
- Raw dataset: 2284 weekly entries, 59 missing CO₂ values. Dropping rows with unavailable past lags or future event outcome left 1998 candidate rows.
- Forecast question: **Will the concentration four weeks later be higher than today's value?** The event is `CO2[t+4] > CO2[t]`; all features (annual position, past-change windows of 1, 4, 8, 13, 26 and 52 weeks) are observed no later than issue time `t`.
- Training 1958–1988: **1320** rows; selection/validation 1989–1994: **309**; final holdout 1995–2001: **361**. Boundary rows whose targets would cross the next split were excluded.
- Observed holdout event prevalence: **59.28%**. This is retrospective forecasting with observed historical measurements, not a live forecast.

## Complete performance comparison

| Model | Validation Brier | Test Brier | Test ROC AUC | Test accuracy @ 0.5 |
|---|---:|---:|---:|---:|
| Constant prevalence | 0.23689 | 0.24159 | 0.5000 | 59.28% |
| Season-only logistic | 0.05531 | 0.07221 | 0.9553 | 90.86% |
| Full logistic | 0.04655 | 0.06973 | 0.9610 | 91.41% |
| Decision tree | 0.04592 | 0.07046 | 0.9565 | 90.86% |
| Random forest | 0.03974 | 0.05973 | 0.9737 | 91.41% |
| Gradient boosting | 0.03920 | 0.06004 | 0.9683 | 92.24% |
| SRDE portals | 0.03707 | 0.06150 | 0.9719 | 91.69% |

**Primary prespecified comparator:** Gradient booster Brier minus portal comparison: portal minus booster = **+0.001465** (positive values favor the booster). Seven-year block-resampled 95% descriptive interval: **[-0.003436, +0.005951]**, 5,000 fixed-seed draws. It includes zero, so this single study does not establish a reliable difference. The best conventional model by descriptive test Brier was **random forest**, with portal minus forest = **+0.001776**.

## What SRDE portals actually did

The portal prototype used conditional **three-coordinate** gates: annual sine, annual cosine and observed change over the last four weeks. A root logistic forecast was refined by local logistic forecasts; gate thresholds and local models were estimated exclusively from the fitting period. Local forecasts were shrunk toward parent forecasts based on support. This implementation is mathematically similar to a **probabilistic model tree**; it is not unique proof of an exotic spatial geometry.

- Portal configured recursion depth cap: **100**. Actual maximum observed fitted depth: **3**, across **7** fitted nodes. 100 deep layers were *not* demonstrated on real data.
- Local predictors are correlated experts, not independent voters; voting count must not be mistaken for evidence independence.
- No affect/valence coordinate `F` exists in the Mauna Loa dataset. Testing `F ∈ [0,1]` requires separately measured human state and ethical safeguards.

## Controls and reverse inference

- **Random-label negative control:** portal retrained on shuffled fitting labels produced test Brier **0.242079**, AUC **0.518**. The predictive advantage disappears when training signals are destroyed.
- **Backward Bayes diagnostic:** given an *already observed future event*, estimate whether the earlier four-week CO₂ trend was positive. This retrospective inference scored Brier **0.161523** versus a prior-only Brier **0.241557**. It is a conventional Bayes calculation and **not** time travel, reverse causation, or a unique SRDE result.
- **Independent audit:** independently recomputed all per-row event labels from raw observations and re-scored every model: **361** rows passed; protocol and dataset SHA-256 hashes agree with the validation lock; no scoring mismatch above `1e-7`.

## Year-to-year diagnostic

| Held-out year | Rows | SRDE Brier | RF Brier | Booster Brier |
|---|---:|---:|---:|---:|
| 1995 | 52 | 0.05614 | 0.06225 | 0.05113 |
| 1996 | 52 | 0.03436 | 0.04074 | 0.04536 |
| 1997 | 52 | 0.04525 | 0.04205 | 0.04686 |
| 1998 | 52 | 0.08310 | 0.06612 | 0.07778 |
| 1999 | 52 | 0.10237 | 0.10750 | 0.10121 |
| 2000 | 53 | 0.06493 | 0.06116 | 0.05432 |
| 2001 | 48 | 0.04286 | 0.03643 | 0.04234 |

The portal system can outperform the forest in particular years while still losing overall. This volatility, autocorrelation and only seven held-out years argue against grand superiority claims.

## Replication instructions

```bash
python -m pip install numpy pandas scipy scikit-learn statsmodels matplotlib reportlab
python test_srde_p2.py
python srde_p2.py --stage validate --output-dir .
python srde_p2.py --stage evaluate --output-dir .
python audit_p2.py
```

Use a new directory for reruns; the evaluator deliberately refuses to overwrite an existing holdout prediction file. Regenerating with different package versions may create small numerical differences. `locked_selection.json` records each chosen configuration, validation trial and package version; the pre-registration and source dataset were SHA-locked before final scoring. `test_predictions.csv` retains each date, observed outcome, and forecast probability. `results.json` includes all losses, confidence intervals and negative controls.

## What P2 changes in the SRDE roadmap

**Keep:** state-dependent local frames, provenance, conditional branching and explicit reversibility testing as research directions.  
**Do not claim:** that more portal depth always helps, that deep connections establish causation, or that a majority vote proves truth.  
**Next:** preregister a **distinct observational domain** (behavioral or operational events) and test an actually different portal operator (learned context-conditioned coordinate transformations, independent evidence lineage, and calibrated abstention) under fixed cost. Any variant developed after seeing P2's holdout must use a fresh, unopened test period or dataset; never retune this test retroactively.

## Provenance and citations

- Primary dataset documentation: https://www.statsmodels.org/stable/datasets/generated/co2.html
- Scripps Mauna Loa historical observations: https://scrippsco2.ucsd.edu/data/atmospheric-co2-data/sampling-station-records/mauna-loa-observatory-hawaii/
- NOAA carbon dioxide observations: https://gmd-prod.cmdl.noaa.gov/ccgg/trends/data.html
- Predecessor public hypothesis (P0): https://github.com/MerluseDan/FACO9000/blob/main/research/srde/portal-hypothesis-2026-11-02/README.md
- Preregistered research protocol: `PREREGISTRATION.md` (also committed to GitHub before validation/test)

**Boundary:** A computational structure that models certain observable patterns is not proof of how human consciousness works, a measure of personal intelligence, or a universal predictive law.
