# SRDE-P8 — Evidence Change-Impact Utility Trial (2026-11-08)

**Status at freeze: protocol and seven-source archive prepared; holdout outcomes and benchmark uncomputed.**

## Motivation and genuinely distinct question

Earlier SRDE-P5 established path-order sensitivity in synthetic affine maps, P6's checkpoint scheduler tied risk-only and lost to covariance-greedy, and P7 showed task-specific additive provenance sensitivity but failure on portal structural edits. Previous local E01-E04 studied witness-lineage drift and selective suspension, with conventional equivalences. This experiment does NOT repeat those. It asks a practical operational question: **can a provenance-aware dependency ledger reliably identify which archived conclusions lose their explicit documentary support when an original passage is corrected, removed, or later restored, while avoiding alerts for still-supported conclusions?**

*The proposed computation is established provenance/incremental maintenance technology, not a new theorem.* Closest external research: Green et al. (2007) provenance semirings; Motik et al. (2015) Backward/Forward incremental Datalog materialization; Calautti et al. (2024) Datalog why-provenance; exact retrieval links in `PRIOR_ART.md`. This test evaluates applied usefulness for Blackbird research evidence, not uniqueness or AI semantic understanding.

## Immutable material and support interpretation

- Seven verbatim markdown research reports from the previously completed P1-P7 archives, frozen by SHA-256 in `SOURCE_MANIFEST.json`; 15 exact-line anchors in `evidence_cards.json` and 20 hand-authored claim cards, some recursively depending on other cards.
- Each claim has explicit OR-of-AND proof paths and a minimum number of **distinct document roots** for applicable proof paths. Two quotations from one report do not count as independent documents. Different reports are **not** proven statistically independent studies.
- 'Supported' means at least one declared citation proof remains present in the source copies with sufficient distinct roots. It does **not** mean the scientific claim is empirically true. No automatic LLM-generated citation edges and no access to sensitive documents.
- The source reports are NEVER edited in place. All adversarial changes operate on independent scratch copies and/or a virtual evidence toggle.
- End-user outputs must show title, status, citations, which anchors vanished, and whether alternate proof paths still support the claim. Unrelated paragraphs must not count as deletions of an anchored line.

## Methods compared

1. `full`: reread all seven copied reports and reconstruct every evidence and claim status from first principles after every change (ground-truth reference).
2. `index`: reread the changed document only, update the indexed evidence, and propagate status changes through exact dependency paths, including alternate proofs and multi-level descendants. The strongest comparator is *semantically identical conventional graph propagation*, not an artificially weak baseline. We will compare accuracy and time but will NOT claim algorithmic uniqueness.
3. `sqlite`: SQLite reverse-edge index with recursive candidate lookup, then the same proof semantics. Includes lookup and update timing, never credits SRDE with exclusive information or a faster language/runtime for no reason.
4. `naive`: flag all claims reachable from a changed document, including unchanged paragraph edits and claims with still-valid alternate proofs. Report false alerts; it is a **weak operational ablation**, not a state-of-the-art comparator.

## Prespecified evaluation

- `real_report_edits`: a deterministic stream of **240** edit/restore/unrelated/duplicate-relabel events in separate copies of the seven actual reports. Seed 20261108. The event stream is constructed after source, code, and this protocol are publicly frozen. Every event is fully rechecked against the independent all-document reference. Measure supported/unsupported status parity and exact changed-status alerts versus full recomputation, naive over-alert, elapsed per-event times, and file-read counts. Fixed-seed 2,000 bootstrap resamples of event-level speed ratios and alert differences are descriptive only.
- `synthetic_scale`: **300 independent workspace replicas**, each deriving 15 citation anchors and 20 claims from the genuine report template (explicitly synthetic workspaces), with 240 deterministic evidence toggles using seed 20261109. Compare full recomputation, native reverse-edge propagation, and SQL recursive-candidate propagation with identical statuses. Report wall/CPU time, node/edge counts and timing limitation; scale results must never be presented as timings from 300 genuinely independent document sets.
- `negative controls`: unrelated textual line edits, duplicated quotations from the same original report, an invalidated proof with a still-valid alternate, a multi-level dependent claim, and restoring a removed anchor. One test claim explicitly requires 2 document roots but has only 2 anchors from the same file and must remain unsupported.
- **Primary success:** 100% agreement with full recomputation over 240 events including all 20 card statuses (4,800 world-claim comparisons), with no missed changes and zero false alerts from the indexed monitor. The visible reviewer queue must contain at least two genuine, traceable changed citations and accurate alternate-support explanations. No minimum speed advantage is assumed.
- **Practical efficiency success:** on the 300-workspace synthetic scale, indexed method processes <=20% of proof checks used by full recomputation for single-source edits. This is a computational property conditional on sparse updates and maintained extra indexes, not a new mathematical discovery.
- All actual tests and timings remain visible even if they fail. No retuning after event results, no post-hoc threshold changes.

## Security and generalization boundaries

- All sources are old SRDE project Markdown reports. Claims are a hand-written manifest; no model understands arbitrary prose. Corpus origin and provenance are author declared, not cryptographically authenticated beyond archived SHA-256. No native FACO installation or GPU activity.
- External-source version changes are *emulated on copies*; this is a practical workflow acceptance test, not a live alert service or a scientifically independent real-data forecast.
- Strong incremental DB systems already address this problem; a conventional index that matches is evidence of implementability, not SRDE superiority. Operational usefulness must be described honestly and qualified by the small actual-corpus size and manually defined dependency maps.
- No editing, replacing, or deleting existing Drive or GitHub research reports. Publish new P8 evidence only.

## Reproduction

`python3 srde_p8.py --help`, `python3 srde_p8.py selftest --project .`, `python3 srde_p8.py evaluate --project .`, then `python3 audit_independent.py --project .`. All Python standard library; CPU-only. Evidence snapshots are content-addressed and raw event outcomes retained in `event_trace.csv` and `results.json`.
