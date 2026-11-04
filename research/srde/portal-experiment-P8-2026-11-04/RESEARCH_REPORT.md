# SRDE-P8: Nonlinear portal memory versus entropy-coded chronology
**Date:** November 4, 2026 (Toronto) | **Project:** Blackbird Intelligence / Proto Alpha | **Status:** complete, CPU-only, preregistered synthetic simulation, independent audit PASS.
**Concept direction:** Dan Merluse. Executable design, calculations, audits and report: AI-assisted. No native FACO application modified. No GPU used.

## Executive verdict
**The nonlinear curvature sketch failed.** The strongest comparator was an ordinary probability-aware arithmetic code of the original portal and provenance event sequence. At 32 bytes it stored all 100 events in every sticky-world holdout (1,200/1,200), none of the high-entropy worlds (0/1,200), and switched to a quantized suffix checkpoint when necessary. It nevertheless achieved overall reconstruction mean squared error **0.00012141**, versus **84.09551** for the second-order sketch. An adaptive hybrid that used the curvature sketch when the full log did not fit scored **27.10150** and failed the preregistered claim of improvement. A 40-byte entropy packet stored the complete sequence in **all 2,400 worlds** and replayed every preregistered query to floating-point precision. Conventional information theory, not a new portal operator, explains the success.

### Fixed-budget held-out scores (lower is better)
| Memory (20 / 24 / 32 / 40 bytes) | 20 B | 24 B | 32 B | 40 B |
|:--|--:|--:|--:|--:|
| Entropy-coded chronology | 0.007954243 | 0.001967661 | 0.0001214117 | 0 |
| Plain recent-event suffix | 0.005992875 | 0.002370357 | 0.0002645011 | 8.7278e-06 |
| Tangent-only sketch | 2.612536 | 2.612536 | 2.612536 | 2.612536 |
| Second-order curvature sketch | 83.38603 | 85.07506 | 84.09551 | 88.40039 |
| Full-log/curvature hybrid | 2.600559 | 56.60739 | 27.1015 | 0 |
The sign-error metrics, population-specific scores and family-specific losses are preserved in `results.json` and all 268,800 per-world rows. The 40-byte full-log zero score is a mathematical saturation outcome, not a new discovery.

![Overall reconstruction MSE by memory budget](P8_memory_tradeoff.png)

## What is actually new in the study design
P5 examined simple ordered affine maps; P6 tested state-checkpoint placement and lost to conventional covariance-greedy placement; P7 tested first-order provenance/rotation memory against an inefficient fixed-bit suffix log. **P8** introduced simultaneous finite edits of two noncommuting portal types, supplied the second-order *mixed* derivative `H_{kl}`, and used strong probability-matched arithmetic coding to eliminate the weak-log comparison. It also introduced independent high-entropy paths as a hard control.
The mathematics of Taylor/Hessian expansions, rate-distortion, entropy coding, and path signatures is established prior art. This is a **new SRDE-specific failure-boundary experiment**, not proof of an original theorem or unique predictive method.

## Exact method
Every authored world has 100 transitions `x(t+1)=A[a(t)]x(t)+b[a(t)]+d[p(t)]`, three portal labels and two provenance labels; initial state is public zero, and all dictionaries are public. **1,200 held-out sticky worlds** follow action repeat probability .67 and provenance repeat .88; **1,200 independent worlds** use uniform action draws and independent provenance bits. Development used separate 800 worlds. Paths are binary memory payloads, not text-only demonstrations; all six non-duplicate methods use 20, 24, 32 or 40 bytes per world (headers and padding included). The decoder never sees the uncompressed history.
For a portal-rotation parameter `θ_k`, the candidate stores quantized `x`, first sensitivity `D_k=∂x/∂θ_k`, pure curvature `H_kk`, and selected cross-curvatures `H_kl=∂²x/∂θ_k∂θ_l`, constrained by budget. Its reconstruction is the second-order Taylor approximation `x(θ)≈x(0)+ΣD_k θ_k+½ΣH_kl θ_k θ_l`. The matched conventional Hessian twin gives **exactly identical predictions** for every stored case. The sketch deliberately does *not* store provenance-additive derivatives, so the additive query is a tradeoff rather than a good result for this candidate.
The conventional coder uses an exact integer arithmetic interval with **true known generative transition probabilities**, a 2-byte header encoding model/length, and a full 100-event lossless stream when it fits. Otherwise the same B-byte payload stores a quantized state checkpoint and a suffix of real event symbols. Source model parameters, like the portal dictionaries and offline weights, are shared public model information not charged to each world; the result is not an independent unknown-source compression guarantee.

### Full-history fit counts
| Budget | Sticky complete / 1,200 | High entropy complete / 1,200 |
|:--|--:|--:|
| 20 bytes | 9 | 0 |
| 24 bytes | 515 | 0 |
| 32 bytes | 1200 | 0 |
| 40 bytes | 1200 | 1200 |
![Lossless full-history fit rate](P8_full_history_fit.png)

