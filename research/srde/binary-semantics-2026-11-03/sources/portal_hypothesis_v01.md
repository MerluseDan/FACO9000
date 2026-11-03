# SRDE: Portal-Based Hierarchical State Spaces for Pre-Event Inference

**Public hypothesis note v0.1 | 2 November 2026**  
**Concept originator:** Dan Merluse  
**Project:** Blackbird Intelligence / Proto Alpha (SRDE: Spatial Recursive Development Engine)  
**Status:** Speculative mathematical/computational architecture with reproducible *synthetic sanity checks*. Not peer-reviewed; not a validated theory of human cognition or future prediction.  
**AI-assisted development:** Formalization, counterexamples, and synthetic testing developed with ChatGPT.

## Abstract

We propose a framework in which a state is represented by a location in a semantic space, an affective valence, a temporal state, and a history of previously traversed coordinate frames. **Portals** are conditional transitions between nested local spaces. Different positions, orientations, states and histories can lead from nominally similar concepts to different deeper spaces. Recursive delegation allocates variable numbers of workers to the subspaces required by a task. Workers provide evidence-dependent signals or votes on event conditions; those votes may decay or persist and are aggregated without treating agreement as proof. The objective shifts from merely assigning meaning to past events to forecasting *whether future events are enabled by present conditions*.

A motivating conjecture is that two concepts that initially appear unrelated may become connected by long, bidirectional portal paths. Critically, **path existence is not evidence of truth, causation, or predictive utility**. We present a 100-level synthetic negative-control experiment demonstrating this distinction. The proposal yields falsifiable predictions about retrieval usefulness, calibrated forecasting, and the cost and reliability of adaptive hierarchical inference.

## 1. Architectural definitions

### 1.1 Local position and state

A node at recursion level `l` is represented by:

`n_i^(l) = (x_i, y_i, z_i, F_i, A_i, S_i, H_i, t_i, provenance_i)`.

- `(x,y,z)` are *local* semantic coordinates; their semantics and metric must be learned or specified and are not presumed to be physical brain locations.
- `F in [0,1]` is **felt valence**: `0` = maximally aversive/nauseating; `1` = maximally pleasant/rewarding. Neutral can be defined near `0.5` for an instrument, but subjective reports require calibration.
- `A in [0,1]` represents arousal/activation separately from valence, avoiding the mistake that high excitement and peaceful contentment are the same state.
- `S` includes context and internal state; `H` is traversal history; `t` denotes time; `provenance` links a claim to independent observations.
- The *recursion level* `l` is **not** necessarily identical to spatial coordinate `z`. Moving deeper enters a new local frame, rather than moving a universal z-axis.

### 1.2 Conditional portals

A portal is a transition, not a claim about literal physical wormholes:

`P_(l,i): (M_l, x, orientation, F, A, S, H, t) -> (M_(l+1), x', S', H')`.

Two entries at different positions may open different subspaces. Local coordinate frames can rotate, rebase or change dimension. "Perpendicular" is a useful metaphor for a new basis, but orthogonality is a measurable hypothesis, not assumed geometry.

### 1.3 Recursive work allocation

A delegator can solve a problem locally, open a few specialist portals, or delegate recursively. The depth and breadth of the worker hierarchy depend on measured uncertainty, decomposability, time and compute cost, not a fixed worker count. All delegated conclusions return with provenance and verification status. Children are not automatically independent voters.

## 2. Pre-event activation and prediction

The proposal distinguishes a condition becoming active from an event actually occurring. Let `v_i(t)` be a signed evidence/vote value in `[-1,1]`, determined from a node's state and location. A hypothetical activation lifetime is:

`a_i(t) = a_i(t_i) exp(-(t-t_i)/tau_i), for t >= t_i and tau_i > 0`.

Small `tau_i` represents a fleeting condition; large `tau_i` a persistent condition. Negative or missing evidence needs its own representation; it cannot be silently counted as a vote to approve.

A candidate readiness function for event `E` is:

`R_E(t) = sigmoid(b + sum_i w_i a_i(t)v_i(t) + sum_(i<j) u_ij a_i(t)a_j(t)v_i(t)v_j(t))`.

The `u_ij` terms allow conjunctions and interactions. This is **only a score**, not a trustworthy event probability until its parameters are fitted and its outputs calibrated on unseen outcomes. A separate Boolean/majority/AND gate can instead represent a setting in which *all specified prerequisites* must be met; such a rule is a domain assumption, not a general law that "every portal must activate".

Forward inference predicts `P(E_future | present evidence)`. Backward inference asks `P(prior causes | observed event)` and ordinarily requires Bayes' rule, priors and care about non-invertible transformations. A graph path traversable backward does not, by itself, justify reversing causality.

## 3. What a vote can establish

Portal position can encode a vote or contribution, but computational consensus and empirical correctness are different quantities. Three workers repeating one unsupported premise provide one source of evidence, not three independent confirmations. Quorum should be based on explicit eligible membership and a safe resolution/escalation policy. A deadlocked portal does not imply a persistent fact about the universe.

A connection is a candidate for investigation when it is supported by independently observed links, remains stable under perturbations, survives negative controls and improves out-of-sample prediction. It is not made true by a sufficiently long chain of associations.

## 4. Reproducible 100-level synthetic tests

The companion standard-library script `srde_portal_experiment.py` fixes the random seed at `20261102`, uses 20,000 synthetic trials per reliability condition, 100 levels and 100 random connectivity worlds. It contains assertions against analytic results. All trials concern binary variables and randomly wired graphs, **not actual human meaning, emotions or future events**.

