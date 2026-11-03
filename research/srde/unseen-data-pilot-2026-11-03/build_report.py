#!/usr/bin/env python3
"""Render evidence-bound PDF/Markdown report from the two observed result receipts."""
from pathlib import Path
from xml.sax.saxutils import escape
import json, hashlib, textwrap
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image, KeepTogether
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.units import inch

base=Path(__file__).resolve().parent
real=json.loads((base/'real_inductive_results.json').read_text())
syn=json.loads((base/'synthetic_results.json').read_text())
real_auc=real['test']['AUC']; real_mrr=real['test']['MRR']
syn_auc={x:y['auc'] for x,y in syn['metrics']['test'].items()}
shift_auc={x:y['auc'] for x,y in syn['metrics']['shifted_confirmation'].items()}
collected=[]
def note(s): collected.append(s)

note('# SRDE / Blackbird Intelligence — Recursive Portal Discovery')
note('Technical research milestone | 03 November 2026 | Conditional/negative result')
note('Research subject: non-obvious relational paths for inductive prediction on previously unseen entities and worlds. Concept: Dan A. Merluse; computational protocol and local evaluations: AI-assisted.')
note('')
note('## Abstract and decision')
note('Two executed experiments were compared with conventional graph methods. On a public inductive knowledge-graph benchmark, a narrow portal-inspired path-voting algorithm achieved AUC 0.6083, essentially tied with a provenance-aware graph-consensus scorer (0.6080) and below a simple 2–3 hop Katz-style baseline (0.6638). The paired test-query AUC difference Portal–Katz was -0.05549, 95% query-bootstrap interval [-0.08780, -0.02439]. In a separate author-designed synthetic state/provenance setting, the portal scored 0.6903 AUC, below a conventional full-feature gradient-boosted graph model at 0.6937. State/provenance ablations worsened portal performance because those properties directly affect this simulator’s outcome process. No general SRDE predictive advantage is supported. This is not a run of the user’s native installed SRDE engine.')
note('')
note('## Questions and predeclared interpretation')
note('H1: Do paths through non-obvious intermediate nodes improve prediction of withheld true relationships over ordinary graph scores? Compare shared-input, matched-ranking methods and keep every negative result.')
note('H2: Does conditional portal state, lineage-aware quorum, or deeper recursive traversal add measurable signal? Isolate with synthetic ablations and a conventional model given the same features.')
note('H3: Is long-chain connectivity merely inevitable in random graphs? Probe null worlds and shuffled labels.')
note('Decision rule: Claim only a scoped advantage when test/confirmation gains survive strong baselines, independent data, and leakage checks. Finding a path is not evidence that it expresses causation or predicts a future event.')
note('')
note('## Historical context recovered')
note('The 02 November 2026 SRDE Portal-Based Hierarchical State Spaces note specifies conditional transitions with position/orientation/valence/arousal/state/history/provenance, worker votes, temporal decay, and random 100-level counterexamples. Its examples were binary synthetic demonstrations rather than forecasting validation.')
note('The 12 October working paper reported an earlier small local-model retrieval advantage of 55/56 versus static graph traversal 48/56; stronger task-aware graph retrieval later tied SRDE 56/56 on a four-seed independent retrieval holdout. E30 local results (16 October, archived in Drive) scored 38/80 for an SRDE activated method and 43/80 for a graph-state challenger, with 18/40 versus 18/40 in shifted confirmation. Those are separate tasks and not pooled with today’s metrics.')
note('')
note('## Experiment A — public inductive link-prediction pilot')
note('Dataset: GraIL FB15k-237 V1 from kkteru/grail. Original train graph: 4,245 typed triples / 1,594 entities. Inductive inference graph: 1,993 triples / 1,093 entities. Entity overlap is zero. Validation: 206 held-out triples; test: 205. 180 distinct relations. Per test positive, rank it against 20 candidate corrupt-tail negatives sampled deterministically from the relevant relation tail pool where possible; exclude all observed inductive positives from these evaluation negatives. This is unseen-entity generalization, not timestamped future prediction.')
note('Training: enumerate 2–3-hop typed directed paths, mask target edge, learn training-only relation/path association log-ratios from 4,245 positives and 2 sampled negatives per positive, retain 2,378 rules, and cap each query at 12,000 edge expansions. All ranking methods operate on these same enumerated paths. No query hit its cap.')
note('Portal-inspired structural scorer: group supporting paths by their first intermediary as a proxy for independent branches. If two positive independent 2-hop witnesses exist, close the portal there; otherwise traverse evidence to depth 3. Score signed rule support with conservative quorum. Graph-consensus scorer uses the same path evidence without adaptive depth closure. Common neighbors, Adamic–Adar, Katz-style 2–3 hop counting, and relation-aware scoring are conventional controls. Neither state-valence/arousal, learned coordinate transforms, nor true recursive workers were implemented on this public data.')
note('')
note('### Experiment A — observed metrics')
for name in ['Katz','Typed','Portal','GraphConsensus','CN','AA','PortalNoQuorum']:
 note(f'{name}: AUC {real_auc[name]:.4f}; MRR {real_mrr[name]:.4f}')
