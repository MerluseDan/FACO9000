# SRDE-P9B: Future Citation Reliability Watch

**Status: PRE-REVISION FREEZE — NOT A COMPLETED PROSPECTIVE TEST.**

Ten current public technical documents and twenty claims are locked at an immutable Git commit on 2026-11-10. New commits after that registry are the study's only eligible outcome data.

[Authoritative frozen 20-claim registry](https://github.com/MerluseDan/FACO9000/blob/1c8ce661a82aeda96f794fe287c71b340f5c154a/research/srde/portal-experiment-P9B-2026-11-10/FROZEN_CLAIM_REGISTRY.json).

## Run locally (Python 3, standard library only)

```bash
python3 p9b_review_checker.py selftest
python3 p9b_review_checker.py scan --out p9b_check_YYYYMMDD.json
```

`selftest` checks five **synthetic** fixtures and makes no network call. `scan` reads the pinned original Git versions and latest main-branch source files; it verifies Git blob identities and Git ancestry. It only writes the specified JSON output, leaves upstream repositories untouched, and labels affected citations **needs review**, not false.

Consult `PREREGISTRATION.md` for inclusion, exclusion, scoring, fairness, independent review and prospective evaluation boundaries, and `PRIOR_ART_AND_SCOPE.md` for established previous methods. `registry_mirror.json` is a lightweight local functional mirror, not a substitute for the immutable GitHub registry.

Scientific evaluation remains pending actual future revisions and independent semantic review. Do not interpret offline selftest results as a prospective finding.
