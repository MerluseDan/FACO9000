# SRDE-P6 — Portal Checkpoint Reconstruction

**Blackbird Intelligence / Proto Alpha · November 3, 2026**

**Status:** COMPLETE. CPU-only, preregistered synthetic experiment; independent audit **PASS**. This does **not** establish a new theorem, a model of human feelings, or an SRDE advantage over conventional reconstruction.

## Main outcome

48 development worlds selected **eta=0, gamma=0** for the proposed SRDE priority/orientation checkpoint scheduler. Consequently it was **identical to conventional risk-only scheduling** on all 160 held-out worlds. Each trajectory had 100 steps in 3D and eight paid noisy checkpoints, plus the same free terminal observation. All policies used identical Gaussian posterior mathematics.

| Method | Weighted expected reconstruction error (lower better) |
|---|---:|
| Conventional covariance-greedy | **0.055794** |
| SRDE hybrid = risk-only | 0.073387 |
| Priority-only | 0.073434 |
| Uniform | 0.076932 |
| Random | 0.090015 |

SRDE versus uniform: paired difference **-0.003545**, 95% world-bootstrap interval **[-0.004797, -0.002347]**. Only **44.375%** of worlds individually favored SRDE; almost all aggregate benefit arose from high-noise burst worlds.

SRDE versus strong conventional greedy: difference **+0.017593**, 95% interval **[+0.016502, +0.018714]**. Positive indicates SRDE performed worse. There is **no new method superiority claim**.

## Verification

- All **160** primary held-out world records, method selections and eight-slot budgets passed audit.
- Independent Kalman/RTS smoothing reproduced 8 selected world scores within about `2e-16`.
- The preregistered 4- and 16-slot stress included another **320** budget/world rows; independent audit passed.
- A 12-geometry / 240-draw Monte Carlo check matched posterior expectations closely.
- A priority-shuffle placebo is *uninformative*, because the selected priority coefficient is zero.
- Frozen preregistration and source were published **before** the holdout; full validation lock was saved before evaluation.

## Public files

- [Frozen protocol](PREREGISTRATION.md)
- [Frozen executable experiment](srde_p6.py)
- [Pre-holdout selection summary](LOCKED_SELECTION_SUMMARY.json)
- [Research report](RESEARCH_REPORT.md)
- [Complete result record](results.json)
- [160-world primary raw records](test_world_results.csv)
- [Independent audit output](audit_independent.json)
- [320-row budget stress](budget_stress.csv)

## Google Drive — authoritative complete package

- [Blackbird SRDE-P6 folder](https://drive.google.com/drive/folders/16AEV9VbI0cqY41Max33kq3Bs7eB6SFuR)
- [Complete 28-file ZIP](https://drive.google.com/file/d/1NDZCXIT0oIraFFkb1hIympQjJ9KhIOzC/view?usp=drivesdk)
- [Illustrated 3-page PDF](https://drive.google.com/file/d/1h09UiQ6ZdtkqcZzihQE3EUhfyd03WUs4/view?usp=drivesdk)
- [Independent audit](https://drive.google.com/file/d/1TblivKumgzOpT7J56W7i38KlD3CFLUaN/view?usp=drivesdk)

Archive contains frozen source, protocol, pre-holdout evidence, validation/holdout logs, raw cases, full checksums, independent audit scripts, budget controls, figures, and the PDF. No native FACO application or GPU was changed.

**Novelty boundary:** Optimal checkpoint schedules (Griewank & Walther, 2000), budgeted stochastic trajectory sensors (Tzoumas et al., 2017), and Kalman-informed sensor placement (Mei et al., 2024) are established. P6 contributes an audited SRDE-specific diagnostic and negative result, not an unclaimed mathematical discovery. A further distinct proposal requires a fresh literature/previous-simulation gate.
