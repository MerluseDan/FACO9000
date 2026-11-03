# SRDE-P3: Recursive Conditional Portals on Real Ocean State Transitions

**Blackbird Intelligence / Proto Alpha | 3 November 2026**  
**Originator:** Dan Merluse | **Status:** First sealed holdout complete, report recovered after serialization failure  
**Study:** Historical NOAA Niño 1+2 region monthly sea-surface temperatures, 1950-2010, as packaged in `statsmodels.datasets.elnino` (ERSST.v3b).

## Abstract

We tested a new state-conditional generative portal operator: each portal samples one next-month temperature change from training analogs, updates a full 13-month local state, repositions in a 9-dimensional local feature space, then opens the next portal. Three recursive transitions generate 256 possible futures per forecast. We predicted whether temperature three months ahead would exceed the present temperature by **at least 0.5 °C**. This is not an official El Niño declaration, nor does it test mental feelings or future prediction beyond physical statistical forecasting.

405 training cases (through Dec 1984 target), 141 validation cases (1985-1996) and 165 sealed holdout cases (1997-Sep 2010 issue date) were used. Models were selected strictly on validation Brier error. The holdout was scored once. Its prediction CSV was saved before the original JSON writer failed on NumPy integer serialization; a separately documented recovery recomputed metrics from that saved CSV without rerunning or changing forecasts. Independent audits recomputed all outcomes from the original dataset and matched the saved result.

## Primary held-out conclusion

Portal Brier **0.04916949**, versus validation-selected random forest Brier **0.05209970**, a portal-minus-forest difference of **-0.00293021**. Paired year-block 95% exploratory bootstrap interval: **[-0.00954158, +0.00351189]**, based on 14 annual clusters. The interval crosses zero; **there is no confirmed predictive advantage**.

The surprising result is the within-calendar-month delta-shuffle control: its Brier **0.04610253** is *better* than the original portal network. Destroying the original local-state→transition correspondence did not destroy forecasting ability. That is a serious negative control against interpreting the observed forecast skill as evidence that the proposed state-dependent relationships are necessary. Seasonality and transition-distribution structure offer alternative explanations.

At the same time, freezing the initial coordinate frame for all three hops increased Brier error to **0.11406915**. Re-centering matters *for this implementation*, without establishing universal superiority of recursive portals over conventional algorithms.

## Predeclared design

- Observations: 732 monthly measurements, historical NOAA sea-surface temperature data, 1950-2010.
- Event: `1[T(t+3) - T(t) >= 0.5 °C]`. Inputs: the current and preceding 12 months, plus calendar month.
- **Recursive operator:** `K(Δ|s)=Σ_j w_j(s) δ(Δ-Δ_j)`, where `w_j` are normalized exponential kernel weights for training nearest-neighbor state analogs. After each drawn Δ, the history shifts and all local coordinates are recalculated.
- 256 deterministic particles per forecast, 3 transitions per particle; model selection `k in {16,32,64}`, kernel temperature `tau in {0.5,1.5}`. Validation selected **k=32**, **tau=0.5**.
- Baselines: constant, calendar logistic, full regularized logistic, random forest, gradient booster, direct single-hop analog; same observed history and validation period.
- Primary comparator: best validation-selected *conventional* method among full logistic, forest, boost, direct analog. Selected comparator: **random_forest**. The calendar-only predictor is also reported separately.
- Metrics: Brier (primary), log loss, AUC, accuracy, 10-bin ECE, and runtime (held-out metrics recovered from saved predictions; model-specific runtime preserved in evaluation stdout but not in the recovered results JSON).
- Negative controls: frozen root coordinate frame; shuffle training next-month increments within calendar months before recursive simulation.

## Complete held-out results

