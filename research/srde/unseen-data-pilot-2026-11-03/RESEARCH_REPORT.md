# SRDE / Blackbird Intelligence — Recursive Portal Discovery
Technical research milestone | 03 November 2026 | Conditional/negative result
Research subject: non-obvious relational paths for inductive prediction on previously unseen entities and worlds. Concept: Dan A. Merluse; computational protocol and local evaluations: AI-assisted.

## Abstract and decision
Two executed experiments were compared with conventional graph methods. On a public inductive knowledge-graph benchmark, a narrow portal-inspired path-voting algorithm achieved AUC 0.6083, essentially tied with a provenance-aware graph-consensus scorer (0.6080) and below a simple 2–3 hop Katz-style baseline (0.6638). The paired test-query AUC difference Portal–Katz was -0.05549, 95% query-bootstrap interval [-0.08780, -0.02439]. In a separate author-designed synthetic state/provenance setting, the portal scored 0.6903 AUC, below a conventional full-feature gradient-boosted graph model at 0.6937. State/provenance ablations worsened portal performance because those properties directly affect this simulator’s outcome process. No general SRDE predictive advantage is supported. This is not a run of the user’s native installed SRDE engine.

## Questions and predeclared interpretation
H1: Do paths through non-obvious intermediate nodes improve prediction of withheld true relationships over ordinary graph scores? Compare shared-input, matched-ranking methods and keep every negative result.
H2: Does conditional portal state, lineage-aware quorum, or deeper recursive traversal add measurable signal? Isolate with synthetic ablations and a conventional model given the same features.
H3: Is long-chain connectivity merely inevitable in random graphs? Probe null worlds and shuffled labels.
Decision rule: Claim only a scoped advantage when test/confirmation gains survive strong baselines, independent data, and leakage checks. Finding a path is not evidence that it expresses causation or predicts a future event.

## Historical context recovered
The 02 November 2026 SRDE Portal-Based Hierarchical State Spaces note specifies conditional transitions with position/orientation/valence/arousal/state/history/provenance, worker votes, temporal decay, and random 100-level counterexamples. Its examples were binary synthetic demonstrations rather than forecasting validation.
The 12 October working paper reported an earlier small local-model retrieval advantage of 55/56 versus static graph traversal 48/56; stronger task-aware graph retrieval later tied SRDE 56/56 on a four-seed independent retrieval holdout. E30 local results (16 October, archived in Drive) scored 38/80 for an SRDE activated method and 43/80 for a graph-state challenger, with 18/40 versus 18/40 in shifted confirmation. Those are separate tasks and not pooled with today’s metrics.

## Experiment A — public inductive link-prediction pilot
Dataset: GraIL FB15k-237 V1 from kkteru/grail. Original train graph: 4,245 typed triples / 1,594 entities. Inductive inference graph: 1,993 triples / 1,093 entities. Entity overlap is zero. Validation: 206 held-out triples; test: 205. 180 distinct relations. Per test positive, rank it against 20 candidate corrupt-tail negatives sampled deterministically from the relevant relation tail pool where possible; exclude all observed inductive positives from these evaluation negatives. This is unseen-entity generalization, not timestamped future prediction.
Training: enumerate 2–3-hop typed directed paths, mask target edge, learn training-only relation/path association log-ratios from 4,245 positives and 2 sampled negatives per positive, retain 2,378 rules, and cap each query at 12,000 edge expansions. All ranking methods operate on these same enumerated paths. No query hit its cap.
Portal-inspired structural scorer: group supporting paths by their first intermediary as a proxy for independent branches. If two positive independent 2-hop witnesses exist, close the portal there; otherwise traverse evidence to depth 3. Score signed rule support with conservative quorum. Graph-consensus scorer uses the same path evidence without adaptive depth closure. Common neighbors, Adamic–Adar, Katz-style 2–3 hop counting, and relation-aware scoring are conventional controls. Neither state-valence/arousal, learned coordinate transforms, nor true recursive workers were implemented on this public data.

### Experiment A — observed metrics
Katz: AUC 0.6638; MRR 0.3556
Typed: AUC 0.6101; MRR 0.3129
Portal: AUC 0.6083; MRR 0.3142
GraphConsensus: AUC 0.6080; MRR 0.3118
CN: AUC 0.5810; MRR 0.2774
AA: AUC 0.5800; MRR 0.2764
PortalNoQuorum: AUC 0.6073; MRR 0.3120
AUC deltas (2,000 paired held-out-query bootstrap resamples): Portal–Katz -0.05549 [ -0.08780, -0.02439 ]; Portal–GraphConsensus +0.000244 [ 0, +0.000732 ]; Portal–Typed -0.00183 [ -0.01000, +0.00707 ]. Only 49/205 test positives contained a positively weighted learned path; a serious coverage limitation.
Validity limits: The 20-negative ranking task is not the official all-entity filtered GraIL evaluation and was not repeated across multiple graph seeds/datasets. No learned modern GraIL, NBFNet, SEAL, factor-graph, or temporal model was run. AUC measures discrimination among these candidates, not calibrated future-event probability. Query bootstrap does not account for dataset/source selection.

