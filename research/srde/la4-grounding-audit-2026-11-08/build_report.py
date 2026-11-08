"""Post-freeze reporting; does not change the scientific run."""
import csv,gzip,json,html,re
from pathlib import Path
from collections import defaultdict
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Image,Table,TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
R=Path(__file__).parent;D=R/'results'
M=json.loads((D/'metrics.json').read_text());B=json.loads((D/'bootstrap.json').read_text());E=json.loads((D/'environment.json').read_text())
def m(n,f='independent'):return next(r for r in M if r['method']==n and r['family']==f and r['split']=='exact')
def boot(n,f='independent'):return next(r for r in B if r['baseline']==n and r['family']==f)
with gzip.open(D/'world_metrics.csv.gz','rt') as f:W=list(csv.DictReader(f))
with gzip.open(D/'query_receipts.csv.gz','rt') as f:Q=list(csv.DictReader(f))
def sub(n,a):
 rr=[r for r in W if r['method']==n and r['split']=='exact' and r['family']=='independent' and float(r['a'])==a]
 return {k:sum(float(r[k]) for r in rr)/len(rr) for k in ['total_loss','queries','coverage','brier']}
def table(f):
 s='| Method | Total loss | Brier | Coverage | Wrong accepted / 1000 cases | ECE10 | Queries |\n|---|---:|---:|---:|---:|---:|---:|\n'
 for n in ['LiteralBits','RobustAbstain','ProvenanceOnly','UniformAnchors','ConfidentAnchors','GreedyDecision','EntropyGreedy','TwoStepTable','TwoStepRecursive','SRDETypedGate','KnownOrientation']:
  r=m(n,f);s+=f"| {n} | {r['total_loss']:.7f} | {r['brier']:.6f} | {r['coverage']:.2%} | {r['wrong_accepted']*1000:.2f} | {r['ece10']:.5f} | {r['queries']:.3f} |\n"
 return s
primary=boot('GreedyDecision');against_stop=boot('RobustAbstain')
fig,ax=plt.subplots(1,2,figsize=(10,3.8))
names=['RobustAbstain','ProvenanceOnly','ConfidentAnchors','GreedyDecision','EntropyGreedy','TwoStepTable','SRDETypedGate']
ax[0].bar(range(len(names)),[m(n)['total_loss'] for n in names],color=['#8c929b','#8c929b','#377b62','#7187a4','#386d9d','#2b7a7a','#a46a50'])
ax[0].set_xticks(range(len(names)),['Abstain','Lineage\nonly','Confident\nanchors','1-step\ndecision','Entropy','2-step\ndecision','Typed\ngate'],rotation=30,ha='right')
ax[0].set_ylabel('Total loss with independent .9-accurate anchors');ax[0].set_ylim(0,.17)
for n,color,label in [('RobustAbstain','#8c929b','Abstain'),('TwoStepTable','#2b7a7a','Two-step decision'),('EntropyGreedy','#386d9d','Entropy acquisition')]:
 ax[1].plot(range(3),[m(n,f)['total_loss'] for f in ['independent','uninformative','dependent_echo']],'o-',label=label,color=color)
