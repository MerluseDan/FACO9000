# SRDE-P7: Compressed Ordered-Portal and Provenance Replay

**Date:** 2026-11-03. **Originating research direction:** Dan Merluse / Blackbird Intelligence. **Status at protocol freeze:** hypotheses and methods fixed; no P7 development, validation or holdout outcomes scored. **Methodological aid:** ChatGPT.

## Novelty gate and predecessor distinction

- SRDE-P5 established that noncommuting/ordered affine portal paths can preserve order effects after root memory decays, and that conventional order-aware calculations tie the SRDE representation.
- SRDE-P6 tested noisy state checkpoint placement across 100 levels; the proposed priority/orientation terms were selected as zero and the conventional covariance-greedy method won.
- Other completed SRDE E01–E04, E22–E30, provenance, hidden-lineage and delayed-feedback research are *not* re-run.
- **Prior art:** path signatures/iterated integrals (Hambly & Lyons 2010); POMDP belief sufficient statistics; rate-distortion memory optimization (e.g. PLOS Computational Biology 2020; related 2026 agent-memory work); forward sensitivity/automatic differentiation; streaming sketches. **Neither derivatives nor sufficient statistics nor order-sensitive signatures are claimed new.** The novel **SRDE-specific question**, not an alleged theorem, is whether a *fixed-bit sensitivity/provenance payload* is a useful, sharply bounded replay interface across different after-the-fact questions.

## Fixed research question

After an ordered, 100-step, 2D affine portal sequence has executed, the user may ask questions that were unknown to the encoder. With a per-world memory limit **B in {12,20,32,40} bytes**, evaluate:

1. Does a provenance-conditioned counterfactual sensitivity sketch retain sufficient information to answer *additive lineage reweighting* queries better than value-only snapshots, and under what budget? 
2. Can a first-order ordered-map derivative extend usefulness to *small structural portal changes*, and how does it fail when changes are large?
3. Does a conventional **information-matched sensitivity sketch** tie the SRDE implementation? Does a sufficiently large raw event log beat it for out-of-family changes?

## Generator and mathematical meaning

100 steps, portal type a_t in {0,1,2}, provenance p_t in {0,1}, both Markov-persistent but never held fixed across worlds. The globally public portal matrices A_a are strictly contracting and not all commute. Starting state x_0=(0,0). Each step is

x_(t+1) = A_(a_t) x_t + b_(a_t) + d_(p_t).

The public b,d,A and the distribution of a,p are available to **all** coders. The actual 100-step token history is NOT available at query time except to the extent encoded within B bytes. Two provenance sensitivities follow exactly:

J_(p,t+1) = A_(a_t) J_(p,t) + I[p_t=p] I_2.

The terminal response to additive source shifts Δ_p is exactly x_T + J_0 Δ_0 + J_1 Δ_1. Three additional 2D first derivatives D_a are propagated for infinitesimal left-rotation of A_a and used for small finite angle queries. They are only first-order approximations. This known mathematics is not claimed novel.

## Fixed payloads and fair competitors

All storage allocations are **exactly B bytes per world**, with deterministic padding when a codec uses fewer. Shared decoder parameters trained on development worlds are accessible to all and separately reported (not counted as per-world data); this is a model-memory limitation.

