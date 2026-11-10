# SRDE-P9B prior art and claims of novelty

This experiment does not invent quote anchoring, prefix/suffix matching, line offsets, source-version hashes, Git diff, or database incremental view maintenance.

- W3C Web Annotation Data Model: `TextQuoteSelector` with exact, prefix and suffix; `TextPositionSelector`; resource states and source selectors. https://www.w3.org/TR/annotation-model/
- Gupta, Mumick & Subrahmanian (SIGMOD 1993), *Maintaining views incrementally*: https://doi.org/10.1145/170036.170066
- Git native commit and blob identifiers, ordinary diffs and compare history: already implemented in Git.
- P8 internal prototype used exact document lines with manually curated AND/OR proof paths and produced the same results as SQLite dependency tracking in its synthetic edits.
- P9A retrospective pilot on six selected actual revision pairs found whole-file line matching missed context-specific changes where the original text survived elsewhere. P9A was not blind, representative, or independent review.

**P9B original contribution sought:** measured reliability and review labor of a *prospectively frozen* evidence-monitoring workflow on revisions that actually occur after the starting point, with equal-information conventional baselines and negative controls. A better outcome would establish useful engineering applicability under the tested conditions, not mathematical novelty.