| Method | Brier ↓ | AUC | Accuracy @ 0.5 |
|---|---:|---:|---:|
| constant | 0.24384449 | 0.50000 | 0.58182 |
| calendar_logistic | 0.05077380 | 0.97917 | 0.91515 |
| logistic | 0.04957310 | 0.98641 | 0.93939 |
| random_forest | 0.05209970 | 0.98098 | 0.92727 |
| hist_boost | 0.06842365 | 0.97705 | 0.89697 |
| direct_analog | 0.05293024 | 0.98354 | 0.92121 |
| recursive_portal | 0.04916949 | 0.98619 | 0.92121 |
| frozen_local_coordinate_frame | 0.11406915 | 0.93229 | 0.84848 |
| within_month_shuffled_training_deltas | 0.04610253 | 0.98777 | 0.92121 |

## One-step, three-step, and 100-step interpretations

Only **three** recursive portal transitions were scored against future observed outcomes. The 100-step extension is solely a stability/possible drift diagnostic. After 100 simulated steps, the three seeded starting states had out-of-historical-range path fractions **2.7%, 4.3%, 1.6%**; this is not a 100-month forecast accuracy measurement. The backwards conditional diagnostic estimates the first simulated temperature step conditioned on a simulated 3-step event versus its complement. That is an association, *not an inference of an observed cause*.

## Execution integrity and unexpected failure

- Public GitHub preregistration was committed before validation scoring.
- A single validation selected configurations using only outcomes through 1996. The holdout data were not scored during model selection. Only 1997-2010 outcomes were used in the sealed final pass.
- One held-out evaluation computed all forecasts and negative-control forecasts, then wrote `test_predictions.csv`. The final `json.dumps` of a report containing NumPy 64-bit integer years raised a TypeError **after** the predictions had been saved. The original script and sealed hash remain unmodified.
- `recover_audit_p3.py` reconstructed the report from the saved 165-row prediction CSV without any model re-fit or forecast replay. `audit_independent.py` recomputed historical outcome labels and all saved Brier scores without importing the model's metric function; both audits passed.
- Predeclared 100-step and reverse diagnostics were separately reconstructed using the frozen kernel parameters; those reconstructions cannot be treated as a second independent holdout.
- Source SHA-256: `83a3d6e1dd55a01ad4659a449edca1512b6b16d993ef5ed886be56931e99ea7f`.
- Preregistered protocol SHA-256: `d8a6b1094da6378a3c5cc9d95f5febd2a14dc668c8b2f07cea82c368da3a932f`.
- Frozen model-code SHA-256: `6562ba9d7a9ecbca8ae70c51d4dec97680a47197e1b22a8c660c035df1c66d5b`.
- Original saved predictions SHA-256: `be37f11329bde7e9279d4eb5102df44c746ac5e5a09243b4e5e6df59c931bc2a`.

## Interpretation, limitations, and next experiment

This experiment does **not** show that a distant semantic relationship is objectively true, that meaning exists beyond physical models, that human subconscious processing equals GPT, or that feelings `F ∈ [0,1]` were measured. The real dataset is a retrospective archived climate series, not an operational ENSO forecast, and may differ from data available at historical issue times. Overlapping three-month targets cause dependence; the bootstrap uses 14 whole-year blocks, which is still a small sampling unit. A near-neighbor generator may underrepresent rare extreme jumps. The within-month shuffle signal cautions against overinterpreting apparent portal skill.

**Recommended next test:** separate seasonal effects from genuine state-conditioning. Evaluate a seasonally matched direct generative baseline and state-perturbed portal operator on a second independently sourced domain; pre-register an outcome that specifically rewards causal state transition tracking, while treating causality as unproven absent appropriate interventions. Preserve P1/P2/P3 negative evidence.

## Provenance and references

- Source metadata: statsmodels elnino `data.py`, "El Nino - Sea Surface Temperatures" (NOAA ERSST.v3b, Niño 1+2): https://github.com/statsmodels/statsmodels/blob/main/statsmodels/datasets/elnino/data.py
- NOAA ENSO and SST background: https://psl.noaa.gov/enso/data.html
- Scoring: Brier (1950) probability forecasts; paired year-clustered bootstrap. All historical data, samples, scores, model code and checkpoints included in archive.
- Conceptual credit: Dan Merluse (SRDE/Blackbird Intelligence); design, implementation and independent auditing with AI assistance. This is exploratory research, not peer-reviewed validation.
