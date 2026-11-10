# SRDE-P9B — Prospective Evidence-Revision Reliability Study

**Registration date (Ontario):** November 10, 2026  
**Status:** Baseline frozen; **future data and semantic outcomes NOT YET OBSERVED**  
**Author concept:** Dan Merluse / Blackbird Intelligence, AI-assisted experimental design and coding

## Goal and novelty boundary

Test whether source-versioned, location- and context-aware citation checks provide a more useful *review queue* after naturally occurring documentation revisions than the previous P8 whole-document exact-line detector, while comparing against a conventional source-diff detector. This is a **prospective evaluation of an operational workflow**, not a claim of new annotation mathematics or peer-reviewed proof. Existing methods include W3C Web Annotation TextQuoteSelector, TextPositionSelector, and conventional incremental data maintenance / Git diff.

### Immutable registration

The authoritative frozen registry is Git commit `1c8ce661a82aeda96f794fe287c71b340f5c154a`:

https://github.com/MerluseDan/FACO9000/blob/1c8ce661a82aeda96f794fe287c71b340f5c154a/research/srde/portal-experiment-P9B-2026-11-10/FROZEN_CLAIM_REGISTRY.json

It contains **ten** named current document versions across **five** independent public GitHub repositories, with **one primary and one control claim per document** (20 total). The file paths, immutable repository commit hashes, Git blob SHA-1 identities, line indices, short quoted excerpts, local context, source scopes, and exact claim wording were locked **before** evaluating subsequent revision events. A reduced local mirror of the same identifiers and claims is provided for offline tooling. The historical P9A corrections are not prospective data, even if the same source document later changes again.

### Primary research question and hypothesis

In future main-branch revisions that actually alter one of the ten monitored files, a five-previous-line contextual selector should reduce **critical missed review events** relative to presence of the old exact citation line *anywhere* in the file, at a manageable additional human review burden.

**Falsification:** The contextual method misses as many independently reviewed materially affected claims as exact-line matching, or its extra false review load outweighs reduction in critical misses. No preference is granted without this paired analysis. A conventional Git-diff neighborhood detector can tie or outperform context matching and must be included.

## Predeclared evaluation

- **Unit of observation:** Registered claim × genuinely new monitored source-file revision, including unchanged and still-supported claims. Multiple commits or changes from one repository are *clustered* for uncertainty calculations, not independent scientific replications.
- **Events:** Git default-branch revisions downstream of the pinned baseline; compare exact baseline Git blob with the actual post-commit blob. Report force-push/diverged branches as unresolved, never infer a legitimate forward revision.
- **Methods:** (1) naive whole-document change alarm; (2) P8 whole-file exact-line matching; (3) exact-line plus five preceding baseline lines (W3C-style context selector); (4) conventional Git diff within ±5 lines of the original anchor. Match candidate information, file access, and review thresholds. Record cases where these methods disagree, including version-guard insertions and duplicate text in a separate section.
- **Review status:** An algorithm produces `REVIEW_REQUIRED`, `ANCHOR_PRESERVED`, `NO_CHANGE`, or `UNVERIFIABLE`, **not** a semantic-true/false finding. A trained human should judge whether the original registered claim remains supported, changed materially, lost scope, or cannot be decided. Independent reviewers should assess blinded source snapshots and adjudicate disagreements, recording time and rationale. Until independently reviewed, report **only detection / review-queue counts**, not precision or recall as scientific truth.
- **Primary measurements:** paired critical false negatives and unnecessary review alerts per claim × revision; cost of review (person-minutes), time to identify at-risk claims, fetch/CPU time, and corpus/index setup overhead. Compare per-document and per-repository strata, not just a pooled average.
- **Controls:** ten registered control claims, every unchanged source file in each check, and genuine non-semantic changes or formatting edits when encountered. Do not manufacture fake new revisions. Retain negative/unknown and missing-data outcomes.
- **Inclusion:** ALL later main-branch changes to the ten pinned paths during active observation, not just correction-message commits; empty-change periods stay in the denominator of checks. A path rename/deletion is an exception requiring a documented follow-up source mapping, not silently dropped.
- **Exclusions:** commits and file revisions before the frozen registry, selected P9A historic examples, synthetic unit-test fixtures, source states not confirmed descendants of the baseline commit, and unavailable reads.
- **Analysis:** no tuning or selecting anchors using evaluation changes, calculate exact TP/FP/FN/TN only if labels verified. For small numbers, give absolute denominators, wide uncertainty, and repository-cluster bootstrap or descriptive bounds; do not claim significance with only a handful of revisions.
- **Horizon:** initial 60-day observation review; continue or stop based on predeclared volume and user's direction. A change-watching automation, if successfully created, is a separate task and will not interrupt existing research jobs.

## Engineering preflight versus real evaluation

The accompanying `p9b_review_checker.py` is standard-library-only and read-only toward all upstream repositories. Its deterministic fixture self-test exercises five artificial scenarios: unchanged, scope modification, duplicate line moved/left elsewhere, original line removed, and unrelated append. These are **not prospectively gathered evidence** and shall never be reported as observed accuracy. The caller must supply a new output filename for each scan so historical receipts are never overwritten.

The tool checks Git blob identities of frozen and current files, refuses to silently accept diverged history, and leaves every contextual alert pending human review. The local mirror may be used for implementation; GitHub's immutable 20-claim registry is authoritative if they differ.

## Integrity and limitations

Twenty manually framed claims from documentation that changes at unknown rates may generate few events. The same documents were partly studied retrospectively in P9A, though new revisions after this freeze are genuinely unseen. Reviewers are not yet recruited. The automated checker doesn't parse full conditional products or automatically know that a conclusion has become scientifically false. Published GitHub source files are cited by their exact immutable Git commit and blob hashes; third-party full copyrighted contents are not republished. No CPU latency or precision figure will be quoted as measured prospective performance until an actual post-freeze event is verified and independently assessed.

**Decision:** P9B is a valid frozen prospective *plan*, with an executable engineering preflight, not a completed accuracy study.
