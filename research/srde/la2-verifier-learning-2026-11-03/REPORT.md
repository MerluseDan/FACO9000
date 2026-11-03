# SRDE LA2 — Learning an imperfect verifier does not guarantee better decisions

Executed 3 November 2026. Research direction: Dan Merluse. Protocol, software, analysis, literature review and audits are AI-assisted.

## Main finding

Typed delayed feedback reduces error in estimating the lineage verifier's reliability. Across the frozen mixture of 160 calibration worlds, its q mean absolute error is 0.02291, versus 0.09360 for selectively verified counts and 0.04357 for randomly verified counts.

The primary paired result favors typed inference over selected counts: total loss difference -0.000369781, with a stratified calibration-world bootstrap 95% percentile interval [-0.000471281, -0.000263150]. They receive identical selected observations, incur identical acquisition charges and use the same deployment action space. This is a conventional likelihood correction in a disclosed synthetic benchmark; it is not a newly invented statistical method.

The broader decision result is negative at the primary 512-case amortization horizon. Typed mixed total loss is 0.118977883; fresh-only is 0.117320490. The mixed learner costs +0.001657393 more per case overall. Latent-only conventional Bayes, which avoids reference-query costs, also has lower overall total loss (0.118790979). Better q estimation is not sufficient to justify buying verification.

SRDETypedRecursive and MixedSelectedBayes have identical fitted posteriors, probabilities, action traces and abstention decisions on every exact and sampled case. No recursive-portal advantage is established.

## Why this experiment follows LA1

LA1 assumed verifier reliability q was known, and showed cheap perfect lineage audits can sometimes beat fresh evidence. LA2 instead learns q from delayed event outcomes and delayed, selectively requested source-lineage references. It then asks whether the learned policy repays the calibration cost. This changes the unknown parameter, information arrival, selection mechanism and cost estimand, rather than merely changing seeds.

The other experiment chats were inspected before design: E04/E05 selective suspension and timestamped evidence; P5/P6 path ordering and limited-storage reconstruction; Study05 worker storage/queues and proposed distributed switching. Those conversation-reported results were not rerun here. No other chat or running job was interrupted.