ax[1].set_xticks(range(3),['Independent\naccuracy .9','Independent\naccuracy .5','Echo of\na source'])
ax[1].set_ylabel('Total loss under actual reference mechanism');ax[1].legend(fontsize=8)
fig.tight_layout();fig.savefig(R/'grounding_and_reference_failure.png',dpi=150);plt.close(fig)
report=f"""# SRDE LA4 — Provenance cannot replace independent grounding

Executed 8 November 2026. Research direction: Dan Merluse. Protocol, code, literature review, mathematical construction, analysis and audits are AI-assisted.

## Main finding

This controlled test separates a statement's lineage from evidence about whether its relationship to the target event is correct. Perfect provenance queries leave target orientation completely unresolved in the paired worlds. Independent event labels can resolve it; source echoes presented as event verification cannot.

With genuinely independent anchors of accuracy .9, two-step decision acquisition scores total loss {m('TwoStepTable')['total_loss']:.7f}, compared with {m('RobustAbstain')['total_loss']:.7f} for abstaining everywhere and {m('ProvenanceOnly')['total_loss']:.7f} for spending the full budget on lineage queries. Its improvement versus abstaining is {against_stop['delta']:+.7f}, with a cluster-bootstrap interval [{against_stop['lower']:+.7f},{against_stop['upper']:+.7f}]. It predicts on {m('TwoStepTable')['coverage']:.2%} of cases; this is not full-coverage forecasting.

The predeclared primary comparison is less decisive. Two-step minus one-step decision acquisition is {primary['delta']:+.7f}, interval [{primary['lower']:+.7f},{primary['upper']:+.7f}]. The interval includes zero. No reliable superiority over one-step planning is established from the 24 independent calibration pools. Its comparison against the strong conventional entropy-acquisition baseline also includes zero.

Unreliable or nonindependent references reverse the value. The learner assumes .9 accuracy in every mode. If anchors are actually uninformative, two-step total loss becomes {m('TwoStepTable','uninformative')['total_loss']:.7f}; if they merely echo a source it becomes {m('TwoStepTable','dependent_echo')['total_loss']:.7f}. Both are worse than robust abstention at .15. More elaborate acquisition cannot compensate for an ungrounded reference channel.

The explicit table and recursive two-step planners give identical forecasts and decisions. The SRDETypedGate heuristic has no demonstrated superiority. The useful boundary is about information content and reference assumptions, not an advantage from recursion.

## What is different from LA3 and the other chats

LA3 learned parameters within a source family. LA4 studies an exact observational ambiguity that parameter learning cannot remove without new information: reports and provenance can have the same distribution while their relationship to a fixed target event is reversed by context. It asks which query type supplies the missing information, what abstention does to acquisition incentives, and how dependent references defeat that inference.

The latest related chats were inspected before design. E07E used real sensor runs with injected source faults; E08 seeks actual claim dependency graphs and independent failure/restoration records. P8 built an evidence-impact tool on simulated edits to real research reports, with prospective revisions next. Study10 tested synthetic neural summarizers and an evidence ledger, with pretrained-model Study11 pending. Their reported results were not independently rerun here. LA4 reuses none of those datasets, revision workloads, claim graphs or models.

The statistical ideas are established. [Ben-David and colleagues, 2010](https://proceedings.mlr.press/v9/david10a/david10a.pdf), section5, use indistinguishable target-label constructions to establish domain-adaptation limits. [Golovin, Krause and Ray, 2010](https://papers.nips.cc/paper_files/paper/2010/hash/1e6e0a04d20f50967c64dac2d639a577-Abstract.html) study noisy Bayesian active learning. [Chen, Hassani and Krause, 2017](https://proceedings.mlr.press/v54/chen17b/chen17b.pdf) examine correlated noisy tests and limitations of common information heuristics. LA4 implements neither EC2 nor ECED and makes no claim to outperform them. It is a documented SRDE observability/grounding robustness extension, not a new theorem or certified worldwide-first experiment. NOVELTY.md records queries, methods read and access gaps.

## The paired-world construction

A balanced latent proxy B generates three observed report bits X. With probability .2, the second report copies the first; otherwise the reports independently match B with accuracy a. Two observed contexts g have unknown target orientations r_g. The target is Y=B xor r_g.

Y=1 retains its target-event definition. The unknown orientation represents a world's report-to-target relationship, not a software decision to redefine truth after prediction. An inverted world is a hard negative for assuming the reports' symbols already supply the correct target mapping.

The marginal P(X,L|r) is independent of r because summing over balanced B removes the target mapping. Even a perfect population-level checker of report and lineage distributions cannot identify orientation. Adaptive provenance-only query transcripts remain invariant. This is an exact identifiability limit in the declared construction, rather than failure to choose a sufficiently strong detector.

For complementary worlds coupled to the same observations and any forecast p based only on those observations:
[(p-Y)^2+(p-(1-Y))^2]/2 = .25+(p-.5)^2 >= .25.
An unresolved symmetric orientation therefore has minimum Brier .25 at p=.5. With abstention costing .15, stopping and abstaining is preferable under that loss. OBSERVABILITY_PROOF.md gives the elementary derivation and its limits. This is an instance of known theory, not an original impossibility theorem.

An event anchor R is a noisy independent measurement of Y in the intended mode. Unlike a lineage response about L, it can orient the report-to-target relationship. An echo anchor R=X_first remains a function of existing reports, so it cannot identify orientation even though a misspecified learner may treat it as corroboration.

## Frozen protocol and independent-unit accounting

Source/design were published in GitHub freeze commit 04cbe0fb35e80484e3e98a5514de28fbf94c712f and eight remote blobs verified before the scientific run. FREEZE.json hashes seven files; the eighth is the manifest itself. Source, seeds, methods, budget, priors and costs were unchanged after scoring.

There are 24 independent calibration pools: 12 seeds at each source accuracy .65 and .8. Each pool contains four cases in each of two contexts, eight cases total. The pool and separate 128-case held-out observable sample are reused counterfactually under four orientation combinations and three reference mechanisms. This yields 288 evaluation worlds, not 288 independent datasets.

The 2,304 stored calibration rows and 36,864 sampled case rows include those counterfactual repetitions. There are 192 distinct calibration source cases and 3,072 distinct sampled source cases before repetition. Forecast counts measure execution/audit coverage; they are not independent sample sizes for confidence intervals.

The primary family contains genuinely independent .9-accurate event anchors. The controls use independent .5-accurate responses or an echo of the first report. Lineage answers are perfect in all modes. Reference noise uniforms are coupled across variants. Every selector starts with the two orientation probabilities at .5 and assumes anchor accuracy .9. It knows source accuracy and copy prior; this is not simultaneous source-parameter estimation.

Selectors receive source bits, context and revealed responses only. The responder owns hidden B,L,Y and potential reference answers. Raw simulator variables are released for audit, but are excluded from initial observation packets. Held-out outcomes never enter query selection. A separate random stream offset30,000,000 generates the held-out sample. Exhaustive finite outcome expectations provide the primary deployment scores.

## Query budget, inference and decisions

Each method can purchase at most four responses. Every calibration case permits one event anchor and one lineage query, each charged .005. Responses arrive immediately; LA4 does not claim to test delayed or online adaptation. Query expense is divided over an assumed128 deployments. Total loss is terminal decision loss plus actual query charges/128.

The predictor uses the full posterior over each context orientation, summing the latent proxy and lineage per underlying calibration case. Combining an anchor with that case's lineage refines the same likelihood; it is not counted as another independent source. Future-report probabilities integrate the orientation posterior. A predicted event probability p incurs squared error, or the method abstains at cost .15 when p*(1-p)>.15. The query objective uses this model-based expected terminal decision risk, not held-out answers.

LiteralBits assumes both report-to-target orientations are normal and buys nothing. RobustAbstain retains unresolved orientation and stops. ProvenanceOnly purchases four lineage responses. UniformAnchors buys two event labels per context. ConfidentAnchors also balances contexts but chooses the reports most informative about B.

GreedyDecision considers one query's expected reduction in decision risk. TwoStepTable explicitly evaluates a two-query tree with stopping, then replans until the four-query cap. TwoStepRecursive evaluates the identical horizon recursively. These are short-lookahead policies, not globally optimal four-query planners. EntropyGreedy is a stronger conventional information-acquisition control: it selects the response expected to reduce orientation entropy most, while information remains and budget permits. Its objective differs from immediate decision loss.

SRDETypedGate is a transparent heuristic: select high-confidence-proxy event anchors in the least oriented context until confidence .95 or the budget cap. KnownOrientation receives the true orientations free; it is an information-privileged diagnostic, not a fair learned competitor. All other policies have the same observations, response options, maximum budget and charges; they can choose to spend less. Literal/robust baselines and the privileged diagnostic spend zero.

## Independent-reference results

{table('independent')}

Lower loss, Brier, ECE and wrong-accepted fraction are better; higher coverage means fewer abstentions. Wrong accepted is normalized by all cases, not only accepted predictions. Reporting it together with coverage prevents an abstain-everywhere policy from appearing to solve prediction. Brier and ECE include all terminal probabilities, including abstained cases. ECE uses ten equal-width bins.

The primary interval resamples the 12 seed clusters within each source-accuracy stratum, retaining all counterfactual variants within a selected cluster:1,000 draws, seed99101. It quantifies calibration-pool variation conditional on this exact generator and fixed condition mixture. It does not resample the many paired forecasts as independent trials. Secondary comparisons are exploratory, with no multiplicity adjustment.

Two-step lookahead has the best observed mean decision loss in the intended family, but its primary comparison against one-step and comparison against entropy acquisition do not establish superiority. ConfidentAnchors is close at {m('ConfidentAnchors')['total_loss']:.7f}. EntropyGreedy has lower full Brier than two-step ({m('EntropyGreedy')['brier']:.6f} versus {m('TwoStepTable')['brier']:.6f}), reflecting a different tradeoff between probability quality and abstention decisions.

## Uninformative and dependent-reference controls

Independent references with actual accuracy .5, while the learner assumes .9:
{table('uninformative')}

Pseudo-references that echo the first source:
{table('dependent_echo')}

All acquired-query policies can become worse than abstaining when the reference assumption fails. Across the equally weighted mixture of all three mechanisms, two-step total is {m('TwoStepTable','all')['total_loss']:.7f}, versus robust abstention .15. That aggregate is a declared stress-test mixture, not an estimated real-world frequency of bad reference channels.

Echo-world query transcripts and source/provenance marginals are identical across orientation variants, including adaptively selected responses. The auditor checks that invariant directly. Treating an echo as independent may produce confident but unidentifiable conclusions. A true-world lineage receipt and an independent event measurement answer different questions; verifying the former does not certify the latter.

## The abstention plateau and negative results

At source accuracy .65, both one- and two-step decision planners stop without buying any query, yielding total .15. The entropy policy buys four responses and scores {sub('EntropyGreedy',.65)['total_loss']:.7f}; its small observed difference is descriptive and is not promoted as a separate significant result. The typed gate also buys four and scores {sub('SRDETypedGate',.65)['total_loss']:.7f}. Spending on information can fail to cross the threshold for making a useful prediction.

At accuracy .8, one-step total is {sub('GreedyDecision',.8)['total_loss']:.7f}; two-step is {sub('TwoStepTable',.8)['total_loss']:.7f}. Calibration-pool variability is substantial. The original pre-freeze unit-test assumption that two queries necessarily escape the .65 plateau was false and was corrected before the protocol freeze. The generator was not tuned to manufacture a two-step win; EXECUTION_NOTES.md preserves the rejected expectation.

The SRDETypedGate scores {m('SRDETypedGate')['total_loss']:.7f} in the intended family and is not the best conventional comparator. Table and recursive two-step forecasts match throughout. No advantage is attributed to recursion or to a newly invented grounding mechanism.

## Verification and reproducibility

The CPU scientific run took {E['runtime_seconds']:.2f} seconds, excluding literature review, audits, reports and publication. It generated152,064 exact weighted forecasts and405,504 sampled forecasts,557,568 total. No GPU or paid Colab allocation was needed.

Twelve unit tests pass: exact observable probability mass and orientation invariance, missing-versus-false distinction, provenance's inability to orient, context-scoped anchors, no repeated queries, outcome normalization, the short-lookahead plateau, recursive/table agreement, the paired Brier bound, counterfactual coupling and dependent echo generation.

The independent auditor imports no experiment runner. It uses a separate evidence-ratio calculation to check all7,472 acquired responses and their selection rules,3,168 fitted states, all forecast probabilities, exact atom weights, abstention, Brier/decision loss, ECE, coverage, wrong accepted fractions and query costs. It verifies report/provenance marginal equality and complete echo-transcript invariance. Heuristic context ties are accepted within1e-12; one first-pass audit exposed such a floating-point tie, and the auxiliary auditor was refined without changing frozen source/results. The maximum numerical error is about1.23e-15.

A second process reproduced all11 scientific output contents exactly, excluding gzip headers and runtime metadata. Clean extraction and manifest checks accompany publication. Run python3 -m unittest -v test_la4.py, then python3 run_la4.py, then python3 audit_results.py from the package directory. Scientific runs require only Python3 standard library; optional PDF/figure generation uses matplotlib/reportlab and a DejaVu font.

The release includes raw simulator records, allowed initial observations, acquired-query receipts, fitted states, exact atoms, sampled cases, forecasts, world/aggregate metrics, cluster-bootstrap results, the frozen protocol, source-linked novelty review, observability derivation, tests and independent audit. SHA-256 hashes cover every packaged payload.

## What this says about 1 and 0

A bit is a symbol with a declared variable and relation to the target. B, Y, L and R are distinct binary variables. Source reports can be correlated, inverted or copied. A missing anchor/lineage response is encoded as unknown, not false. A purchase decision is not a truth assertion, and abstention is a loss-based action rather than a third factual outcome.

LA4 supports a precise interpretation of the original hypothesis: source agreement and provenance do not by themselves ground which report-to-target relationship holds. Independent observations can supply that missing information under declared reference assumptions. It does not show that binary computation is fundamentally inadequate or that changing the encoding of0/1 solves truth. Four-valued logic, concept representation learning, natural-language grounding and affect are not experimentally validated here. Affect F in[0,1], with0 aversive and1 pleasant, remains distinct from truth and confidence.

## Limitations and retained inference points

The worlds are deliberately constructed, stationary and small. Source-channel accuracy, copying prevalence and target balance are known. Only orientation is learned. Reference failures are controls, not detected by a new reliability learner. No independent empirical dataset, actual physical repair diagnosis, human cognitive validation or native Blackbird integration is established. There are only24 independent calibration pools; counterfactual evaluation expands coverage, not statistical independence. Changing the abstention price, query cost, source asymmetry or class balance can change the acquisition policies.

LA4-I1: lineage verification and target grounding are distinct information channels. Supported by the exact marginal/transcript identity and provenance-only control.
LA4-I2: an abstention threshold can make information gathering appear valueless to a short-horizon decision objective. Supported by the .65-source plateau; two-step lookahead does not universally remove it.
LA4-I3: a source echo cannot become independent grounding by being called a reference. Supported by the echo-world invariance and degraded scores.
LA4-I4: the positive independent-anchor result depends on the validity of the anchor channel; the primary two-step-versus-one-step superiority claim remains unsupported.

LA4-R1: which independent operational records can anchor report-to-target meaning, with documented reliability and cost? Check E08's scope before another empirical design.
LA4-R2: can acquisition remain useful when uncertainty about reference independence/reliability is modeled rather than assumed away? Related noisy/correlated active-learning work above must be the baseline.
LA4-R3: would a stronger globally planned or entropy-surrogate policy cross useful decision thresholds under sparse grounding? This is established planning/active-learning territory, requiring an explicit new comparative question.
LA4-R4: how should Blackbird preserve separate evidence fields for claim content, lineage, grounding observation and valence without collapsing unknown into false? This is an engineering consequence to test separately, not a cognitive-theory conclusion.

GitHub directory: https://github.com/MerluseDan/FACO9000/tree/main/research/srde/la4-grounding-audit-2026-11-08 .
"""
# Improve spacing in numeric prose without rewriting identifiers or hashes.
for old,new in [('stratum, retaining','stratum, retaining'),('cluster:1,000','cluster: 1,000'),('about1.23','about 1.23'),('source/results','source/results'),('generated152,064','generated 152,064'),('and405,504','and 405,504'),('forecasts,557,568','forecasts, 557,568'),('all7,472','all 7,472'),('responses and their selection rules,3,168','responses and their selection rules, 3,168'),('within1e-12','within 1e-12'),('all11 scientific','all 11 scientific'),('only24 independent','only 24 independent'),('of0/1','of 0/1'),('F in[0,1]','F in [0,1]'),('with0 aversive','with 0 aversive'),('and1 pleasant','and 1 pleasant')]:report=report.replace(old,new)
(R/'REPORT.md').write_text(report)
pdfmetrics.registerFont(TTFont('DejaVu','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'));styles=getSampleStyleSheet()
for st in styles.byName.values():st.fontName='DejaVu'
styles['BodyText'].fontSize=9;styles['BodyText'].leading=12
story=[]
def para(s,style='BodyText'):
 s=html.escape(s);s=re.sub(r'\[([^]]+)\]\((https?://[^ )]+)\)',r'<link href="\2" color="#216a91">\1</link>',s);story.extend([Paragraph(s,styles[style]),Spacer(1,5)])
