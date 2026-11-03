# SRDE-P1: Blind-world 100-level portal prediction experiment

**Preregistration freeze target:** 2026-11-03, before test-world execution.  
**Project:** SRDE / Blackbird Intelligence / Proto Alpha.  
**Concept originator:** Dan Merluse. **Implementation and critical controls:** AI-assisted.  
**Status at preregistration:** Methods fixed, primary/secondary outcomes not yet observed.

## Purpose and falsifiable hypotheses

Assess whether SRDE-style conditional local coordinate-frame transitions (*portals*) yield useful **forward probabilistic predictions** and **backward probabilistic inference** on previously unseen stochastic synthetic worlds, compared with conventional graph algorithms given the **same transition information**. This is an experiment on computational structures, *not* on real-life future events, human feelings, neuroscience, or general semantic understanding.

- **H1 (strict and primary):** Portal inference improves average forward Brier loss versus an information-matched, state-aware graph sum-product baseline across held-out worlds. Primary contrast: `Brier(portal) - Brier(state_graph)`, world-clustered 95% bootstrap percentile interval. Negative is better for SRDE. A tie is a null result.
- **H2 (secondary):** Context/geometry-aware inference improves Brier loss over an intentionally state-blind graph approximation. This is an ablation, *not* a claim of superiority over strong graph models.
- **H3 (secondary):** Backward Bayes inference of an earlier latent root from an observed later event is calibrated and does not simply interpret reversed reachability as causal evidence.
- **H4 (negative control):** Independently generated outcomes and shuffled/mismatched portal paths do not show reliable predictive advantage; random path existence must not be treated as evidence.

## Frozen workload and split

- Independent held-out synthetic worlds = **72**, with world id and RNG derived from master seed `2026110301`; **48 trials per world** = **3,456** forward event cases. No fitting or retuning on held-out worlds.
- Three routes per case, each **100 local-frame transitions**; per-transition bit-preservation probability from `[0.985, 0.995, 0.999]`, balanced as 24 worlds per setting.
- Event is the majority of three branch terminal bits with independent event flip probability `0.04`.
- `R ~ Bernoulli(0.5)` is a known starting condition in forward prediction, but unobserved in backward reconstruction. Coordinates `(x,y,z)` are discrete local-frame variables; orientation, binary context, synthetic valence `F in [0,1]` and synthetic arousal `A in [0,1]` alter transitions. These **synthetic scalar variables are not measurements of human emotion**.
- Transition tables are freshly generated per world; world generator specifies a gated state-dependent stochastic process, not naturally occurring relations. All methods get identical rule tables, q and input state. Semantic labels, relevance, human meaning and real causal structure are **not** assessed.
- A separate development/sanity stream seeded `2026110300` is for invariants and no outcome-based method selection.

## Predeclared methods

1. `srde_portal`: scalar Bernoulli probability propagated through conditional local-frame gates, including state/valence changes.
2. `state_graph`: explicit two-state factor graph / sum-product recursion using **the same gates, inputs and transition probabilities**. This is a strong competitor capable of equivalent exact inference. Reaching a tie is expected on mathematical grounds; there is no exclusivity claim.
3. `state_blind_graph`: same stochastic propagation but deletes the state-dependent gate flip, illustrating the effect of losing portal conditions.
4. `constant_0_5`: no-evidence forecast.
5. `shuffled_world`: mismatched transition rules from a separate world of the same q stratum, to expose spurious long-range matches.
6. `provenance_null`: for independent outcomes with no authentic causal link, report `0.5` despite arbitrarily drawable paths.

## Primary scoring and audit

- Store every test-world/trial-level forecast, observed event, true root and expected backward posterior. No rejecting difficult failures; no retries based on labels.
- Forward: Brier score (primary), log loss, threshold accuracy, Brier skill against 0.25, ECE in five fixed bins; report by q and world.
- Backward: compute `P(R=1|E)` from `P(E|R=0)` and `P(E|R=1)` under `P(R=1)=0.5` using Bayes; score Brier and log loss for root reconstruction.
- World-clustered paired nonparametric bootstrap with **5,000** resamples, RNG seed `2026110399`; units are the 72 independent worlds, not repeated queries. Report CI for H1 and H2. No significance inference from individual cases as independent worlds.
- Runtime: measured CPU wall-clock durations per method, including per-query gate calculations but excluding data generation, with hardware/software logged. Timings are descriptive and may vary with execution order and Python overhead; no fair GPU comparison or optimized graph implementation claimed.
- Control: independent synthetic null events must not be scored as true because a graph happens to contain a path. Report `Brier` for erroneous predictions applied to null outcomes versus provenance-correct `0.5`.
- State sensitivity: compare model outputs at F=0 and F=1 under identical other inputs; changes verify implemented conditionality only, *not psychology*.

## Safety and interpretation rules

The synthetic simulator *knows its own generative transitions*, hence exact inference can succeed. That is not "predicting the future" in an unknown world. An information-equivalent graph algorithm can match portal inference. Any advantage over a state-blind ablation arises from supplied state information, not demonstrated mathematical novelty. Unseen = generated independently of calibration/development seeds, **not an external observational dataset**. Results are exploratory for architecture verification and are not proof of causation, self-awareness, emotion, supernatural precognition, or general reasoning improvement. Release all negative results and code, don't reclassify nulls post hoc.

## Relevant pre-existing methods

- Kschischang, Frey & Loeliger (2001), factor graphs / sum-product: https://doi.org/10.1109/18.910572
- Gastinger et al. (2024), simple temporal graph forecasting baselines: https://doi.org/10.24963/ijcai.2024/444
- Gastinger et al. (2024), TGB 2.0 benchmark protocol: https://proceedings.neurips.cc/paper_files/paper/2024/hash/fda026cf2423a01fcbcf1e1e43ee9a50-Abstract-Datasets_and_Benchmarks_Track.html
- Pearl (2010), causal inference and the difference between association and intervention: https://escholarship.org/uc/item/1sv6k47m