note('AUC deltas (2,000 paired held-out-query bootstrap resamples): Portal–Katz -0.05549 [ -0.08780, -0.02439 ]; Portal–GraphConsensus +0.000244 [ 0, +0.000732 ]; Portal–Typed -0.00183 [ -0.01000, +0.00707 ]. Only 49/205 test positives contained a positively weighted learned path; a serious coverage limitation.')
note('Validity limits: The 20-negative ranking task is not the official all-entity filtered GraIL evaluation and was not repeated across multiple graph seeds/datasets. No learned modern GraIL, NBFNet, SEAL, factor-graph, or temporal model was run. AUC measures discrimination among these candidates, not calibrated future-event probability. Query bootstrap does not account for dataset/source selection.')
note('')
note('## Experiment B — synthetic conditional/state/provenance stress test')
note('80 training worlds × 150 cases = 12,000 training cases; 20 validation worlds × 150 = 3,000; 60 unseen test worlds × 150 = 9,000; 40 shifted confirmation worlds × 150 = 6,000. Worlds separated by seed groups. State/context matching, orientation, evidence decay, lineage IDs, duplicate witnesses and 2–3 hop depth are observable. The authored outcome generator deliberately uses a signed independent-source evidence sum plus a bonus for two positive independent witnesses. Thus this simulator establishes only conditional feasibility, not independent discovery of biological semantics or causal paths.')
note('Each univariate rule score was calibrated with a training-only logistic regressor. Conventional linear and gradient-boosted comparators received the full observed feature vector, including provenance and state. They had greater model flexibility; this is an equal-information, not equal-parameter-count, comparison. Test data did not participate in fitting.')
note('')
note('### Experiment B — observed ROC-AUC on unseen worlds / shifted confirmation')
for name in ['FullGraphHGB','FullGraphLogistic','Portal','ProvenanceGraph','TypedGraph','PortalNoLineage','PortalNoState','PortalDepth2','Katz']:
 note(f'{name}: test {syn_auc[name]:.4f}; shift {shift_auc[name]:.4f}')
