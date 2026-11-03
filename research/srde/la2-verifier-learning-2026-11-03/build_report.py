"""Post-freeze reporting; does not modify scientific protocol or results."""
import json,csv,gzip,html,re
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
def m(name,f='all',h=512):return next(r for r in M if r['method']==name and r['family']==f and r['horizon']==h)
# Additional descriptive diagnostic, added after the freeze: ten equal-width forecast bins.
bins=defaultdict(lambda:[[0.,0.,0.] for _ in range(10)])
with gzip.open(D/'exact_predictions.csv.gz','rt') as f:
 for r in csv.DictReader(f):
  p=float(r['p']);w=float(r['weight']);y=int(r['y']);b=bins[(r['world'],r['method'])][min(int(p*10),9)]
  b[0]+=w;b[1]+=w*p;b[2]+=w*y
ece=[]
for (world,name),bb in bins.items():
 total=sum(b[0] for b in bb);value=sum(abs(b[1]-b[2]) for b in bb)/total
 ece.append({'world':world,'method':name,'ece_10':value,'status':'post-freeze descriptive metric; not a selection criterion'})
(R/'CALIBRATION_DIAGNOSTIC.json').write_text(json.dumps(ece,indent=2)+'\n')
def ec(name,fam):
 v=[r['ece_10'] for r in ece if r['method']==name and (fam=='all' or (int(r['world'][1:3])%2==0)==(fam=='specified'))]
 return sum(v)/len(v)
tables={}
for fam in ['all','specified','source_model_error']:
 t='| Method | q mean absolute error | Deployment loss | Total at H=512 | Brier | ECE (10 bins) | Forecast coverage |\n|---|---:|---:|---:|---:|---:|---:|\n'
 for name in ['FreshOnly','AssumePerfect','LatentBayes','TargetHardCounts','RandomVerifiedCounts','SelectedVerifiedCounts','MixedRandomBayes','MixedSelectedBayes','DoubleCountSelected','SRDETypedRecursive','KnownAuditQ']:
  r=m(name,fam)
  q='—' if name in ['FreshOnly','AssumePerfect','KnownAuditQ'] else f"{r['q_error']:.5f}"
  t+=f"| {name} | {q} | {r['deployment_loss']:.8f} | {r['total_loss']:.8f} | {r['brier']:.8f} | {ec(name,fam):.5f} | {r['coverage']:.2%} |\n"
 tables[fam]=t
primary=next(x for x in B if x['family']=='all' and x['baseline']=='SelectedVerifiedCounts')
break_even=m('MixedSelectedBayes','specified')['calibration_cost']/(m('FreshOnly','specified')['deployment_loss']-m('MixedSelectedBayes','specified')['deployment_loss'])
fig,axs=plt.subplots(1,2,figsize=(10,3.7))
names=['SelectedVerifiedCounts','RandomVerifiedCounts','LatentBayes','MixedSelectedBayes']
axs[0].bar(range(4),[m(n)['q_error'] for n in names],color=['#bd6a50','#787e99','#2c8aaf','#297861'])
axs[0].set_xticks(range(4),['Selected\ncounts','Random\ncounts','Latent\nBayes','Typed\nmixed'])
axs[0].set_ylabel('Mean absolute error in verifier reliability q')
for fam,color,label in [('specified','#297861','Source model correct'),('source_model_error','#bd6a50','Source model wrong')]:
 hs=[64,512,4096];vals=[m('MixedSelectedBayes',fam,h)['total_loss']-m('FreshOnly',fam,h)['total_loss'] for h in hs]
 axs[1].plot(hs,vals,'o-',color=color,label=label)
