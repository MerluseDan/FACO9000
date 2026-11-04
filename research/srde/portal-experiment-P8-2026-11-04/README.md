# SRDE-P8: Nonlinear portal memory vs entropy-coded history

**Completed and independently audited November 4, 2026.** 2,400 synthetic 100-level paths; 268,800 raw forecasts/family score rows. Negative main result; ordinary entropy-coded chronology dominates finite-rotation Taylor sketches. No mathematical or cognitive novelty claim.

- `PREREGISTRATION.md`: frozen protocol, prior-art overlap audit and prospectively frozen H1–H4.
- `srde_p8.py`: immutable model/generator/codecs (hash-frozen before holdout).
- `LOCKED_VALIDATION.json`: validation counts, hashes and holdout unopened state.
- `results.json`: all methods, budgets, query families, hypothesis intervals, negative controls.
- `RESEARCH_REPORT.md` / `SRDE_P8_Research_Report.pdf`: scientific report, charts and limitations.
- `audit_independent.py` / `audit_independent.json`: independently re-score 268,800 rows and recover all 4,124 complete and 5,476 fallback entropy-log payloads.
- `source_and_truths.npz`: source action/provenance per world, true nonlinear query terminal outputs.
- `all_forecasts.npz`: 7 method forecasts at each of 4 budgets from actual decoded per-world bytes.
- `test_world_metrics.csv`: every per-world method/family loss and sign-error.
- `actual_payload_*.bin`: exact stored memory bytes for each method/budget.
- `nonlinear_radius_diagnostic.csv`: **exploratory post-hoc fresh-seed** angle validity study, never used for model tuning.
- `SHA256SUMS.txt`, `ARCHIVE_MANIFEST.json`: exact-file provenance.

The 40-byte full-log error is 0 due to lossless coding of the known source, not a new theorem. Prototype and dataset are fully synthetic; no GPU, no app release.

## Source links

GitHub repository: https://github.com/MerluseDan/FACO9000/tree/main/research/srde/portal-experiment-P8-2026-11-04/

Blackbird Google Drive folder: https://drive.google.com/drive/folders/1UPsj4Ay8XiE9CmPpJM4LmuMMr8XBoLm9
