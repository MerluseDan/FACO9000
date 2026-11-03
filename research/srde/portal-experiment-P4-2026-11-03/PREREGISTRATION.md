# SRDE-P4: Conditional Portal State Signal Versus Seasonal Coincidence

**Frozen protocol date:** 2026-11-03 (America/Toronto). **Originating concept:** Dan Merluse. **Platform:** Blackbird Intelligence / Proto Alpha. **Study status at creation:** predictions and test labels NOT yet evaluated by this protocol. **Classification:** exploratory retrospective comparison, not a prospective forecast or a neuroscience experiment.

## Scientific motivation

P3's strong within-month-shuffled-transition control (Brier 0.04610) outperformed its unshuffled recursive portal (0.04917) on Niño 1+2. P4 tests whether **state-conditioned residual transitions add predictive value beyond calendar-conditioned transitions**. A long portal path is not evidence of causal, semantic, or psychological relatedness.

## Data and temporal split

Primary source: NOAA Physical Sciences Laboratory, `https://psl.noaa.gov/data/correlation/nina34.anom.data`; Niño 3.4 area-mean monthly sea surface temperature anomaly, as served November 3, 2026. The source's *file footer* specifies ERSST **V6**; the older PSL landing page displays a stale V5 heading. Preserve a byte-for-byte or faithfully normalized immutable source snapshot and hash, and cite NOAA's V6 transition notice. For consistency, include 1950-01 through 2025-12 and **exclude 2026 and missing sentinels**. NOAA's current historical archive is not a series of contemporaneous real-time vintages; back revisions may exist.

One observation per issue month `t`, using only values at or before `t` to derive features; target is `y(t)=1[x(t+3)-x(t) >= +0.50 °C]` (an exploratory temperature-change threshold, **not** NOAA's official El Niño event classification). Require 13 prior/current monthly observations. Features: anomaly now, 1-, 3-, 6-, 12-month changes, second derivative, last-six-month first-difference volatility, and month sine/cosine. Event/feature indices must be forward only, without using t+1, t+2 or t+3 in inference features.

Chronological partitions, with outcome dates fully contained in each partition: training targets <=2002-12; validation issues >=2003-01 and targets <=2013-12; final holdout issues >=2014-01 and targets <=2025-12. Excluded boundary issues stay excluded. The validation stage must *not construct holdout outcomes* and must freeze a source hash, code hash, protocol hash, selected parameter set and validation grid before the evaluation stage opens holdout labels. This is chronological backtesting, not a genuinely unknown future.

## Models and selection rule

All models receive the same permitted historical observations. Use CPU only, fixed seeds, no GPU scheduling or long-running job. Prediction output is the probability of the defined event. Calibrate no parameters on the final holdout.

1. Constant Bernoulli prevalence.
2. Calendar-only logistic regression using annual phase sine/cosine and second harmonic (fixed `C=1`).
3. All-feature logistic regression with `C in {0.1, 1, 10}`.
4. All-feature random forest with 160 trees, min_samples_leaf in {5, 15}.
5. All-feature gradient boosting with max leaf nodes in {7, 15}, 140 iterations.
6. Supervised direct k-nearest-neighbor probability baseline on all state + month features: k in {12, 36}, tau in {0.5, 1.5}.
7. **Seasonal portal:** empirical monthly transition distribution, 3 recursive one-month hops, 128 particles, updated calendar/coordinate history.
8. **State-conditional portal:** 3 recursive hops, 128 particles, month-conditioned candidate pool; scale the seven noncalendar state features on training data only, take nearest `k in {6, 12, 24}` analogs in the *same calendar month*, with kernel softmax temperature `tau in {0.4, 1.2}`. Each sampled next-step change is monthly mean change plus the matching training residual. Recompute state coordinates after every step. The portal consists of state-conditional stochastic transitions and is related to established analog/Markov forecasting, **not a new theorem**.

Select the best configuration for each family using only validation Brier score, tie breaking by sorted canonical JSON of config. The **single** selected state-conditional-portal configuration is reused unchanged for the portal ablations. Retrain fitted methods on training+validation after locking choices; the final holdout consists of one sealed scoring pass.

## Prespecified controls and questions

- **Primary A (incremental state signal):** State-conditional portal minus seasonal portal Brier on holdout. Improvement requires delta <= -0.005 and the upper 95% calendar-year block bootstrap CI <0 to be called convincing on this dataset. The threshold is a stringent decision criterion, not a statistical truth.
- **Primary B (state-transition assignment):** State-conditional portal minus the *mean* of five within-month residual-shuffle portal Brier scores, shuffling historical one-step residuals among examples of the same issue month with seeds 20261120..20261124. This preserves the marginal seasonal change distribution and breaks which initial state led to which transition. Same selected k/tau, particles and prediction seeds. Strong evidence requires mean placebo worse by >=0.005 and bootstrap CI entirely below zero. Report all five placebo scores individually.
- **Secondary C (conventional predictive advantage):** State-conditional portal minus the *best validation-selected conventional family*, among all-feature logistic, random forest, gradient boosting, supervised direct analog and calendar-only logistic. Its choice is frozen by validation; do not substitute the best holdout method for primary comparator. Report separate descriptive holdout ranking.
- **Secondary D (recursion importance):** State-conditional updated-frame versus fixed-origin-state portal while updating calendar at every step. If the fixed version performs better, do not infer state-recursion benefit.
- **Negative control E:** Randomly shuffle *training event labels* for a supervised direct model and report performance to catch obvious leakage. May be omitted with reason if runtime/feature availability fails, without altering primaries.
- **Long-chain stability:** Up to 100 portal hops from three prespecified validation-era states, separately labeled a generative stability stress test, NOT a 100-month prediction test. Never score as forecasting superiority.

Use deterministic seeds (base 20261103, particles 128), equal event target for every model, and preserve code/source hashes. Report Brier, log loss, AUC, ECE, event prevalence, accuracy, run time, actual portal depth and 95% year-block bootstrap (5000 seed-fixed resamples). Overlapping target windows produce dependent forecasts; year blocks rather than individual months are the bootstrap units. Use 5000 resamples with replacement for the holdout years, RNG seed 20261106. Report number of independent year blocks and the limitations of short holdout. A difference with a confidence interval spanning zero is inconclusive, regardless of ranking.

## Interpretation and boundary

This tests a specific state-conditioned probabilistic transition architecture, not consciousness, literal portals, emotions, autonomous decision-making, universal event prediction, or intellectual ability. The input series contains no subjective human feeling scale F. Data revisions, anomaly climatology choices, human-known historical outcomes, sampling noise, possible nonstationarity and correlated monthly cases limit claims. Never hide negative or broken outcomes, invent independence, or transfer apparent P1/P2/P3 gains to P4.

## Reproducibility and failure policy

Stage `validate` freezes outputs, rejects existing lock, and never builds future target labels. Stage `evaluate` verifies hashes, rejects an existing holdout result, writes all forecasts and scores once. Retain stdout, exact package versions, source snapshot, validation grid, locked configs, full holdout records, diagnostics, errors, and all source code. A report-only error must be repaired on a *versioned copy* without mutating original predictions. The full package goes under `Google Drive / Blackbird Knowledge Repository / SRDE_P4_2026-11-03`, with public scientific results mirrored to Dan's FACO9000 GitHub repository when possible. No guarantee of benefit is asserted.