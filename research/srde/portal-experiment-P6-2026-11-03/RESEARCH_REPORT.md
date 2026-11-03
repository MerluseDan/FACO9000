# SRDE-P6: Portal Checkpoints, Partial Memory, and 100-Level Reconstruction

**Blackbird Intelligence / Proto Alpha | 3 November 2026 | Original SRDE exploratory research**

**Concept:** Dan Merluse. **Research execution:** AI-assisted mathematical formalization, simulation, independent auditing, reporting. **Status:** Completed CPU-only synthetic experiment; *not a new theorem or a demonstrated cognition model*.

## Executive finding

After examining prior SRDE simulations and checkpointing literature, we tested whether a fixed budget of eight intermediate snapshots could recover noisy hidden states along 100 locally rotated, noncommuting 3D portal transitions. Every method received exactly the same Gaussian state/noise model and free terminal observation. Parameters were frozen on 48 development worlds before 160 independent held-out worlds were scored.

**The proposed SRDE geometry and priority additions were not selected by validation** (`eta=0`, `gamma=0`). Thus the final SRDE hybrid is exactly the conventional risk-only quantile scheduler, on all held-out worlds and checkpoint budgets. It improves average weighted posterior error over uniform checkpoints but does not provide unique algorithmic capability. A stronger conventional posterior-covariance greedy scheduler is substantially better.

## Primary results: held-out K=8

| Method | Weighted expected MSE / coordinate | Unweighted expected MSE |
|---|---:|---:|
| Covariance-greedy | 0.05579 | 0.05604 |
| SRDE / risk-only | 0.07339 | 0.07469 |
| Priority-only | 0.07343 | 0.07445 |
| Uniform | 0.07693 | 0.07171 |
| Random | 0.09002 | 0.08151 |

- SRDE/risk-only minus uniform: **-0.00354515**, 95% independent-world bootstrap CI **[-0.00479701, -0.00234706]**. This is a 4.61% mean reduction, not a win in every world.
- SRDE/risk-only minus conventional covariance-greedy: **+0.01759280**, CI **[+0.01650200, +0.01871402]**. Positive means SRDE is worse.
- SRDE/risk-only beats uniform in **44.375%** of individual test worlds despite better *average* error. This matters because gains are concentrated in a subset of difficult worlds.

![Scenario comparison](p6_scenario_errors.png)

## Where the improvement originates

| Scenario (40 unseen worlds each) | Uniform | SRDE/risk-only | Covariance-greedy | SRDE minus uniform |
|---|---:|---:|---:|---:|
| steady | 0.05745 | 0.05772 | 0.04472 | +0.00027 |
| bursts | 0.12732 | 0.11030 | 0.08194 | -0.01702 |
| frames | 0.07069 | 0.07313 | 0.05440 | +0.00245 |
| decoys | 0.05227 | 0.05240 | 0.04211 | +0.00013 |

**Only burst-noise worlds show a meaningful average benefit versus uniform spacing**. In steady, frame-change and priority-decoy worlds, SRDE/risk-only is slightly worse than uniform. This result does not justify promoting geometric weighting or its current parameters into a general SRDE rule.

## Memory scaling stress test (160 unseen worlds per budget)

| Paid checkpoints | Uniform | SRDE/risk-only | Priority-only | Covariance-greedy |
|---:|---:|---:|---:|---:|
| 4 | 0.11252 | 0.10385 | 0.10154 | **0.07821** |
| 8 | 0.07693 | 0.07339 | 0.07343 | **0.05579** |
| 16 | 0.05034 | 0.04891 | 0.04713 | **0.03983** |

![Memory scaling](p6_memory_scaling.png)

## Equations and exact-information comparator

The simulator evolves `x_t = A_t x_(t-1) + b_t + e_t`, with `e_t ~ Normal(0,Q_t)` and `x_0 ~ Normal(0,I_3)`. Every selected checkpoint observes `x_t + Normal(0,0.04 I_3)`; the noisy terminal observation is free. Noncommuting local rotations may affect the covariance, but all algorithms know the same `A_t,Q_t` matrices and task priority weights.

