# SRDE-P6 — Path-Dependent Checkpoint Selection for Noisy Portal Reconstruction

**Frozen design dated 2026-11-03.** Concept originator: Dan Merluse (Blackbird Intelligence / Proto Alpha); mathematical formalization, code and critical tests AI-assisted. **Status at signing:** pre-evaluation hypothesis; no held-out P6 worlds scored yet. CPU-only, simulated geometry and processes; no human brain/feeling observations or real-world forecasting.

## Prior-simulation overlap gate

Reviewed project evidence: portal hypothesis, P1–P5, internal E01–E04, hidden lineage, learned temporal evidence, delayed-feedback results, E30, and the existing 18-primary-study novelty audit. P5 already established an affine order residual and severe inverse noise amplification after 100 levels. P1–P4 studied graph inference or state-conditioned forecasting; local E studies examine testimony/lineage and temporal reliability. **None of the inspected completed experiments evaluated information-matched placement of a fixed number of noisy 3D intermediate-state checkpoints to reconstruct an entire 100-step hidden path.** E28's complete primary archive remains unverified and the internal corpus audit is not exhaustive.

Published prior art includes Revolve/Griewank-Walther (2000, optimal reverse-computation checkpointing), Tzoumas et al. (2017, sensor activation for stochastic path state estimation), and Mei-Brunton-Kutz (2024, Kalman-informed limited sensing). Checkpoint selection, Kalman smoothing and greedy posterior-variance minimization are **established concepts**. P6 tests an SRDE-specific engineering combination, **not** an assertion of global novelty, a new mathematical theorem or method superiority.

## Question

Does an SRDE-specific **portal geometry + priority + process-risk** checkpoint scheduler improve reconstruction of noisy, noncommuting 100-level histories over equal-budget uniform, random, priority-only and process-risk-only schedules, and how close is it to a strong conventional posterior-covariance greedy scheduler that sees all the same metadata?

## Frozen generator

- Independent 3D Gaussian latent trajectories, one hundred transitions. `x_0 ~ Normal(0,I3)` and `x_t = A_t x_{t-1} + b_t + e_t`, `e_t ~ Normal(0,Q_t)`.
- `A_t` is a generated rotation of an anisotropic contracting diagonal operator. Rotation order and local branch history may not commute. `Q_t` is positive-definite; state-independent uncertainty is intentionally known to *all* selection policies, preventing an oracle-only portal advantage. `b_t` and priors are known to every method.
- Four scenarios: steady noise; episodic high-noise bursts; orientation-rich frame transitions; misleading high-priority decoys. Query-priority weights `w_t` are metadata-known, fixed before outcomes and unrelated to subjective feeling. No scenario ID is given as a predictor feature beyond the observable `A,Q,w` metadata.
- 100 levels, 3 axes, eight *paid* checkpoints among times `1..99`; a noisy terminal observation at `t=100` is free for everyone. Each paid state observation `z_t=x_t+Normal(0,0.04 I3)`; identical fixed observation noise for all policies. Every method reconstructs the full trajectory with the **same exact linear-Gaussian posterior** (Kalman-equivalent smoothing); only selected checkpoint times differ.
- No candidate sees true latent `x`, innovations or checkpoint measurement values before selecting times. Even the offline greedy planner is allowed only the known covariance model and future metadata, never realized outcomes. It is a strong-information comparator, not an exact global optimum.

## Policies and budgets

1. Evenly spaced: eight fixed times.
2. Random: eight fixed pseudorandom times using a separate schedule seed.
3. Priority-only quantile scheduler: allocates slots to the cumulative priority mass `w_t`.
4. Risk-only quantile scheduler: allocates slots to cumulative known transition process risk `trace(Q_t)`.
5. `SRDE_hybrid`: quantile schedule of `trace(Q_t) + eta * normalized(w_t) + gamma * normalized([A_t,A_(t-1)]_F)` with parameters selected on **development worlds only**. This scheduler is offline with metadata known but receives no realizations; it is not described as online learning.
6. Conventional greedy posterior-covariance scheduler: sequentially adds the observation time giving the largest marginal reduction in the **same weighted exact posterior trajectory trace**. It uses the entire known planning horizon and carries substantially more CPU cost. It is a strong conventional reference, not an oracle of hidden trajectories.

At most eight distinct paid checkpoints; no candidate receives more state observations than another. No checkpoint is silently treated as exact or noise-free. The conventional greedy has more computation, which must be reported.

## Model selection, holdout and metrics

- Fixed seed family: development seeds `960100..960147` (12 independent worlds per scenario) and untouched test seeds `970100..970259` (40 per scenario). No generator parameter or model selection change after the first test score.
- Tune `eta in {0,0.5,1,2}`, `gamma in {0,0.5,1}` on development worlds with the weighted conditional posterior trace. Tie break smallest eta then gamma. Keep process coefficient 1.0 and normalize all risk terms on *the same world's available public metadata*. Other policies have no tuned parameters.
- Primary metric: weighted expected posterior MSE per state-axis over levels 1..99, exact for the specified Gaussian generator; **lower is better**. Weight `w_t` is shared with all methods, so priority-only and conventional greedy have identical evaluation information.
- Primary contrast: `SRDE_hybrid` minus evenly spaced and minus **conventional greedy**, on all 160 independent held-out geometries. Also report by scenario, budget adherence, exact root uncertainty, and both weighted and unweighted risk.
- Negative controls: permute observed priority labels independently of Q/frames and re-score (no re-tuning); zero-out geometry contribution; stable/decoy worlds. No new hidden-event or human affect claims.
- Bootstrap confidence intervals: whole-world resampling of paired loss differences with 5,000 fixed-seed draws. Retain all losses, including ties and negative outcomes. Correlated real draws within one model geometry are not falsely treated as independent for primary inference.
- Additional empirical reconstruction audit: on **twelve** preselected test geometries with **twenty** independently seeded trajectory+measurement draws each, form the Gaussian posterior mean from the checkpoints and compute actual weighted squared error. Compare with expected risk; do not use those draws to alter policy settings.
- Stress: checkpoint budgets `K=4, 8, 16` as descriptive controls on the same test geometries; primary is K=8. No 100-step *prediction* claim: these are retrospective reconstruction experiments.

## Stopping, novelty and integrity

If the hybrid ties or loses to a conventional model, classify as negative/equivalence and retain. Improvement over uniform alone is not uniqueness. Audit independent recalculation of file hashes, exact budget, per-world records, policy coverage, and risk values. Public preregistration plus exact frozen code/source digest **precede** the holdout. No Colab or NVIDIA/Arc GPU use, no native FACO application modifications. Publish report, source, per-world data, failure records and checksums to Blackbird Knowledge Repository and public GitHub, with explicit caveats.

**Nearest methods:** Griewank & Walther, ACM TOMS 2000 https://doi.org/10.1145/347837.347846 ; Tzoumas et al., ACC 2017 https://doi.org/10.23919/ACC.2017.7963015 ; Mei et al., Sensors 2024 https://doi.org/10.3390/s24123727 .
