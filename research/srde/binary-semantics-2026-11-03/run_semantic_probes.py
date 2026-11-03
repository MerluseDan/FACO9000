"""Exhaustive finite semantic probes; separate from learned prediction benchmark."""
import itertools,json
from pathlib import Path
from run_experiment import evidence_state,fde_not,fde_and,fde_or
root=Path(__file__).parent
states=list(itertools.product([0,1],repeat=2))
tables=[dict(a=a,b=b,neg_a=fde_not(a),conjunction=fde_and(a,b),disjunction=fde_or(a,b)) for a,b in itertools.product(states,repeat=2)]
collapse=[dict(evidence_for=a,evidence_against=b,state=evidence_state(a,b),positive_present_bit=a) for a,b in states]
# Unknown equally likely codebook: in one world symbol 1 means true, in the other false.
scores=[]
for codebook in [0,1]:
    for guess in [0,1]:
        accuracy=sum((bit^guess)==(bit^codebook) for bit in [0,1])/2
        scores.append(dict(codebook=codebook,decoder=guess,accuracy=accuracy))
out=dict(four_state_table=tables,boolean_collapse=collapse,codebook_scores=scores,unknown_codebook_expected_accuracy=.5,anchored_codebook_accuracy=1.,note='Exhaustive toy symmetry demonstration, not learned general meaning. The positive-present bit merges neither with false-only and true-only with both. A probability .5 can also describe either unknown or exactly balanced contradictory evidence; store evidence state separately.')
(root/'results/semantic_probes.json').write_text(json.dumps(out,indent=2)+'\n')
print('16 connective cases, 4 evidence states, 4 codebook/decoder cases executed')