ci=syn['bootstrap']['test']['FullGraphHGB']
note(f"World-bootstrap for Portal–FullGraphHGB: pooled AUC delta {ci['delta_portal_minus_comparator_pooled']:+.5f}; 95% world-mean interval [{ci['ci95_world_mean'][0]:+.5f}, {ci['ci95_world_mean'][1]:+.5f}] from {ci['bootstrap_world_resamples']} whole-world resamples. This is an authored simulator, not a generalizable p-value.")
note(f"Shuffled test labels: Portal AUC {syn['label_shuffle_control']['Portal']:.4f} (approximate chance). 200 random 100-layer null worlds reached mean {syn['100_level_null']['mean_reachable_endpoints']:.3f} /12 endpoints with no true semantics. All four available integrity checks passed.")
note('')
note('## Research insights and inference boundaries')
note('1. Portal paths can expose candidate relational support, but topology-only 2–3-hop counts gave better genuine unseen-entity rankings in Experiment A; non-obvious does not automatically mean useful.')
note('2. Repeated paths from one shared ancestor are not independent evidence. Source-lineage deduplication helps in a simulator where the label is generated by independent sources. A conventional graph model can use that same feature; it is not proof of unique portal intelligence.')
note('3. Context gates, orientation, source reliability, and evidence decay change synthetic predictions. Their useful definitions must be learned or measured from time-stamped real observations, never invented to fit the outcome.')
note('4. Recursive depth can recover weaker indirect evidence but risks path proliferation and spurious consensus. The 100-level null confirms this risk. Require capped search, provenance independence, calibrated uncertainty and an abstain/unknown option.')
note('5. Prediction gain and semantic explanation are different. A model that ranks a hidden relationship does not establish why it exists, causal direction, emotional meaning or the certainty of a future event.')
note('')
note('## Next milestone: strongest falsifiable protocol')
note('Freeze a second test before viewing results. Evaluate FB15k-237 V2–V4 and WN18RR inductive families plus at least one timestamped ICEWS/GDELT-style temporal split; verify rights, schema and source version first. For time-series, prohibit future-edge and future-node metadata from training and candidate generation. Reuse established GraIL/NBFNet or SEAL implementations with matched model selection and negative sets, not weakened stand-ins.')
note('Use 5+ random seeds, hard HeaRT-style negatives, source-ancestor duplicate poisoning, shift in context distributions, shuffled-edge nulls, and target-relation-cold-start cases. Report MRR/Hits@K, AUROC/PR-AUC when appropriate, calibrated Brier/log loss, false-assertion rates, recall/abstention, source-dependence errors, paths searched, CPU/GPU/latency, memory and full setup cost. Code and all raw cases should be available before results are inspected.')
note('Acceptance threshold for a claimed improvement: demonstrate a predeclared practical uplift over the best conventional baseline across multiple independent data families with confidence interval excluding zero and no material worsening in calibration, false assertions or matched compute cost. The current mechanism fails that threshold.')
note('')
note('## Data provenance and reproducibility')
note('GitHub source: https://github.com/kkteru/grail (paths/hashes in real_inductive_results.json). The actual real-data evaluation ran through connected GitHub file retrieval and an isolated JavaScript evaluator; run_real_inductive.mjs is the corresponding independent Node reproduction script for environments with repository file access, but no second full-data local rerun was completed because this sandbox could not reach the GitHub raw endpoint. A synthetic fixture self-test of the script is distinctly labeled and excluded from the results bundle.')
note('The synthetic Python experiment was run locally with numpy/scikit-learn on the CPU. FROZEN_PROTOCOL.json records the exact evaluation design and seed/world IDs, synthetic_results.json the full measurements, and synthetic_test_cases.csv the individual held-out cases. Historical claims are linked to earlier research files, not silently treated as new results.')
note('')
note('## References')
note('1. Merluse, D. A. SRDE: Portal-Based Hierarchical State Spaces for Pre-Event Inference, v0.1, 02 Nov 2026; original source in user Library.')
note('2. Merluse, D. A. FACO-SRDE Working Paper, 12 Oct 2026; original source in user Library.')
note('3. FACO-SRDE E30 Local Results Report, 16 Oct 2026: https://drive.google.com/file/d/1rWVGiB4-ngjEnNDwP-apC6U3U_kfb1Kt/view')
note('4. Teru et al., Inductive Relation Prediction by Subgraph Reasoning (GraIL), ICML 2020: https://github.com/kkteru/grail')
note('5. Li et al., Evaluating Graph Neural Networks for Link Prediction: Current Pitfalls and New Benchmarking (HeaRT), 2023: https://arxiv.org/abs/2306.10453')
note('6. Zhang et al., Revisiting Graph Neural Networks for Link Prediction (SEAL), 2020: https://arxiv.org/abs/2010.16103')

md='\n'.join(collected)+'\n'
(base/'RESEARCH_REPORT.md').write_text(md)

# Charts: no imposed palette; matplotlib defaults.
fig,ax=plt.subplots(figsize=(9,3.3))
names=['Katz','Typed','Portal','GraphConsensus','CN']
ax.bar(names,[real_auc[k] for k in names])
ax.set(ylim=(0,.8),ylabel='Held-out AUC',title='Inductive FB15k-237 V1 | 205 unseen relationships')
for i,n in enumerate(names):ax.text(i,real_auc[n]+.015,f'{real_auc[n]:.3f}',ha='center',fontsize=9)
fig.tight_layout();fig.savefig(base/'real_auc.png',dpi=150);plt.close(fig)
fig,ax=plt.subplots(figsize=(9,3.5))
names=['FullGraphHGB','Portal','ProvenanceGraph','No lineage','No state','Depth 2','Katz']
keys=['FullGraphHGB','Portal','ProvenanceGraph','PortalNoLineage','PortalNoState','PortalDepth2','Katz']
y=[syn_auc[k] for k in keys]
ax.bar(range(len(keys)),y);ax.set_xticks(range(len(keys)),names,rotation=20,ha='right',fontsize=8)
ax.set(ylim=(.48,.77),ylabel='Held-out AUC',title='Synthetic conditional-state worlds | 9,000 unseen cases')
for i,v in enumerate(y):ax.text(i,v+.01,f'{v:.3f}',ha='center',fontsize=8)
fig.tight_layout();fig.savefig(base/'synthetic_auc.png',dpi=160);plt.close(fig)

