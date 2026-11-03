# SRDE-P7 — Compressed Portal Order and Provenance Replay

**Blackbird Intelligence / Proto Alpha | 2026-11-03 | Audited synthetic experiment**

## Result

The 20-byte source-conditioned Jacobian memory reconstructs the responses to new *additive provenance* perturbations with ~2.61447e-8 mean squared error per coordinate across 3,000 independent 100-step worlds. A conventional reverse-product sensitivity representation ties it exactly. Value-only snapshots and recent partial action logs are materially worse at that budget.

The same memory does **not** capture arbitrary structural portal edits. A first-order 32-byte structural derivative is worse than a packed action log on small rotation queries, and fails substantially for a large edit. At 40 bytes, a conventional complete packed 100-step action/provenance log is exact on all supplied queries.

This is an **information-preservation tradeoff within a known affine simulator**, not a new theorem, original path-signature mathematics, externally validated prediction, or demonstration of brain-like reasoning.

## Artifacts

- `PREREGISTRATION.md` — protocol committed before validation or test scoring
- `srde_p7.py` — exact frozen scientific program
- `P7_PREHOLDOUT_FROZEN.zip` — time-separated frozen protocol, code, model selection and weights
- `LOCKED_SELECTION.json`, `snapshot_models.npz` — validation-only choices and decoder
- `PREHOLDOUT_MANIFEST.json` — hash-protected prior selection evidence
- `results.json` — complete family/budget metrics, paired intervals and controls
- `holdout_world_metrics.csv` — 240,000 world-level method/budget/family records
- `holdout_srde_B*.bin`, `holdout_snapshots_B*.bin`, `holdout_recent_log_B*.bin` — actual real-world-sized (synthetic) byte payloads, exactly B bytes per world
- `audit_independent.py`, `audit_independent.json` — independent audit and its results
- `RESEARCH_REPORT.md`, `SRDE_P7_Research_Report.pdf` and three PNG figures — explanatory research report
- `build_publication.py` — publication-only code, no model/scoring changes
- `SHA256SUMS.txt`, `PACKAGE_MANIFEST.json` — bytes and integrity inventory for the delivered archive

## Reproduce

Python 3, NumPy, scikit-learn, pandas, matplotlib and reportlab are used across experiment and publication; CPU only.

On a clean output directory with the scientific source and the original preregistration:

```bash
python srde_p7.py selftest --out <new-directory>
python srde_p7.py validate --out <new-directory>
python srde_p7.py evaluate --out <new-directory>
```

For a frozen-replay evaluation without refitting, copy the exact `PREREGISTRATION.md`, `srde_p7.py`, `LOCKED_SELECTION.json`, and `snapshot_models.npz` into a fresh output directory that contains no holdout results, then call `evaluate`. The runner refuses to overwrite an already-scored holdout file.

## Provenance and limits

The creator's original SRDE research direction and portal vocabulary are credited to Dan Merluse. The computational design, source, audit, and presentation were AI-assisted. The source and protocol were frozen on GitHub and Google Drive before the validation model was selected. The selection lock was also archived before 3,000 independent test worlds were evaluated. The independent audit did not import the experiment implementation.

Known adjacent methods: forward sensitivities, path signatures/iterated integrals, belief-state sufficiency, rate-distortion memory, counterfactual replay. Novelty has **not** been established. Nothing was integrated into FACO software or run on the user's GPU.
