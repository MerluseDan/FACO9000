# SRDE-P9A — Real Git Revision Evidence-Impact Pilot

**Date:** 2026-11-08  
**Status:** Completed, retrospective exploratory pilot; source revisions directly verified via the connected GitHub account; local receipts consistency check passed.  
**Concept:** Extend the P8 evidence-impact system from edited copies of SRDE reports to actual historic corrections in independently authored technical documentation.

## Why this matters

P8 identified whether exact evidence lines survived 240 simulated removals/restorations. That is useful inside its constructed proof graph, but a real document may change meaning while retaining the same text, or preserve the meaning while changing the wording. P9A targeted those failure modes using six real Git commits drawn from **five independent public repositories**, each compared with its actual parent revision and exact Git blob hashes.

This pilot is *not* prospective or a randomized holdout: the six commits were deliberately chosen because their public messages indicated corrections. The author manually assessed five claims as changed and one as still supported. Each revision also supplied one stable-line control selected after inspecting both versions. These methodological choices make the specificity and recall figures optimistic and non-generalizable.

## Two detectors

- **P8-style exact-line check:** alert when the originally cited line disappears anywhere in its source document.
- **P9A scoped-line check:** alert unless the originally cited exact line survives *with the same five preceding source lines*. This is a simple textual context approximation; it does not understand product-version logic, file semantics, or independent scientific truth.

Both methods are applied to identical 12 probes (six claim anchors and six stable controls). The human-assessed status-change label is a separate comparison, not an output the methods can know.

## Results

| Method | True alerts | False alerts | Missed changes | True negatives | Precision | Recall |
|---|---:|---:|---:|---:|---:|---:|
| Whole-file exact-line presence | 3 | 1 | 2 | 6 | 75.0% | 60.0% |
| Exact-line + five-line scope | 5 | 1 | 0 | 6 | 83.3% | 100.0% |

**The improvement comes from the two previously missed changes.** It does not establish 100% recall outside these selected examples.

## Case-by-case observations

| Genuine source correction | Original exact line elsewhere? | Five-line context preserved? | Claim status reviewed |
|---|---|---|---|
| MDN `JSON.parse` reviver's `context` semantics | No | No | Changed |
| GitHub Actions approval expiration per product version | **Yes** | No | Changed |
| Python PEP 694 upload-session file-status enumeration | No | No | Changed |
| Rust Book on direct `.await`, `Pin` and `Unpin` | No | No | Changed |
| GitHub Desktop caches credentials (general claim) | No | No | **Still supported** |
| PyPA `pylock.toml` wheel file URL/path | **Yes, in another section** | No | Changed |

**Important failure A — modified conditional scope.** A GitHub Docs update inserted a product-version conditional around an unchanged sentence about deletion of unapproved runs. Old exact text remained, but its applicability narrowed. P8's file-global line check missed the changed scope.

**Important failure B — duplicate source sentence.** The PyPA correction updated the wheel-file section to point to wheel URLs and paths. The old sentence remained valid elsewhere in the *source-distribution* section. A file-wide line search mistakenly accepted that other occurrence as proof the wheel claim remained supported.

**Important failure C — unchanged meaning, edited wording.** GitHub Desktop documentation simplified outdated password-specific wording while retaining the general statement that the application caches credentials. Both literal detectors generated a review alert, even though the deliberately broad claim did not lose support. These alerts should be *review tasks*, not automatic falsification.

## What P9A establishes

The verified historical revisions show that citation maintenance needs more than exact string preservation. At minimum, its evidence key must bind a source version, document identity, section/location, conditional applicability, and local text context. Context changes trigger review, not a truth verdict. Evidence from multiple quotes in one source must still be treated as one source root, preserving the P8 design.

**No novel algorithmic superiority is claimed.** Similar source/version anchoring, structured-document diffs, and database provenance are established. The novel value, if any, must be demonstrated as a better complete review workflow, with independently curated claims and fair conventional comparators.

## Verification and reproducibility

Every before/after source was fetched directly from its pinned repository path at a full parent/head commit hash. File blob identities were recorded in `real_revision_receipts.json`; the unmodified third-party full documents are **not republished**. `audit_receipts.py` independently recomputes the score aggregation from those receipts. It does **not** independently re-fetch the source files or independently review semantics, so its PASS is correctly called *consistency*, not an independent scientific audit.

- Source-backed complete metadata, including per-case evidence and manually stated reasoning: [GitHub P9A original source receipts](https://github.com/MerluseDan/FACO9000/blob/main/research/srde/portal-experiment-P9-2026-11-08/P9A_REAL_GIT_REVISIONS.json).
- Raw Git commit evidence links and pinned blob identities: `real_revision_receipts.json`.
- The [P8 predecessor](https://github.com/MerluseDan/FACO9000/blob/main/research/srde/portal-experiment-P8-2026-11-08/README.md) remains unchanged.

## Decision / next falsifiable step

**Advance the P8 prototype's evidence identity to contextual/versioned anchors and make review explicit; do not auto-mark a conclusion false.** The next rigorous study should register claims *before* subsequent real revisions occur, use two independent blind reviewers for substantive correctness and relevant product scope, include naturally occurring no-change and pure-reformat edits, and compare complete review cost and critical miss rate against both structured document diff and a conventional dependency graph. No live deployment, host installation or ongoing monitoring was initiated in P9A.
