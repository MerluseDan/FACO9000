# SRDE-P7 — Compressed Portal-Order and Provenance Replay

**Blackbird Intelligence / Proto Alpha — November 3, 2026**  
**Concept direction:** Dan Merluse. **Experiment, audit and report:** AI-assisted.  
**Status:** COMPLETE; 3,000 independent synthetic held-out worlds; CPU only; **independent audit PASS**. Not a peer-reviewed new mathematical theorem.

## Executive verdict

An ordered 100-step path can be compressed to a small set of **provenance-conditioned response coefficients**, preserving the exact responses to an entire class of later source-reweighting questions. In the fixed synthetic generator, the 20-byte SRDE representation achieved held-out mean squared error **2.614e-08** per coordinate, versus **0.005927** for a packed 20-byte recent-event log and **0.141750** for half-precision value snapshots with a trained, query-aware decoder. A conventional mathematical sensitivity sketch holding the identical coefficients **tied SRDE exactly**.

The effect is sharply task-bound. For small structural portal rotations, the 32-byte SRDE sketch had error **0.084121**, while a recent-event log achieved **6.182e-05**. For the large rotation query, the 32-byte derivative extrapolation failed severely (**2.330210** MSE), worse than simply reusing the terminal endpoint (**0.278176**). At 40 bytes a packed full 100-token action/provenance log achieved zero error to floating-point precision on the tested additive, structural, and stress queries.

**Scientific interpretation:** This is a useful SRDE representation boundary, not an independently new predictive mechanism. Sensitivities are sufficient for additive source perturbations of known affine transformations; they are not sufficient for arbitrary subsequent changes to the operators.

## 1. Novelty review and relationship to prior SRDE work

- **P5** tested 100-level portal-order residue and full reverse-path noise amplification. **P6** studied optimal placement of noisy state checkpoints and found no unique SRDE advantage over conventional posterior-covariance planning. This study does not rerun either result.
- Earlier E01–E04 and E22–E30 separately examined evidence lineage, feedback and change detection; this research instead evaluates **fixed-bit question-time replay after the full path history is discarded**.
- Ordered path representations and their signatures are established (Hambly and Lyons, *Annals of Mathematics*, 2010); belief states, forward sensitivities and rate-distortion memory design are also established. No priority, patentability, or global mathematical novelty is claimed.
- Specific P7 distinction: an end-state + source-specific Jacobian + finite-change portal-derivative payload, charged per byte and evaluated on both in-family and out-of-family counterfactual questions.

## 2. Precise mathematics

In each independent world, 100 transitions are driven by portal class `a_t` in `{0,1,2}` and provenance label `p_t` in `{0,1}`:

`x_(t+1) = A_(a_t) x_t + b_(a_t) + d_(p_t)`, with public `x_0 = (0,0)`.

The 2D portal matrices `A_a` contract but do not all commute. The `a` and `p` sequences are Markov-persistent and vary independently across worlds; the actual sequences are **not** provided to the decoder except through their stored bytes.

For source-specific additive perturbation vectors `Delta_0` and `Delta_1`, define each 2-by-2 Jacobian recursively:

`J_(p,t+1) = A_(a_t) J_(p,t) + 1[p_t = p] I_2`; `J_(p,0) = 0`.

Then **exactly** for the specified affine class:

`x_T(Delta_0, Delta_1) = x_T + J_(0,T) Delta_0 + J_(1,T) Delta_1`.

For structural portal changes `A_a -> R(theta) A_a`, P7 stores `D_a = d x_T / d theta_a` in higher-capacity memories and uses the first-order estimate `x_T(theta) ~= x_T + theta D_a`. That is approximate and deliberately stress-tested outside small angles.

## 3. Equal per-world byte budgets and comparisons

All policies receive one of **12, 20, 32, or 40 bytes per world**. All codes are actual packed bytes; payload lengths were verified across all 3,000 holdout worlds, not hypothetical dimensions.

1. **SRDE provenance sketch:** `x_T`, two 2x2 source Jacobians, and (from 32 bytes upward) three 2D rotation derivatives. 12-byte mode uses signed 8-bit quantization; 20-byte mode uses 10 half-precision numbers; 32-/40-byte modes store 16 half-precision numbers (plus 8 padding bytes at 40).
2. **Exact information-matched conventional sensitivity:** independent reverse-ordered suffix-product computation, encoded with the same bytes. By design this provides a compulsory equal-information control.
3. **Value-only snapshots + trained decoder:** `floor(B/4)` evenly spaced, 2D half-precision snapshots; a common offline Ridge model predicts source-response and finite structural counterfactuals. Alpha was chosen only on a separate validation population.
4. **Packed recent event log:** 3 bits per `{portal type, provenance}` token, with a 4-byte starting state for incomplete suffixes. At 40 bytes it stores all 100 tokens (38 bytes + padding), with public root known.
5. **Terminal endpoint only**, and negative controls corrupting source lineage or token order while preserving the proper original terminal state.

Offline training and decoder model parameters are shared. Their total bytes are **not** included in the per-world budget; the comparison is fair in *per-episode stored bytes*, not total stored bits or compute.

## 4. Frozen experimental timeline