styles=getSampleStyleSheet()
styles.add(ParagraphStyle(name='DocTitle',parent=styles['Title'],fontSize=19,leading=24,spaceAfter=12,textColor=colors.HexColor('#122538')))
styles.add(ParagraphStyle(name='SectionHead',parent=styles['Heading2'],fontSize=12.5,leading=16,spaceBefore=18,spaceAfter=7,textColor=colors.HexColor('#183c52')))
styles.add(ParagraphStyle(name='Subsection',parent=styles['Heading3'],fontSize=10.7,leading=14,spaceBefore=12,spaceAfter=5,textColor=colors.HexColor('#1e4b60')))
styles.add(ParagraphStyle(name='BodyMain',parent=styles['BodyText'],fontSize=9.2,leading=13.7,spaceAfter=9))
styles.add(ParagraphStyle(name='SmallMain',parent=styles['BodyText'],fontSize=8.1,leading=11.2,spaceAfter=7))
styles.add(ParagraphStyle(name='DeckSub',parent=styles['BodyText'],fontSize=10.2,leading=15,spaceAfter=16,textColor=colors.HexColor('#4d6170')))
styles.add(ParagraphStyle(name='Tiny',parent=styles['BodyText'],fontSize=7.4,leading=10))

def esc(s):
    return escape(str(s)).replace('–','-').replace('—','-')

def table(data, widths):
    cells=[]
    for row in data:
        cells.append([Paragraph(esc(v),styles['Tiny']) for v in row])
    t=Table(cells,colWidths=widths,repeatRows=1,hAlign='LEFT')
    t.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e5edf2')),
        ('VALIGN',(0,0),(-1,-1),'TOP'),
        ('LINEBELOW',(0,0),(-1,0),.65,colors.HexColor('#a4b4be')),
        ('LINEBELOW',(0,1),(-1,-1),.25,colors.HexColor('#dce4e9')),
        ('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),
        ('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)
    ]));return t

story=[]
def para(s,style='BodyMain'):story.append(Paragraph(esc(s),styles[style]))
def h(s):story.append(Paragraph(esc(s),styles['SectionHead']))
def sub(s):story.append(Paragraph(esc(s),styles['Subsection']))
def chart(fn,h):story.append(Image(str(base/fn),width=6.9*inch,height=h*inch))

