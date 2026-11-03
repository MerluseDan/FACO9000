# Final arithmetic audit

The first independent arithmetic audit used unclipped saved probabilities and flagged a maximum Brier difference of 0.0000001770563 in extreme raw-score arms. The benchmark consistently clips metric input probabilities to [1e-7, 1-1e-7] before computing every metric, including Brier. After the independent auditor applied that same scoring convention, all arithmetic checks passed. No frozen experiment code, predictions, model settings or reported scores changed. The initial audit result is retained as AUDIT_INITIAL_UNCLIPPED.json, with the final result in AUDIT_RESULTS.json.

The scoring convention is visible in the frozen metrics function. It has no material effect on the conclusions or four-decimal tables. Future protocols should state numerical clipping directly beside each metric definition.
