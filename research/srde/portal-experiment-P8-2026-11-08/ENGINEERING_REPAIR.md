# SRDE-P8 Pre-scoring engineering repair — 2026-11-08

Frozen protocol and original `srde_p8.py` remain unchanged and publicly committed at GitHub commit `d562344c841b48768cc923b09acd8b937febe644`. The first `evaluate` attempt **failed before any event was executed, no holdout labels or metrics scored**, because the deterministic 240-event planner exhausted all active anchor IDs by repeatedly choosing removals. The exception `IndexError: Cannot choose from an empty sequence` is retained in `evaluation_failure_pre_score.log`.

This repair adds one guard: if the proposed operation has no possible candidates (every anchor is retracted), choose a restoration of a retracted anchor. No data, model, source citations, proof semantics, event count, comparisons, methods, seeds, or scoring code change. The fully amended runner is `srde_p8_repaired.py` and is SHA-frozen and publicly published BEFORE any test events are scored.

This is a **transparent preregistered-run engineering deviation**: relative frequencies of removal/restoration events change only where the former event specification was undefined. Both versions remain archived; any results belong to the repaired-run version and not the original unexecutable code.