- Pre-registered protocol and exact scientific Python source were committed to GitHub before validation or scoring the held-out worlds.
- 5,000 training worlds (seed 714001); 1,000 validation worlds (714002); **3,000 independent holdout worlds** (714003).
- Validation selected Ridge penalties by budget using average additive and small-structural validation error. Full selection files, model `.npz` and their SHA-256 hashes were archived on Google Drive and the summary was committed on GitHub before opening the test seeds.
- 4 additive source questions; 6 small structural edits (`theta=+/-0.12` for each of three portal types); 1 large structural edit (`theta=0.45`); and 1 unchanged endpoint question.
- All policy outputs were evaluated on the same worlds. 2,000 fixed-seed paired whole-world bootstrap replicates quantify uncertainty; no post-hoc tuning or excluded failures.

## 5. Held-out results

### Exact-scope provenance replay and small structural changes

| B (bytes) | SRDE additive MSE | Snapshot additive MSE | Packed-log additive MSE | SRDE small-rotation MSE | Packed-log small-rotation MSE |
|---:|---:|---:|---:|---:|---:|
| 12 | 0.000478 | 0.141719 | 0.041097 | 0.109472 | 0.015765 |
| 20 | 2.614e-08 | 0.141750 | 0.005927 | 0.109048 | 0.002268 |
| 32 | 2.614e-08 | 0.142148 | 0.000286 | 0.084121 | 6.182e-05 |
| 40 | 2.614e-08 | 0.142344 | 1.485e-31 | 0.084121 | 0.000000 |

`MSE` is mean squared end-state error **per coordinate**, averaged over the appropriate prespecified query family and across 3,000 independent worlds. Lower is better. The complete 240,000 world/method/budget/family aggregate records are retained in `holdout_world_metrics.csv`.

At B=20, SRDE minus packed-log additive error is **-0.005927**, with paired 95% world-bootstrap interval **[-0.006062, -0.005800]**, favoring the sketch for this query family. At B=32, SRDE minus packed-log **small structural** error is **0.084059**, with 95% interval **[0.080951, 0.087191]**, strongly favoring the raw-event log. These intervals measure variation over the designed synthetic world population, not external scientific generalization.

The strongest in-class result is a standard mathematical property: the source-conditioned Jacobians carry exactly the information required by *additive* perturbation queries. They do not miraculously recover all action history.

### Large structural change: deliberate negative result

For B=32, the first-order portal derivative had stress MSE **2.330210**, compared with **0.000261** for a packed suffix and **0.278176** for an unchanged end-state prediction. Under a 40-byte complete log, both small and large structural-change replay are exact. **A compressed first-order response should not be extrapolated to large, nonlinear operator changes.**

### The provenance and ordering controls

At B=20, correct additive-memory MSE was **2.614e-08**. Randomly shuffling provenance labels before constructing source derivatives increased it to **0.115478**; shuffling portal order increased it to **0.300444**. Both preserve the original terminal state, isolating the information contributed by source/order history within the constructed dynamics.

On the *unchanged endpoint*, the 12-byte, signed-8-bit SRDE payload made more rounding error than the half-precision value snapshots. This is the other side of allocating bits to future sensitivity instead of only present-state fidelity.

## 6. Independent audit and reproducibility

Independent script `audit_independent.py` does not import the experimental module. It verified all **240,000** saved world score rows and **80** group averages, every actual byte budget, **all 3,000 full 100-step action/provenance logs at B=40**, an independent reverse-suffix Jacobian reconstruction on 80 worlds, exact conventional parity, and an independent reproduction of the prespecified B=20 paired confidence interval. Source/protocol/selection model hashes matched. Audit record: `audit_independent.json`, status **PASS**.

No GPU was used. No installed FACO program, live account, or physical equipment was modified. All scientific inputs and reports are retained as separate files, with a pre-holdout snapshot that was published before the results.

## 7. Interpretation and limits

**What P7 establishes in its authored simulator:** fixed byte budgets force different choices about preserving current state versus preserving the effect of past operations. Source-conditioned, order-dependent sensitivities provide compact exact-class counterfactuals for a *known linear-affine operator family*. They fail for finite structural changes, while a full compressed action log can replay those changes exactly. This justifies a typed-memory design that records *which future questions a compressed representation can answer*.

**What P7 does NOT establish:** original mathematical invention; a nonconventional advantage over equally informed forward sensitivity/automatic differentiation; brain/subconscious modeling; external event prediction; behavior of arbitrary nonlinear portals; fairness of overall model training weights/compute costs; source provenance authenticity; or a universal 100-level semantic law.

**Future research gate:** before testing nonlinear higher-order replay, study derivative jets, hyperdual methods, continuous path signatures, and budgeted query-aware memory. A new label, more depth, or a better compression of known sufficient statistics alone is **not** a novelty-cleared research result.

## 8. Sources and reference record

- Hambly & Lyons (2010), *Uniqueness for the signature of a path of bounded variation and the reduced path group*. Annals of Mathematics, https://annals.math.princeton.edu/2010/171-1/p02
- *Exploring replay* (2025), Nature Communications, https://www.nature.com/articles/s41467-025-56731-y
- *Optimal forgetting: Semantic compression of episodic memories* (2020), PLOS Computational Biology, https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1008367
- Zou et al. (2026), *Remember the Decision, Not the Description: A Rate-Distortion Framework for Agent Memory*, https://arxiv.org/abs/2605.10870
- SRDE P5 and P6 prior-art gates and complete archives remain separately immutable at github.com/MerluseDan/FACO9000/tree/main/research/srde/.
