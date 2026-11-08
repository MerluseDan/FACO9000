# SRDE LA4 — Provenance cannot replace independent grounding

Executed 8 November 2026. Research direction: Dan Merluse. Protocol, code, literature review, mathematical construction, analysis and audits are AI-assisted.

## Main finding

This controlled test separates a statement's lineage from evidence about whether its relationship to the target event is correct. Perfect provenance queries leave target orientation completely unresolved in the paired worlds. Independent event labels can resolve it; source echoes presented as event verification cannot.

With genuinely independent anchors of accuracy .9, two-step decision acquisition scores total loss 0.1261965, compared with 0.1500000 for abstaining everywhere and 0.1501562 for spending the full budget on lineage queries. Its improvement versus abstaining is -0.0238035, with a cluster-bootstrap interval [-0.0293994,-0.0180864]. It predicts on 19.55% of cases; this is not full-coverage forecasting.

The predeclared primary comparison is less decisive. Two-step minus one-step decision acquisition is -0.0054389, interval [-0.0161478,+0.0022690]. The interval includes zero. No reliable superiority over one-step planning is established from the 24 independent calibration pools. Its comparison against the strong conventional entropy-acquisition baseline also includes zero.

Unreliable or nonindependent references reverse the value. The learner assumes .9 accuracy in every mode. If anchors are actually uninformative, two-step total loss becomes 0.1976825; if they merely echo a source it becomes 0.2269734. Both are worse than robust abstention at .15. More elaborate acquisition cannot compensate for an ungrounded reference channel.

The explicit table and recursive two-step planners give identical forecasts and decisions. The SRDETypedGate heuristic has no demonstrated superiority. The useful boundary is about information content and reference assumptions, not an advantage from recursion.

## What is different from LA3 and the other chats

LA3 learned parameters within a source family. LA4 studies an exact observational ambiguity that parameter learning cannot remove without new information: reports and provenance can have the same distribution while their relationship to a fixed target event is reversed by context. It asks which query type supplies the missing information, what abstention does to acquisition incentives, and how dependent references defeat that inference.

The latest related chats were inspected before design. E07E used real sensor runs with injected source faults; E08 seeks actual claim dependency graphs and independent failure/restoration records. P8 built an evidence-impact tool on simulated edits to real research reports, with prospective revisions next. Study10 tested synthetic neural summarizers and an evidence ledger, with pretrained-model Study11 pending. Their reported results were not independently rerun here. LA4 reuses none of those datasets, revision workloads, claim graphs or models.

