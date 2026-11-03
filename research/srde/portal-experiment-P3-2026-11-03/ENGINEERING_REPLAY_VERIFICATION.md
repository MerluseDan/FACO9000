# SRDE-P3 engineering replay verification (separate from scientific holdout)

**2026-11-03 | result: PASS.** The first frozen model run produced 165 held-out predictions and both negative-control predictions but failed during JSON report serialization. That exact original `srde_p3.py` and `test_predictions.csv` are preserved without modification.

For functional reproducibility, a separately versioned `srde_p3_repaired.py` changes only the NumPy JSON encoding in two report-output statements (one JSON file write, one console print). No feature, model, hyperparameter, data split, seed, transition, forecast, or metric operation changed.

The repaired version was replayed in an isolated fresh directory (`QA_REPLAY2`) with a fresh validation and a fresh engineering-only evaluation, **not included as new independent scientific evidence**. Both stages exited 0. Its `test_predictions.csv` is byte-identical to the original first sealed run, including all seven method forecasts and both controls. Corresponding model Brier scores are identical. The independently audited first run remains the scientific evidence.

- Frozen model SHA-256: `6562ba9d7a9ecbca8ae70c51d4dec97680a47197e1b22a8c660c035df1c66d5b`
- Repaired model SHA-256: `2eb9f1d36e6740abf47cf786ed3cc19c23ad1bdec0ae2826938793f311277ae0`
- First-run and replay forecast SHA-256: `be37f11329bde7e9279d4eb5102df44c746ac5e5a09243b4e5e6df59c931bc2a`
- Repaired replay exit code: 0.

### Replay command

```bash
mkdir srde_p3_replay
cp PREREGISTRATION.md srde_p3_replay/
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 python srde_p3_repaired.py --stage validate --out srde_p3_replay
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 python srde_p3_repaired.py --stage evaluate --out srde_p3_replay
```

The repaired file is supplied for future reproducibility; the preregistered original file is retained for audit and its failure remains in the logs. Replaying the same historical holdout does not strengthen the original statistical claim.
