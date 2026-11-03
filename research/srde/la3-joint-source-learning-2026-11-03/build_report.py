"""Reporting only; protocol and experimental outputs are read-only."""
import json,csv,gzip,html,re
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Image,Table,TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
R=Path(__file__).parent;D=R/'results'
M=json.loads((D/'metrics.json').read_text());B=json.loads((D/'bootstrap.json').read_text());E=json.loads((D/'environment.json').read_text());A=json.loads((R/'AUDIT_RESULTS.json').read_text())
def m(n,f='all',h=512):return next(r for r in M if r['method']==n and r['family']==f and r['horizon']==h and r['split']=='exact')
def b(n,f='all'):return next(r for r in B if r['baseline']==n and r['family']==f)
def table(f):
 s='| Method | Deployment loss | Total H512 | Brier | ECE10 | Coverage | Audit rate |\n|---|---:|---:|---:|---:|---:|---:|\n'
 for n in ['FixedFresh','QOnlyFull','JointMAPFull','JointMeanFull','JointBMAFull','JointBMAFresh','NoAuditTrainFresh','SRDERecursive','KnownAll']:
  r=m(n,f);s+=f"| {n} | {r['loss']:.8f} | {r['total_loss']:.8f} | {r['brier']:.8f} | {r['ece10']:.5f} | {r['coverage']:.2%} | {r['audit_rate']:.2%} |\n"
 return s
break_even=m('JointBMAFull')['calibration_cost']/(m('NoAuditTrainFresh')['loss']-m('JointBMAFull')['loss'])
fig,ax=plt.subplots(1,2,figsize=(10,3.5))
names=['QOnlyFull','JointBMAFull','JointBMAFresh','NoAuditTrainFresh']
ax[0].bar(range(4),[m(n)['total_loss'] for n in names],color=['#b8654c','#2d779a','#7b899c','#377b62'])
ax[0].set_xticks(range(4),['Learn q\nonly','Joint +\naudits','Joint +\nfresh only','Cheaper learned\nfresh only']);ax[0].set_ylabel('Total loss at H512; lower is better');ax[0].set_ylim(.095,.125)
for fam,label,color in [('on_grid','True parameters on grid','#377b62'),('off_grid','True parameters between grid values','#b8654c')]:
 vals=[m('JointBMAFull',fam,h)['total_loss']-m('NoAuditTrainFresh',fam,h)['total_loss'] for h in [64,512,4096]]
 ax[1].plot([64,512,4096],vals,'o-',label=label,color=color)
