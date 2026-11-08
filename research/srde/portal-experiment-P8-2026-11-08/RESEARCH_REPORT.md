# SRDE-P8 — Evidence Change-Impact Utility Trial

**Blackbird Intelligence | 8 November 2026 | CPU-only applied research**  
**Origin:** SRDE concept by Dan Merluse; coding, experimental testing and audit are AI-assisted.  
**Status:** Completed; P8 repaired runner was frozen before its only successful scored evaluation; independent audit **PASS**. This is **not** a novel mathematical theorem or a live real-world deployment.

## Executive result: a defensible practical use case

P8 demonstrates a **working citation-change reviewer**: with hand-authored dependency mappings, it can show which prior research conclusions lose the textual support of their cited original passages after a correction, and which conclusions remain supported by an alternate source. This operates on seven unchanged, genuine archived P1–P7 Markdown research reports. The edits themselves were **simulated in scratch copies**.

Over **240 edits**, including **90 removals, 78 restorations, 48 unrelated text edits, and 24 duplicate-wording edits**, the indexed reviewer matched independent full rescanning for all **4,800 claim-status decisions**. It detected exactly **210 evidence-support status transitions** (precision and recall 100% **relative to explicit proof rules**, not to semantic truth). A document-level approach that would flag every possibly affected claim generated **1,429 warnings**, including **1,219 unnecessary warnings** under this definition. That is an **85.3% reduction** in status-change alerts while retaining every actual loss/regain of anchored textual support.

This establishes a reproducible **workflow capability**, not uniqueness: the conventional SQLite reverse-dependency implementation computed equivalent statuses. Incremental dependency maintenance and why-provenance were researched long before SRDE.

## Actual research records and declared evidence

- **7 original research reports** (`corpus/P1.md` through `P7.md`, byte-for-byte copies, immutable originals untouched), source SHA-256 hashes in `SOURCE_MANIFEST.json`.
- **15 exact-line passage anchors**, each with a GitHub source-link, line number, and passage hash. A passage that changes or disappears is marked absent; moving the same complete line does not invalidate it.
- **20 explicitly authored claim cards** with OR-of-AND proof alternatives and recursive relationships. Root lineage is the specific report file. Different reports are separate *document roots* but not independently authenticated scientific studies.
- A deliberate null control requiring two document roots despite citing two P1 passages remains **unsupported**. It cannot manufacture independent corroboration from duplicated text.

There is **no LLM extraction** of arbitrary claims. A citation still present does **not** mean its proposition is necessarily true. The engine reports traceability, not truth, and context changes away from anchored lines may go undetected.

## Prespecified real-report change test

| Measurement | Result |
|---|---:|
| Controlled edits to actual report **copies** | 240 |
| Number of evaluated claim-status decisions | 4,800 |
| All incremental and SQLite statuses equal full scan | **PASS** |
| Independent audit of all status changes | **PASS** |
| Genuine status-change alerts | 210 |
| Indexed false or missed alerts, by declared proof rules | **0** |
| Naive document-level change alerts | 1,429 |
| Unnecessary naive alerts | 1,219 |
| Distinct removed anchors causing status changes | 13 |

A concrete counterfactual: if the archived P1 main-result passage is removed, `C_P1_NULL` loses its support. However `C_NO_UNIQUE_EDGE`, `C_CAUTION`, and `C_PRIORITIZE_VERIFICATION` remain supported by other recorded proof paths. By contrast, revoking P7's additive-memory finding produces three lost-support claims while four other related claims remain backed by alternative statements. The exact reviewer receipts and their citations are bundled.

### Measured time (this container; 240 actual-report-copy edits)

| Method | Combined wall time | Median per event | Source-file reads |
|---|---:|---:|---:|
| Full baseline: reread all seven reports | 109.88 ms | 0.423 ms | 1,680 |
| P8 indexed: reread changed report only | **18.57 ms** | **0.054 ms** | 240 |
| SQLite dependency propagation **only** | 13.65 ms | 0.048 ms | 240 shared upstream reads |

The indexed path was **5.9x faster** than full rescanning in this constrained task. The SQL propagation timing **excludes the one-file reread** and must not be used as an end-to-end victory over the indexed method. Extra dependency indexes are cached by both incremental strategies; speed will differ with corpus size and edit frequency.

## Explicitly synthetic scalability check

