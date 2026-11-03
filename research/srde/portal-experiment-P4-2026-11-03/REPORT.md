# SRDE-P4 - State-dependent portal transitions versus seasonal coincidence

**Blackbird Intelligence / Proto Alpha | November 3, 2026**  
**Research concept originator:** Dan Merluse  
**Method:** AI-assisted implementation, preregistration, comparative tests and independent score audit  
**Status:** Completed single retrospective chronological holdout; all outcomes preserved. Not peer reviewed; not evidence of human consciousness or feelings.

## Executive conclusion

The state-dependent recursive portal achieved a **Brier score of 0.12753** across 141 monthly forecasts (2014-01 to 2025-09), versus **0.16679** for calendar-month-only portals and **0.17658** as the mean of five independently within-month shuffled-state transition controls. Its improvements passed both *prespecified exploratory gain criteria*: deltas <= -0.005 and year-block 95% CI entirely below zero. This is evidence that the *assignment of a change to its current state* helps forecast this specific historical ocean temperature-change task beyond season-only transitions.

The state portal **did not win overall**: direct-analog supervised retrieval had Brier **0.12618**, slightly better than the state portal. The portal outperformed the validation-selected gradient booster (Brier 0.15147), but that paired difference had a 95% CI that included zero. No claim of general superiority is justified.

## Data and untouched-holdout discipline

- Source: NOAA/PSL monthly Niño 3.4 sea-surface temperature anomalies from `https://psl.noaa.gov/data/correlation/nina34.anom.data`, normalized 1950-2025 source preserved. The file footer identifies **ERSST V6** (although an older landing-page heading says V5); the series uses 1981-2010 anomaly reference.
- Source snapshot verified byte-for-byte against GitHub's pre-evaluation Git blob `1baa53c6c65a9ce6f02e6f11dd3673d051c42963`; source SHA-256 `1b781bd28a560b5d4d364e0fcdbe38e13164e6368eb340754669a3d1071c7ed6`.
- Target: at the issue month, forecast whether **anomaly(t+3) - anomaly(t) >= 0.50 deg C**; this is not NOAA's official El Niño episode definition.
- Model inputs: current anomaly, recent changes (1, 3, 6, 12 months), acceleration, volatility, and calendar Fourier features. No input includes a future anomaly or future label.
- Train: 621 issue records, with target dates <=2002-12. Validation: 129 records, 2003-2013. Holdout: 141 issue records, 2014-01 through 2025-09, with outcomes through 2025-12. Holdout positive cases: 29 (20.57%).
- The frozen preregistration, data, source, selected parameters and validation stdout were uploaded in **P4_PREHOLDOUT_FROZEN.zip** before holdout evaluation. Model selection used validation only. This is a retrospective backtest; the historical outcomes are public today, not a genuinely prospective real-time forecast.

## Frozen validation selection

Selected state-portal parameters: **k = 6**, kernel temperature **1.2**, 128 particles per issue, 3 recursive one-month transitions with state recomputation. All models used the same supervised outcome. The best conventional validation family was **gradient boosting**, fixed before holdout scoring.

| Family | Validation Brier | Holdout Brier |
|---|---:|---:|
| direct analog | 0.11565 | 0.12618 |
| state portal | 0.11719 | 0.12753 |
| random forest | 0.12486 | 0.14346 |
| hist boost | 0.11152 | 0.15147 |
| logistic | 0.12526 | 0.15537 |
| calendar logistic | 0.14698 | 0.15977 |
| constant | 0.15232 | 0.16534 |
| season portal | 0.15725 | 0.16679 |

## Primary comparisons and control results

**Primary A: state portal vs season-only portal.** Paired holdout Brier delta (state minus season) = **-0.03926**, 95% calendar-year block bootstrap **[-0.08131, -0.00434]**; preregistered exploratory criterion **MET**.

