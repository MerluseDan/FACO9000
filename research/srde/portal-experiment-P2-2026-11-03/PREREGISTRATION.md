# SRDE-P2 — Real-Observation, Next-Month Event Forecasting

**Protocol date:** 2026-11-03. **Project:** Blackbird Intelligence / Proto Alpha — SRDE.
**Status of this file:** preregistration frozen before the holdout forecast is evaluated. Concept by Dan Merluse; model design, testing and report are AI-assisted.

## Hypothesis and limits
On real weekly atmospheric CO2 observations from Mauna Loa (the fixed, locally packaged `statsmodels.datasets.co2` dataset, 1958–2001), a recursively state-conditioned **portal predictor** may achieve lower Brier score on later, completely held-out observations than a strong conventional benchmark. The null is a tie or loss. A *portal* here is a train-fitted conditional choice of a local coordinate subspace, implemented as a local probabilistic model tree; this is not a fundamentally novel mathematical primitive or a general test of cognition. No feeling/valence F, neural measurements, or human behavior occurs in this dataset.

## Prediction question
For every observation date `t`, use historical records available no later than `t` to predict the binary event `E_t = 1[CO2(t+4 weeks) > CO2(t)]`, where `t+4` means exactly four sampled weekly entries later. Drop a row if the target or any required lag is absent; do NOT impute outcomes. Use strictly causal features from `t` or earlier: sine/cosine annual position; differences CO2(t) - CO2(t - {1,4,8,13,26,52} weeks); and selected lag levels expressed as local deltas. Exclude raw absolute CO2 levels to mitigate secular trend drift. At inference t, no future date's values, labels or derived statistics may be used as inputs. Note that complete daily/weekly measurement values become available after acquisition; 'forecast issued at t' is a retrospective conceptual issuance, not an operational live forecast.

## Fixed chronological partitions / target isolation
- Training issues: dates in 1958–1988, **with target date <= 1988-12-31**.
- Model-selection validation issues: 1989–1994, **with target date <= 1994-12-31**.
- Frozen test issues: 1995–2001, **with target date <= 2001-12-31**.
- Choose hyperparameters solely by validation Brier score, then refit winning variants on training + validation rows and evaluate 1995–2001 exactly once.
- Report each sample's issue date and target date; confirm no overlap of target dates with evaluation years.

## Competitors and model selection
1. Constant base rate from the training label prevalence.
2. Season-only logistic regression on week-of-year sine/cosine, with `C=0.3`.
3. Full regularized logistic regression, `C ∈ {0.03,0.3,3}`.
4. Standard decision tree, `max_depth ∈ {2,4,6,100}`, minimum leaf 40.
5. Random forest, 200 trees, min leaf size in `{10,30,60}`, seed 20261103.
6. Histogram gradient boosting, 200 iterations, learning rate 0.05, leaf count in `{7,15,31}`, min_samples_leaf 20, L2 = 1.0, seed 20261103.
7. **SRDE portal model:** root regularized logistic model plus recursively gated local logistic submodels. The *three spatial coordinates* are annual sine, annual cosine, and recent 4-week CO2 change standardized on fitting data. A portal node splits at train-only quantiles {.30,.50,.70} along these coordinates if reduction in binary Gini impurity >= 0.005 and each child has >= 100 training rows. Local models are combined using deterministic support-aware shrinkage. Maximum allowed recursive depths `{1,3,6,100}`, shrinkage factors `{0.35,0.65}`; 8 hyperparameter combinations chosen on validation. The 100-level setting is a *cap*, not a claim that 100 layers are beneficial or actually traversed. Record actual fitted depth and number of nodes.

The portal method and the tree-based baselines receive exactly the same predictive features. Model families have different compute costs and small, unequal grid sizes; report training and inference time rather than calling them compute-matched. Model-selection search does not inspect the test split.

## Primary and secondary outcomes
Primary: mean squared probability error (Brier score), portal minus **best** conventional model (lowest test Brier among full logistic, decision tree, forest, gradient boosting), with the important caveat that selecting the comparator on test is a descriptive, not a prespecified pairwise inferential contrast. Also report portal minus **validation-selected gradient booster** as a prespecified strong comparator. Lower score is better. Provide year-block bootstrap descriptive 95% intervals (5000 draws, fixed seed 20261104) on portal-minus-booster paired Brier delta, keeping weeks within each year grouped. Secondary: accuracy at threshold 0.5, ROC AUC (if both classes present), log loss, calibration error with ten bins, and train/prediction timing. Preserve all per-date holdout forecasts.

## Controls, reversibility, and robustness
- Train-label-shuffle negative control for portal: permute **training+validation** outcome labels with seed 20261105, fit the same selected architecture, evaluate on unchanged test targets. We expect the negative control not to carry meaningful predictivity; no guarantee in any particular sample.
- Report observed percentage of positive outcomes in each split, and a simple 'constant' forecast.
- Backward inferential diagnostic, separate from forecasting: from a known *future event outcome*, estimate using training Bayes counts whether the *earlier* four-week trend was positive. Score on the test period, and call this retrospective probabilistic inference, not reverse causation or event forecasting.
- Test consistency assertions: no feature has positive-time index, date sorting, no target leakage across split boundaries, sum of holdout rows equals prediction count, all forecast probabilities finite in [0,1], and independent recomputation of Brier and accuracy.

## Scientific caveats and interpretation
- Results are one historic observational dataset with a known seasonal signal; not evidence of causality, universal mapping, human cognition, emotional valence, or future prediction beyond this specific time-series task.
- Autocorrelation reduces effective independent sample size; bootstrap groups by year and is descriptive with only seven held-out calendar years.
- Default `statsmodels` dataset is a fixed historical snapshot, not the most current NOAA station file. Cite its version and source. Data quality/revisions and historical measurement delays are limitations.
- All losses and null results are recorded without retries or post-hoc threshold changes. Negative experiment P1/E30 histories remain acknowledged and distinct.