The statistical ideas are established. [Ben-David and colleagues, 2010](https://proceedings.mlr.press/v9/david10a/david10a.pdf), section5, use indistinguishable target-label constructions to establish domain-adaptation limits. [Golovin, Krause and Ray, 2010](https://papers.nips.cc/paper_files/paper/2010/hash/1e6e0a04d20f50967c64dac2d639a577-Abstract.html) study noisy Bayesian active learning. [Chen, Hassani and Krause, 2017](https://proceedings.mlr.press/v54/chen17b/chen17b.pdf) examine correlated noisy tests and limitations of common information heuristics. LA4 implements neither EC2 nor ECED and makes no claim to outperform them. It is a documented SRDE observability/grounding robustness extension, not a new theorem or certified worldwide-first experiment. NOVELTY.md records queries, methods read and access gaps.

## The paired-world construction

A balanced latent proxy B generates three observed report bits X. With probability .2, the second report copies the first; otherwise the reports independently match B with accuracy a. Two observed contexts g have unknown target orientations r_g. The target is Y=B xor r_g.

Y=1 retains its target-event definition. The unknown orientation represents a world's report-to-target relationship, not a software decision to redefine truth after prediction. An inverted world is a hard negative for assuming the reports' symbols already supply the correct target mapping.

The marginal P(X,L|r) is independent of r because summing over balanced B removes the target mapping. Even a perfect population-level checker of report and lineage distributions cannot identify orientation. Adaptive provenance-only query transcripts remain invariant. This is an exact identifiability limit in the declared construction, rather than failure to choose a sufficiently strong detector.

For complementary worlds coupled to the same observations and any forecast p based only on those observations:
[(p-Y)^2+(p-(1-Y))^2]/2 = .25+(p-.5)^2 >= .25.
An unresolved symmetric orientation therefore has minimum Brier .25 at p=.5. With abstention costing .15, stopping and abstaining is preferable under that loss. OBSERVABILITY_PROOF.md gives the elementary derivation and its limits. This is an instance of known theory, not an original impossibility theorem.

An event anchor R is a noisy independent measurement of Y in the intended mode. Unlike a lineage response about L, it can orient the report-to-target relationship. An echo anchor R=X_first remains a function of existing reports, so it cannot identify orientation even though a misspecified learner may treat it as corroboration.

## Frozen protocol and independent-unit accounting

Source/design were published in GitHub freeze commit 04cbe0fb35e80484e3e98a5514de28fbf94c712f and eight remote blobs verified before the scientific run. FREEZE.json hashes seven files; the eighth is the manifest itself. Source, seeds, methods, budget, priors and costs were unchanged after scoring.

There are 24 independent calibration pools: 12 seeds at each source accuracy .65 and .8. Each pool contains four cases in each of two contexts, eight cases total. The pool and separate 128-case held-out observable sample are reused counterfactually under four orientation combinations and three reference mechanisms. This yields 288 evaluation worlds, not 288 independent datasets.

The 2,304 stored calibration rows and 36,864 sampled case rows include those counterfactual repetitions. There are 192 distinct calibration source cases and 3,072 distinct sampled source cases before repetition. Forecast counts measure execution/audit coverage; they are not independent sample sizes for confidence intervals.

The primary family contains genuinely independent .9-accurate event anchors. The controls use independent .5-accurate responses or an echo of the first report. Lineage answers are perfect in all modes. Reference noise uniforms are coupled across variants. Every selector starts with the two orientation probabilities at .5 and assumes anchor accuracy .9. It knows source accuracy and copy prior; this is not simultaneous source-parameter estimation.

Selectors receive source bits, context and revealed responses only. The responder owns hidden B,L,Y and potential reference answers. Raw simulator variables are released for audit, but are excluded from initial observation packets. Held-out outcomes never enter query selection. A separate random stream offset30,000,000 generates the held-out sample. Exhaustive finite outcome expectations provide the primary deployment scores.

## Query budget, inference and decisions

Each method can purchase at most four responses. Every calibration case permits one event anchor and one lineage query, each charged .005. Responses arrive immediately; LA4 does not claim to test delayed or online adaptation. Query expense is divided over an assumed128 deployments. Total loss is terminal decision loss plus actual query charges/128.

The predictor uses the full posterior over each context orientation, summing the latent proxy and lineage per underlying calibration case. Combining an anchor with that case's lineage refines the same likelihood; it is not counted as another independent source. Future-report probabilities integrate the orientation posterior. A predicted event probability p incurs squared error, or the method abstains at cost .15 when p*(1-p)>.15. The query objective uses this model-based expected terminal decision risk, not held-out answers.

LiteralBits assumes both report-to-target orientations are normal and buys nothing. RobustAbstain retains unresolved orientation and stops. ProvenanceOnly purchases four lineage responses. UniformAnchors buys two event labels per context. ConfidentAnchors also balances contexts but chooses the reports most informative about B.

GreedyDecision considers one query's expected reduction in decision risk. TwoStepTable explicitly evaluates a two-query tree with stopping, then replans until the four-query cap. TwoStepRecursive evaluates the identical horizon recursively. These are short-lookahead policies, not globally optimal four-query planners. EntropyGreedy is a stronger conventional information-acquisition control: it selects the response expected to reduce orientation entropy most, while information remains and budget permits. Its objective differs from immediate decision loss.

SRDETypedGate is a transparent heuristic: select high-confidence-proxy event anchors in the least oriented context until confidence .95 or the budget cap. KnownOrientation receives the true orientations free; it is an information-privileged diagnostic, not a fair learned competitor. All other policies have the same observations, response options, maximum budget and charges; they can choose to spend less. Literal/robust baselines and the privileged diagnostic spend zero.

## Independent-reference results

| Method | Total loss | Brier | Coverage | Wrong accepted / 1000 cases | ECE10 | Queries |
|---|---:|---:|---:|---:|---:|---:|
| LiteralBits | 0.2784751 | 0.353545 | 45.75% | 228.75 | 0.29070 | 0.000 |
| RobustAbstain | 0.1500000 | 0.250000 | 0.00% | 0.00 | 0.00000 | 0.000 |
| ProvenanceOnly | 0.1501562 | 0.250000 | 0.00% | 0.00 | 0.00000 | 4.000 |
| UniformAnchors | 0.1304612 | 0.195505 | 16.10% | 4.20 | 0.11485 | 4.000 |
| ConfidentAnchors | 0.1274275 | 0.185020 | 18.40% | 4.80 | 0.05386 | 4.000 |
| GreedyDecision | 0.1316354 | 0.200959 | 21.85% | 16.60 | 0.03862 | 1.958 |
| EntropyGreedy | 0.1291701 | 0.180363 | 24.91% | 18.42 | 0.07941 | 4.000 |
| TwoStepTable | 0.1261965 | 0.197040 | 19.55% | 5.10 | 0.02512 | 2.000 |
| TwoStepRecursive | 0.1261965 | 0.197040 | 19.55% | 5.10 | 0.02512 | 2.000 |
| SRDETypedGate | 0.1313860 | 0.181750 | 24.15% | 19.92 | 0.09282 | 4.000 |
| KnownOrientation | 0.1130249 | 0.146455 | 45.75% | 36.60 | 0.00000 | 0.000 |


Lower loss, Brier, ECE and wrong-accepted fraction are better; higher coverage means fewer abstentions. Wrong accepted is normalized by all cases, not only accepted predictions. Reporting it together with coverage prevents an abstain-everywhere policy from appearing to solve prediction. Brier and ECE include all terminal probabilities, including abstained cases. ECE uses ten equal-width bins.

The primary interval resamples the 12 seed clusters within each source-accuracy stratum, retaining all counterfactual variants within a selected cluster: 1,000 draws, seed99101. It quantifies calibration-pool variation conditional on this exact generator and fixed condition mixture. It does not resample the many paired forecasts as independent trials. Secondary comparisons are exploratory, with no multiplicity adjustment.

Two-step lookahead has the best observed mean decision loss in the intended family, but its primary comparison against one-step and comparison against entropy acquisition do not establish superiority. ConfidentAnchors is close at 0.1274275. EntropyGreedy has lower full Brier than two-step (0.180363 versus 0.197040), reflecting a different tradeoff between probability quality and abstention decisions.

## Uninformative and dependent-reference controls

Independent references with actual accuracy .5, while the learner assumes .9:
| Method | Total loss | Brier | Coverage | Wrong accepted / 1000 cases | ECE10 | Queries |
|---|---:|---:|---:|---:|---:|---:|
| LiteralBits | 0.2784751 | 0.353545 | 45.75% | 228.75 | 0.29070 | 0.000 |
| RobustAbstain | 0.1500000 | 0.250000 | 0.00% | 0.00 | 0.00000 | 0.000 |
| ProvenanceOnly | 0.1501562 | 0.250000 | 0.00% | 0.00 | 0.00000 | 4.000 |
| UniformAnchors | 0.2134364 | 0.310665 | 17.25% | 102.60 | 0.23567 | 4.000 |
| ConfidentAnchors | 0.2003244 | 0.287986 | 13.80% | 79.90 | 0.15724 | 4.000 |
| GreedyDecision | 0.1883627 | 0.274048 | 17.25% | 69.90 | 0.10834 | 1.917 |
| EntropyGreedy | 0.1873096 | 0.277648 | 18.40% | 70.20 | 0.17320 | 4.000 |
| TwoStepTable | 0.1976825 | 0.287108 | 16.10% | 80.50 | 0.12597 | 2.000 |
| TwoStepRecursive | 0.1976825 | 0.287108 | 16.10% | 80.50 | 0.12597 | 2.000 |
| SRDETypedGate | 0.1937336 | 0.275851 | 19.84% | 84.20 | 0.19879 | 4.000 |
| KnownOrientation | 0.1130249 | 0.146455 | 45.75% | 36.60 | 0.00000 | 0.000 |


Pseudo-references that echo the first source:
| Method | Total loss | Brier | Coverage | Wrong accepted / 1000 cases | ECE10 | Queries |
|---|---:|---:|---:|---:|---:|---:|
| LiteralBits | 0.2784751 | 0.353545 | 45.75% | 228.75 | 0.29070 | 0.000 |
| RobustAbstain | 0.1500000 | 0.250000 | 0.00% | 0.00 | 0.00000 | 0.000 |
| ProvenanceOnly | 0.1501562 | 0.250000 | 0.00% | 0.00 | 0.00000 | 4.000 |
| UniformAnchors | 0.2191420 | 0.315229 | 24.15% | 120.75 | 0.26017 | 4.000 |
| ConfidentAnchors | 0.2270516 | 0.328709 | 25.30% | 126.50 | 0.26385 | 4.000 |
| GreedyDecision | 0.2243699 | 0.313802 | 24.15% | 120.75 | 0.17366 | 1.958 |
| EntropyGreedy | 0.2285850 | 0.328778 | 26.06% | 130.28 | 0.26273 | 4.000 |
| TwoStepTable | 0.2269734 | 0.315614 | 25.30% | 126.50 | 0.18120 | 2.000 |
| TwoStepRecursive | 0.2269734 | 0.315614 | 25.30% | 126.50 | 0.18120 | 2.000 |
| SRDETypedGate | 0.2261419 | 0.327889 | 25.30% | 126.50 | 0.26961 | 4.000 |
| KnownOrientation | 0.1130249 | 0.146455 | 45.75% | 36.60 | 0.00000 | 0.000 |


All acquired-query policies can become worse than abstaining when the reference assumption fails. Across the equally weighted mixture of all three mechanisms, two-step total is 0.1836175, versus robust abstention .15. That aggregate is a declared stress-test mixture, not an estimated real-world frequency of bad reference channels.

Echo-world query transcripts and source/provenance marginals are identical across orientation variants, including adaptively selected responses. The auditor checks that invariant directly. Treating an echo as independent may produce confident but unidentifiable conclusions. A true-world lineage receipt and an independent event measurement answer different questions; verifying the former does not certify the latter.

## The abstention plateau and negative results

At source accuracy .65, both one- and two-step decision planners stop without buying any query, yielding total .15. The entropy policy buys four responses and scores 0.1499452; its small observed difference is descriptive and is not promoted as a separate significant result. The typed gate also buys four and scores 0.1501562. Spending on information can fail to cross the threshold for making a useful prediction.

At accuracy .8, one-step total is 0.1132707; two-step is 0.1023930. Calibration-pool variability is substantial. The original pre-freeze unit-test assumption that two queries necessarily escape the .65 plateau was false and was corrected before the protocol freeze. The generator was not tuned to manufacture a two-step win; EXECUTION_NOTES.md preserves the rejected expectation.

The SRDETypedGate scores 0.1313860 in the intended family and is not the best conventional comparator. Table and recursive two-step forecasts match throughout. No advantage is attributed to recursion or to a newly invented grounding mechanism.

## Verification and reproducibility

The CPU scientific run took 6.50 seconds, excluding literature review, audits, reports and publication. It generated 152,064 exact weighted forecasts and 405,504 sampled forecasts, 557,568 total. No GPU or paid Colab allocation was needed.

Twelve unit tests pass: exact observable probability mass and orientation invariance, missing-versus-false distinction, provenance's inability to orient, context-scoped anchors, no repeated queries, outcome normalization, the short-lookahead plateau, recursive/table agreement, the paired Brier bound, counterfactual coupling and dependent echo generation.

The independent auditor imports no experiment runner. It uses a separate evidence-ratio calculation to check all 7,472 acquired responses and their selection rules, 3,168 fitted states, all forecast probabilities, exact atom weights, abstention, Brier/decision loss, ECE, coverage, wrong accepted fractions and query costs. It verifies report/provenance marginal equality and complete echo-transcript invariance. Heuristic context ties are accepted within 1e-12; one first-pass audit exposed such a floating-point tie, and the auxiliary auditor was refined without changing frozen source/results. The maximum numerical error is about 1.23e-15.

A second process reproduced all 11 scientific output contents exactly, excluding gzip headers and runtime metadata. Clean extraction and manifest checks accompany publication. Run python3 -m unittest -v test_la4.py, then python3 run_la4.py, then python3 audit_results.py from the package directory. Scientific runs require only Python3 standard library; optional PDF/figure generation uses matplotlib/reportlab and a DejaVu font.

The release includes raw simulator records, allowed initial observations, acquired-query receipts, fitted states, exact atoms, sampled cases, forecasts, world/aggregate metrics, cluster-bootstrap results, the frozen protocol, source-linked novelty review, observability derivation, tests and independent audit. SHA-256 hashes cover every packaged payload.

## What this says about 1 and 0

A bit is a symbol with a declared variable and relation to the target. B, Y, L and R are distinct binary variables. Source reports can be correlated, inverted or copied. A missing anchor/lineage response is encoded as unknown, not false. A purchase decision is not a truth assertion, and abstention is a loss-based action rather than a third factual outcome.

LA4 supports a precise interpretation of the original hypothesis: source agreement and provenance do not by themselves ground which report-to-target relationship holds. Independent observations can supply that missing information under declared reference assumptions. It does not show that binary computation is fundamentally inadequate or that changing the encoding of 0/1 solves truth. Four-valued logic, concept representation learning, natural-language grounding and affect are not experimentally validated here. Affect F in [0,1], with 0 aversive and 1 pleasant, remains distinct from truth and confidence.

## Limitations and retained inference points

The worlds are deliberately constructed, stationary and small. Source-channel accuracy, copying prevalence and target balance are known. Only orientation is learned. Reference failures are controls, not detected by a new reliability learner. No independent empirical dataset, actual physical repair diagnosis, human cognitive validation or native Blackbird integration is established. There are only 24 independent calibration pools; counterfactual evaluation expands coverage, not statistical independence. Changing the abstention price, query cost, source asymmetry or class balance can change the acquisition policies.

LA4-I1: lineage verification and target grounding are distinct information channels. Supported by the exact marginal/transcript identity and provenance-only control.
LA4-I2: an abstention threshold can make information gathering appear valueless to a short-horizon decision objective. Supported by the .65-source plateau; two-step lookahead does not universally remove it.
LA4-I3: a source echo cannot become independent grounding by being called a reference. Supported by the echo-world invariance and degraded scores.
LA4-I4: the positive independent-anchor result depends on the validity of the anchor channel; the primary two-step-versus-one-step superiority claim remains unsupported.

LA4-R1: which independent operational records can anchor report-to-target meaning, with documented reliability and cost? Check E08's scope before another empirical design.
LA4-R2: can acquisition remain useful when uncertainty about reference independence/reliability is modeled rather than assumed away? Related noisy/correlated active-learning work above must be the baseline.
LA4-R3: would a stronger globally planned or entropy-surrogate policy cross useful decision thresholds under sparse grounding? This is established planning/active-learning territory, requiring an explicit new comparative question.
LA4-R4: how should Blackbird preserve separate evidence fields for claim content, lineage, grounding observation and valence without collapsing unknown into false? This is an engineering consequence to test separately, not a cognitive-theory conclusion.

GitHub directory: https://github.com/MerluseDan/FACO9000/tree/main/research/srde/la4-grounding-audit-2026-11-08 .