ax[1].set_xscale('log');ax[1].set_xticks([64,512,4096],['64','512','4096']);ax[1].axhline(0,color='black',lw=.7)
ax[1].set_xlabel('Assumed deployments sharing calibration cost');ax[1].set_ylabel('Joint audit minus cheaper learned fresh loss');ax[1].legend(fontsize=7)
fig.tight_layout();fig.savefig(R/'source_learning_and_cost.png',dpi=150);plt.close(fig)
report=f"""# SRDE LA3 — Learning the sources repairs much more than calibrating the verifier

Executed 3 November2026. Research direction: Dan Merluse. Software, protocol, literature review, analysis and audits are AI-assisted.

## Result

Learning source accuracy a and copying prevalence pi alongside verifier reliability q materially improves this benchmark. The primary total-loss difference, JointBMAFull minus QOnlyFull, is {b('QOnlyFull')['delta']:+.9f} with a stratified calibration-world bootstrap 95% percentile interval [{b('QOnlyFull')['lower']:+.9f},{b('QOnlyFull')['upper']:+.9f}]. At the primary H512 horizon the losses are {m('JointBMAFull')['total_loss']:.9f} and {m('QOnlyFull')['total_loss']:.9f}, a {(1-m('JointBMAFull')['total_loss']/m('QOnlyFull')['total_loss']):.2%} reduction. Both receive identical packets, charges and deployment action options.

The broader cost comparison remains negative for verification. NoAuditTrainFresh learns source parameters from existing reports and delayed event labels, buys no calibration audits or lineage references, and scores {m('NoAuditTrainFresh')['total_loss']:.9f}. JointBMAFull scores {m('JointBMAFull')['total_loss']:.9f}; its excess loss is {b('NoAuditTrainFresh')['delta']:+.9f}, interval [{b('NoAuditTrainFresh')['lower']:+.9f},{b('NoAuditTrainFresh')['upper']:+.9f}]. Better modeling helps substantially; extra verification is still not the best total-cost choice at H512.

When calibration expense is already sunk, allowing deployment audits improves on the identical-posterior fresh-only policy by {b('JointBMAFresh')['delta']:+.9f}. That is a small incremental action value, not evidence that acquiring the calibration is worthwhile. Audits are purchased on {m('JointBMAFull')['audit_rate']:.2%} of cases.

Model averaging has no overall measured advantage over the simpler MAP or posterior-mean parameter plug-ins. Recursive SRDE and conventional backward induction have identical predictions and action traces in every exact and sampled case. No unique recursive-portal superiority result appears.

## Prior work and distinction from other experiments

LA2 showed accurate q estimates can coexist with poor decisions when source assumptions are wrong. LA3 changes the learned parameter set, propagates its joint uncertainty into decisions, and adds a cheaper learned fresh-only baseline. It tests the source-model explanation of LA2's negative result. The fixed-source baseline now also shares the coarse q grid and Bayesian predictive integration, so this is not a literal rerun of LA2 scores.

These methods have strong precedents. [Dong et al.,2009](https://www.vldb.org/pvldb/vol2/vldb09-pvldb47.pdf), section4.3, jointly analyze source accuracy, dependence and truth. [Zhao et al.,2012](https://hanj.cs.illinois.edu/pdf/vldb12_bzhao.pdf), sections5.2–5.3, infer truth and source quality with a probabilistic model. [Hinne et al.,2020](https://journals.sagepub.com/doi/full/10.1177/2515245919898657) explain Bayesian model averaging. [Li and Oliva,2021](https://arxiv.org/pdf/2010.02433) formulate active feature acquisition with learned generative models. LA3 is a documented SRDE robustness extension, not new statistical mathematics or certified worldwide originality.

The latest chats were inspected before design. E05 completed a real air-quality sensor test, with E06 directed toward another real dataset and verification/abstention. P6 completed limited-storage reconstruction. Study06 completed local distributed authority-service tests. Their results are conversation-reported and were not independently rerun here. LA3 uses none of E05's sensor data and does not test the same empirical failure-detection question. NOVELTY.md records sources, read scope, queries and access gaps.

## Frozen protocol and data

GitHub freeze commit211fb23fcf96fc303a09fde0709a0cb3aa946a1c was published and seven remote source/design blobs verified before scoring. FREEZE.json hashes six files; the seventh is the freeze manifest itself. No source, model, seed, cost, prior or threshold changed after held-out outcomes were inspected.

There are120 independent calibration worlds:12 seeds for each of10 fixed conditions. Eight on-grid conditions cross a in {{.65,.8}}, pi in {{.2,.8}} and q in {{1,.5}}. Two stationary off-grid conditions use (a,pi,q)=(.7,.35,.8) and(.9,.65,.2). These test finite parameter support; they are not temporal drift or an independent empirical dataset.

Each calibration world contains128 cases issued at times0–127. Event Y arrives at issue+5. A selected lineage reference L arrives at issue+17. Calibration freezes at128, making124 event labels potentially visible. Reference requests use a cap32 and probabilities .8 if Z agrees with the fixed-model MAP lineage, otherwise .1. Selection sees x,Y,Z after Y arrives, never hidden L. A request still pending at cutoff is charged.

The source-data release includes hidden simulator Y/L for arithmetic verification, but fitting functions receive sanitized observation packets only. Sampled deployment cases use a separate random stream offset20,000,000. An exhaustive finite deployment outcome distribution is also scored. No deployment outcomes select model parameters.

The joint prior is uniform over a in {{.55,.65,.8,.95}}, pi in {{.1,.2,.5,.8}}, and q in {{0,.25,.5,.75,.8,1}}:96 parameter triples. QOnlyFull uses the same six q values with a=.8,pi=.2 fixed. The posterior uses the full observation likelihood, summing unknown Y/L and conditioning on arrived reference labels. A later reference refines one underlying case likelihood rather than creating another independent vote. The selection probability is constant in parameters once observed x,Y,Z are conditioned upon; it does not depend on hidden L in this design.

## Predictive inference and decisions

JointBMAFull integrates parameter uncertainty into a joint predictive distribution P(x,Y,L,Z|calibration) before conditioning on the new x. Fresh observations update the within-case posterior and potential audit response distribution. This preserves correlations that would be lost by independently averaging a,pi,q first. The global posterior is frozen across deployment cases; the experiment is not online cross-case adaptation.

For this finite family, parameter uncertainty can be exactly integrated into eight hidden states (Y,L,Z). The resulting three-slot action graph permits stop, at most two fresh reports at .015 each, and one lineage audit at .00375. Audit response arrives after its action. Fresh reports have known accuracy .7. Terminal risk is squared probability error, or abstention costing .15, plus query costs. Ties prefer stop, then fresh, then audit with1e-12 tolerance. Impossible model observations fall back to probability .5 and abstention.

The table policy solves the finite graph by backward induction. SRDERecursive independently traverses the same graph recursively. Equal information, actions, costs and outcomes make their equivalence a necessary control, rather than evidence that recursive naming adds capability.

## Comparators and acquisition costs

FixedFresh retains the .8 source accuracy/.2 copy prior and does no calibration. QOnlyFull learns verifier reliability only. JointMAPFull uses the highest-posterior parameter triple, with frozen grid order breaking ties. JointMeanFull inserts posterior mean parameters into one model. JointBMAFresh uses the same joint posterior as JointBMAFull but disallows deployment audits. NoAuditTrainFresh learns a/pi from x and available Y while ignoring Z and lineage references. KnownAll receives the true parameters without calibration; it is privileged and not a matched-information learned competitor.

All methods have the same three-slot deployment cap; removing audit actions defines the fresh-only controls. Every calibrated-audit method pays128*.00375 plus .003 for each requested lineage reference, including pending ones. JointBMAFull and JointBMAFresh pay identical calibration costs. NoAuditTrainFresh pays no incremental audit/reference charge. Existing initial reports and delayed Y labels are assumed already available at no incremental acquisition cost for all methods. This assumption matters to the cheaper baseline's advantage and must be changed if event labels cost money or effort in a deployment.

Total loss adds calibration cost divided by H in {{64,512,4096}}. H denotes counterfactual stable deployments sharing calibration cost. It does not change the128 sampled held-out cases per world. Cost units are specified loss penalties, not measured money or wall-clock time.

## All conditions: primary exact metrics

{table('all')}

Lower loss, Brier and ECE are better. Coverage is one minus abstention. Brier/ECE include all terminal probabilities, including abstained cases. ECE uses ten equal-width bins and was specified before scoring. Averaging is equal across the10 fixed conditions and12 calibration seeds per condition. It is not an estimate of how often those conditions occur in the world.

The bootstrap resamples calibration worlds within each fixed condition, retaining pairing across methods:1,000 draws, seed88321. It quantifies calibration-sample variability conditional on the fixed generator mixture and exact deployment outcomes. It does not treat within-world predictions as independent observations. The primary interval is predeclared; secondary intervals are exploratory without multiplicity adjustment.

## Parameter-grid stress

On-grid conditions:
{table('on_grid')}

Off-grid conditions:
{table('off_grid')}

Within the on-grid family, joint-learning policies are well calibrated under the known generator structure. Off-grid ECE and losses worsen. The off-grid audit-action difference relative to JointBMAFresh is {b('JointBMAFresh','off_grid')['delta']:+.9f}, interval [{b('JointBMAFresh','off_grid')['lower']:+.9f},{b('JointBMAFresh','off_grid')['upper']:+.9f}]. The interval includes zero: no useful off-grid audit benefit is established.

MAP is slightly better on-grid in this condition mixture. JointBMAFull minus JointMAPFull overall is {b('JointMAPFull')['delta']:+.9f}, interval [{b('JointMAPFull')['lower']:+.9f},{b('JointMAPFull')['upper']:+.9f}]. Model averaging does not win the overall comparison. Bayesian optimality under a prior does not guarantee the best frequentist score under this deliberately chosen condition mixture.

q=.5 supplies an uninformative-audit control, while correctly known parameters diagnose remaining estimation error. The sampled predictions and every unfavorable condition are retained. No new model or threshold was chosen after observing these comparisons.

## Amortization and practical implication

Across all conditions, joint audit learning's algebraic break-even against NoAuditTrainFresh is approximately {break_even:.1f} stable deployments. At H4096, JointBMAFull total is {m('JointBMAFull','all',4096)['total_loss']:.9f} and NoAuditTrainFresh is {m('NoAuditTrainFresh','all',4096)['total_loss']:.9f}, a tiny difference. This break-even is descriptive, conditional on the frozen mixture and charge assumptions; no bootstrap interval for a newly selected H threshold is claimed.

LA3 supports learning the source model before adding verification complexity. It does not support forcing lineage audits into every decision or treating recursion as a performance improvement. The stronger cheap learned baseline is essential: comparing only against frozen assumptions would overstate verification's value.

## Verification and reproduction

The CPU scientific run took {E['runtime_seconds']:.2f} seconds, separate from literature review, audits, packaging and publication. No GPU or paid Colab resources were required. It generated15,360 calibration cases,15,360 sampled held-out cases,165,888 exact forecasts and138,240 sampled forecasts:304,128 forecasts in total.

Eleven unit tests pass. They check delayed packets, exclusion of hidden variables, ignoring audit data in the no-audit learner, posterior normalization, model-mixture conditioning, impossible-observation abstention, recursive/table equality, frozen source identity, and exhaustive reduction of a single-model predictive planner to the previously validated LA1 core.

The standalone auditor imports neither runner. It recomputes360 fitted parameter posteriors,1,080 predictive joint models, every exact atom mass, every forecast probability, cost, abstention, query timing, world metric, and every action's optimality with a separate recursive dynamic program. It confirms all recursive/conventional traces. Its maximum numerical discrepancy is {A['max_numeric_error']:.3g}. A second process reproduced all12 scientific output contents exactly, excluding gzip headers and runtime metadata.

From the extracted package directory, run python3 -m unittest -v test_la3.py, python3 run_la3.py, and python3 audit_results.py. Python3 standard library suffices for scientific runs. Optional report/figure regeneration uses matplotlib/reportlab plus a DejaVu font. All source data, sanitized packets, hidden simulator records, posterior weights, predictive joint masses, exact atoms, sampled cases, forecasts, fit summaries, metrics and bootstrap outputs are provided with a SHA-256 manifest.

## Meaning of 1 and 0, limits, and next questions

Y is simulated event truth, L is source copying state, Z is a verifier report about L, and q is that verifier's reliability. Their zeros have different semantics. Missing Y/L stays null rather than false. An unused audit is an action choice, not evidence against a claim. q=0 means consistently inverted reports. Affect F in[0,1] is not present and must not be equated with truth, confidence or source reliability.

All observations are synthetic; this is a statistical robustness test of a small, declared family. No human cognitive theory, semantic grounding, real-world forecast skill, production Blackbird integration, physical source failure detection or universal identifiability result is established. Source errors are symmetric and share one a. Fresh-source accuracy and event prevalence are known. References are perfect. Copying involves only the first pair. No higher-order hidden dependence, adversarial reporting, temporal changes or missing-not-at-random verification is tested. The parameter grid excludes accuracies below.5, imposing a semantic orientation that real unsupervised systems may lack.

LA3-I1: source-model learning explains a large part of LA2's failure under these conditions; supported by the matched QOnly comparison.
LA3-I2: useful deployment audits can still be an unattractive investment once calibration charges are included; supported by same-posterior fresh and cheaper learner comparisons.
LA3-I3: integrating uncertainty changes behavior but does not guarantee a better score in a selected condition mixture; supported by MAP/mean comparisons.
LA3-I4: recursive and conventional planning remain equivalent in this finite problem.

LA3-R1: is lineage verification worth purchasing when event labels also have a cost? Link to active acquisition precedent above. This needs a new cost/information question, not a free relabeling of H.
LA3-R2: how does posterior predictive model checking expose structural dependence errors outside this family? Link to source-dependence prior work; LA3 did not test structural diagnosis.
LA3-R3: can an independently documented provenance dataset estimate the incremental value of lineage labels over learned conventional predictors? Coordinate scope with E06 through read-only overlap checks before designing another empirical run.
LA3-R4: which orientation assumptions permit source truth/reliability identification without independent labels? Link to latent source-quality work. Known labels in this study anchor the meaning of Y=1/0; ungrounded label symmetry remains unresolved.

Public research directory: https://github.com/MerluseDan/FACO9000/tree/main/research/srde/la3-joint-source-learning-2026-11-03 .
"""
for old,new in [('November2026','November 2026'),('et al.,2009','et al., 2009'),('et al.,2012','et al., 2012'),('et al.,2020','et al., 2020'),('Oliva,2021','Oliva, 2021'),('section4.3','section 4.3'),('sections5.2','sections 5.2'),('commit211','commit 211'),('are120','are 120'),('conditions:12','conditions: 12'),('contains128','contains 128'),('making124','making 124'),('cap32','cap 32'),('triples.','triples.'),(':96 parameter',': 96 parameter'),('tolerance.','tolerance.'),('and12 calibration','and 12 calibration'),('condition:1,000','condition: 1,000'),('seed88321','seed 88321'),('generated15,360','generated 15,360'),('audits.','audits.'),('recomputes360','recomputes 360'),('all12 scientific','all 12 scientific')]:report=report.replace(old,new)
(R/'REPORT.md').write_text(report)
pdfmetrics.registerFont(TTFont('DejaVu','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))
styles=getSampleStyleSheet()
for st in styles.byName.values():st.fontName='DejaVu'
styles['BodyText'].fontSize=9;styles['BodyText'].leading=12
story=[]
def para(s,style='BodyText'):
 s=html.escape(s);s=re.sub(r'\[([^]]+)\]\((https?://[^ )]+)\)',r'<link href="\2" color="#216a91">\1</link>',s)
 story.extend([Paragraph(s,styles[style]),Spacer(1,5)])
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
  t=Table([[Paragraph(html.escape(x),styles['BodyText']) for x in rr] for rr in rows],colWidths=[112]+[64]*(len(rows[0])-1),repeatRows=1,hAlign='LEFT')
  t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e3edf2')),('VALIGN',(0,0),(-1,-1),'TOP'),('GRID',(0,0),(-1,-1),.3,colors.HexColor('#b8c5ce'))]))
  story.extend([t,Spacer(1,10)]);continue
 if s.startswith('# '):para(s[2:],'Title')
 elif s.startswith('## '):
  para(s[3:],'Heading2')
  if s=='## All conditions: primary exact metrics':story.append(Image(str(R/'source_learning_and_cost.png'),width=495,height=173))
 else:para(s)
 i+=1
SimpleDocTemplate(str(R/'REPORT.pdf'),pagesize=(650,842),rightMargin=38,leftMargin=38,topMargin=35,bottomMargin=35,title='SRDE LA3 - Joint source learning',author='SRDE research').build(story)
print('Research report and figure built')
