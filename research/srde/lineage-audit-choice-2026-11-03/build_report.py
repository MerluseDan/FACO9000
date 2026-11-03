import csv,json,html,re,hashlib
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Image,Table,TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
R=Path(__file__).parent;D=R/'results'
metrics=json.loads((D/'metrics.json').read_text());cond=json.loads((D/'condition_metrics.json').read_text());proto=json.loads((R/'PROTOCOL.json').read_text());env=json.loads((D/'environment.json').read_text());boot=json.loads((D/'bootstrap.json').read_text())
def met(n,s='specified'):return next(x for x in metrics if x['split']=='exact' and x['subset']==s and x['method']==n)
names=['StopBayes','NaiveIndependent','FreshOnlyDP','AuditFirst','GreedyVOI','SRDE_AuditRule','GraphFullDP','PortalFullDP','OracleLineageDP']
table='| Policy | Exact total loss | Full Brier | Coverage | Audit requests |\n|---|---:|---:|---:|---:|\n'
for n in names:
 x=met(n);table+=f'| {n} | {x["loss"]:.8f} | {x["brier"]:.8f} | {x["coverage"]:.2%} | {x["audit_rate"]:.2%} |\n'
delta=met('GraphFullDP')['loss']-met('FreshOnlyDP')['loss']
cases=[]
for sc in proto['scenarios']:
 a={x['method']:x for x in cond if x['condition']==sc['id']}
 cases.append({'condition':sc['id'],'family':sc['family'],'pi_assumed':sc['assumed']['pi'],'pi_actual':sc['actual']['pi'],'audit_q_assumed':sc['assumed']['q'],'audit_q_actual':sc['actual']['q'],'delay':sc['assumed']['delay'],'audit_cost':sc['assumed']['ca'],'full_minus_fresh_loss':a['GraphFullDP']['loss']-a['FreshOnlyDP']['loss'],'full_audit_rate':a['GraphFullDP']['audit_rate']})
