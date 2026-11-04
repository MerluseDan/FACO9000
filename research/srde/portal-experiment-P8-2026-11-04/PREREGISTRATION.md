# SRDE–P8: Nonlinear portal interaction memory versus entropy-coded chronology

**Protocol date:** 2026-11-04 (America/Toronto). **Status:** prospective, pre-evaluation, experimental. Research direction: Dan Merluse / Blackbird Intelligence; AI-assisted implementation. CPU only. Do not promote results to a novel mathematics or cognitive discovery. Prior P1–P7 are not modified.

## Novelty audit and mechanism

P5 showed ordered affine portal maps can retain order after root memory contracts, and reverse inversion amplifies endpoint noise. P6 evaluated a limited number of **state checkpoints**; priority and orientation bonuses were rejected and a conventional covariance-greedy planner won. P7 evaluated equal-byte **terminal-state and first-order provenance/rotation sensitivity sketches** versus weak fixed 3-bit/event recent logs. The P7 sketch excelled at additive provenance queries but lost on finite structural rotations. P8 does not re-run P7 as a new discovery. It adds (a) simultaneous finite edits to TWO different noncommuting portal types, (b) second mixed sensitivities (curvature), (c) lossless entropy-coded full path as a strong non-SRDE comparator, and (d) both sticky and independent high-entropy portal sequences, in a matched byte budget. The central novelty candidate is the *combination of this exact SRDE retrieval-task/memory failure-boundary*, NOT Taylor/Hessian calculus or arithmetic coding in general.

