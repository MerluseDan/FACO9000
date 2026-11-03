# SRDE-P5 — Portal Order Memory / Reverse-Path Instability

**Blackbird Intelligence / Proto Alpha — 2026-11-03**

An original exploratory SRDE architecture test in 3-D local coordinates with a simulated scalar F. It asks whether different traversal orders can produce durable location differences over 100 levels even when the original root location becomes unidentifiable. The result concerns a prespecified *synthetic affine model*; it is not evidence about human brains or a new mathematical theorem.

## Summary

- 4,096 independently seeded synthetic worlds; 100 levels per path; seed 20261103.
- Two alternating 100-step paths, `ABAB...` and `BABA...`, contain 50 A and 50 B each yet retain a nonzero order residue.
- Reverse paths with noisy terminal positions amplify error by `a^-100` in the tested contraction family.
- On the constructed event task, order-aware Brier `0.011889` versus order-blind `0.024040`; paired interval of difference `[-0.014084,-0.010143]`.
- **A conventional order-aware closed-form model achieves the same score as SRDE**; this is a representation study, not a general new performance breakthrough.
- The commuting same-anchor control produces zero difference. Same-axis rotational controls also commute.
- Independent audit status: PASS, including all 4096 individual predictions and bootstrap reconstruction.

## Reproduction

Python 3.10+ with NumPy and SciPy is required for the experiment; ReportLab and Matplotlib are needed only for the PDF figures.

Run from this folder (which already contains the frozen protocol):

```bash
python srde_p5.py --out .
python audit_independent.py
```

`srde_p5.py` intentionally uses the same fixed seed and creates an identical synthetic world CSV and metrics JSON. Do **not** overwrite the original archive to claim an independent empirical replication. For a genuinely independent check, run in a separate directory with the frozen preregistration and compare file SHA-256 digests.

## Files

`PREREGISTRATION.md` — publicly locked plan, before the experiment was run.  
`srde_p5.py` — frozen scientific simulation and analysis.  
`synthetic_worlds_4096.csv` — raw 4,096 synthetic cases, portal parameters, generated labels and predictions.  
`results.json` — full metrics, controls, hashes, reverse diagnostics, orientation check.  
`audit_independent.py`, `audit_independent.json` — independent re-scoring without importing experiment code.  
`REPORT.md` — complete research note with limits and formulas.  
`SRDE_P5_Research_Report.pdf` — illustrated two-page report.  
`build_report.py` and `*.png` — PDF and figure build script and charts.  
`execution.log` — original program output.  
`SHA256SUMS.txt` — hashes of the original full-package files.

## Integrity boundary

Our novel work here is an SRDE *interpretation and operator proposal* applying order memory, state dependence, and reverse confidence to a navigable meaning-space architecture. The underlying affine composition and rotation noncommutativity are standard mathematics; the simulation is not an external predictive benchmark. Additional worker quorum, subjective feeling, state-updating valence, learned semantic coordinates, and human cognition **were not tested**.