with (R/'DECISION_BOUNDARY.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(cases[0]));w.writeheader();w.writerows(cases)
chosen=[x for x in cases if x['full_audit_rate']>0]
fig,ax=plt.subplots(figsize=(8,3.8));ax.bar([x['condition'] for x in chosen],[x['full_minus_fresh_loss'] for x in chosen],color=['#227aab' if x['full_minus_fresh_loss']<0 else '#c95842' for x in chosen]);ax.axhline(0,color='black',lw=.7);ax.set_ylabel('Exact total loss: full policy minus fresh-only');ax.set_xlabel('Conditions in which full policy purchases audits');fig.tight_layout();fig.savefig(R/'audit_value_and_failure.png',dpi=150);plt.close(fig)
conditions='| Condition | Assumed/actual copy prior | Assumed/actual audit accuracy | Delay | Loss delta |\n|---|---:|---:|---:|---:|\n'
for x in chosen:conditions+=f'| {x["condition"]} | {x["pi_assumed"]:.1f}/{x["pi_actual"]:.1f} | {x["audit_q_assumed"]:.1f}/{x["audit_q_actual"]:.1f} | {x["delay"]} | {x["full_minus_fresh_loss"]:+.8f} |\n'
report=f'''# SRDE LA1 — Is checking a source's lineage worth more than another report?

Executed 3 November 2026. Concept/research direction: Dan Merluse. Protocol, code, source review, analysis and audits are AI-assisted.

## Result

Lineage audits have a narrow value region in this finite known-model problem. The exact optimal policy purchases audits in only **2 of 36 correctly specified settings**: a low copy prior (.2), a perfect inexpensive audit (.00375 loss units), and a response that arrives within the three-slot deadline. Neither noisy audits of accuracy .8, expensive audits, uninformative audits nor late audits are worth purchasing anywhere else on this declared grid.

The primary exact expected total-loss difference, full policy minus fresh-only, is **{delta:+.9f}** across the 36 settings. This is about {abs(delta)/met('FreshOnlyDP')['loss']:.3%} of the fresh-only loss: a small benefit conditional on the model and grid. In the two useful settings the difference is -0.001027334 per case, with audits requested on 19.2% of cases. That conditional effect is diluted across many settings where no audit is selected.

Overtrust reverses the gain. Holding the low copy prior and cheap audit fixed, an audit assumed perfect but actually uninformative produces +0.002597091 additional loss; an always-inverted audit produces +0.006221515. The exact recursive and conventional full-policy outputs and action traces are identical. There is no portal-specific superiority result.

## Why this does not repeat the other chats

Recent available turns of Recursive Portal Experiment, SRDE Research Options and Memory Worker Architecture were read before design. Their E01–E03 work concerns delayed learning, hidden source groups and change detection; E04 proposes selective suspension. P3–P4 test state/seasonal transition forecasts, and the newly published P5 preregistration tests affine path ordering and reverse instability. The memory-worker work tests governance and permission freshness under queue load. LA1 instead makes a fallible query about unknown source dependence compete with another assertion under an explicit decision budget. These conversations were read, not interrupted. Their reported results were not independently rerun here.

The full comparison, literature queries, scope and source links are in NOVELTY_AND_CROSS_CHAT.md. Dynamic copying inference, source selection, Bayesian information acquisition and uncertainty over provenance all predate this experiment. Recent GraphEcho already measures redundant paths, provenance and active exploration; PQ-EID already analyzes uncertain provenance partitions. LA1 is a documented extension of our SRDE evaluation program, not a new decision-theory algorithm or a certified worldwide first. [GraphEcho methods](https://arxiv.org/html/2609.17695v1); [PQ-EID](https://www.mdpi.com/1999-5903/18/11/582).

## Frozen design

The protocol, novelty record, runner and tests were published before scoring in GitHub commit **faad7f25854b278ce427995f85e9284ba3835c1b**, then their remote Git blob identities were checked against the local bytes. An earlier publication attempt returned a GitHub service error; absence of the freeze was confirmed before retrying. No experimental score was computed before the successful freeze.

There are 42 frozen conditions: 36 correctly specified settings, four audit-quality shifts and two copy-prior shifts. Exhaustive enumeration retains **6,528 positive-probability atoms and 58,752 policy forecasts**. A separately written sampler generates **21,000 held-out cases and 189,000 forecasts** across five untouched seeds. No hyperparameter or model selection uses these cases.

Y is the binary event. L indicates whether the first two of three initial reports are copies of one observation. Each original source has accuracy .8; the third is independent. Two optional new observations have accuracy .7. One audit observes L, with its own error rate and delay. Thus a binary audit response asserts something about provenance, not event truth. No affect/valence input is used in this round.

At most three actions occur before the terminal deadline: acquire an assertion, request the single audit, wait for it, or stop. Each assertion costs .015; audit cost is .00375 or .06. Delay is 0, 2 or 4 slots, with delay 4 arriving too late. A zero-delay response becomes usable at the next decision slot; there is no separate within-slot reaction. Costs are modeled decision-loss units, not money or compute bills.

The terminal action minimizes expected squared probability error or a fixed .15 abstention loss, then adds acquisition costs. Full Brier scores include probabilities even when a policy abstains. Coverage and error among accepted cases are reported separately. All methods receive known assumed generative probabilities; this is not a learned grounding or source-identification system.

## Correctly specified exact results

{table}

Lower loss/Brier is better. OracleLineageDP receives actual hidden L for free and is an information-advantaged diagnostic, not a fair competitor. GraphFullDP performs conventional reachable-state backward induction. PortalFullDP expands the same action graph recursively. Their equality is expected from their identical information and objective, and was checked both per model state and per emitted forecast.

Full-policy Brier is slightly worse than fresh-only here even though declared total decision loss is slightly better. The policy optimizes selective squared-error/abstention/cost utility, not full Brier. The two metrics must not be interchanged after the result. AuditFirst barely changes Brier in specified worlds but raises total loss substantially by buying audits regardless of value. The simple SRDE_AuditRule also loses narrowly to fresh-only on the full specified grid.

The independent sample estimates full minus fresh-only loss at {boot['FreshOnlyDP']['delta']:+.9f}, with a paired case-bootstrap interval [{boot['FreshOnlyDP']['lower']:+.9f}, {boot['FreshOnlyDP']['upper']:+.9f}]. It includes zero. The sample does not establish a statistically convincing improvement. The exhaustive calculation is exact for this finite distribution, not an estimate of real-world performance.

## Reliability and latency boundary

{conditions}

![Audit value and failure](audit_value_and_failure.png)

Only rows where the full policy actually requests audits are shown. C12 and C14 are the useful specified settings. Q36 and Q38 show audit-model failures. The high-copy-prior audit shifts Q37/Q39 do not cause full-policy damage because it never requests an audit there. P40/P41 show that a lineage-prior shift can change the value of an otherwise accurate audit in either direction. Averaging them hides that asymmetry.

Across all 42 settings, full-policy loss is {met('GraphFullDP','all')['loss']:.8f}, versus fresh-only {met('FreshOnlyDP','all')['loss']:.8f}: adding these six misspecification settings makes the pooled comparison worse. This arbitrary 36:4:2 mixture is a stress-test summary, not an estimated prevalence of failures. In the four audit-quality shifts alone, full loss is {met('GraphFullDP','audit_shift')['loss']:.8f} versus {met('FreshOnlyDP','audit_shift')['loss']:.8f}. Always auditing and the simple pattern rule are more vulnerable.

## Verification and reproducibility

Fourteen pre-scoring analytic/contract tests passed and were rerun after scoring. A separate output auditor, which does not import the runner, recomputed every one of **247,752 forecasts**, its posterior, acquired evidence, response chronology, cost, abstention and total loss. Maximum aggregate discrepancy was 1.65e-14. A second independent optimizer partitions weighted latent-world atoms instead of using the runner's belief/transition code; it matches all 36 specified-condition optima within 1.39e-17.

An independent second Python process reproduced all eight scientific JSON and decompressed CSV outputs exactly. Gzip metadata and runtime are excluded from byte equality. The first measured run took {env['runtime_seconds']:.2f} seconds on local CPU, excluding literature review, design, publication and reporting. No GPU, paid Colab allocation, new model or live app was used. Core reproduction and audits use only the Python standard library. Plot/PDF rendering is optional and uses matplotlib/reportlab.

## Limits and retained questions

The primary weak improvement from expanding an exactly optimized action set is guaranteed in principle under a correct known model. The measured contribution is the narrow region where that option is actually used and how model error changes its value; it is not a newly discovered theorem. Results depend on the selected accuracies, costs, priors, three-slot horizon and abstention loss. They do not show general portal superiority, human cognition, actual-world forecasts or an empirically calibrated source-verification service.

No independent empirical dataset was added. The sampler and exact enumeration are different implementations of the same authored mechanism. The states are not a longitudinal stream; there is no delayed gold learning, concept-drift detection, real scheduling or natural-language provenance extraction. Those broader parts of the earlier candidate remain open and are not claimed completed.

RQ-LA2: Can audit reliability itself be estimated and kept calibrated from independent, delayed verification without making verification circular? A distinct future protocol must first compare relevant reliability-learning and active verification research. RQ-LA3: What is the value of lineage queries with several possible copy partitions and shared-cause errors, where the current binary L simplification fails? RQ-LA4: Can an independently curated dataset support these distinctions with verified derivation chains and acquisition costs? These are candidates, not novelty-cleared next experiments.

Keep LA1 as completed bounded evidence. Do not promote the heuristic, arbitrary pooled mean or correct-model optimum into an installed SRDE capability.
'''
(R/'RESEARCH_REPORT.md').write_text(report)
with (R/'METRICS_SUMMARY.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(metrics[0]));w.writeheader();w.writerows(metrics)
pdfmetrics.registerFont(TTFont('DejaVu','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))
styles=getSampleStyleSheet()
for st in styles.byName.values():st.fontName='DejaVu'
styles['BodyText'].fontSize=9;styles['BodyText'].leading=13
story=[]
for block in report.split('\n\n'):
 b=block.strip()
 if not b:continue
 if b.startswith('!['):story.extend([Image(str(R/'audit_value_and_failure.png'),width=480,height=228),Spacer(1,8)]);continue
 if b.startswith('|'):
  rows=[[x.strip() for x in ln.strip('|').split('|')] for ln in b.splitlines() if not ln.startswith('|---')]
  data=[[Paragraph(html.escape(x),styles['BodyText']) for x in row] for row in rows]
  widths=[145,90,90,80,80] if len(rows[0])==5 else None
  t=Table(data,colWidths=widths,repeatRows=1,hAlign='LEFT');t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e2eff8')),('VALIGN',(0,0),(-1,-1),'TOP'),('LINEBELOW',(0,0),(-1,0),.5,colors.grey),('BOTTOMPADDING',(0,0),(-1,-1),5)]));story.extend([t,Spacer(1,8)]);continue
 sty='Title' if b.startswith('# ') else 'Heading2' if b.startswith('## ') else 'BodyText'
 b=re.sub(r'^#{1,2} ','',b);b=html.escape(b);b=re.sub(r'\*\*(.*?)\*\*',r'<b>\1</b>',b);b=re.sub(r'\[([^]]+)\]\((https?://[^)]+)\)',r'<a href="\2" color="blue">\1</a>',b)
 story.extend([Paragraph(b,styles[sty]),Spacer(1,7)])
SimpleDocTemplate(str(R/'SRDE_LA1_Research_Report.pdf'),leftMargin=40,rightMargin=40,topMargin=40,bottomMargin=40).build(story)
print('Report, PDF, chart and comparison CSVs generated')
