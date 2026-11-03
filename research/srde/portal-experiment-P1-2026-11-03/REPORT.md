# SRDE-P1 — 100-level portal forecasting: first blind-world controlled benchmark

**Execution date:** 3 November 2026 (UTC run 2026-11-03T13:38:25.810668+00:00)  
**Concept originator:** Dan Merluse | **Project:** Blackbird Intelligence / Proto Alpha | **AI-assisted formalization, code and verification**  
**Status:** Synthetic computer experiment completed, output audit PASS. This report is **not** a peer-reviewed result or a demonstration of real-world prediction.  
**Preregistration:** [GitHub commit 48c34c7](https://github.com/MerluseDan/FACO9000/commit/48c34c733f276ca6e4e836cf3525edf225188a8d). Frozen before this run; outcome analysis follows the declared comparison.

## Executive result

**72 independently generated held-out worlds; 48 trials per world; 3,456 predictions; three independent paths of 100 local-frame transitions per case.** CPU only; no GPU access. Synthetic valence and arousal (normalized 0–1) influence which conditional gate applies at each level. The output is a future *simulated* binary event with noise.

**Primary hypothesis H1 failed to show SRDE superiority:** portal recursion and the equally informed state-aware probabilistic graph achieved exactly the same **Brier score 0.20037**, with difference -0.00000 (world-bootstrap 95% CI -0.00000 to +0.00000). This tie is expected: state-explicit factor graphs can exactly represent the same stochastic transitions. The proposed portals are a useful **representation**, not evidence of a mathematically superior predictor.

**Secondary H2 supported only against a deliberately weaker state-blind ablation:** portal Brier 0.20037 vs state-blind 0.34021; Δ -0.13984 (world-bootstrap 95% CI -0.17337 to -0.10756). The gain comes from using state-dependent gate information the ablation omits, not from inventing otherwise unavailable information. An uninformed forecast scores 0.25 Brier.

## Quantitative results

Brier (primary, lower better), log loss (lower better), threshold accuracy (higher better). CPU median durations cover two root-conditional forecasts and are descriptive, not optimized-system benchmarks.

| Method | Forward Brier | Accuracy | Log loss | Backward Brier | Median CPU ms |
|---|---:|---:|---:|---:|---:|
| srde_portal | 0.20037 | 66.26% | 0.58244 | 0.20037 | 1.207 |
| state_graph | 0.20037 | 66.26% | 0.58244 | 0.20037 | 1.266 |
| state_blind_graph | 0.34021 | 49.10% | 0.99915 | 0.34021 | 0.004 |
| constant_0_5 | 0.25000 | 49.97% | 0.69315 | 0.25000 | 0.000 |
| shuffled_world | 0.29530 | 51.01% | 0.82743 | 0.29530 | 1.203 |

**By independent-world transition reliability (q):**

| q per transition | Cases | Portal Brier | Strong graph Brier | State-blind Brier | 0.5 Brier |
|---:|---:|---:|---:|---:|---:|
| 0.985 | 1,152 | 0.25091 | 0.25091 | 0.25073 | 0.25000 |
| 0.995 | 1,152 | 0.22951 | 0.22951 | 0.31911 | 0.25000 |
| 0.999 | 1,152 | 0.12069 | 0.12069 | 0.45080 | 0.25000 |

At q=0.985, the portal scored 0.25091, slightly **worse than uninformed 0.25** on this finite sample. At q=0.999, it scored 0.12069, versus the uninformed 0.25. Deep noisy pathways can destroy information. We preserve the weak stratum rather than hiding it.

### Backward inference

After observing a later event E, both portal and graph compute `P(root=1 | E)` using Bayes' rule and balanced root priors. Their backward root Brier scores were both 0.20037. This is an exact inference capability *given the true transition model*, not proof that reversing a path identifies real causes.

### Negative controls and feeling-state inputs

- Shuffled/mismatched portal rules (same q group) scored Brier 0.29530; portal vs shuffled Δ -0.09493 (world-bootstrap 95% CI -0.12129 to -0.06849). A visually plausible long path using the wrong gates damages forecasts.
- Predictions improperly applied to **independent unrelated events** scored 0.29422; refusing to infer from a nonexistent provenance link and reporting 0.5 scored **0.25000**. Mere reachability is not evidential support.
- In 72 matched synthetic state interventions, moving the input's numeric valence F from 0 to 1 changed predictions by mean absolute 0.21057; nonzero in 75.0% of worlds. This confirms the code uses the F coordinate; it is **not** an empirical claim about human feelings, psychology, or survival.

## What the simulator actually does

A case begins at a local `(x,y,z)` coordinate, orientation, synthetic valence F, synthetic arousal A and context. Each portal level selects a conditional binary gate based on those inputs, then moves into a new local coordinate frame; the recursion index is independent of z. Three 100-level stochastic paths feed an event majority vote, followed by event noise. The true transition rules and reliability q are shared by all methods. SRDE uses scalar Bernoulli recursion. The state-aware graph uses a full two-state sum-product table and obtains the same distribution. The state-blind baseline discards each local gate's state-dependent flip, intentionally reducing its information. No model is fitted using outcomes from the 72 held-out worlds.

Input geometry and valence are **engineered synthetic variables**. These worlds are held out from the development/smoke seed but are drawn from the **same synthetic process** as the experimental code. They are not independently collected temporal records of human actions, cognition or natural events. The simulator's causal structure is known *by design*; forecasting an event generated by that simulator is not discovering future events from reality.

## Audit and provenance

- Preregistration SHA-256: `7a5525cc61d571208eb69de057e4bb2e93502990722d04c774ea2bd4d1f5d5e3`
- Frozen executed script SHA-256: `be682e35aac8f02a54d821fa7d84a1f279c009c9d87af47cbc40c80f790065d0`
- Per-trial predictions SHA-256: `1dca1fd6ee732e8cba6c782ee4643db65dd6479b749fd7d526cb8448f49718cd`
- Summary SHA-256: `00258de0be0cdace5bd489c6e931c78830b201ad3e1a110d420c6c95763ba279`
- Independent output regrader/audit: **PASS**, all 3456 case IDs unique, all 72 worlds balanced, all probabilities in range, portal and graph agree to <1e-11, all aggregate metrics independently recomputed.
- Local execution: 3.13.5 Python; standard library only; CPU; run wall time 18.80 seconds (reported by `/usr/bin/time` in execution log; includes generating and scoring); peak RSS 113,416 KiB (single run). Timings will vary across environments.
- Uncorrected report of every observed result; no post-hoc change to holdout seeds, q strata, number of worlds, or method list. The code's smoke tests used a disjoint seed and tested mathematical invariants, not heldout outcomes.

## Decisions and next experiment

**Do not conclude** that SRDE surpasses graph computation: on this fixed finite-state model, it does not. The representation can match exact probabilistic inference and can require the model to track conditional coordinates/valence, but a state-aware graph can encode the identical information. The next high-value step is a **real timestamped external event dataset with withheld future outcomes**, strong time-aware graph/factor-graph and simple seasonal/repetition baselines, limited compute, realistic provenance, predeclared Brier/calibration and separate negative controls. This stage is **not yet executed** by P1. Also, before claiming any architectural efficiency, compare against optimized conventional graph implementations with identical preprocessing costs; the small CPU runtime difference here is not evidence.

## Nearby research

- Kschischang, Frey & Loeliger (2001): [Factor graphs and sum-product](https://doi.org/10.1109/18.910572)
- Gastinger et al. (2024): [History Repeats Itself: Temporal Graph Forecasting Baseline](https://doi.org/10.24963/ijcai.2024/444)
- Gastinger et al. (2024): [Temporal Graph Benchmark 2.0](https://proceedings.neurips.cc/paper_files/paper/2024/hash/fda026cf2423a01fcbcf1e1e43ee9a50-Abstract-Datasets_and_Benchmarks_Track.html)
- Pearl (2010): [Causal inference](https://escholarship.org/uc/item/1sv6k47m)

## Files for verification

`PREREGISTRATION.md`, `srde_portal_p1.py` (frozen experiment runner), `summary.json`, `heldout_predictions.jsonl` (all 3,456 raw row-level predictions and events), `audit_p1.py` (separate output regrader), `audit_p1.json` (audit outcome and pre-audit SHA registry), `execution_stdout.log`, `LOCKED_INPUT_SHA256.txt`, `OUTPUT_SHA256.txt`, and this report. All code is standard-library Python 3.10+ and rerunnable with `python srde_portal_p1.py --outdir .` in a fresh directory (using the same script and seeds). The code writes new local outputs, not Google Drive files.
