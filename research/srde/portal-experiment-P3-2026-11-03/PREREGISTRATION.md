# SRDE-P3 - Recursive Conditional Portals on Real Ocean State Transitions

**Protocol locked:** 2026-11-03, before validation/holdout model scoring.  
**Originator:** Dan Merluse (SRDE / Blackbird Intelligence / Proto Alpha).  
**Execution:** AI-assisted independent computational evaluation, CPU only.  
**Status at lock:** protocol only. Neither positive nor negative performance is presupposed.

## Scientific question

Does recursively *regenerating the local coordinate frame after each proposed transition* improve forecasts of a future event over (i) standard discriminative forecasters and (ii) a direct analog-neighbor predictor given the same observations? Does any apparent advantage survive held-out chronological testing and negative controls?

This is an implementation hypothesis, not a claim that mathematical paths establish real semantic connections or model human feelings. P2's conventional portal tree lost to random forest; P3 tests a genuinely different transition mechanism.

## Observed dataset and forecast

- The packaged `statsmodels.datasets.elnino` series: 61 years x 12 monthly mean sea-surface temperatures in degrees Celsius, Jan 1950 through Dec 2010, NOAA ERSST.v3b Niño 1+2 region. This is an existing historical research dataset, not a current NOAA feed.
- Task: for each observable month `t`, forecast binary event `E[t] = 1[T[t+3] - T[t] >= 0.5°C]` where `T` is monthly sea-surface temperature. Do not label this event an official El Niño declaration.
- Available feature information at issue time: current and preceding 12 monthly values only; all features computed from this history plus the month index.
- The data are retrospective and may have been revised since original release; therefore this is **not a real-time point-in-time vintage** experiment.
- Source snapshot: CSV captured from locally installed statsmodels package and SHA-256 recorded before scoring. No network download required.

## Chronological split and contamination controls

- Training rows: `target_date <= 1984-12-01` (issue may be no later than Sep 1984).
- Validation: `1985-01-01 <= issue_date` and `target_date <= 1996-12-01`.
- **Final sealed holdout:** `1997-01-01 <= issue_date` and `target_date <= 2010-12-01`.
- Discard any incomplete histories; exclude boundary rows whose 3-month target crosses split boundaries. Initial rows require at least 12 months of history.
- Training+validation may be combined for a single final refit using validation-locked configurations. No re-tuning after opening holdout outcomes.
- Source code must provide `validate` and `evaluate` stages; `validate` must compute no holdout outcome metrics, hashes or target labels from test data. It may count eligible test issue dates without reading their outcomes.
- Record exact source, protocol and code hashes with locked model selections before evaluation; reruns do not overwrite the first published predictions.

## Models

### Primary proposed operator: stochastic conditional portals (SCP)

At state `s_t` containing the last 13 temperatures and the calendar month, compute a local coordinate `x_t` consisting of current T, one-/three-/six-/twelve-month changes, acceleration, six-month increment volatility, and sin/cos calendar phase. A portal from `s_t` is a kernel-weighted sampling of a **training-observed next-month temperature increment** from analogous states. The transition creates `s_{t+1}` by appending that increment and removing the oldest observation; recompute *all* coordinates before the next jump. Apply three sequential portals to sample possible 3-month futures. Predict the fraction meeting the predeclared event threshold. This is a path-dependent generative model, not the P2 local-logistic tree. It approximates a conditional empirical transition kernel; it does not infer an actual portal in the brain or atmosphere.

- Standardize inputs with training-only means/standard deviations; use Euclidean distance in the 9-feature local state.
- Grid: nearest neighbors `k = {16, 32, 64}` and distance temperature `tau = {0.5, 1.5}`. Use normalized weights `exp(-(d - d_min)/tau)` within retrieved neighbor set.
- 256 particles per origin; deterministic seeds determined by source seed `20261103`, candidate index, issue index and stage. No per-output retry.
- Smoothed forecast `(count + 0.5)/(257)` to avoid exact 0 or 1 probability. No mixing with post-hoc baselines.
- Depth for task exactly **three**; a separate 100-step stress test is diagnostic only, not part of the forecasting score.

### Controls and baselines

- Constant prevalence forecast learned from training.
- Calendar-only regularized logistic regression (month sine/cosine).
- Full-feature regularized logistic regression, C in `{0.1,1.0,10.0}`.
- Random forest, 200 trees, minimum leaf `{5,20}`.
- Histogram gradient boosting, max leaf nodes `{7,15}`, max 160 iters, learning rate .05.
- Direct analog 3-month outcome estimator, k `{16,32,64}` and tau `{0.5,1.5}`, same local features and kernel weights as SCP; it conditions directly on observed 3-month outcomes rather than recursively generating futures.
- **Ablation 1:** frozen-frame SCP - reuse root-state candidate neighbor distribution across each of the three hops without recomputing local coordinate; same particle budget.
- **Negative control 2:** shuffle one-step training increments *within calendar-month groups*, preserving rough seasonality but disconnecting local state and next-step change; refit SCP kernel using these perturbed transitions.

Choose each baseline's grid winner using validation Brier score only. Choose SCP (k,tau) by validation Brier. Freeze the complete selection and its file hashes before final holdout evaluation. Comparison of SCP against the single best **validation-selected** conventional method (among full logistic, random forest, gradient booster, direct analog) is primary; full held-out method rankings descriptive. No after-the-fact feature changes.

## Primary metric and interpretation

- Primary: held-out Brier score `mean((p-y)^2)` on eligible 1997-2010 issue months.
- Secondary: log-loss, ROC-AUC, accuracy at 0.5, 10-bin expected calibration error, predictive latency and fit time, per-year variation.
- Paired year-cluster bootstrap: 5,000 resamples of whole issue-year blocks, fixed seed `20261104`, for `SCP Brier - validation-selected baseline Brier`. Positive means portals worse; negative means better. Bootstrap is exploratory.
- Report all method failures, incomplete rows, runtime, selected hyperparams, actual realized recursion, possible out-of-distribution drift and any calibration issues.
- Report quality of backwards conditional explanation using simulated first-step delta distribution given the event. This is an *inferential diagnostic* not causal identification.
- 100-depth paths only to measure divergence/instability; they are not 100-month validated forecasts and should not be used for policy.
- The `F in [0,1]` valence coordinate is *not measured* by this dataset and **must not** be fabricated.

## Outcome-neutral stop rule

After one frozen selection and a single holdout pass, stop. Publish positive, negative or null outcomes equally. Do not use test outcomes to revise the methodology. Separate any subsequent repair/follow-up study with a new version and holdout dataset.