lines=report.splitlines();i=0
while i<len(lines):
 s=lines[i]
 if not s.strip():i+=1;continue
 if s.startswith('|'):
  rr=[]
  while i<len(lines) and lines[i].startswith('|'):
   row=[x.strip() for x in lines[i].strip('|').split('|')]
   if not all(re.fullmatch(r'[-:]+',x) for x in row):rr.append(row)
   i+=1
  t=Table([[Paragraph(html.escape(x),styles['BodyText']) for x in row] for row in rr],colWidths=[112]+[64]*(len(rr[0])-1),repeatRows=1,hAlign='LEFT')
  t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e3edf2')),('GRID',(0,0),(-1,-1),.3,colors.HexColor('#b8c5ce')),('VALIGN',(0,0),(-1,-1),'TOP')]))
  story.extend([t,Spacer(1,10)]);continue
 if s.startswith('# '):para(s[2:],'Title')
 elif s.startswith('## '):
  para(s[3:],'Heading2')
  if s=='## Independent-reference results':story.append(Image(str(R/'grounding_and_reference_failure.png'),width=495,height=188))
 else:para(s)
 i+=1
SimpleDocTemplate(str(R/'REPORT.pdf'),pagesize=(650,842),leftMargin=38,rightMargin=38,topMargin=35,bottomMargin=35,title='SRDE LA4 - Provenance and independent grounding',author='SRDE research').build(story)
print('Detailed report and figure built')