For stacked trajectory covariance `C`, selected observation-component indices `J` and observation noise variance `R`, the Gaussian posterior covariance is:

`C_post = C - C[:,J] @ inverse(C[J,J] + R I) @ C[J,:]`.

The predeclared outcome is `sum(w_t * trace(C_post[t,t])) / (3 * sum(w_t))` over `t=1..99`. Unlike a direct ill-conditioned 100-step inverse, this calculates a regularized conditional posterior. All checkpoint schedules use the *same* posterior mathematics. The conventional greedy planner selects the next slot to maximize its marginal expected posterior-error reduction, with additional offline computation. It is not asserted globally optimal.

## Checks, failure modes, and boundaries

- Pre-evaluation source and preregistration hashes locked on GitHub before test outcomes: source SHA-256 `5dbdb3bf3eadd8b2cfd53e0db8db2d722affa74a0d7901772e7eec7ba4689465`, protocol SHA-256 `3b580b981a73155ffa7f19e0be81364fc391d0571ad551e349312f09e254ac30`. The frozen validation record selected `(eta, gamma)=(0,0)` with no test-world scores.
- Independent audit: **PASS** for all 160 worlds, exact eight-slot budgets, all method averages and paired bootstraps. A separately written 3D Kalman/Rauch-Tung-Striebel smoother reproduced scores for eight selected worlds (all policies), maximum absolute residual **1.943e-16**.
- Independent stress audit: **PASS** for all 320 K=4/K=16 world rows, including 16 separate Kalman smoothing cross-checks, maximum residual **2.776e-16**.
- Monte Carlo check: twelve preselected held-out geometries times twenty trajectory/measurement draws each. Mean expected SRDE risk **0.057938** versus mean realized squared error **0.058043**; this is a synthetic model check, not external validation.
- **Failed/degenerate control:** permuting priority metadata leaves the final SRDE/risk-only schedule unchanged because validation selected `eta=0`. Consequently this control is *uninformative* about the importance of priority. It must not be cited as positive or negative evidence about emotional state.
- These are artificial Gaussian state spaces, not observed cognition, human feeling, survival, semantic coordinates, or future real-world events. The model knows exact process covariance. No claim of scientifically new mathematics or a practical SRDE advantage follows.

## Research decision

**Do not adopt the SRDE-P6 geometric/priority checkpoint mechanism as a validated new Blackbird capability.** Retain the negative validation and the conditional burst improvement. The useful engineering lesson is that a fixed memory budget helps recover partial histories, but a strong conventional estimator does it better under equal information. The next candidate should test whether a *compressed portal-order/provenance signature* preserves information that noisy state snapshots alone lose at equal bit budgets, only after checking the relevant coding, sufficient-statistic and event-log literature.

## Prior work / novelty boundary

- [Griewank & Walther (2000), Revolve checkpointing](https://doi.org/10.1145/347837.347846) - optimal reverse-computation checkpoint schedules exist.
- [Tzoumas et al. (2017), scheduling nonlinear sensors](https://doi.org/10.23919/ACC.2017.7963015) - budgeted stochastic trajectory sensing exists.
- [Mei, Brunton & Kutz (2024), mobile sensor path planning for Kalman spatiotemporal estimation](https://doi.org/10.3390/s24123727) - Kalman-informed limited sensing and optimal placement have prior work.
- [Existing Blackbird SRDE prior-simulation audit](https://drive.google.com/file/d/146kf39FmXtvNIehBUywDG1EBUkaQo5i9/view?usp=drivesdk) and [P5 original research](https://drive.google.com/drive/folders/1xOIEbLetVNGP4ayEenpqFic--EwLsdzo) - internal overlap check before P6.

Publication status: this report records a reproducible original *SRDE-specific test question* and its negative/conditional outcomes, **not** a peer-reviewed publication or novel theorem.
