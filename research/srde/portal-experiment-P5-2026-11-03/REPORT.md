# SRDE-P5: Portal Order Memory and Reverse-Path Instability

**Research date:** 2026-11-03  
**Concept:** Dan Merluse, Blackbird Intelligence / Proto Alpha  
**Methodology:** Original SRDE exploratory hypothesis formalized, coded and independently audited with ChatGPT  
**Status:** COMPLETE; CPU-only synthetic mathematical experiment; **not peer-reviewed or established real-world forecasting**.

## Abstract

Two sequences can contain identical portals in identical amounts yet produce different destinations because the **order of traversal matters**. We isolated this in a 100-level model with three local spatial coordinates and a fourth state coordinate `F` in `[0,1]`. In 4,096 synthetic worlds, a sequence-aware predictor achieved Brier `0.011889`, versus `0.024040` for the Bayesian order-blind mixture (paired improvement `0.012151`; 95% world-bootstrap interval for ordered minus unordered `[-0.014084,-0.010143]`). A conventional order-aware closed-form calculation performed identically. This supports a representation requirement—retain path order—not a novel forecasting advantage. Meanwhile, the initial coordinate's contribution decayed as `a^100`, making reverse reconstruction very unstable under noise. No empirical psychological interpretation follows from these results.

## 1. The proposed SRDE construct

We represent local meaning-like position as `x=(x,y,z)` and a simulated valence input as `F in [0,1]`. The contraction is `a(F)=0.72 + 0.18F`. This input is **not measured human emotion**. Two distinct portals have anchors `u` and `v`:

```
A(x) = a*x + (1-a)*u
B(x) = a*x + (1-a)*v
```

`AB` means enter A, then B. `BA` means enter B, then A. Repeat each pair 50 times for 100 levels. Both traversals contain exactly fifty A doors and fifty B doors; only their order differs.

Analytic destinations are:

```
x_AB(100) = a^100*x0 + ((1-a^100)/(1+a))*(a*u + v)
x_BA(100) = a^100*x0 + ((1-a^100)/(1+a))*(a*v + u)

x_AB(100) - x_BA(100) = ((1-a^100)*(1-a)/(1+a))*(v-u)
```

The original starting coordinate enters with factor `a^100`; the order-dependent displacement approaches a persistent finite ratio `(1-a)/(1+a)` for this particular contraction family. This is a direct algebraic consequence of known affine transformations, not a claim of previously undiscovered mathematics.

## 2. Measured 100-level residuals

| F (simulated state) | a(F) | Normalized order residue | Original-position coefficient |
|---:|---:|---:|---:|
| 0.0 | 0.72 | 0.162791 | 5.411e-15 |
| 0.5 | 0.81 | 0.104972 | 7.055e-10 |
| 1.0 | 0.90 | 0.052630 | 2.656e-05 |

Maximum difference between iterative 100-level traversal and closed-form coordinates: `1.332e-15`. Same-anchor commuting null max difference: `0.0e+00`. Independent audit status: `PASS`.

![Order residue by depth](order_residue_by_depth.png)
![Root memory by depth](root_memory_by_depth.png)

## 3. Synthetic event prediction: order-aware versus order-blind

Each world draws independent `x0,u,v,w,F`, selects AB or BA with equal probability, and generates a binary event from the terminal projection plus independent Normal(0,0.04^2) noise. All methods know the exact generating equations except for any information deliberately withheld by their definition. The **order-blind mixture is uncertainty aware** (it averages the two order-conditional probabilities); it is not a naive guess. The matched conventional order-aware predictor sees the same information as SRDE.

| Method | Brier score (lower better) | Accuracy |
|---|---:|---:|
| Ordered SRDE | 0.011889 | 98.32% |
| Same-info math | 0.011889 | 98.32% |
| Order-blind mixture | 0.024040 | 96.14% |
| Wrong order | 0.059667 | 93.36% |
| Uninformed | 0.250000 | 48.39% |

Brier(ordered) minus Brier(order-blind): **-0.012151**; 95% bootstrap from independent synthetic worlds: **[-0.014084, -0.010143]**. This comparison is **mechanism-matched and constructed**: known ordered maps generate the labels. It should not be called an independent discovery of real-world predictive power.

![Forecast error chart](forecast_brier.png)

## 4. Backward navigation and loss of root identity

With known affine portal maps and observation noise, applying the exact inverse path multiplies endpoint error by `a^-100`. With three-dimensional endpoint noise standard deviation `1e-4` per coordinate, the observed median root-reconstruction error was:

| F | a | Inverse amplification factor | Median root error |
|---:|---:|---:|---:|
| 0.0 | 0.72 | 1.848e+14 | 2.906e+10 |
| 0.5 | 0.81 | 1.417e+09 | 2.192e+05 |
| 1.0 | 0.90 | 3.765e+04 | 6.059e+00 |

Even when the maps are reversible in exact arithmetic, reconstruction is ill-conditioned. The distance from the initial position is not preserved by contraction. This **does not** imply that all reverse semantic reasoning or causal inference is impossible: it identifies a failure mode for an operator that contracts this strongly.

## 5. Perpendicular orientation sanity check

For 1,024 independent random pairs of 3-D rotation angles, rotations about different axes yielded average Frobenius order residual **0.478237** (minimum **0.034206**). Same-axis rotation null residual was below **1.57e-16**. This is established rotational algebra used as a check for a proposed orientation-sensitive local coordinate operator, not a novel theorem.

## 6. Interpretation and boundaries

**What P5 supports:** the SRDE representation should retain an ordered traversal history, local orientation, and uncertainty about reverse inference. Merely keeping the set of portals entered is lossy. 100-level memory of ordering can coexist with almost total loss of origin under specified dynamics.

**What it does not support:** claims about human consciousness, subconscious prediction, biological stress, universal meaning, true subjective feelings, natural causation, peer-reviewed novelty, or superiority to a conventional algorithm with equal information. The matched conventional approach tied exactly. The only paths tested for the primary identity were alternating AB and BA with equal counts.

**Next original question, not yet tested:** Can an SRDE observer reconstruct a *useful partial history* without exploding inverse noise by storing local loop signatures and independent evidence checkpoints? Follow up with heterogeneous frames, state-updated F, correlated worker votes, unknown maps, and independently generated held-out worlds. Compare against the best ordinary sequence model at matched computational cost, including commuting and random-link negative controls.

## 7. Provenance

- Protocol SHA-256: `86cbf24c544b151bc79670b03705d3748276999295bafa6861fb4e9a4d35c920`
- Model script SHA-256: `178c7f82bf5629f83aa1a7226359dc66f37c1bdc288480498ba40ed1b458dae8`
- Every-world CSV SHA-256: `4948253791d28fa97512b98493cadeb16ce3bcd51d2db002b46b85a14afa9c24`
- 4,096 independently generated worlds, 100 transitions per path; random seed `20261103`; 2,000 fixed-seed bootstrap replicates; no hyperparameter tuning.
- Separate independent auditor `audit_independent.py` recomputes individual predictions, event labels, scoring and bootstrap from saved CSV, without importing the model script.
- Code and preregistration were publicly committed **before** the experiment output was scored.