The second test replicated the **same** 15-anchor/20-claim template into 300 distinct artificial workspace namespaces. This resulted in **4,500 synthetic evidence anchors, 6,000 synthetic claim nodes, and 240 toggles**. All methods were compared over identical graph statements; this does *not* mean 300 independent real document collections.

| Calculation | Full graph | In-memory index | SQLite index |
|---|---:|---:|---:|
| Total measured time | 13,422.89 ms | **450.77 ms** | 452.83 ms |
| Claim proof reevaluations | 1,440,000 | **839** | Equivalent impacted set |
| All claim statuses equal | Yes | Yes | Yes |

The indexed strategy performed about **1,716x fewer** claim proof reevaluations and was approximately **29.8x faster** in this synthetic sparse-change benchmark. This is a scaling result for conventional incremental recomputation; it does not prove algorithmic novelty.

## Why the provenance paths matter

An edit's location alone does not reveal whether the claim lost all support. Three useful distinctions are preserved:

1. **Retraction vs unrelated edit:** new paragraphs in a report do not necessarily invalidate precise quoted evidence.
2. **Lost path vs lost conclusion:** deleting one explanation can leave another still intact. P8 only raises a *changed-support-status* alert when the support classification changes, but records proof-path changes separately for review.
3. **Same file vs independent document roots:** two passages from one report cannot satisfy a two-document requirement. Root-set alternatives are propagated even if a child status remains true; otherwise a dependent claim could silently lose its required distinct-source support.

A conventional Datalog/provenance engine can compute the same semantics. This is a **specification and QA demonstration**, not new logic or verified causal inference.

## Transparency and independent evidence

The preregistration, source report SHA manifest, manually declared evidence cards, and original Python source were publicly frozen **before holdout**. The first execution failed **before scoring** because the event generator exhausted candidates for removal. That error and its traceback are preserved. A minimal guarded event-planner repair was published as `srde_p8_repaired.py` with `ENGINEERING_REPAIR.md` **before opening any test events**. No claim semantics, source passages, scoring definition, number of events, or output metrics were retuned in response to the result. The repaired event plan produced 90 removals, 78 restorations, 48 unrelated edits and 24 duplicate edits.

The separate `audit_independent.py` **does not import** the evaluator. It independently regenerates all 240 events, 4,800 statuses, each changed-alert set, the 1,429 naive flags, duplicated-document-root null, and the 839 synthetic-scale indexed candidate checks; it also checks every original source file's SHA. Audit result: **PASS**. Timing measurements are *not* independently repeated by the audit.

## Boundaries and decision

**Demonstrated:** for this explicitly curated record set and controlled edits, P8 reliably maintains *textual evidence support* with fewer unnecessary alerts and less processing than a complete rescan. It has an installable, read-only `.deb` demo plus a reproducible CLI archive. The package was inspected and extracted/run under test; **not installed on the user's computer**.

**Not demonstrated:** originality of incremental algorithms, automatic meaning extraction, authenticity/independence of claims, verification of scientific conclusions, live Google Drive/GitHub event monitoring, correctness on arbitrary large documents, human cognition, or real-world production accuracy. The reference documents are real research artifacts, but the edits and scaling worlds were constructed. Existing report text can remain false, outdated, or out of context while its exact cited line still exists.

**Research decision:** P8 meets its prespecified operational accuracy/efficiency gates. Further evidence of field utility should come from a *prospective shadow-run*: independently authored claim maps for a real document workflow, actual changed files and timestamps, human adjudication of review usefulness, and information-matched standard provenance tooling. No live record editing should occur without separate authorization.

## Publications

- Research folder: https://drive.google.com/drive/folders/1WIZSE2JhAZ4_sKaP9xbpqlnvxNrE8JOe
- Public preregistration: https://github.com/MerluseDan/FACO9000/blob/main/research/srde/portal-experiment-P8-2026-11-08/PREREGISTRATION.md
- Fixed experiment source and engineering repair: https://github.com/MerluseDan/FACO9000/tree/main/research/srde/portal-experiment-P8-2026-11-08
- Precedent: Motik et al. (AAAI 2015) https://ojs.aaai.org/index.php/AAAI/article/view/9409 ; Calautti et al. (AAAI 2024) https://ojs.aaai.org/index.php/AAAI/article/view/28914 ; OpenIVM https://openivm.org/how-it-works/ .
