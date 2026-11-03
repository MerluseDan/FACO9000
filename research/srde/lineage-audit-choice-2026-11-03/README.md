# SRDE LA1 — lineage audit choice

Completed bounded CPU experiment, 3 November 2026. Read RESEARCH_REPORT.md, NOVELTY_AND_CROSS_CHAT.md and frozen PROTOCOL.md before interpreting scores.

Core reproduction requires Python 3.10+ and only the standard library:

```sh
python3 -m unittest test_experiment.py -v
python3 run_experiment.py
python3 audit_results.py
python3 audit_optimality.py
```

run_experiment.py regenerates results/. Use an alternate output path to preserve delivered results. Scientific JSON and decompressed CSV files are deterministic; gzip timestamps and environment runtime are not. PDF/chart regeneration additionally needs matplotlib and reportlab and is separate from scientific reproduction.

The exact model has no fitted learner. OracleLineageDP gets free hidden information; it is a diagnostic bound. Recursive and bottom-up policies are equivalents. Simulation costs are not bills. No natural affect, human cognition, native SRDE or actual-world prediction is validated.