Prior-art guardrails: Rissanen & Langdon (1979), arithmetic coding (https://ieeexplore.ieee.org/document/5390830/); path signatures/log-signatures and truncated approximation (https://doi.org/10.1007/978-3-031-97239-3_1); 2023 model reduction via interpolation (https://www.sciencedirect.com/science/article/pii/S0021999123005508); 2026 dynamic approximation via signature CDEs (https://arxiv.org/abs/2607.13886). These establish the general tools, and literature review is **targeted, not exhaustive patent or novelty clearance**. Historical E28 primary evidence remains incomplete. A unique SRDE algorithm advantage cannot be declared merely from a new term or family label.

## Frozen simulator and information access

100 discrete portals, each action `a_t in {0,1,2}`, provenance `p_t in {0,1}`. Shared publicly known matrices `A[3]`, translations `b[3]`, provenance translations `d[2]` and x0=(0,0), matching the frozen P7 numerical constants. Path evolves `x[t+1]=A[a_t] x[t]+b[a_t]+d[p_t]` for 100 steps.

Two equal-prior populations, generated with disjoint seeds: `sticky` has action repeat probability 0.67, otherwise chooses one of the other two uniformly, and provenance repeat probability 0.88; `iid` uses independent uniform actions and Bernoulli(1/2) provenance. Both populations use independent seeds and are hidden holdout draws. Shared codebooks include BOTH population models, selected population mode is correctly encoded in the log's own header (no free per-world mode metadata to the decoder).

Developer / validation: seed 880101, 400 worlds per population (800 total), to test code, compression fit rates, and lock any fallback choices. Held-out: seed 880202, **1,200 independent worlds per population (2,400 total)**. No heldout outcomes accessed during validation or method choices. The generator's action/provenance stream is available to ALL encoders, not to compressed decoders. All decoders get the same publicly shared constants and one fixed-size per-world memory payload. Training parameters are not learned, except any choices explicitly frozen in the validation selection. The shared codebooks and physical source dictionaries are free to all methods, and this external-memory advantage must be reported.

## Four query families, preregistered

Each stored memory is later queried for terminal x at new parameters; all predictions must be made **only** from that memory and the public model:

1. `add`: one simultaneous provenance translation change, source 0 +(.085,-.062), source 1 +(-.076,.088) (one query).
2. `rotation`: two single-type finite edits: portal 0 +0.35 radians, portal 1 -0.35 radians.
3. `joint`: two separate simultaneous-edit queries: portal 0 +0.35 and portal 1 -0.30, and portal 0 +0.32 and portal 2 +0.30 radians. These explicitly test cross-Hessian terms and noncommutative composition.
4. `stress`: portal 0 +0.85 radians, where a local quadratic sketch may fail.

Each family has weight **1/4** in the primary squared coordinate error, regardless of number of individual queries. Binary sign errors under fixed projection (0.6,0.8) are secondary. The gold outcomes are obtained by full forward replay of the true 100-step sequence with the changed publicly specified portal maps. No physical feeling, human semantics, causal experiment, or real-world event is simulated.

## Exact fixed-budget policies

Budgets: **20, 24, 32, 40 bytes per world**, including header/padding/quantized payload. Every stored payload is checked for byte-exact length and decoded from its actual bytes. Models:

- `terminal`: 2D terminal x float16; no history or derivatives.
- `tangent`: x + first derivatives for each portal-type rotation and provenance changes where possible, quantized float16; remaining space zero padded.
- `curvature`: x, first rotation derivatives, second pure and mixed rotation derivatives and provenance derivatives, with a fixed priority order determined by available bytes, quantized float16. At 20/24/32/40 bytes the same frozen layout rule is applied; no future test labels choose fields. This is the candidate P8 SRDE memory. The matched **conventional Hessian jet** decoder must tie it exactly: calculus is not original.
- `suffix`: quantized 2D state before a three-bit/event stored suffix; `k=floor(8*(B-5)/3)` with header and zero padding. Old prefix edits are unobservable. If B=40 the `suffix` remains incomplete and is NOT quietly promoted to a full log.
- `entropy`: exact context-conditioned integer arithmetic interval code in 2-byte header with population mode, when the entire path fits; otherwise a marked suffix fallback that remains inside B bytes. The exact code is strongly conventional, gets the TRUE source distribution as publicly available model information, and must decode all full-log cases with zero token errors.
- `hybrid`: exact entropy full log if it fits; otherwise an approximate curvature sketch at B-1 bytes plus a one-byte mode header. It is a straightforward codec switch, not a novel information-theoretic theorem.

When the bit budget is enough for a full lossless event log (including its length and population header), no other *deterministic method with identical source information* can claim reconstruction superiority over exact replay; the corresponding cases are a saturation control, not a new achievement.

## Prospective hypotheses and falsification

**H1 (compression audit):** entropy-coded full 100-step logs will fit in 32 bytes in >=90% of sticky worlds and <20% of independent high-entropy worlds. This tests whether P7's 3-bit log comparison overstated the sketch's information advantage.

**H2 (curvature relevance):** In high-entropy worlds at B=32, the curvature sketch has lower `joint` mean square error than the tangent-only sketch; bootstrap a paired 95% interval over whole worlds. If this fails, extra curvature is a wasted storage choice for this simulator.

**H3 (new method advantage, explicitly not assumed):** At B=32, across BOTH populations and all four query families, the hybrid memory will reduce overall weighted error at least 10% relative to the stronger of `entropy` and `curvature`. This is falsified if it merely equals whichever is stronger or worsens the other. The matched conventional twin remains a parity check, not a weaker control.

**H4 (stress boundary):** In high-entropy worlds at B=32, a rotation of 0.85 rad generates more squared error for the curvature approximation than a 0.35-rad single rotation on average. If not, the presumed Taylor local validity problem is absent here.

Confidence intervals: paired bootstrap resampling **whole worlds** within population, 2,000 fixed seed 880303 replicates for H2 and H4 and overall H3. Report descriptive effect sizes, exact fit counts and per-population performance; avoid statistical claims across constructed generators. Multiple proposed hypotheses are exploratory despite preregistration.

## Validation, freeze, and audit

Stages: `selftest`, `validate`, `evaluate` once. `validate` creates a SHA-256 lock binding exact protocol, program, selection and model constants; no held-out seed is materialized. Commit protocol and program publicly to existing GitHub repository prior to evaluate; copy pre-test lock to Google Drive. `evaluate` checks SHA lock and fails rather than overwriting existing results; records all decoded payloads, true streams, full gold and forecasts, per-world outcomes, exact coder bit lengths, paired intervals and negatives.

An **independent audit script**, without importing evaluation/scoring functions, must recompute losses from the saved prediction NPZ and verify stream tokens, byte budgets, exact decoder parity and full-log fit rates. Extra controls: wrong provenance, wrong portal order, and a conventional Hessian-twin parity check. Retain all failures and protocol deviations, including if a coding bug requires a documented repaired version. Use no GPU. Archive exact reproducible package and report under Blackbird Knowledge Repository on Google Drive and publish method/metrics to GitHub. No native FACO app modification.