## Experiment B — synthetic conditional/state/provenance stress test
80 training worlds × 150 cases = 12,000 training cases; 20 validation worlds × 150 = 3,000; 60 unseen test worlds × 150 = 9,000; 40 shifted confirmation worlds × 150 = 6,000. Worlds separated by seed groups. State/context matching, orientation, evidence decay, lineage IDs, duplicate witnesses and 2–3 hop depth are observable. The authored outcome generator deliberately uses a signed independent-source evidence sum plus a bonus for two positive independent witnesses. Thus this simulator establishes only conditional feasibility, not independent discovery of biological semantics or causal paths.
Each univariate rule score was calibrated with a training-only logistic regressor. Conventional linear and gradient-boosted comparators received the full observed feature vector, including provenance and state. They had greater model flexibility; this is an equal-information, not equal-parameter-count, comparison. Test data did not participate in fitting.

### Experiment B — observed ROC-AUC on unseen worlds / shifted confirmation
FullGraphHGB: test 0.6937; shift 0.6266
FullGraphLogistic: test 0.6913; shift 0.6266
Portal: test 0.6903; shift 0.6247
ProvenanceGraph: test 0.6839; shift 0.6231
TypedGraph: test 0.6641; shift 0.6192
PortalNoLineage: test 0.6640; shift 0.6187
PortalNoState: test 0.6273; shift 0.5656
PortalDepth2: test 0.6256; shift 0.5766
Katz: test 0.5370; shift 0.5261
World-bootstrap for Portal–FullGraphHGB: pooled AUC delta -0.00337; 95% world-mean interval [-0.00566, -0.00081] from 500 whole-world resamples. This is an authored simulator, not a generalizable p-value.
Shuffled test labels: Portal AUC 0.4952 (approximate chance). 200 random 100-layer null worlds reached mean 9.795 /12 endpoints with no true semantics. All four available integrity checks passed.

## Research insights and inference boundaries
1. Portal paths can expose candidate relational support, but topology-only 2–3-hop counts gave better genuine unseen-entity rankings in Experiment A; non-obvious does not automatically mean useful.
2. Repeated paths from one shared ancestor are not independent evidence. Source-lineage deduplication helps in a simulator where the label is generated by independent sources. A conventional graph model can use that same feature; it is not proof of unique portal intelligence.
3. Context gates, orientation, source reliability, and evidence decay change synthetic predictions. Their useful definitions must be learned or measured from time-stamped real observations, never invented to fit the outcome.
4. Recursive depth can recover weaker indirect evidence but risks path proliferation and spurious consensus. The 100-level null confirms this risk. Require capped search, provenance independence, calibrated uncertainty and an abstain/unknown option.
5. Prediction gain and semantic explanation are different. A model that ranks a hidden relationship does not establish why it exists, causal direction, emotional meaning or the certainty of a future event.

## Next milestone: strongest falsifiable protocol
Freeze a second test before viewing results. Evaluate FB15k-237 V2–V4 and WN18RR inductive families plus at least one timestamped ICEWS/GDELT-style temporal split; verify rights, schema and source version first. For time-series, prohibit future-edge and future-node metadata from training and candidate generation. Reuse established GraIL/NBFNet or SEAL implementations with matched model selection and negative sets, not weakened stand-ins.
Use 5+ random seeds, hard HeaRT-style negatives, source-ancestor duplicate poisoning, shift in context distributions, shuffled-edge nulls, and target-relation-cold-start cases. Report MRR/Hits@K, AUROC/PR-AUC when appropriate, calibrated Brier/log loss, false-assertion rates, recall/abstention, source-dependence errors, paths searched, CPU/GPU/latency, memory and full setup cost. Code and all raw cases should be available before results are inspected.
Acceptance threshold for a claimed improvement: demonstrate a predeclared practical uplift over the best conventional baseline across multiple independent data families with confidence interval excluding zero and no material worsening in calibration, false assertions or matched compute cost. The current mechanism fails that threshold.

## Data provenance and reproducibility
GitHub source: https://github.com/kkteru/grail (paths/hashes in real_inductive_results.json). The actual real-data evaluation ran through connected GitHub file retrieval and an isolated JavaScript evaluator; run_real_inductive.mjs is the corresponding independent Node reproduction script for environments with repository file access, but no second full-data local rerun was completed because this sandbox could not reach the GitHub raw endpoint. A synthetic fixture self-test of the script is distinctly labeled and excluded from the results bundle.
The synthetic Python experiment was run locally with numpy/scikit-learn on the CPU. FROZEN_PROTOCOL.json records the exact evaluation design and seed/world IDs, synthetic_results.json the full measurements, and synthetic_test_cases.csv the individual held-out cases. Historical claims are linked to earlier research files, not silently treated as new results.

## References
1. Merluse, D. A. SRDE: Portal-Based Hierarchical State Spaces for Pre-Event Inference, v0.1, 02 Nov 2026; original source in user Library.
2. Merluse, D. A. FACO-SRDE Working Paper, 12 Oct 2026; original source in user Library.
3. FACO-SRDE E30 Local Results Report, 16 Oct 2026: https://drive.google.com/file/d/1rWVGiB4-ngjEnNDwP-apC6U3U_kfb1Kt/view
4. Teru et al., Inductive Relation Prediction by Subgraph Reasoning (GraIL), ICML 2020: https://github.com/kkteru/grail
5. Li et al., Evaluating Graph Neural Networks for Link Prediction: Current Pitfalls and New Benchmarking (HeaRT), 2023: https://arxiv.org/abs/2306.10453
6. Zhang et al., Revisiting Graph Neural Networks for Link Prediction (SEAL), 2020: https://arxiv.org/abs/2010.16103
