# SRDE LA3 — Learning the sources repairs much more than calibrating the verifier

Executed 3 November 2026. Research direction: Dan Merluse. Software, protocol, literature review, analysis and audits are AI-assisted.

## Result

Learning source accuracy a and copying prevalence pi alongside verifier reliability q materially improves this benchmark. The primary total-loss difference, JointBMAFull minus QOnlyFull, is -0.015882659 with a stratified calibration-world bootstrap 95% percentile interval [-0.016020739,-0.015697568]. At the primary H512 horizon the losses are 0.104022821 and 0.119905480, a 13.25% reduction. Both receive identical packets, charges and deployment action options.

The broader cost comparison remains negative for verification. NoAuditTrainFresh learns source parameters from existing reports and delayed event labels, buys no calibration audits or lineage references, and scores 0.103041187. JointBMAFull scores 0.104022821; its excess loss is +0.000981633, interval [+0.000920829,+0.001033090]. Better modeling helps substantially; extra verification is still not the best total-cost choice at H512.

When calibration expense is already sunk, allowing deployment audits improves on the identical-posterior fresh-only policy by -0.000101039. That is a small incremental action value, not evidence that acquiring the calibration is worthwhile. Audits are purchased on 2.42% of cases.

Model averaging has no overall measured advantage over the simpler MAP or posterior-mean parameter plug-ins. Recursive SRDE and conventional backward induction have identical predictions and action traces in every exact and sampled case. No unique recursive-portal superiority result appears.

## Prior work and distinction from other experiments

LA2 showed accurate q estimates can coexist with poor decisions when source assumptions are wrong. LA3 changes the learned parameter set, propagates its joint uncertainty into decisions, and adds a cheaper learned fresh-only baseline. It tests the source-model explanation of LA2's negative result. The fixed-source baseline now also shares the coarse q grid and Bayesian predictive integration, so this is not a literal rerun of LA2 scores.