### 4.1 Long-chain information retention

A binary variable is passed through `L=100` independent steps, each preserving the bit with probability `q`. Its endpoint agrees with the starting bit with theoretical probability:

`r(q,L) = [1 + (2q - 1)^L]/2`.

The three-route example creates **independent conditional copies** and defines a synthetic end event by a majority of the three endpoints. If the root is used to anticipate that event, theoretical accuracy is `3r^2 - 2r^3`. This compares *two different synthetic event mechanisms*, not the performance of two algorithms on the same forecasting task. Copying the same ballot three times does not produce that gain.

| Per-step preservation q | Single route, measured | Three independent routes, measured | One-route theoretical | One-route Brier score* |
|---|---:|---:|---:|---:|
| 0.995 | 67.685% | 75.725% | 68.302% | 0.21876 |
| 0.980 | 51.240% | 51.585% | 50.844% | 0.24986 |
| 0.900 | 50.775% | 49.890% | 50.000% | 0.25000 |
| 0.500 | 50.395% | 50.415% | 50.000% | 0.25000 |

*The Brier forecast uses the **oracle-known** transition probability `q`, not one estimated from data. For these balanced outcomes, the uninformed `0.5` forecast has an expected Brier score of `0.25`. These numbers show information degradation with depth, not a novel predictor.

### 4.2 Random portal connectivity negative control

A separate test constructs random layered directed graphs with 12 nodes per layer, two randomly chosen outgoing edges per node, and 100 layers. Each graph begins with only one reachable node at level 0. Across 100 randomly wired worlds, **without meaningful or causal links**, the average number of reachable endpoints is:

| Depth | 0 | 1 | 2 | 3 | 5 | 10 | 25 | 50 | 100 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Mean | 1.00 | 2.00 | 3.73 | 5.92 | 9.04 | 9.92 | 10.01 | 10.03 | 9.90 |

This is the critical counterexample: **after enough steps, even completely random portals connect seemingly unrelated endpoints**. A connection is cheap. Evidence quality and predictive performance are the hard parts.

### 4.3 Test interpretation

The synthetic runs establish that the supplied script implements known combinatorics and probabilistic behavior. They do **not** validate the SRDE portal proposal, establish consciousness operates this way, justify universal mapping claims, or show a model predicts real-world events. Earlier SRDE-family experiments on distinct tasks have mixed/negative comparison outcomes; no historical benchmark advantage is transferred to this untested architecture.

## 5. Falsifiable research program

1. **Explicit representation:** Learn or specify coordinates from a frozen corpus. Store each transition's source, destination, orientation, conditional state and evidence lineage.
2. **Equal-budget baselines:** Compare portal traversal with lexical retrieval, conventional graph traversal, temporal/provenance graphs, factor-graph message passing and embedding search under matched token, compute and latency budgets.
3. **Bidirectionality:** Compare forward prediction, backward explanation, and bidirectional consistency. Backward traces must be ranked as hypotheses, not certified causes.
4. **Holdout outcomes:** Use timestamped pre-event evidence with future outcomes withheld. Score Brier/log loss, discrimination, calibration, false-discovery rate, abstentions and wall-clock/compute cost.
5. **Adversarial and negative controls:** Inject random cross-links, duplicated voters, correlated workers, shuffled evidence, misleading paths and depth=100 null graphs. Require the system to avoid reporting arbitrary connectivity as a discovery.
6. **Affect and welfare:** Treat valence and arousal as optional, separately measured state inputs. Test whether they change retrieval priority or human-rated usefulness without equating reward with truth, survival or happiness.
7. **Preregistration and exit:** Predeclare hypotheses, seeds, datasets, evaluation and failures. Include stopping rules; abandon an added mechanism if it produces no improvement under matched costs.

## 6. Adjacent literature and novelty boundary

This idea is related to local coordinate charts, probabilistic graphical models, layered graphs, belief propagation, causal modeling and dimensional theories of affect. Those are established areas, not new SRDE discoveries. The *proposed combination* of state-conditional portal transitions, recursive delegation, evidence-aware voting, emotional coordinates and pre-event forecasting is an architectural hypothesis requiring independent comparison.

- Kschischang, Frey & Loeliger (2001), *Factor graphs and the sum-product algorithm*, IEEE Transactions on Information Theory, DOI: https://doi.org/10.1109/18.910572
- Watts & Strogatz (1998), *Collective dynamics of 'small-world' networks*, Nature, DOI: https://doi.org/10.1038/30918
- Russell (1980), *A circumplex model of affect*, Journal of Personality and Social Psychology, DOI: https://doi.org/10.1037/h0077714
- Stanford Encyclopedia of Philosophy, *Causal Models*: https://plato.stanford.edu/entries/causal-models/
- Zhang et al. (2026), *Are we measuring oversmoothing in graph neural networks correctly?*, ICLR 2026: https://proceedings.iclr.cc/paper_files/paper/2026/hash/e830d5039c08492baff635fb8beac4a0-Abstract-Conference.html
- Murphy (1973), *A new vector partition of the probability score*, DOI: https://doi.org/10.1175/1520-0450(1973)012%3C0595:ANVPOT%3E2.0.CO;2

## Availability and credit

The reproducible code and raw aggregate results accompany this note. This document is a time-stamped public hypothesis and research proposal, **not** a peer-reviewed publication, a verified new mathematical theorem, or a patent filing. The originating conceptual descriptions are credited to Dan Merluse, with AI-assisted formalization and critical controls. No grant of an open-source or open-content license is implied by publication.