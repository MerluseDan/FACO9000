# SRDE-P10 preregistration — operational intelligence navigation

**Frozen study date:** 2026-11-11 (America/Toronto). **Study status at freeze:** pre-holdout / no held-out results.  **Protocol version:** 1.0.

## Research question and novelty boundary

Does a 2D task-state navigation heuristic increase *validated work completed under a fixed execution budget* compared with a strong conventional persistent dependency-graph scheduler with exactly the same task-state, evidence-version metadata, learning history, action selection model, and budget? The alternative use of SRDE as an operational memory/navigation *layer* is under test; no invented theorem or AI superiority assumed.

Prior art includes AMA-Bench (Zhao et al., ICML 2026), Microsoft's STATE-Bench (2026), and LangGraph durable checkpointing. Their actual benchmarks are **not** executed here. This is an intentionally small, fully synthetic, deterministic CPU microbenchmark of task orchestration, not a genuine LLM, browser, or production-work benchmark. Model work is represented by precommitted deterministic stochastic success tables; simulated cost units are *not* token counts or GPU timing. No human cognitive claims.

## Frozen environment

Each world generates six concurrent projects, nine task stages each (54 tasks), a bounded DAG (including cross-project dependencies), ten versioned evidence records, repeating procedural skill types, and deterministic publication/verification criteria. Tasks arrive gradually; scheduled evidence revisions invalidate prior outputs and downstream dependencies. Interrupts reset volatile focus but do not erase persisted graph/recipe state. Every attempted operation passes through the same synthetic executor; stochastic tool outcomes are keyed by world, task, tier, and attempt so policy ordering does not re-roll results. Consequential actions are only virtual and never modify external files/apps.

Five scenario families: `steady`, `churn`, `interrupt`, `decoy`, `shift`. Scenarios cover few/many evidence changes, repeated context resets, misleading spatial proximity, and learned recipe distribution shift. A world has at most 150 decision turns and a fixed synthetic execution budget of **320 units**. Costs (units, inclusive of verification): deterministic 1.5, tiny model proxy 4.5, large model proxy 12.5, validated recipe proxy 1.8; inter-project switch 0.7 (including focus resets). Deterministic success table and confidence limits are in frozen code. Every policy gets the exact same task DAG, evidence events, noisy worker capability, resource costs, and start state.

## Frozen policies and controls

- `recency`: simple arrival-order queue; tracks completed bits but not evidence-version lineage, intentionally weaker and includes explicit stale-output failure controls.
- `fullscan`: conventional *correct* dependency-graph planner with source-version invalidation and tool verification; no procedural recipe cache.
- `graph_cached`: STRONG conventional comparator with exact dependency+version validity, persistent validated recipe reuse, model-tier escalation, and project-locality scheduling.
- `srde`: same data structures, validity proofs, recipe cache, model tiers, and action budget as `graph_cached`, plus a two-dimensional task-coordinate heuristic to bias navigation. No extra observations, hidden oracles, or free memory.
- `srde_no_evidence`: negative ablation of the selected SRDE policy, with evidence-version checks disabled; stale actions and apparent completions are evaluated against independent true validity.

The `srde` coordinate strength `lambda` is chosen **only** by 100 development worlds total (20 per scenario), from `(0, 0.2, 0.6, 1.0)` to maximize mean final correctly validated weighted task value. Ties go to smaller lambda. If zero is selected, `srde` must tie `graph_cached` exactly and the conclusion is a null geometry result. **Holdout:** 400 independently seeded worlds (80/scenario) at precommitted seeds in `p10.py`, never used in development. No model/cost/metric changes after lock. Scripts refuse duplicate scoring unless fresh directory is used.

## Endpoints

**Primary endpoint:** paired mean difference `srde - graph_cached` in final *truly valid* weighted completed-task value, with a whole-world 95% bootstrap CI (fixed bootstrap seed, 4,000 draws). **No claim of a win** unless lower CI > 0, with no increase in invalid-precondition attempts and no increase in average budget; point estimates without positive CI remain exploratory. Report separately per scenario, and include any losses.

**Secondary endpoints:** counts of truly valid completed tasks, stale/unsafe attempted actions, model-tier call counts, validated recipe uses, model/work units expended, budget per validated task, corrected invalidations, interruptions, and independently recomputed final validity. All five methods' per-world raw metrics retained. The `recency` baseline is a deliberately weaker control and cannot establish an SRDE-specific advantage. Strong conventional `graph_cached` is the decisive comparator. The fullscan policy is also conventional and must handle evidence truth correctly.

## Validity and matched-information guard

The true oracle recalculates completion validity recursively from recorded evidence version and exact generation of prerequisite outputs; it is not the planner's perceived status. A task cannot become valid if a required source changes or a prerequisite output becomes obsolete. The developer/holdout seeds and revision streams are isolated. An identical policy with zero lambda must be bit-for-bit equivalent to `graph_cached` under paired task-level randomness. Stale action failures are logged, never counted as completed. Priority coordinates only affect *which ready task to execute next*; they never add missing evidence.

## Limits and follow-up

This simulation tests a deterministic controller and stylized model-call proxies, **not** a trained tiny model, actual search/retrieval, external memory traffic, OSWorld, AMA-Bench, STATE-Bench, human interventions, or true real-world productivity. A real follow-up requires plugging the same controllers into a shared model and STATE-Bench/OSWorld-like stateful tasks, exact token/cost/latency logs, resets, independent human grading, and naturally changing evidence, with a new preregistration.

## Prior-art links

- AMA-Bench: https://proceedings.mlr.press/v306/zhao26bs.html
- STATE-Bench: https://github.com/microsoft/STATE-Bench
- LangGraph persistence: https://github.com/langchain-ai/docs/blob/main/src/oss/langgraph/persistence.mdx
- OSWorld2.0: https://osworld-v2.xlang.ai/
- P8: https://github.com/MerluseDan/FACO9000/blob/main/research/srde/portal-experiment-P8-2026-11-08/README.md
- P9B: https://github.com/MerluseDan/FACO9000/blob/1c8ce661a82aeda96f794fe287c71b340f5c154a/research/srde/portal-experiment-P9B-2026-11-10/FROZEN_CLAIM_REGISTRY.json