## Preregistered hypothesis decisions
- **H1 — confirmed for this generator:** at 32 bytes, 100% of sticky and 0% of independent worlds fit a complete lossless event record (preregistered thresholds ≥90% and <20%).
- **H2 — rejected:** on high-entropy joint-rotation queries at 32 bytes, curvature *increased* MSE relative to tangent by **4.97229**, 95% world-bootstrap interval **[4.63009, 5.31962]**. Extra stored curvature is harmful for these finite edits.
- **H3 — strongly rejected:** at 32 bytes, the proposed hybrid MSE was **27.10150** compared with **0.00012141** for conventional entropy/suffix memory. Hybrid minus conventional **27.10138**, interval **[24.27793,29.86555]**. The preregistered 10% improvement was not observed.
- **H4 — confirmed as an approximation limitation:** high-entropy large-angle curvature MSE exceeded moderate-angle curvature MSE by **195.237**, interval **[176.990,214.484]**.
Whole-world bootstrap: 2,000 fixed-seed resamples of independent authored worlds, exploratory intervals rather than real-world population guarantees. Sign-error rates and both population strata are reported in `results.json`.

## Exploratory fresh-seed follow-up — local radius of validity
After the held-out test, a separately identified fresh seed (880505, 300 worlds of each type) evaluated untouched first- and second-order coefficients at new rotation angles. This diagnostic was **not preregistered or used to retune the model**. In iid worlds with a single type-0 rotation, second-order unquantized MSE was ~0.0120 versus 0.0255 for tangent at θ=0.10, but 0.254 versus 0.175 at θ=0.18, and 4.730 versus 0.866 at θ=0.35. Float16 storage changed these values little. This directly isolates **Taylor truncation outside the local validity radius**, rather than merely blaming insufficient bytes.
![Fresh-seed rotation radius](P8_curvature_radius.png)

## Independent verification
The independent auditor imports **no experimental/scoring module**. It reconstructed all **268,800** score records from saved true and predicted coordinates; it validated every payload length, code/protocol hashes and expected population counts. It independently recovered and compared **4,124** exact arithmetic-coded complete paths against all 100 original action/provenance labels, and separately verified **5,476** fallback suffixes and source checkpoints. Maximum absolute discrepancy per raw MSE was **2.84e-14**. All preregistered bootstrap CIs were reproduced, and conventional Hessian predictions matched the SRDE-coded candidate exactly. Status: **PASS**.
Adversarial history manipulation (1200 independently designated worlds) increased additive-query MSE to **0.555493** when action order was permuted and **0.358286** when provenance order was permuted. These controls verify information relevance; they do not validate a cognitive meaning theory.

## Scientific decision and next candidate
**Reject P8 curvature and the tested hybrid as general-purpose long-chain counterfactual memory.** Do not promote their local Taylor coefficients into a universal meaning representation. For this toy generator, keeping an entropy-coded chronology is simpler and overwhelmingly more accurate, and source entropy determines when lossless replay fits. Future distinct work could test **certified, query-dependent local approximation with automatic fallback to exact chronology under genuinely unknown data-generating statistics**, but this requires its own prior-art novelty gate. Check competing compressed-trace coding and learned nonparametric codecs, shared-model complexity, and out-of-distribution paths. No app integration is authorized by these research results.

## Prior art and references (targeted, not exhaustive)
1. Rissanen & Langdon (1979), *Arithmetic Coding*, IBM Journal of Research and Development. https://ieeexplore.ieee.org/document/5390830/ . Context-model arithmetic coding is well established.
2. *A Primer on the Signature Method in Machine Learning*, Springer Nature (2025). https://doi.org/10.1007/978-3-031-97239-3_1 . Path signatures, truncation and log-signatures are existing methods.
3. *DRIPS: A framework for dimension reduction and interpolation in parameter space* (2023), Journal of Computational Physics. https://www.sciencedirect.com/science/article/pii/S0021999123005508 . Parameter surrogate modeling is established.
4. Carrondo et al. (2026), *Dynamic Universal Approximation via Signature Controlled Differential Equations*. https://arxiv.org/abs/2607.13886 . Path-dependent approximation does not make this SRDE result original mathematics.
5. Blackbird archive: P7 frozen previous study, internal user research. https://drive.google.com/drive/folders/1NQ8uDBR_m2Bo7yALpQsSOPNnGKqtNdT5 .

**Reproduction:** `OPENBLAS_NUM_THREADS=1 python srde_p8.py selftest --out .`; `validate` then `evaluate` stages were executed **once** in that order with the hash-frozen source. Holdout re-execution must use a new output folder and explicitly declare it a replay, not a fresh blind test. Check `SHA256SUMS.txt`, `results.json`, raw `.bin` memory payloads, `all_forecasts.npz`, `source_and_truths.npz`, `test_world_metrics.csv`, and `audit_independent.py` for complete independent verification.