**Primary B: state portal vs within-month shuffled state-to-transition assignments.** Five shuffled control Briers: 0.16212, 0.17061, 0.19034, 0.17352, 0.18630; mean **0.17658**. Paired delta = **-0.04905**, 95% year-block bootstrap **[-0.09661, -0.00992]**; preregistered criterion **MET**. The comparison uses the *average of five individual squared errors*, not the artificially more favorable error of their probability ensemble.

**Secondary C: state portal vs validation-selected gradient boosting.** Delta = **-0.02394**, year-block 95% CI **[-0.06309, 0.00611]**. The interval includes zero; no statistically convincing gain.

**Secondary D: freeze the root-state coordinates instead of recomputing after each hop.** Brier = **0.14552** versus state portal **0.12753**. A distinction exists for this implementation; no universal recursion advantage is established.

**Negative control: shuffle logistic training labels.** Brier = **0.16745**, substantially worse than the unshuffled logistic baseline. This is a basic leakage sanity check, not a complete proof of causal validity.

**Descriptive comparison with best holdout conventional method (direct analog):** portal minus direct-analog Brier = **+0.00135**, post-hoc year-block interval **[-0.00679, 0.00932]**. This is a descriptive sensitivity check, *not* the preregistered conventional comparator or a claim of a statistically meaningful difference.

## Independent audit and provenance

An independent script reads the locked source/code/protocol hashes and saved `test_predictions.csv`, reconstructs all 141 ground-truth outcomes from the source, recalculates Brier and log-loss scores, rebuilds each predeclared paired bootstrap interval using 12 calendar-year blocks, and checks temporal split boundaries without refitting models. **Audit: PASS**. No holdout model was retuned or rerun for the audit.

```
Protocol SHA-256: 22a8d8491bcea404d3986f9d6aa746b4e9d0753c57d7dbd314b7d9e7f190db41
Code SHA-256:     5efacae4e482b5faccdbf6755d8c3183ccb7308546752d79d5ca9173c24fbe02
Data SHA-256:     1b781bd28a560b5d4d364e0fcdbe38e13164e6368eb340754669a3d1071c7ed6
```

## Interpretation, related mathematics, and limitations

The portal here is a state-conditioned empirical Markov/analog transition operator, recomputed after each one-month step. Conditioning on current state can improve forecasts because a series' dynamics vary with state. That principle is not new mathematics. The new SRDE research hypothesis is whether an adaptive, recursively navigable family of such operators provides repeatable advantages over established alternatives *in additional unrelated domains*.

Crucial limitations: (1) Only one additional observational dataset; NOAA Niño 3.4 and P3 Niño 1+2 are physically related, so this is not independent-domain replication. (2) Historical ERSSTv6 data can be revised; this is not authentic month-by-month historical real-time data. (3) Only 12 year blocks and overlapping three-month outcomes, so uncertainty is substantial. (4) State-conditioned portals did not beat all traditional methods. (5) The synthetic long-chain diagnostic is not a 100-month prediction test. (6) No human valence, subconscious, causal interventions, or psychological state measurements were involved.

**Decision:** keep the conditional portal mechanism as a candidate, preserve the favorable and negative findings, and next test it on a **non-ocean-domain** time series with strong conventional baselines and an independent observation period. Do not market this as general intelligence, verified consciousness, or universal event forecasting.

## Public and scientific references

- NOAA Physical Sciences Laboratory: `https://psl.noaa.gov/data/timeseries/month/Nino34_CPC/`
- NOAA historical source values: `https://psl.noaa.gov/data/correlation/nina34.anom.data`
- NOAA notice of ERSSTv6 transition (August 3, 2026): `https://www.psl.noaa.gov/data/notices/`
- NOAA ERSSTv6 scientific dataset: `https://doi.org/10.25921/z7cw-es89`
- Preceding SRDE P3 report, retained independently: `https://github.com/MerluseDan/FACO9000/blob/main/research/srde/portal-experiment-P3-2026-11-03/REPORT.md`