axs[1].axhline(0,color='black',linewidth=.7);axs[1].set_xscale('log');axs[1].set_xticks([64,512,4096],['64','512','4096'])
axs[1].set_xlabel('Assumed deployment cases sharing calibration cost')
axs[1].set_ylabel('Typed mixed minus fresh-only total loss');axs[1].legend(fontsize=8)
fig.tight_layout();fig.savefig(R/'reliability_and_cost.png',dpi=150);plt.close(fig)
report=f"""# SRDE LA2 — Learning an imperfect verifier does not guarantee better decisions

Executed 3 November 2026. Research direction: Dan Merluse. Protocol, software, analysis, literature review and audits are AI-assisted.

## Main finding

Typed delayed feedback reduces error in estimating the lineage verifier's reliability. Across the frozen mixture of 160 calibration worlds, its q mean absolute error is {m('MixedSelectedBayes')['q_error']:.5f}, versus {m('SelectedVerifiedCounts')['q_error']:.5f} for selectively verified counts and {m('RandomVerifiedCounts')['q_error']:.5f} for randomly verified counts.

The primary paired result favors typed inference over selected counts: total loss difference {primary['delta']:+.9f}, with a stratified calibration-world bootstrap 95% percentile interval [{primary['lower']:+.9f}, {primary['upper']:+.9f}]. They receive identical selected observations, incur identical acquisition charges and use the same deployment action space. This is a conventional likelihood correction in a disclosed synthetic benchmark; it is not a newly invented statistical method.

The broader decision result is negative at the primary 512-case amortization horizon. Typed mixed total loss is {m('MixedSelectedBayes')['total_loss']:.9f}; fresh-only is {m('FreshOnly')['total_loss']:.9f}. The mixed learner costs {m('MixedSelectedBayes')['total_loss']-m('FreshOnly')['total_loss']:+.9f} more per case overall. Latent-only conventional Bayes, which avoids reference-query costs, also has lower overall total loss ({m('LatentBayes')['total_loss']:.9f}). Better q estimation is not sufficient to justify buying verification.

SRDETypedRecursive and MixedSelectedBayes have identical fitted posteriors, probabilities, action traces and abstention decisions on every exact and sampled case. No recursive-portal advantage is established.

## Why this experiment follows LA1

LA1 assumed verifier reliability q was known, and showed cheap perfect lineage audits can sometimes beat fresh evidence. LA2 instead learns q from delayed event outcomes and delayed, selectively requested source-lineage references. It then asks whether the learned policy repays the calibration cost. This changes the unknown parameter, information arrival, selection mechanism and cost estimand, rather than merely changing seeds.

The other experiment chats were inspected before design: E04/E05 selective suspension and timestamped evidence; P5/P6 path ordering and limited-storage reconstruction; Study05 worker storage/queues and proposed distributed switching. Those conversation-reported results were not rerun here. No other chat or running job was interrupted.

Observer-error learning and verification bias have longstanding precedents. [Dawid & Skene, 1979](https://crowdsourcing-class.org/readings/downloads/ml/EM.pdf) estimated observer error rates with latent true labels. [Hui & Walter, 1980](https://pubmed.ncbi.nlm.nih.gov/7370371/) studied error-rate identification under assumptions. [Begg & Greenes, 1983](https://pubmed.ncbi.nlm.nih.gov/6871349/) addressed selective verification. NOVELTY.md records read scope, search families, access gaps and recent provenance-related predecessors. Classification: SRDE benchmark extension and robustness test. Worldwide originality is not certified.

## Frozen design and leakage boundary

The protocol and six source/design files were publicly frozen in GitHub commit 684f1974e7a1cdee9ca19c5a4d575283a61c04f5 before the scientific run. The experiment uses 20 seeds per condition, eight conditions and 128 calibration cases per world. Conditions cross true audit reliability q in {{1,.8,.5,0}} with actual source accuracy .8 or .65. The learner assumes .8 throughout. The .65 family is source-model misspecification, not temporal drift.

An event label Y arrives five time steps after each case. A requested perfect simulated lineage reference L arrives 17 steps after issue, twelve after Y. Calibration freezes at time128; 124 event labels can be visible. References requested after time111 have not arrived, but their costs are charged. Requests occur only after Y is known, with a maximum32 per strategy. Random verification requests with probability .25; selected verification requests with probability .8 when the audit agrees with the model's MAP lineage, otherwise .1. Selection uses observed x,Y,z and never hidden L.

All learners see sanitized packets. The data release additionally includes hidden simulator variables for audit; they are never passed to learners. Deployment uses a separate seeded stream offset by10,000,000. The fixed finite outcome distribution is exhaustively evaluated as a separate exact expectation. There was no parameter selection on deployment scores.

Each learner receives128 audit reports at cost .00375 each, plus .003 for every requested lineage reference, even pending requests. The q posterior starts uniform over101 values from0 to1. Its mean is quantized to .01 for the decision planner. This is a plug-in posterior-mean policy, not a Bayes-adaptive planner integrating q uncertainty. q remains fixed during deployment.

Deployment reuses the unchanged LA1 three-slot decision problem: stop, acquire up to two fresh reports at .015 each, or purchase one lineage audit at .00375. Abstention costs .15. Otherwise terminal loss is squared probability error, plus query cost. Total per-case loss also adds calibration cost divided by H in {{64,512,4096}}. H is a counterfactual number of stable deployments sharing calibration; it is not the sampled test-set size. The sampled set has128 held-out cases per world regardless of H.

## What the learners mean

LatentBayes uses one correctly marginalized factor per report, with whatever Y has arrived, and no lineage references. TargetHardCounts wrongly treats MAP-inferred lineage from x,Y as verified lineage. RandomVerifiedCounts and SelectedVerifiedCounts use only arrived verified lineage and ignore the rest; the latter is a deliberately exposed verification-bias baseline. MixedRandomBayes and MixedSelectedBayes use all reports, replacing a marginal factor with the finer verified-lineage factor when it arrives.

For a report, t=P(L=z|x,Y observed so far), and its q-dependent factor is q*t+(1-q)*(1-t). If lineage is verified, t becomes the indicator L=z. Later evidence refines the same report's likelihood; it does not create another independent report. Selection depends on already observed x,Y,z, so its probability is constant in q for that recorded packet; conditioning on those observations makes the selection mechanism ignorable in the full likelihood. Counts that discard unverified packets lose that protection.

DoubleCountSelected deliberately multiplies overlapping issue-time, event-label and lineage factors from the same report. It is a negative control, not an acceptable independent-evidence interpretation. SRDETypedRecursive uses the same typed posterior as MixedSelectedBayes and recursively solves the same action graph that the conventional policy solves by backward induction. Both have identical information and actions. KnownAuditQ receives the true q without calibration charge; it is an information-advantaged diagnostic, and still assumes the source accuracy .8. It is not a full oracle in the misspecified family.

## Primary metrics: all eight frozen conditions

{tables['all']}

Loss and Brier are lower-is-better. Forecast coverage is one minus abstention. Brier and ECE include all terminal probabilities, including abstained cases. ECE uses ten equal-width probability bins and is a post-freeze descriptive diagnostic; it was not used to select the model or declare the primary result. q-error is omitted for nonlearners because their fixed/privileged q values are not comparable parameter estimates.

The typed mixed 95% equal-tail grid interval contains true q in {m('MixedSelectedBayes')['interval_contains_q']:.2%} of calibration worlds; selected counts achieve {m('SelectedVerifiedCounts')['interval_contains_q']:.2%}. These are repeated-simulation interval inclusion rates under this fixed condition mixture, not universal confidence guarantees. Boundary q values0 and1 make coverage and posterior-mean behavior sensitive to the discrete prior.

## Correct source model

{tables['specified']}

Typed inference lowers deployment loss before calibration charges. At H512, its total is still above fresh-only. At H4096 it falls to {m('MixedSelectedBayes','specified',4096)['total_loss']:.9f}, below fresh-only {m('FreshOnly','specified',4096)['total_loss']:.9f}. The pooled expected break-even is about {break_even:.1f} stable deployment cases. This is a descriptive algebraic break-even for this fixed mixture and cost model; it does not establish an operational threshold in real data. Latent-only Bayes remains slightly better in total at H4096.

## Wrong source model

{tables['source_model_error']}

Typed q estimation is accurate in this particular misspecified family, but the planner still trusts source reports too much. Its deployment loss exceeds fresh-only before calibration charges; amortizing its calibration expense over more cases cannot repair that fixed policy. Even KnownAuditQ loses to fresh-only. This separates verifier reliability from the accuracy of the rest of the inference model.

## Uncertainty and negative results

The primary interval resamples independent calibration worlds within each of the eight fixed conditions, 1,000 bootstrap draws using seed61621. It describes variation from calibration sampling for the declared mixture, conditional on the exact deployment distribution. It does not treat correlated forecasts within one world as independent trials, and it does not generalize across arbitrary worlds. Secondary comparisons are exploratory and are not adjusted for multiple testing.

Random verified counts are much stronger than selected counts. In the correctly specified family, typed mixed minus random counts is -0.000003205 with interval [-0.000026059,+0.000021254], overlapping zero. The broad primary improvement over selected counts should not be read as superiority over all conventional methods.

The double-counting control is only slightly worse in decision loss overall, despite its defective likelihood. Its interval inclusion rate is {m('DoubleCountSelected')['interval_contains_q']:.2%}, versus {m('MixedSelectedBayes')['interval_contains_q']:.2%} for the typed learner. This negative control does not produce a dramatic collapse here. TargetHardCounts has poor q estimation but nearly fresh-only deployment behavior: it often avoids buying audits. This illustrates why parameter accuracy and decision utility need separate metrics.

The q=.5 cases are hard negatives for useful audit information; q=0 cases are perfectly inverted evidence, not absent or neutral evidence. AssumePerfect performs poorly when that assumption is false. Full condition-level fits, posterior weights, forecasts and metrics are supplied so no unfavorable condition is hidden.

## Verification and reproducibility

Executed entirely on CPU in {E['runtime_seconds']:.2f} seconds for the scientific run; no GPU or paid Colab resource was required. There are {E['calibration_cases']:,} calibration cases and {E['holdout_cases']:,} sampled held-out cases. All11 methods produce {E['exact_prediction_rows']:,} exact weighted forecasts and {E['sample_prediction_rows']:,} sampled forecasts.

Twelve unit tests pass, covering delayed availability, hidden-variable exclusion, reference caps, pending-query charges, conditional-likelihood identity and unchanged LA1 source identity. A separate auditor imports neither runner and recomputes calibration selection, 1,280 posterior fits, exact atom weights, every forecast probability, chronology, costs, abstention, loss, world metrics and recursive/conventional equality. It checks478,720 forecast rows with maximum numerical discrepancy1.47e-14. A second process reproduced all11 scientific output contents exactly; compressed headers and runtime metadata are excluded from that equality check. Audit and replay receipts are included.

To reproduce with Python3 standard library: run python3 -m unittest -v test_la2.py, then python3 run_la2.py, then python3 audit_results.py. Plot/PDF generation is optional and uses matplotlib and reportlab. The data include calibration_raw, calibration_packets, posterior_weights, exact_atoms, exact_predictions, sample_cases, sample_predictions, fits, world_metrics, metrics and bootstrap outputs. MANIFEST.sha256 covers the packaged files.

## Interpretation of 1 and 0

A bit is a symbol until its variable and semantics are specified. Here Y=0 means the simulated event is false; L=0 means sources are independent; z=0 is a verifier's report about L. q=0 means the verifier always inverts L. Missing Y or L is encoded as null/blank and never converted to false. An abstention is a decision under loss, not a truth value. An inactive or unpurchased audit does not count as evidence against an event.

This study uses probabilistic latent-state inference over binary variables; it does not claim to test all four-valued logics, semantic representation learning, human concept grounding or affect. Affect F in [0,1], with0 aversive and1 pleasant, is a separate variable not present in this task and cannot be inferred from event truth. Conflict, staleness, context and valence remain distinct concepts. Earlier semantic tests should be read alongside this narrower verifier-learning experiment.

## Limitations and next inference points

All data are synthetic and generated within one family. Exact expectations are conditional on that generator, not actual predictive success or validation of human cognition. There is no independent empirical dataset, native Blackbird integration, model learned from text, real provenance verifier, deployment drift, uncertain reference truth, or utility measurement in money. Delayed feedback is used only for one calibration cutoff; no online adaptation occurs. The planner does not learn source accuracy, and q plug-in quantization discards posterior uncertainty.

Inference point LA2-I1: typing observations prevents event feedback from being silently treated as verified lineage. Supported by the mechanism and q-error comparison here; not a universal theorem.
LA2-I2: good verifier calibration can coexist with a wrong event posterior and worse decisions. Supported by the .65 source-accuracy family and known-q diagnostic.
LA2-I3: reference acquisition may be unnecessary when ordinary latent inference already learns enough q to select similar actions. Supported by the latent-only cost comparison.
LA2-I4: no portal-specific advantage appeared. All recursive/conventional forecasts and traces tie.

Research question LA2-R1: can source-model misspecification be diagnosed on held-out observational data before deciding to buy lineage evidence? Related identification precedent: Hui & Walter; the next protocol needs a new bounded overlap review and stronger model-learning baseline.
LA2-R2: what changes if lineage reference labels are themselves wrong, or verification depends on unobserved L? Related precedent: Dawid & Skene and verification-bias literature; no missing-not-at-random robustness is established here.
LA2-R3: can actual non-sensitive provenance data support a fair temporal validation with independent labels and realistic query costs? Requires a sourced dataset and access/license check.
LA2-R4: does integrating q posterior uncertainty change acquisition decisions enough to beat cheap plug-in Bayes? This is established Bayesian decision theory; any next run must be labeled an SRDE extension, not a novel algorithm.

Full source/novelty records: https://github.com/MerluseDan/FACO9000/tree/main/research/srde/la2-verifier-learning-2026-11-03 .
"""
(R/'REPORT.md').write_text(report)
# Portable PDF: linked prose, readable tables and figure; no source-code dumps.
pdfmetrics.registerFont(TTFont('DejaVu','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))
styles=getSampleStyleSheet()
for st in styles.byName.values():st.fontName='DejaVu'
styles['BodyText'].fontSize=9;styles['BodyText'].leading=12
story=[]
def para(s,style='BodyText'):
 s=html.escape(s);s=re.sub(r'\[([^]]+)\]\((https?://[^ )]+)\)',r'<link href="\2" color="#216a91">\1</link>',s)
 story.append(Paragraph(s,styles[style]));story.append(Spacer(1,5))
lines=report.splitlines();i=0
while i<len(lines):
 s=lines[i]
 if not s.strip():i+=1;continue
 if s.startswith('|'):
  rows=[]
  while i<len(lines) and lines[i].startswith('|'):
   rr=[x.strip() for x in lines[i].strip('|').split('|')]
   if not all(re.fullmatch(r'[-:]+',x) for x in rr):rows.append(rr)
   i+=1
  rows=[[Paragraph(html.escape(x),styles['BodyText']) for x in row] for row in rows]
  t=Table(rows,colWidths=[112]+[64]*(len(rows[0])-1),repeatRows=1,hAlign='LEFT')
  t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e3edf2')),('VALIGN',(0,0),(-1,-1),'TOP'),('GRID',(0,0),(-1,-1),.3,colors.HexColor('#b8c5ce')),('LEFTPADDING',(0,0),(-1,-1),4),('RIGHTPADDING',(0,0),(-1,-1),4)]))
  story.extend([t,Spacer(1,10)]);continue
 if s.startswith('# '):para(s[2:],'Title')
 elif s.startswith('## '):
  para(s[3:],'Heading2')
  if s=='## Primary metrics: all eight frozen conditions':story.append(Image(str(R/'reliability_and_cost.png'),width=495,height=183))
 else:para(s)
 i+=1
SimpleDocTemplate(str(R/'REPORT.pdf'),pagesize=(650,842),rightMargin=38,leftMargin=38,topMargin=35,bottomMargin=35,title='SRDE LA2 - Learning an imperfect verifier',author='SRDE research').build(story)
print('Report and figure built')