These methods have strong precedents. [Dong et al., 2009](https://www.vldb.org/pvldb/vol2/vldb09-pvldb47.pdf), section 4.3, jointly analyze source accuracy, dependence and truth. [Zhao et al., 2012](https://hanj.cs.illinois.edu/pdf/vldb12_bzhao.pdf), sections 5.2–5.3, infer truth and source quality with a probabilistic model. [Hinne et al., 2020](https://journals.sagepub.com/doi/full/10.1177/2515245919898657) explain Bayesian model averaging. [Li and Oliva, 2021](https://arxiv.org/pdf/2010.02433) formulate active feature acquisition with learned generative models. LA3 is a documented SRDE robustness extension, not new statistical mathematics or certified worldwide originality.

The latest chats were inspected before design. E05 completed a real air-quality sensor test, with E06 directed toward another real dataset and verification/abstention. P6 completed limited-storage reconstruction. Study06 completed local distributed authority-service tests. Their results are conversation-reported and were not independently rerun here. LA3 uses none of E05's sensor data and does not test the same empirical failure-detection question. NOVELTY.md records sources, read scope, queries and access gaps.

## Frozen protocol and data

GitHub freeze commit 211fb23fcf96fc303a09fde0709a0cb3aa946a1c was published and seven remote source/design blobs verified before scoring. FREEZE.json hashes six files; the seventh is the freeze manifest itself. No source, model, seed, cost, prior or threshold changed after held-out outcomes were inspected.

There are 120 independent calibration worlds:12 seeds for each of10 fixed conditions. Eight on-grid conditions cross a in {.65,.8}, pi in {.2,.8} and q in {1,.5}. Two stationary off-grid conditions use (a,pi,q)=(.7,.35,.8) and(.9,.65,.2). These test finite parameter support; they are not temporal drift or an independent empirical dataset.

Each calibration world contains 128 cases issued at times0–127. Event Y arrives at issue+5. A selected lineage reference L arrives at issue+17. Calibration freezes at128, making 124 event labels potentially visible. Reference requests use a cap 32 and probabilities .8 if Z agrees with the fixed-model MAP lineage, otherwise .1. Selection sees x,Y,Z after Y arrives, never hidden L. A request still pending at cutoff is charged.

The source-data release includes hidden simulator Y/L for arithmetic verification, but fitting functions receive sanitized observation packets only. Sampled deployment cases use a separate random stream offset20,000,000. An exhaustive finite deployment outcome distribution is also scored. No deployment outcomes select model parameters.

The joint prior is uniform over a in {.55,.65,.8,.95}, pi in {.1,.2,.5,.8}, and q in {0,.25,.5,.75,.8,1}: 96 parameter triples. QOnlyFull uses the same six q values with a=.8,pi=.2 fixed. The posterior uses the full observation likelihood, summing unknown Y/L and conditioning on arrived reference labels. A later reference refines one underlying case likelihood rather than creating another independent vote. The selection probability is constant in parameters once observed x,Y,Z are conditioned upon; it does not depend on hidden L in this design.

## Predictive inference and decisions

JointBMAFull integrates parameter uncertainty into a joint predictive distribution P(x,Y,L,Z|calibration) before conditioning on the new x. Fresh observations update the within-case posterior and potential audit response distribution. This preserves correlations that would be lost by independently averaging a,pi,q first. The global posterior is frozen across deployment cases; the experiment is not online cross-case adaptation.

For this finite family, parameter uncertainty can be exactly integrated into eight hidden states (Y,L,Z). The resulting three-slot action graph permits stop, at most two fresh reports at .015 each, and one lineage audit at .00375. Audit response arrives after its action. Fresh reports have known accuracy .7. Terminal risk is squared probability error, or abstention costing .15, plus query costs. Ties prefer stop, then fresh, then audit with1e-12 tolerance. Impossible model observations fall back to probability .5 and abstention.

The table policy solves the finite graph by backward induction. SRDERecursive independently traverses the same graph recursively. Equal information, actions, costs and outcomes make their equivalence a necessary control, rather than evidence that recursive naming adds capability.

## Comparators and acquisition costs

FixedFresh retains the .8 source accuracy/.2 copy prior and does no calibration. QOnlyFull learns verifier reliability only. JointMAPFull uses the highest-posterior parameter triple, with frozen grid order breaking ties. JointMeanFull inserts posterior mean parameters into one model. JointBMAFresh uses the same joint posterior as JointBMAFull but disallows deployment audits. NoAuditTrainFresh learns a/pi from x and available Y while ignoring Z and lineage references. KnownAll receives the true parameters without calibration; it is privileged and not a matched-information learned competitor.

All methods have the same three-slot deployment cap; removing audit actions defines the fresh-only controls. Every calibrated-audit method pays128*.00375 plus .003 for each requested lineage reference, including pending ones. JointBMAFull and JointBMAFresh pay identical calibration costs. NoAuditTrainFresh pays no incremental audit/reference charge. Existing initial reports and delayed Y labels are assumed already available at no incremental acquisition cost for all methods. This assumption matters to the cheaper baseline's advantage and must be changed if event labels cost money or effort in a deployment.

Total loss adds calibration cost divided by H in {64,512,4096}. H denotes counterfactual stable deployments sharing calibration cost. It does not change the128 sampled held-out cases per world. Cost units are specified loss penalties, not measured money or wall-clock time.

## All conditions: primary exact metrics

| Method | Deployment loss | Total H512 | Brier | ECE10 | Coverage | Audit rate |
|---|---:|---:|---:|---:|---:|---:|
| FixedFresh | 0.11856673 | 0.11856673 | 0.13750856 | 0.08023 | 73.45% | 0.00% |
| QOnlyFull | 0.11878053 | 0.11990548 | 0.13830260 | 0.07944 | 73.65% | 4.65% |
| JointMAPFull | 0.10289115 | 0.10401610 | 0.13441479 | 0.00664 | 56.34% | 2.53% |
| JointMeanFull | 0.10289474 | 0.10401969 | 0.13482804 | 0.00781 | 55.61% | 2.54% |
| JointBMAFull | 0.10289787 | 0.10402282 | 0.13489247 | 0.00801 | 55.55% | 2.42% |
| JointBMAFresh | 0.10299891 | 0.10412386 | 0.13480854 | 0.00805 | 55.50% | 0.00% |
| NoAuditTrainFresh | 0.10304119 | 0.10304119 | 0.13480773 | 0.00961 | 55.40% | 0.00% |
| SRDERecursive | 0.10289787 | 0.10402282 | 0.13489247 | 0.00801 | 55.55% | 2.42% |
| KnownAll | 0.10241534 | 0.10241534 | 0.13370017 | 0.00000 | 56.69% | 1.92% |


Lower loss, Brier and ECE are better. Coverage is one minus abstention. Brier/ECE include all terminal probabilities, including abstained cases. ECE uses ten equal-width bins and was specified before scoring. Averaging is equal across the10 fixed conditions and 12 calibration seeds per condition. It is not an estimate of how often those conditions occur in the world.

The bootstrap resamples calibration worlds within each fixed condition, retaining pairing across methods:1,000 draws, seed 88321. It quantifies calibration-sample variability conditional on the fixed generator mixture and exact deployment outcomes. It does not treat within-world predictions as independent observations. The primary interval is predeclared; secondary intervals are exploratory without multiplicity adjustment.

## Parameter-grid stress

On-grid conditions:
| Method | Deployment loss | Total H512 | Brier | ECE10 | Coverage | Audit rate |
|---|---:|---:|---:|---:|---:|---:|
| FixedFresh | 0.12691512 | 0.12691512 | 0.14700992 | 0.08627 | 72.14% | 0.00% |
| QOnlyFull | 0.12718237 | 0.12830731 | 0.14800248 | 0.08520 | 72.39% | 5.81% |
| JointMAPFull | 0.10837226 | 0.10949720 | 0.14197906 | 0.00040 | 54.32% | 2.54% |
| JointMeanFull | 0.10841674 | 0.10954168 | 0.14259869 | 0.00269 | 53.36% | 2.40% |
| JointBMAFull | 0.10841792 | 0.10954286 | 0.14264647 | 0.00280 | 53.33% | 2.40% |
| JointBMAFresh | 0.10854634 | 0.10967128 | 0.14254395 | 0.00283 | 53.22% | 0.00% |
| NoAuditTrainFresh | 0.10857994 | 0.10857994 | 0.14281544 | 0.00504 | 52.96% | 0.00% |
| SRDERecursive | 0.10841792 | 0.10954286 | 0.14264647 | 0.00280 | 53.33% | 2.40% |
| KnownAll | 0.10837088 | 0.10837088 | 0.14199877 | 0.00000 | 54.26% | 2.40% |


Off-grid conditions:
| Method | Deployment loss | Total H512 | Brier | ECE10 | Coverage | Audit rate |
|---|---:|---:|---:|---:|---:|---:|
| FixedFresh | 0.08517316 | 0.08517316 | 0.09950309 | 0.05607 | 78.66% | 0.00% |
| QOnlyFull | 0.08517316 | 0.08629816 | 0.09950309 | 0.05636 | 78.66% | 0.00% |
| JointMAPFull | 0.08096669 | 0.08209169 | 0.10415774 | 0.03158 | 64.43% | 2.47% |
| JointMeanFull | 0.08080673 | 0.08193173 | 0.10374545 | 0.02828 | 64.60% | 3.11% |
| JointBMAFull | 0.08081768 | 0.08194268 | 0.10387645 | 0.02883 | 64.43% | 2.49% |
| JointBMAFresh | 0.08080917 | 0.08193417 | 0.10386688 | 0.02891 | 64.59% | 0.00% |
| NoAuditTrainFresh | 0.08088617 | 0.08088617 | 0.10277687 | 0.02789 | 65.18% | 0.00% |
| SRDERecursive | 0.08081768 | 0.08194268 | 0.10387645 | 0.02883 | 64.43% | 2.49% |
| KnownAll | 0.07859318 | 0.07859318 | 0.10050580 | 0.00000 | 66.41% | 0.00% |


Within the on-grid family, joint-learning policies are well calibrated under the known generator structure. Off-grid ECE and losses worsen. The off-grid audit-action difference relative to JointBMAFresh is +0.000008508, interval [-0.000086275,+0.000107650]. The interval includes zero: no useful off-grid audit benefit is established.

MAP is slightly better on-grid in this condition mixture. JointBMAFull minus JointMAPFull overall is +0.000006724, interval [-0.000037505,+0.000045897]. Model averaging does not win the overall comparison. Bayesian optimality under a prior does not guarantee the best frequentist score under this deliberately chosen condition mixture.

q=.5 supplies an uninformative-audit control, while correctly known parameters diagnose remaining estimation error. The sampled predictions and every unfavorable condition are retained. No new model or threshold was chosen after observing these comparisons.

## Amortization and practical implication

Across all conditions, joint audit learning's algebraic break-even against NoAuditTrainFresh is approximately 4018.9 stable deployments. At H4096, JointBMAFull total is 0.103038489 and NoAuditTrainFresh is 0.103041187, a tiny difference. This break-even is descriptive, conditional on the frozen mixture and charge assumptions; no bootstrap interval for a newly selected H threshold is claimed.

LA3 supports learning the source model before adding verification complexity. It does not support forcing lineage audits into every decision or treating recursion as a performance improvement. The stronger cheap learned baseline is essential: comparing only against frozen assumptions would overstate verification's value.

## Verification and reproduction

The CPU scientific run took 5.74 seconds, separate from literature review, audits, packaging and publication. No GPU or paid Colab resources were required. It generated 15,360 calibration cases,15,360 sampled held-out cases,165,888 exact forecasts and138,240 sampled forecasts:304,128 forecasts in total.

Eleven unit tests pass. They check delayed packets, exclusion of hidden variables, ignoring audit data in the no-audit learner, posterior normalization, model-mixture conditioning, impossible-observation abstention, recursive/table equality, frozen source identity, and exhaustive reduction of a single-model predictive planner to the previously validated LA1 core.

The standalone auditor imports neither runner. It recomputes 360 fitted parameter posteriors,1,080 predictive joint models, every exact atom mass, every forecast probability, cost, abstention, query timing, world metric, and every action's optimality with a separate recursive dynamic program. It confirms all recursive/conventional traces. Its maximum numerical discrepancy is 1.33e-15. A second process reproduced all 12 scientific output contents exactly, excluding gzip headers and runtime metadata.

From the extracted package directory, run python3 -m unittest -v test_la3.py, python3 run_la3.py, and python3 audit_results.py. Python3 standard library suffices for scientific runs. Optional report/figure regeneration uses matplotlib/reportlab plus a DejaVu font. All source data, sanitized packets, hidden simulator records, posterior weights, predictive joint masses, exact atoms, sampled cases, forecasts, fit summaries, metrics and bootstrap outputs are provided with a SHA-256 manifest.

## Meaning of 1 and 0, limits, and next questions

Y is simulated event truth, L is source copying state, Z is a verifier report about L, and q is that verifier's reliability. Their zeros have different semantics. Missing Y/L stays null rather than false. An unused audit is an action choice, not evidence against a claim. q=0 means consistently inverted reports. Affect F in[0,1] is not present and must not be equated with truth, confidence or source reliability.

All observations are synthetic; this is a statistical robustness test of a small, declared family. No human cognitive theory, semantic grounding, real-world forecast skill, production Blackbird integration, physical source failure detection or universal identifiability result is established. Source errors are symmetric and share one a. Fresh-source accuracy and event prevalence are known. References are perfect. Copying involves only the first pair. No higher-order hidden dependence, adversarial reporting, temporal changes or missing-not-at-random verification is tested. The parameter grid excludes accuracies below.5, imposing a semantic orientation that real unsupervised systems may lack.

LA3-I1: source-model learning explains a large part of LA2's failure under these conditions; supported by the matched QOnly comparison.
LA3-I2: useful deployment audits can still be an unattractive investment once calibration charges are included; supported by same-posterior fresh and cheaper learner comparisons.
LA3-I3: integrating uncertainty changes behavior but does not guarantee a better score in a selected condition mixture; supported by MAP/mean comparisons.
LA3-I4: recursive and conventional planning remain equivalent in this finite problem.

LA3-R1: is lineage verification worth purchasing when event labels also have a cost? Link to active acquisition precedent above. This needs a new cost/information question, not a free relabeling of H.
LA3-R2: how does posterior predictive model checking expose structural dependence errors outside this family? Link to source-dependence prior work; LA3 did not test structural diagnosis.
LA3-R3: can an independently documented provenance dataset estimate the incremental value of lineage labels over learned conventional predictors? Coordinate scope with E06 through read-only overlap checks before designing another empirical run.
LA3-R4: which orientation assumptions permit source truth/reliability identification without independent labels? Link to latent source-quality work. Known labels in this study anchor the meaning of Y=1/0; ungrounded label symmetry remains unresolved.

Public research directory: https://github.com/MerluseDan/FACO9000/tree/main/research/srde/la3-joint-source-learning-2026-11-03 .
