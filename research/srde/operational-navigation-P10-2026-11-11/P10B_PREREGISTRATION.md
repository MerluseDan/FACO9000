# SRDE-P10B — independently seeded conventional-locality challenge

**Date:** November 11, 2026. **Study status at freeze:** follow-up proposed after seeing P10 primary positive outcome; P10B development and confirmation NOT yet scored. This is a *post-P10 hypothesis* with distinct, newly frozen seeds, not part of original P10 primary registration.

## Why the challenger matters

P10's SRDE scheduler used a continuous 2D distance bonus and reduced project switches relative to a standard graph priority scheduler with a **fixed** 0.31 same-project preference. That comparison is not sufficient to establish distinct spatial value, because a conventional graph controller may simply need a larger project-locality bonus. P10B tests this explanation directly.

## Exact matched design

Retain the original published P10 graph, task worlds, evidence revisions, worker success mechanism, procedural recipe cache, decision horizon, simulated model work costs and budget *without any modifications*. The challenger is `TunedGraph`: it uses exactly the conventional graph_cached state, evidence-version validity, recipe cache and model routing, and replaces its fixed project-stickiness coefficient with a validated scalar, **without reading spatial coordinates**. The P10 spatial scheduler remains frozen with `lambda=1.0`, unchanged.

- Conventional project bonus grid: `(0.31, 0.6, 0.9, 1.2, 1.5)`.
- New development: 100 worlds = 20 per original scenario at seeds `1111000 + 10000*i + j` for i=0..4, j=0..19. Choose bonus maximizing mean final correctly valid weighted work, tie lowest bonus. No confirmation seeds may be evaluated in this stage.
- New confirmation: 400 worlds = 80 per scenario at seeds `1311000 + 10000*i + j` for i=0..4, j=0..79; distinct from original P10 development/holdout and P10B development. Paired policies on every world; one evaluation only.
- Primary endpoint: mean paired `SRDE(lambda=1.0) - TunedGraph` weighted validated work (400-world bootstrap 95% CI with seed 20261112 and 4,000 draws). For a *distinct* spatial advantage, CI lower bound must exceed zero and no increase in invalid-precondition attempts or average simulated effort. Positive P10 main result does not license passing a neutral/tied P10B.
- Secondary: truly valid tasks, synthetic effort, context switches, large/tiny/recipe proxy calls, `all_tasks_valid` fraction, distribution-shift strata, failure modes, fraction worlds SRDE better/equal/worse.
- Preserve **negative outcomes** and compare matched information and budget. No tool's numerical success probabilities estimate an actual model's performance. No external/LLM deployment, real human tasks, or originality claim.

The P10B source and this protocol are committed before its development/confirmation. The development-selected challenger bonus must be immutably committed again before confirmation. No revising policies or switching seed sets after scores.

Core frozen source & strong baseline preregistration:
- https://github.com/MerluseDan/FACO9000/blob/92df0c226c9d943b1d15e115350ef643f5d1e68b/research/srde/operational-navigation-P10-2026-11-11/p10.py
- https://github.com/MerluseDan/FACO9000/blob/99002da7cc78a9dc686109c644509b618050603b/research/srde/operational-navigation-P10-2026-11-11/PREREGISTRATION.md
