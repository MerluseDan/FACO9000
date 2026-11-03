# Accessible-context conversation summary

Coverage: this FACO SRDE E30 Work conversation, retained earlier-turn summary,
visible user requests, existing source and completed run receipts. This is not a
full verbatim transcript. The original ChatGPT conversation was read earlier;
its complete export and unrelated Work conversations are not included. No hidden
reasoning or system instructions are included.

## Objective and accepted constraints

Continue Dan's prepared-but-unrun E30 and run a frozen repaired experiment on his
local NVIDIA machine and free Google Colab. Preserve tracker spelling
**[Faco] SRDV rollout**. The model is Qwen/Qwen2.5-1.5B-Instruct, model/tokenizer
revision 989aa7980e4cf806f80c7fef2b1adb7bc71aa306. Evidence budget <=320 tokens;
methods lexical, temporal_graph, graph_state, srde_activated.

Dan approved both platforms and later approved Colab Terms Agree and a local
smoke after unrelated GPU work finished. No paid compute, termination of others'
jobs, CPU substitution, new Drive OAuth grants, public sharing or deletion.
Latest instruction: consolidate before credits run out, upload privately, stop.

## Milestones and actual evidence

All experiment work below occurred on 2026-10-16; original release dated 2026-10-15.

| Stage | Outcome | Evidence in reused ZIP |
|---|---|---|
| Source recovery | Original local ZIP preserved; CRC clean, 17 payload hashes match; notebook identical to original Library notebook | original/, evidence/original_provenance.json |
| Original regression | 23 tests actually rerun and passed | original/original_tests.log |
| Versioned audited repairs | Structural preflight gate; full resume identity; lossless JSONL-tail recovery; exact key/hash/grade checks; same-generator label; CUDA/dependency lock; durable checkpoints; full-visible-world cost disclosure | e30_repair_v3/source, protocol, tests |
| Pre-run verification | Exact repaired release 41 tests passed; all484 prompt/token manifests audited, max314 evidence tokens; eight consumed model files hashed | evidence/*tests.log, *_expected_prompts.json, MODEL_FILES.json |
| v2 smoke failure | Float16 emitted80 exclamation-mark tokens with no EOS, TRUNCATED; no v2 measured study calls | evidence/local_smoke.json |
| Numeric diagnosis | Weights finite; fp16 activations/logits nonfinite, fp32 forward finite; root cause not established | evidence/local_numeric_diagnostic*.json |
| v3 pre-main repair | Separate immutable float32 freeze for both platforms; questions, corpus, scoring unchanged from repaired v2; exact46-package closure | E30_REPAIRED_v3_FROZEN.zip |
| Local v3 smoke | Correct strict JSON and EOS, excluded from study scores | evidence/local_smoke_v3.json |
| Local campaign | 4 preflight +320 main +160 confirmation completed, process exit0; all484 rows independently validated | local_results_v3/, evidence/local_v3_completed_validation.json |
| Guarded interruption/resume | Own run stopped at160 main rows when another GPU job appeared; resumed unchanged after clear guards; original160-row bytes and runtime metadata preserved | evidence/local_resume_metadata_proof.json, logs |
| Repeated-input audit | 86 repeated-input groups covering174 calls, zero generated-token divergences; within-run evidence only | evidence/local_v3_reproducibility.json |
| Colab setup | Free T4 observed; exact frozen ZIP and manifest verified; isolated46-package environment installed;41-test subprocess returned0 | evidence/colab_live_resource_receipt.json, report |
| Colab failure/blocker | Old smoke cell Python syntax error before execution; browser control later Transport closed; zero model calls | evidence/colab_orchestration_failures.json, colab_browser_transport_latest.json |
| Delivery |154-payload evidence ZIP CRC and all hashes verified, saved privately to Library | LOCAL_COMPLETE_DELIVERY_RECEIPT.json, Library IDs below |

## Findings and later discussion

| Method | Main | Independent-seed same-generator confirmation |
|---|---:|---:|
| lexical |35/80|17/40|
| temporal_graph |28/80|13/40|
| graph_state |43/80|18/40|
| srde_activated |38/80|18/40|

SRDE minus graph_state main: -6.25 percentage points, exploratory world-clustered
95% bootstrap interval [-8.75,-2.50]; confirmation0, interval[-7.50,7.50].
Invalid answers count as wrong. Four preflight answers were wrong but structurally
valid, correctly allowing execution. No outputs were salvaged or cherry-picked.

Dan then asked whether to ditch the system or whether more experiments remained.
The response recommended retaining SRDE as research while questioning this
particular activation rule. A subsequent inspection of existing rows found:
- Main prompts identical between state methods on56/80 questions, changed on24.
  Activation hurt5, helped0 and left correctness unchanged on19 changed prompts.
- Confirmation identical28/40, changed12: hurt1, helped1, unchanged10.
- Both methods retained both designated supporting records in every harmed case.
  This motivates separating evidence ordering, competing records and selection;
  it does not establish the cause of the errors.

Proposed, NOT implemented/run: (1) same-records ordering-only ablation, separately
from selection; (2) changing-memory updates/revocations/dependency failures and
recovery/recomputation cost; (3) evidence-budget/cost comparison followed by
untouched seeds and a second model. E30 stays frozen. Retire/redesign activation
if it repeatedly fails at matched cost on held-out evaluation. The user has not
selected or authorized a new experiment after this proposal.

## Limits and current decision

Real model inference over synthetic software-memory questions; eight main worlds,
four confirmation worlds from the same generator. No real-world validation,
distribution shift or E29 learned-detector replication. Both state methods resolve
the full visible world before evidence truncation; costs are disclosed and counted.
Local mean inference roughly0.42–0.44s; per-call peak allocation6318436352bytes.
Latency is descriptive because intermittent other GPU work triggered a pause.
No cross-platform comparison exists until Colab actually completes.

Current decision: preserve this checkpoint and stop. No new inference, development,
download, test rerun, paid capacity or unrelated-thread work during consolidation.