- **SRDE-P7 sensitivity sketch:** terminal x (2 numbers), two 2x2 source derivatives J_0,J_1 (8 numbers), and if B>=32, three 2D map-angle derivatives D_a (6 numbers). At B=12, signed 8-bit fixed-range quantization of x/J (10 bytes + 2 pad), at B=20, half-precision 10 values, at B>=32, half-precision 16 values. Correct question-time decoding uses these exact stored bytes.
- **Conventional sensitivity twin:** independent reverse-product derivation of the same source sensitivities, with identical byte codec and predictions. A tie is expected and must be reported.
- **Uniform state snapshot + trained question-aware decoder:** exactly floor(B/4) 2D half-precision states at fixed evenly spaced times including terminal; offline Ridge decoder learns source sensitivities and six structural query corrections from training worlds, with alpha selected only on validation.
- **Most-recent event log:** for B<38, stores a half-precision 2D state at time T-k (4 bytes) plus last floor((8B-32)/3) three-bit action/provenance tokens; for B>=38, packs all 100 three-bit tokens in 38 bytes (x_0 publicly known). Unknown prefix alterations are not fabricated; its partial replay ignores prefix perturbations.
- **Terminal-only:** half-precision terminal state, with no inferred path response.
- **Wrong-provenance negative control:** terminal state correct, but J lineage assignments are randomly shuffled at encoding. Valid counterfactual source reweighting should be degraded.
- **Wrong-order negative control:** shuffle the same token multiset before recomputing sensitivities while retaining correct terminal x.

## Frozen query sets (unseen at encoding)

- **Additive provenance:** 4 prespecified pairs of Δ_0 and Δ_1 vectors. Exact end-state replay is the target. Primary loss: per-coordinate squared error averaged over 4 queries and held-out worlds.
- **Small structural change:** a in {0,1,2} and angle theta in {-0.12,+0.12}, left-multiplying A_a only when action a occurs. Secondary loss: per-coordinate squared error over 6 queries.
- **Large structural stress:** action 0 and theta=+0.45, a deliberately out-of-linearization-range query, scored separately.
- **Original endpoint:** no-change endpoint reconstruction, scored separately, expecting state snapshots/logging to be strong.
- Binary projected decisions (sign of dot([0.6,0.8], end_state)) are secondary; MSE is primary.

## Split freeze and anti-leakage

- Training: generator seed 714001, 5,000 worlds. Validation: seed 714002, 1,000 separate worlds. Test/holdout: seed 714003, 3,000 separate worlds. No worlds are shared.
- Validation chooses only snapshot Ridge alpha from {0.1,1,10,100} per budget, scoring a fixed average of additive and small structural query losses. No SRDE/J codec tuning on test.
- Holdout is opened **once**, after the code, protocol, and selection lock are saved to Google Drive and GitHub. All code, source and selection SHA-256 values are retained.
- 3,000 independent worlds are resampling units; 2,000 world-level bootstrap replications with seed 714004 compare paired MSE. No statistically supported superiority claim solely from a designed synthetic task.
- Four storage budgets, all query families, all baselines and negative controls are reported. No test-driven parameter tuning, no silent dropped worlds.

## Predeclared decision/falsification rules

- Do not call source-specific replay a discovery unless its source-specific information advantage survives valid controls, is absent when that information is destroyed, and does not disappear under the matched same-information conventional decoder.
- The likely **representation-usefulness** outcome (additive source perturbations with compact Jacobians) and expected **structural-failure** outcome (finite map perturbations and raw full-event-log parity/win) must both be published; a benefit is task-specific.
- If the conventional sensitivity twin ties, state that SRDE did not develop a new algorithm or theorem.
- Treat out-of-family changes as *diagnostics of limits*, not retroactive grounds to change the objective.

## Prior sources cited for originality boundary

- Hambly, B. and Lyons, T. (2010), *Uniqueness for the signature of a path of bounded variation and the reduced path group*, Annals of Mathematics: https://annals.math.princeton.edu/2010/171-1/p02
- POMDP belief-state sufficiency and history, *Exploring replay* (2025), Nature Communications: https://www.nature.com/articles/s41467-025-56731-y
- *Optimal forgetting: Semantic compression of episodic memories* (2020), PLOS Computational Biology: https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1008367
- Zou et al. (2026), *Remember the Decision, Not the Description*, arXiv: https://arxiv.org/abs/2605.10870
- Previous verified SRDE-P5 and P6 public artifacts in github.com/MerluseDan/FACO9000/research/srde/.
