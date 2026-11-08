# Elementary observational-twin construction
This is an explicit instance of established identifiability/domain-adaptation limitations, not a new theorem.

Let B be balanced binary proxy state; L be a source-copying indicator independent of the target mapping. Generate observed source bits X from B,L by the declared source channel. Context g is observed. For any orientation r_g, define the target Y=B xor r_g. The target event definition is fixed; r specifies the unknown relationship of the reports to that event in a world.

P(X=x,L=l | r_g)=sum_b P(B=b,L=l,X=x), which contains no r_g. Therefore even the full population distribution of X and perfect lineage responses cannot identify r_g. Adaptive sequences that ask only about lineage preserve that property, since each next action/response is a function of the same invariant transcript. Finite-data tests cannot evade an exact population equivalence.

Couple r and its complement with the same B,L,X. Target labels are opposite while every unlabeled observation matches. Any fixed or randomized forecast p based only on that transcript has paired expected Brier:
[(p-Y)^2+(p-(1-Y))^2]/2 = .25+(p-.5)^2 >= .25.
The pointwise identity also holds conditional on any random seed of the learner. Abstaining for cost .15 has lower symmetric decision loss than predicting under unresolved orientation; positive query costs make uninformative provenance purchases worse than stopping.

An independent event anchor R with P(R=Y)=alpha>.5 breaks this symmetry when the source channel is informative about B. A purported anchor that only repeats a source bit does not: its transcript remains a function of X and is invariant to r. Calling such a response independent does not make it grounded. Tests enumerate the distribution identity and paired squared-error identity; the report will also verify them on all saved counterfactual source records.

This construction does not imply all real-world shift is undetectable, that label semantics are arbitrary, or that independent references are infallible. It states exactly what information is missing under this specified observation channel.
