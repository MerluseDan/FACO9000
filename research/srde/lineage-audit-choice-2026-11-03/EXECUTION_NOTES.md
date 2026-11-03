# Execution notes

The first public-freeze publication attempt returned a transient GitHub service error. Readback showed no public FREEZE.json, so publication was retried before scientific scoring. Successful commit faad7f25854b278ce427995f85e9284ba3835c1b was verified against local Git blob hashes. Frozen scientific sources remained unchanged thereafter.

The protocol's statement about no paid service concerns computational execution: no GPU, Colab allocation, paid model endpoint or new compute service was provisioned for this experiment. Literature and publication used existing connected tools; their aggregate billing/credit cost is not established here and is not claimed zero. Query costs in the simulator are abstract loss units.

Draft tool-call formatting errors and an unavailable P5 README route were corrected during preparation; the actual P5 PREREGISTRATION.md was retrieved. They were not scientific runs or held-out outcome revisions. The MDPI direct page returned 429; the same primary text was subsequently retrieved using Firecrawl. The L2M PDF required a local download/text extraction after the web reader rejected its content type. Third-party full texts are not redistributed.

Core code uses only Python's standard library. PDF/chart rendering uses installed matplotlib/reportlab. Runtime is measured for the scientific runner only, not research, design, checks or publication.