Observer-error learning and verification bias have longstanding precedents. [Dawid & Skene, 1979](https://crowdsourcing-class.org/readings/downloads/ml/EM.pdf) estimated observer error rates with latent true labels. [Hui & Walter, 1980](https://pubmed.ncbi.nlm.nih.gov/7370371/) studied error-rate identification under assumptions. [Begg & Greenes, 1983](https://pubmed.ncbi.nlm.nih.gov/6871349/) addressed selective verification. NOVELTY.md records read scope, search families, access gaps and recent provenance-related predecessors. Classification: SRDE benchmark extension and robustness test. Worldwide originality is not certified.

## Frozen design and leakage boundary

The protocol and six source/design files were publicly frozen in GitHub commit 684f1974e7a1cdee9ca19c5a4d575283a61c04f5 before the scientific run. The experiment uses 20 seeds per condition, eight conditions and 128 calibration cases per world. Conditions cross true audit reliability q in {1,.8,.5,0} with actual source accuracy .8 or .65. The learner assumes .8 throughout. The .65 family is source-model misspecification, not temporal drift.

An event label Y arrives five time steps after each case. A requested perfect simulated lineage reference L arrives 17 steps after issue, twelve after Y. Calibration freezes at time128; 124 event labels can be visible. References requested after time111 have not arrived, but their costs are charged. Requests occur only after Y is known, with a maximum32 per strategy. Random verification requests with probability .25; selected verification requests with probability .8 when the audit agrees with the model's MAP lineage, otherwise .1. Selection uses observed x,Y,z and never hidden L.

All learners see sanitized packets. The data release additionally includes hidden simulator variables for audit; they are never passed to learners. Deployment uses a separate seeded stream offset by10,000,000. The fixed finite outcome distribution is exhaustively evaluated as a separate exact expectation. There was no parameter selection on deployment scores.

Each learner receives128 audit reports at cost .00375 each, plus .003 for every requested lineage reference, even pending requests. The q posterior starts uniform over101 values from0 to1. Its mean is quantized to .01 for the decision planner. This is a plug-in posterior-mean policy, not a Bayes-adaptive planner integrating q uncertainty. q remains fixed during deployment.

Deployment reuses the unchanged LA1 three-slot decision problem: stop, acquire up to two fresh reports at .015 each, or purchase one lineage audit at .00375. Abstention costs .15. Otherwise terminal loss is squared probability error, plus query cost. Total per-case loss also adds calibration cost divided by H in {64,512,4096}. H is a counterfactual number of stable deployments sharing calibration; it is not the sampled test-set size. The sampled set has128 held-out cases per world regardless of H.

## What the learners mean

LatentBayes uses one correctly marginalized factor per report, with whatever Y has arrived, and no lineage references. TargetHardCounts wrongly treats MAP-inferred lineage from x,Y as verified lineage. RandomVerifiedCounts and SelectedVerifiedCounts use only arrived verified lineage and ignore the rest; the latter is a deliberately exposed verification-bias baseline. MixedRandomBayes and MixedSelectedBayes use all reports, replacing a marginal factor with the finer verified-lineage factor when it arrives.

For a report, t=P(L=z|x,Y observed so far), and its q-dependent factor is q*t+(1-q)*(1-t). If lineage is verified, t becomes the indicator L=z. Later evidence refines the same report's likelihood; it does not create another independent report. Selection depends on already observed x,Y,z, so its probability is constant in q for that recorded packet; conditioning on those observations makes the selection mechanism ignorable in the full likelihood. Counts that discard unverified packets lose that protection.

DoubleCountSelected deliberately multiplies overlapping issue-time, event-label and lineage factors from the same report. It is a negative control, not an acceptable independent-evidence interpretation. SRDETypedRecursive uses the same typed posterior as MixedSelectedBayes and recursively solves the same action graph that the conventional policy solves by backward induction. Both have identical information and actions. KnownAuditQ receives the true q without calibration charge; it is an information-advantaged diagnostic, and still assumes the source accuracy .8. It is not a full oracle in the misspecified family.

## Primary metrics: all eight frozen conditions

| Method | q mean absolute error | Deployment loss | Total at H=512 | Brier | ECE (10 bins) | Forecast coverage |
|---|---:|---:|---:|---:|---:|---:|
| FreshOnly | — | 0.11732049 | 0.11732049 | 0.13624293 | 0.06032 | 71.93% |
| AssumePerfect | — | 0.12039024 | 0.12039024 | 0.14569508 | 0.06480 | 70.74% |
| LatentBayes | 0.03066 | 0.11785348 | 0.11879098 | 0.13824021 | 0.06124 | 72.44% |
| TargetHardCounts | 0.14742 | 0.11732634 | 0.11826384 | 0.13629912 | 0.06040 | 71.95% |
| RandomVerifiedCounts | 0.04357 | 0.11793911 | 0.11905122 | 0.13845927 | 0.06142 | 72.44% |
| SelectedVerifiedCounts | 0.09360 | 0.11822567 | 0.11934766 | 0.13929727 | 0.06201 | 72.41% |
| MixedRandomBayes | 0.02360 | 0.11787970 | 0.11899181 | 0.13831742 | 0.06104 | 72.44% |
| MixedSelectedBayes | 0.02291 | 0.11785589 | 0.11897788 | 0.13824891 | 0.06106 | 72.44% |
| DoubleCountSelected | 0.02642 | 0.11786367 | 0.11898567 | 0.13830319 | 0.06099 | 72.44% |
| SRDETypedRecursive | 0.02291 | 0.11785589 | 0.11897788 | 0.13824891 | 0.06106 | 72.44% |
| KnownAuditQ | — | 0.11785500 | 0.11785500 | 0.13822805 | 0.06074 | 72.44% |


Loss and Brier are lower-is-better. Forecast coverage is one minus abstention. Brier and ECE include all terminal probabilities, including abstained cases. ECE uses ten equal-width probability bins and is a post-freeze descriptive diagnostic; it was not used to select the model or declare the primary result. q-error is omitted for nonlearners because their fixed/privileged q values are not comparable parameter estimates.

The typed mixed 95% equal-tail grid interval contains true q in 98.75% of calibration worlds; selected counts achieve 75.00%. These are repeated-simulation interval inclusion rates under this fixed condition mixture, not universal confidence guarantees. Boundary q values0 and1 make coverage and posterior-mean behavior sensitive to the discrete prior.

## Correct source model

| Method | q mean absolute error | Deployment loss | Total at H=512 | Brier | ECE (10 bins) | Forecast coverage |
|---|---:|---:|---:|---:|---:|---:|
| FreshOnly | — | 0.07383000 | 0.07383000 | 0.08396659 | 0.00000 | 78.18% |
| AssumePerfect | — | 0.07588343 | 0.07588343 | 0.09159906 | 0.00727 | 77.00% |
| LatentBayes | 0.03558 | 0.07332660 | 0.07426410 | 0.08446699 | 0.00075 | 78.59% |
| TargetHardCounts | 0.13998 | 0.07380463 | 0.07474213 | 0.08399739 | 0.00010 | 78.20% |
| RandomVerifiedCounts | 0.04296 | 0.07333677 | 0.07445122 | 0.08455269 | 0.00094 | 78.59% |
| SelectedVerifiedCounts | 0.09144 | 0.07341931 | 0.07454087 | 0.08505635 | 0.00194 | 78.55% |
| MixedRandomBayes | 0.02665 | 0.07333143 | 0.07444588 | 0.08450012 | 0.00044 | 78.59% |
| MixedSelectedBayes | 0.02626 | 0.07332646 | 0.07444802 | 0.08446157 | 0.00047 | 78.59% |
| DoubleCountSelected | 0.02918 | 0.07333652 | 0.07445808 | 0.08454232 | 0.00043 | 78.59% |
| SRDETypedRecursive | 0.02626 | 0.07332646 | 0.07444802 | 0.08446157 | 0.00047 | 78.59% |
| KnownAuditQ | — | 0.07331634 | 0.07331634 | 0.08437747 | 0.00000 | 78.59% |


Typed inference lowers deployment loss before calibration charges. At H512, its total is still above fresh-only. At H4096 it falls to 0.073466655, below fresh-only 0.073830004. The pooled expected break-even is about 1140.4 stable deployment cases. This is a descriptive algebraic break-even for this fixed mixture and cost model; it does not establish an operational threshold in real data. Latent-only Bayes remains slightly better in total at H4096.

## Wrong source model

| Method | q mean absolute error | Deployment loss | Total at H=512 | Brier | ECE (10 bins) | Forecast coverage |
|---|---:|---:|---:|---:|---:|---:|
| FreshOnly | — | 0.16081098 | 0.16081098 | 0.18851927 | 0.12063 | 65.69% |
| AssumePerfect | — | 0.16489706 | 0.16489706 | 0.19979111 | 0.12233 | 64.48% |
| LatentBayes | 0.02575 | 0.16238036 | 0.16331786 | 0.19201342 | 0.12172 | 66.28% |
| TargetHardCounts | 0.15486 | 0.16084804 | 0.16178554 | 0.18860086 | 0.12069 | 65.71% |
| RandomVerifiedCounts | 0.04418 | 0.16254146 | 0.16365122 | 0.19236585 | 0.12190 | 66.29% |
| SelectedVerifiedCounts | 0.09576 | 0.16303203 | 0.16415446 | 0.19353818 | 0.12209 | 66.27% |
| MixedRandomBayes | 0.02054 | 0.16242797 | 0.16353773 | 0.19213473 | 0.12164 | 66.29% |
| MixedSelectedBayes | 0.01955 | 0.16238531 | 0.16350775 | 0.19203625 | 0.12164 | 66.28% |
| DoubleCountSelected | 0.02365 | 0.16239081 | 0.16351325 | 0.19206407 | 0.12154 | 66.28% |
| SRDETypedRecursive | 0.01955 | 0.16238531 | 0.16350775 | 0.19203625 | 0.12164 | 66.28% |
| KnownAuditQ | — | 0.16239366 | 0.16239366 | 0.19207862 | 0.12148 | 66.28% |


Typed q estimation is accurate in this particular misspecified family, but the planner still trusts source reports too much. Its deployment loss exceeds fresh-only before calibration charges; amortizing its calibration expense over more cases cannot repair that fixed policy. Even KnownAuditQ loses to fresh-only. This separates verifier reliability from the accuracy of the rest of the inference model.

## Uncertainty and negative results

The primary interval resamples independent calibration worlds within each of the eight fixed conditions, 1,000 bootstrap draws using seed61621. It describes variation from calibration sampling for the declared mixture, conditional on the exact deployment distribution. It does not treat correlated forecasts within one world as independent trials, and it does not generalize across arbitrary worlds. Secondary comparisons are exploratory and are not adjusted for multiple testing.

Random verified counts are much stronger than selected counts. In the correctly specified family, typed mixed minus random counts is -0.000003205 with interval [-0.000026059,+0.000021254], overlapping zero. The broad primary improvement over selected counts should not be read as superiority over all conventional methods.

The double-counting control is only slightly worse in decision loss overall, despite its defective likelihood. Its interval inclusion rate is 92.50%, versus 98.75% for the typed learner. This negative control does not produce a dramatic collapse here. TargetHardCounts has poor q estimation but nearly fresh-only deployment behavior: it often avoids buying audits. This illustrates why parameter accuracy and decision utility need separate metrics.

The q=.5 cases are hard negatives for useful audit information; q=0 cases are perfectly inverted evidence, not absent or neutral evidence. AssumePerfect performs poorly when that assumption is false. Full condition-level fits, posterior weights, forecasts and metrics are supplied so no unfavorable condition is hidden.

## Verification and reproducibility

Executed entirely on CPU in 6.26 seconds for the scientific run; no GPU or paid Colab resource was required. There are 20,480 calibration cases and 20,480 sampled held-out cases. All11 methods produce 253,440 exact weighted forecasts and 225,280 sampled forecasts.

Twelve unit tests pass, covering delayed availability, hidden-variable exclusion, reference caps, pending-query charges, conditional-likelihood identity and unchanged LA1 source identity. A separate auditor imports neither runner and recomputes calibration selection, 1,280 posterior fits, exact atom weights, every forecast probability, chronology, costs, abstention, loss, world metrics and recursive/conventional equality. It checks478,720 forecast rows with maximum numerical discrepancy1.47e-14. A second process reproduced all11 scientific output contents exactly; compressed headers and runtime metadata are excluded from that equality check. Audit and replay receipts are included.

To reproduce with Python3 standard library: run python3 -m unittest -v test_la2.py, then python3 run_la2.py, then python3 audit_results.py. Plot/PDF generation is optional and uses matplotlib and reportlab. The data include calibration_raw, calibration_packets, posterior_weights, exact_atoms, exact_predictions, sample_cases, sample_predictions, fits, world_metrics, metrics and bootstrap outputs. MANIFEST.sha256 covers the packaged files.

## Interpretation of 1 and 0

A bit is a symbol until its variable and semantics are specified. Here Y=0 means the simulated event is false; L=0 means sources are independent; z=0 is a verifier's report about L. q=0 means the verifier always inverts L. Missing Y or L is encoded as null/blank and never converted to false. An abstention is a decision under loss, not a truth value. An inactive or unpurchased audit does not count as evidence against an event.

This study uses probabilistic latent-state inference over binary variables; it does not claim to test all four-valued logics, semantic representation learning, human concept grounding or affect. Affect F in [0,1], with0 aversive and1 pleasant, is a separate variable not present in this task and cannot be inferred from event truth. Conflict, staleness, context and valence remain distinct concepts. Earlier semantic tests should be read alongside this narrower verifier-learning experiment.

## Limitations and next inference points

All data are synthetic and generated within one family. Exact expectations are conditional on that generator, not actual predictive success or validation of human cognition. There is no independent empirical dataset, native Blackbird integration, model learned from text, real provenance verifier, deployment drift, uncertain reference truth, or utility measurement in money. Delayed feedback is used only for one calibration cutoff; no online adaptation occurs. The planner does not learn source accuracy, and q plug-in quantization discards posterior uncertainty.

Inference point LA2-I1: typing observations prevents event feedback from being silently treated as verified lineage. Supported by the mechanism and q-error comparison here; not a universal theorem.
LA2-I2: good verifier calibration can coexist with a wrong event posterior and worse decisions. Supported by the .65 source-accuracy family and known-q diagnostic.
LA2-I3: reference acquisition may be unnecessary when ordinary latent inference already learns enough q to select similar actions. Supported by the latent-only cost comparison.
LA2-I4: no portal-specific advantage appeared. All recursive/conventional forecasts and traces tie.

Research question LA2-R1: can source-model misspecification be diagnosed on held-out observational data before deciding to buy lineage evidence? Related identification precedent: Hui & Walter; the next protocol needs a new bounded overlap review and stronger model-learning baseline.
LA2-R2: what changes if lineage reference labels are themselves wrong, or verification depends on unobserved L? Related precedent: Dawid & Skene and verification-bias literature; no missing-not-at-random robustness is established here.
LA2-R3: can actual non-sensitive provenance data support a fair temporal validation with independent labels and realistic query costs? Requires a sourced dataset and access/license check.
LA2-R4: does integrating q posterior uncertainty change acquisition decisions enough to beat cheap plug-in Bayes? This is established Bayesian decision theory; any next run must be labeled an SRDE extension, not a novel algorithm.

Full source/novelty records: https://github.com/MerluseDan/FACO9000/tree/main/research/srde/la2-verifier-learning-2026-11-03 .