para('SRDE / BLACKBIRD INTELLIGENCE', 'DeckSub')
story.append(Paragraph('Recursive Portals and Prediction on Unseen Data',styles['DocTitle']))
para('Executed research milestone | 3 November 2026 | Negative / conditional outcome','DeckSub')
para('Concept originator: Dan A. Merluse. AI-assisted experiment design, code, calculations and reporting. Research-stage evaluation, not a verified native SRDE deployment.','SmallMain')
h('Executive decision')
para('The current portal-inspired predictor did not outperform strong ordinary graph methods on a public genuinely unseen-entity benchmark. It essentially tied a provenance-aware graph-consensus scorer and trailed a simple 2-3 hop Katz-style baseline. Synthetic evidence shows that state and source lineage can help when the data-generating process truly depends on them, but ordinary graph learning can use the same signal.')
story.append(table([
['Experiment','Portal AUC','Best conventional AUC','Conclusion'],
['Inductive real graph (205 facts)','0.6083','Katz 0.6638','No portal advantage'],
['Synthetic unseen worlds (9,000 cases)','0.6903','Graph HGB 0.6937','No portal advantage'],
['Synthetic shifted confirmation (6,000)','0.6247','Graph HGB 0.6266','No stable advantage']
],[2.20*inch,1.28*inch,1.59*inch,1.83*inch]))
h('Prior SRDE evidence respected')
para('The Nov 2 portal hypothesis specifies conditional transitions, position/orientation/state/history, affective coordinates, source provenance, decaying evidence and worker consensus. Its synthetic 100-level example warns that random long chains can connect nearly anything; it is not pre-event forecasting proof. The Oct 12 local-model working paper found 55/56 correct evidence-assisted answers versus static graph retrieval 48/56, but a later intent-aware graph holdout tied SRDE at 56/56. The E30 local report recorded SRDE 38/80 versus graph-state 43/80, and a confirmation tie at 18/40.')
h('Experiment A | Genuine unseen-entity relational prediction')
para('GraIL FB15k-237 V1: 4,245 training triples among 1,594 entities; a separate inference graph has 1,993 triples among 1,093 entirely different entities (zero overlap); 206 validation and 205 held-out test triples. A deterministic 20-negative candidate task was created for each target relation with known positives excluded from evaluation negative sampling. This is unseen-entity generalization, not true chronological event forecasting.')
para('A relation-aware path-rule learner searched 2-3 hop paths, masked each target training edge, fit 2,378 association patterns using training positives and 2 corrupt negatives per positive. Eight scoring variants used the same enumerated path evidence. The portal-inspired variant grouped witness paths by first intermediary and stopped at depth two when two independent positive branches were observed; otherwise it included depth-three paths. This is a structural portal approximation, not the full SRDE algorithm.')
chart('real_auc.png',2.55)
story.append(table([
['Method','Test AUC','Test MRR','Assessment'],
['Katz 2-3 hop','0.6638','0.3556','Best of tested'],
['Typed graph','0.6101','0.3129','Marginally > portal AUC'],
['Portal prototype','0.6083','0.3142','Near consensus tie'],
['Graph consensus','0.6080','0.3118','Near portal tie'],
['Common neighbors','0.5810','0.2774','Weaker topology']
],[2.1*inch,1.0*inch,1.0*inch,2.8*inch]))
sub('Uncertainty and coverage')
para('On 205 paired test positives, Portal - Katz AUC = -0.05549, with 95% 2,000-resample query-bootstrap interval [-0.08780, -0.02439]. Portal - conventional graph consensus = +0.000244 with interval [0.000000, 0.000732]: this tiny difference is effectively one affected query and not a meaningful improvement. Only 49/205 held-out positives had any positive learned rule path. All candidate sets contained 20 negatives; none of the graph traversals reached the 12,000-expansion cap.')
para('Critical caveats: ranking uses sampled negatives rather than official all-entity filtered metrics; one V1 dataset and seed; no published neural GNN/GraIL/NBFNet/SEAL implementation; no time-indexed future data, learned affect, or full recursive worker behavior. Results cannot establish calibrated event probabilities or robust deployment economics.','SmallMain')
h('Experiment B | Conditional-state and provenance stress test')
para('Synthetic worlds: 80 training (12,000 examples), 20 validation (3,000), 60 new test (9,000) and 40 shifted confirmation (6,000). Each pair receives independent source-level signs, context tags, orientation, reliability, age/decay and 2-3 hop evidence; duplicated paths retain a common provenance ID. The generator makes labels probabilistically depend on independent, context-active source support. This deliberately matches the candidate mechanism, so it is a diagnostic feasibility test rather than independent semantic proof.')
chart('synthetic_auc.png',2.7)
story.append(table([
['Method','Unseen AUC','Shift AUC','Interpretation'],
['Full graph HGB','0.6937','0.6266','Conventional flexible learner'],
['Full graph logistic','0.6913','0.6266','Conventional same-input model'],
['Portal','0.6903','0.6247','No superior prediction'],
['Provenance graph','0.6839','0.6231','Lineage useful'],
['Portal, no lineage','0.6640','0.6187','Duplicate-vote error'],
['Portal, no state','0.6273','0.5656','Context matters'],
['Portal, 2 hops','0.6256','0.5766','Depth helps this generator'],
['Katz','0.5370','0.5261','Topology insufficient here']
],[2.16*inch,1.08*inch,1.10*inch,2.56*inch]))
para('Portal - HGB AUC is -0.00337 pooled on unseen synthetic cases. Resampling entire test worlds 500 times yielded a 95% interval for world-mean AUC difference [-0.00566, -0.00081]. In shifted confirmation, the conventional full graph learner also edged portal. Unlike Experiment A, this is within a designer-authored generator which directly specifies the role of state and provenance.')
sub('Negative controls')
para(f"Shuffled synthetic test labels yielded portal AUC {syn['label_shuffle_control']['Portal']:.4f} (near chance). In 200 entirely random 100-layer graphs, average reachable endpoints = {syn['100_level_null']['mean_reachable_endpoints']:.3f} of 12, illustrating why a long portal path alone is not evidential. Integrity assertions passed for separated seeds/worlds, exact case counts and bounded path observations.")
h('What is inferable — and what is not')
for p in [
 'Supported for the tested scope: ordinary 2-3 hop graph topology beat the structural portal prototype on unseen-entity relational ranking. Structural path and relation rule learning is not automatically better than simple connectivity.',
 'Conditional: context gating, decayed reliability and source independence can improve predictions when the unknown target really depends on such variables; conventional models can use the same evidence.',
 'Not supported: that long chains prove meaningful or causal links; that affective states are faithfully encoded by synthetic tags; that recursive portals forecast future events, unlock universal semantic geometry or outperform trained modern graph neural networks.',
 'New research priority: explicitly distinguish relation existence from causal direction, false-assertion cost from abstention, independent source IDs from multiple copies, and pre-event evidence timestamps from post-event leakage.'
]: para(p)
h('Next rigorous experiment / gate')
para('Expand to independent inductive graph families (FB15k-237 V2-V4 and WN18RR where suitable), hard HeaRT-style negative sampling, and a chronological prediction dataset (candidate ICEWS/GDELT). Run official evaluation protocols and modern SEAL/GraIL/NBFNet baselines, preserve all methods within equal data access and report full compute. Train and choose hyperparameters on training/validation only; freeze code before testing; preregister success criteria, then confirm on held-out shifted datasets and repeat across at least five seeds. Add adversarial path copying, correlated upstream sources, random links, orientation/state mislabeling and ablation of recursive depth.')
para('Promote SRDE only if it shows a reproducible positive uplift over the strongest conventional matched comparator, confidence intervals exclude zero across multiple independent data sources, and calibration, false positives, abstention and compute costs remain acceptable. No such advancement is supported yet.')
h('Provenance and supplied artifacts')
para('Public benchmark read directly through GitHub-connected file tools. Four source path names and Git object SHA1 hashes are preserved in real_inductive_results.json. A Node reproduction script is included and syntax/synthetic-fixture smoke-tested; no second full real-data Node rerun occurred in the isolated container because the external raw GitHub endpoint was inaccessible. The real observed results came from the independent GitHub-connected evaluator, not that smoke fixture.')
para('Synthetic run executed locally using Python / NumPy / scikit-learn. Frozen protocol, source code, raw held-out case CSV, all per-method metrics and JSON receipts are included. The PDF and Markdown are summaries and do not replace the raw receipts.')
h('Research references')
for x in [
 'SRDE Portal-Based Hierarchical State Spaces for Pre-Event Inference, v0.1, Nov 2 2026 (source in user Library).',
 'FACO-SRDE Working Paper, Oct 12 2026 (source in user Library).',
 'FACO-SRDE E30 Local Results Report, Oct 16 2026 (Drive file ID 1rWVGiB4-ngjEnNDwP-apC6U3U_kfb1Kt).',
 'GraIL original data and code: https://github.com/kkteru/grail',
 'Li et al., Evaluating Graph Neural Networks for Link Prediction: Current Pitfalls and New Benchmarking: https://arxiv.org/abs/2306.10453',
 'Zhang et al., Revisiting Graph Neural Networks for Link Prediction: https://arxiv.org/abs/2010.16103',
]:para(x,'SmallMain')

def footer(c,doc):
 c.saveState();c.setFont('Helvetica',7);c.setFillColor(colors.HexColor('#576774'))
 c.drawString(doc.leftMargin,0.45*inch,'SRDE / Blackbird | Research-stage simulation | 2026-11-03')
 c.drawRightString(8.5*inch-doc.rightMargin,0.45*inch,f'{doc.page}')
 c.restoreState()

pdf=base/'SRDE_Recursive_Portals_Unseen_Data_Report_2026-11-03.pdf'
doc=SimpleDocTemplate(str(pdf),pagesize=(8.5*inch,11*inch),leftMargin=.8*inch,rightMargin=.8*inch,topMargin=.77*inch,bottomMargin=.72*inch,
                     title='SRDE Recursive Portal Predictions on Unseen Data | Experiment Report 2026-11-03',author='Blackbird Intelligence SRDE research',pageCompression=1)
doc.build(story,onFirstPage=footer,onLaterPages=footer)
print('Markdown', (base/'RESEARCH_REPORT.md').stat().st_size, 'PDF', pdf.stat().st_size)
