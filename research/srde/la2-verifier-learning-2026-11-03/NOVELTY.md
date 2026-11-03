# LA2 prior-work and internal-overlap record
Checked 3 November 2026 before held-out scoring. Status: benchmark extension / robustness test, not a newly invented statistical method.

Question: can delayed event labels and selectively obtained lineage references calibrate an imperfect lineage-audit service, and when do resulting decisions repay calibration cost? LA1 assumed audit reliability was known. LA2 learns it, respects delayed observation types, tests selected verification, and charges calibration. Scientific reason: better parameter estimation need not improve a thresholded action policy enough to pay for evidence.

Primary predecessors:
- Dawid & Skene (1979), observer error-rate estimation by EM. Primary full-text methods read: https://crowdsourcing-class.org/readings/downloads/ml/EM.pdf . Error-rate learning from latent classes is established; LA2 uses a small exact grid posterior with explicit source-copy state.
- Hui & Walter (1980), estimating diagnostic-test error rates: https://pubmed.ncbi.nlm.nih.gov/7370371/ . Primary abstract read; full-text retrieval failed (404/timeout). Latent accuracy identification depends on assumptions. LA2 does not claim new identification theory.
- Begg & Greenes (1983), verification subject to selection bias: https://pubmed.ncbi.nlm.nih.gov/6871349/ . Primary abstract read. Verification-selection bias is established; LA2 measures downstream audit decisions under a fully disclosed synthetic selection rule.
- GraphEcho: https://arxiv.org/html/2609.17695v1 ; PQ-EID: https://www.mdpi.com/1999-5903/18/11/582 ; L2M: https://proceedings.mlr.press/v306/kobayashi26a.html . Methods reviewed in LA1 novelty check. Recursive evidence, provenance and active information acquisition already have substantial prior art.
- LA1: https://github.com/MerluseDan/FACO9000/tree/main/research/srde/lineage-audit-choice-2026-11-03 . Exact conventional/recursive tie, cheap known-reliability audits useful only narrowly; wrong reliability harmful. Reuse its decision core verbatim.

Internal chats read before design:
- Recursive Portal Experiment, 6ae9dd53-fd80-83e9-8331-54f1ecee6e48: E04 selective-suspension test completed, E05 timestamped evidence direction. Conversation-reported results, not rerun here.
- SRDE Research Options, 6ae93ab2-549c-83e9-ac03-14d6d1babe3d: P5 complete, P6 selective checkpoint/reconstruction proposal.
- Memory Worker Architecture, 6ae93c9a-668c-83ea-8fc9-959a99d55a4d: Study05 storage/queue implementation complete, distributed switching direction next.
These concern suspension, checkpoint storage and worker architecture, rather than unknown audit-error estimation. No other chat interrupted or messaged.

Search families: Dawid Skene observer error 1979; Hui Walter latent test accuracy 1980; selective labels active verification reliability; worker reliability delayed gold; Begg Greenes verification bias; active learning verification bias; Dawid Skene active selection bias. Bounded search cannot establish worldwide originality. Full-text gaps are disclosed; generic calibration/selection novelty is expressly rejected.

Estimand and budgets: primary paired total-loss difference for two learners on identical selected packets, audit/reference costs and deployment action space. Random verification, no-audit fresh baseline, perfect-assumption baseline, latent-only inference, hard proxy labels, repeated-factor negative control, and known-q diagnostic expose alternative explanations. Independent empirical validation remains open. Freeze hashes accompany the source; no outcome-based tuning.
