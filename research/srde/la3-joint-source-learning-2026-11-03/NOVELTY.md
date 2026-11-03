# LA3 prior-work/internal-overlap review
Checked 3 November2026 before freeze and scoring. Status: documented robustness extension of LA2, not a new statistical method.

Scientific delta: LA2 learned audit reliability q while fixing source accuracy a and copying prevalence pi; its accurate q could still produce poor decisions. LA3 learns all three parameters, propagates their joint uncertainty into acquisition planning, and compares audit utility against a policy trained on the same posterior and a cheaper fresh-only learner. Two off-grid stationary worlds challenge discrete parameter support. These changes address a demonstrated failure, rather than changing seeds/scale alone.

Prior primary methods inspected:
- Dong, Berti-Equille & Srivastava (2009), Integrating Conflicting Data: The Role of Source Dependence. https://www.vldb.org/pvldb/vol2/vldb09-pvldb47.pdf . Methods section4.3/Algorithm2 explicitly combine source accuracy, dependence and truth. This generic idea is already established.
- Zhao, Rubinstein, Gemmell & Han (2012), A Bayesian Approach to Discovering Truth from Conflicting Sources for Data Integration. https://hanj.cs.illinois.edu/pdf/vldb12_bzhao.pdf . Sections5.2–5.3 inspected: latent truth inference and source-quality learning via collapsed sampling. LA3 uses tiny exact grids rather than claiming a new truth-discovery algorithm.
- Hinne et al. (2020), A Conceptual Introduction to Bayesian Model Averaging. https://journals.sagepub.com/doi/full/10.1177/2515245919898657 . Primary article read for model uncertainty/prediction. Model averaging is established.
- Li & Oliva (2021), Active Feature Acquisition with Generative Surrogate Models. https://arxiv.org/pdf/2010.02433 . Primary PDF retrieved; abstract and framework reviewed. Acquiring observations through model-based decisions has established predecessors.
- LA1 and LA2 public data: https://github.com/MerluseDan/FACO9000/tree/main/research/srde/la2-verifier-learning-2026-11-03 . LA3 directly follows LA2's source-model error finding, with its protocol/data preserved.

Search families: Bayesian source-accuracy/dependence learning, truth-discovery copying identifiability, Bayesian model averaging and active feature acquisition, cost-aware model uncertainty. The initial arXiv HTML URL returned404; the PDF was retrieved instead. This bounded review is not worldwide novelty certification.

Latest chats read, without interruption or messaging:
- Recursive Portal Experiment 6ae9dd53-fd80-83e9-8331-54f1ecee6e48: E05 real air-quality sensor study completed; E06 seeks adaptive prediction plus verification/abstention on another real dataset. LA3 uses no E05 outcomes/data and no real failure-detection task.
- SRDE Research Options 6ae93ab2-549c-83e9-ac03-14d6d1babe3d: P6 checkpoint reconstruction completed, stronger conventional covariance-greedy method won.
- Memory Worker Architecture 6ae93c9a-668c-83ea-8fc9-959a99d55a4d: Study06 distributed HTTP services/authority failure tests completed.
These are source-reported results, not independently rerun here. Real-data E06, reconstruction and distributed authority remain separate work.

Estimand/budgets/controls are fixed in PROTOCOL.json. QOnly isolates source-model learning, JointBMAFresh isolates deployment audit action, NoAuditTrainFresh is a strong cheaper learned baseline, MAP/mean test parameter compression, KnownAll is privileged, FixedFresh anchors LA2's fixed assumptions, and SRDERecursive checks equivalence rather than assuming portal advantage. No originality claim rests on recursive implementation, new names, seeds or the discrete grid.
