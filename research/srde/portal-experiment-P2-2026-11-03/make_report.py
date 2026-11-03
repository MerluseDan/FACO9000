#!/usr/bin/env python3
import json,math
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER,TA_LEFT
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,Image,PageBreak,KeepTogether

P=Path(__file__).resolve().parent
r=json.loads((P/'results.json').read_text());s=json.loads((P/'locked_selection.json').read_text());a=json.loads((P/'audit.json').read_text())
pd.set_option('display.precision',6)
models=['constant','seasonal_logistic','logistic','decision_tree','random_forest','hist_gradient_boosting','srde_portal']
labels={'constant':'Constant prevalence','seasonal_logistic':'Season-only logistic','logistic':'Full logistic','decision_tree':'Decision tree','random_forest':'Random forest','hist_gradient_boosting':'Gradient boosting','srde_portal':'SRDE portals'}
rows=[]
for name in models:
    z=r['models'][name];v=next(x for x in s['validation_grid'] if x['method']==name and x['config']==z['config'])
    rows.append({'method':labels[name], 'validation':v['validation']['brier'], 'holdout':z['metrics']['brier'], 'auc':z['metrics']['roc_auc'], 'accuracy':z['metrics']['accuracy_at_0_5']})
T=pd.DataFrame(rows)
T.to_csv(P/'validation_and_test_comparison.csv',index=False)

# Plot 1: mean squared probability error on completely held-out years
fig,ax=plt.subplots(figsize=(9.0,4.8),constrained_layout=True)
X=T.iloc[::-1]
ax.barh(X.method,X.holdout)
for k,v in enumerate(X.holdout):ax.text(float(v)+.003,k,f'{v:.4f}',va='center',fontsize=9)
ax.set_xlim(0,.29);ax.set_xlabel('Brier score (lower is better)')
ax.set_title('SRDE-P2 | 1995-2001 holdout: next-four-week CO₂ increase')
ax.spines['right'].set_visible(False);ax.spines['top'].set_visible(False)
fig.savefig(P/'holdout_brier.png',dpi=180);plt.close(fig)
# Plot 2: time axis of forecast probabilities, clear retrospective perspective
pred=pd.read_csv(P/'test_predictions.csv',parse_dates=['issue_date'])
fig,ax=plt.subplots(figsize=(10.0,4.1),constrained_layout=True)
ax.plot(pred.issue_date,pred.prob_srde_portal,linewidth=1.25,label='SRDE portals')
ax.plot(pred.issue_date,pred.prob_random_forest,linewidth=1.0,alpha=.8,label='Random forest')
ax.scatter(pred.issue_date,pred.target,s=5,alpha=.23,label='Observed event (0/1)')
ax.set_ylim(-.04,1.04);ax.set_ylabel('Forecast probability / observed event')
ax.set_title('Frozen 1995-2001 retrospective forecasts and observed outcomes')
ax.legend(loc='upper right',fontsize=8,ncol=3)
ax.spines['right'].set_visible(False);ax.spines['top'].set_visible(False)
fig.savefig(P/'holdout_predictions.png',dpi=180);plt.close(fig)
# Plot 3: year-specific errors
Y=a['yearwise_holdout'];years=list(map(int,Y))
fig,ax=plt.subplots(figsize=(9.5,3.7),constrained_layout=True)
for name in ('srde_portal','hist_gradient_boosting','random_forest'):
    ax.plot(years,[Y[str(t)][name] for t in years],marker='o',label=labels[name])
ax.set_ylabel('Brier score');ax.set_xlabel('Held-out issue year');ax.set_title('Performance varies from year to year')
ax.legend(fontsize=9);ax.spines['right'].set_visible(False);ax.spines['top'].set_visible(False)
fig.savefig(P/'yearwise_brier.png',dpi=180);plt.close(fig)

b=r['year_block_bootstrap_portal_minus_gradient_booster']
def m(name):return r['models'][name]['metrics']
report=f'''# SRDE-P2 — Real-Observation Portal Forecasting: Completed Research Report

**Proto Alpha / Blackbird Intelligence — November 3, 2026**  
**Research concept:** Dan Merluse  
**Formalization, implementation, auditing:** ChatGPT-assisted  
**Status:** Single-domain, historical, independently audited, preregistered proof-of-concept. **Negative superiority result.**

## Executive result

On **361 real future-event labels withheld from training and model selection** (1995–2001), the portal model scored **{m('srde_portal')['brier']:.6f}** Brier, compared with **{m('random_forest')['brier']:.6f}** for random forest and **{m('hist_gradient_boosting')['brier']:.6f}** for gradient boosting. **The SRDE prototype did not win.** It outperformed logistic regression (Brier **{m('logistic')['brier']:.6f}**) but not stronger nonlinear competitors. The earlier 1989–1994 validation advantage of SRDE (Brier **0.03707**) did **not** generalize to 1995–2001. Higher AUC is not proof of better calibration; both are recorded.

This is a useful null/negative finding: conditional local subspaces alone do not establish a better forecast architecture. The *hypothesis remains falsifiable and unproven.* No claims of human neuroscience, feelings, universal meaning mapping, or general prediction follow from this test.

## Data, target, and chronology

- Fixed, public historical observations: `statsmodels.datasets.co2` from Mauna Loa Observatory, Hawaii, **1958-03-29 to 2001-12-29**, supplied by installed statsmodels **{s['version_info']['statsmodels']}** (origination: NOAA/Scripps observational series); this is an archival snapshot rather than an operational real-time feed.
- Raw dataset: {r['dataset']['rows_original']} weekly entries, {r['dataset']['original_missing']} missing CO₂ values. Dropping rows with unavailable past lags or future event outcome left {r['dataset']['rows_with_complete_lags_and_target']} candidate rows.
- Forecast question: **Will the concentration four weeks later be higher than today's value?** The event is `CO2[t+4] > CO2[t]`; all features (annual position, past-change windows of 1, 4, 8, 13, 26 and 52 weeks) are observed no later than issue time `t`.
- Training 1958–1988: **{r['dataset']['rows_train']}** rows; selection/validation 1989–1994: **{r['dataset']['rows_validation']}**; final holdout 1995–2001: **{r['dataset']['rows_test']}**. Boundary rows whose targets would cross the next split were excluded.
- Observed holdout event prevalence: **{r['observed_test_positive_rate']:.2%}**. This is retrospective forecasting with observed historical measurements, not a live forecast.

## Complete performance comparison

| Model | Validation Brier | Test Brier | Test ROC AUC | Test accuracy @ 0.5 |
|---|---:|---:|---:|---:|
'''
for z in rows:report+=f"| {z['method']} | {z['validation']:.5f} | {z['holdout']:.5f} | {z['auc']:.4f} | {z['accuracy']:.2%} |\n"
report+=f'''
**Primary prespecified comparator:** Gradient booster Brier minus portal comparison: portal minus booster = **+{b['portal_minus_booster_brier_mean']:.6f}** (positive values favor the booster). Seven-year block-resampled 95% descriptive interval: **[{b['ci95_year_resample'][0]:+.6f}, {b['ci95_year_resample'][1]:+.6f}]**, 5,000 fixed-seed draws. It includes zero, so this single study does not establish a reliable difference. The best conventional model by descriptive test Brier was **random forest**, with portal minus forest = **+{r['best_test_conventional_descriptive']['portal_minus_best_brier']:.6f}**.

## What SRDE portals actually did

The portal prototype used conditional **three-coordinate** gates: annual sine, annual cosine and observed change over the last four weeks. A root logistic forecast was refined by local logistic forecasts; gate thresholds and local models were estimated exclusively from the fitting period. Local forecasts were shrunk toward parent forecasts based on support. This implementation is mathematically similar to a **probabilistic model tree**; it is not unique proof of an exotic spatial geometry.

- Portal configured recursion depth cap: **100**. Actual maximum observed fitted depth: **{r['models']['srde_portal']['max_observed_depth']}**, across **{r['models']['srde_portal']['fitted_nodes']}** fitted nodes. 100 deep layers were *not* demonstrated on real data.
- Local predictors are correlated experts, not independent voters; voting count must not be mistaken for evidence independence.
- No affect/valence coordinate `F` exists in the Mauna Loa dataset. Testing `F ∈ [0,1]` requires separately measured human state and ethical safeguards.

## Controls and reverse inference

- **Random-label negative control:** portal retrained on shuffled fitting labels produced test Brier **{r['portal_label_shuffle_negative_control']['metrics']['brier']:.6f}**, AUC **{r['portal_label_shuffle_negative_control']['metrics']['roc_auc']:.3f}**. The predictive advantage disappears when training signals are destroyed.
- **Backward Bayes diagnostic:** given an *already observed future event*, estimate whether the earlier four-week CO₂ trend was positive. This retrospective inference scored Brier **{r['reverse_bayesian_diagnostic']['test_brier']:.6f}** versus a prior-only Brier **{r['reverse_bayesian_diagnostic']['test_baseline_prevalence_brier']:.6f}**. It is a conventional Bayes calculation and **not** time travel, reverse causation, or a unique SRDE result.
- **Independent audit:** independently recomputed all per-row event labels from raw observations and re-scored every model: **{a['verified_rows']}** rows passed; protocol and dataset SHA-256 hashes agree with the validation lock; no scoring mismatch above `1e-7`.

## Year-to-year diagnostic

| Held-out year | Rows | SRDE Brier | RF Brier | Booster Brier |
|---|---:|---:|---:|---:|
'''
for yr,z in a['yearwise_holdout'].items():report+=f"| {yr} | {z['n']} | {z['srde_portal']:.5f} | {z['random_forest']:.5f} | {z['hist_gradient_boosting']:.5f} |\n"
report+='''
The portal system can outperform the forest in particular years while still losing overall. This volatility, autocorrelation and only seven held-out years argue against grand superiority claims.

## Replication instructions

```bash
python -m pip install numpy pandas scipy scikit-learn statsmodels matplotlib reportlab
python test_srde_p2.py
python srde_p2.py --stage validate --output-dir .
python srde_p2.py --stage evaluate --output-dir .
python audit_p2.py
```

Use a new directory for reruns; the evaluator deliberately refuses to overwrite an existing holdout prediction file. Regenerating with different package versions may create small numerical differences. `locked_selection.json` records each chosen configuration, validation trial and package version; the pre-registration and source dataset were SHA-locked before final scoring. `test_predictions.csv` retains each date, observed outcome, and forecast probability. `results.json` includes all losses, confidence intervals and negative controls.

## What P2 changes in the SRDE roadmap

**Keep:** state-dependent local frames, provenance, conditional branching and explicit reversibility testing as research directions.  
**Do not claim:** that more portal depth always helps, that deep connections establish causation, or that a majority vote proves truth.  
**Next:** preregister a **distinct observational domain** (behavioral or operational events) and test an actually different portal operator (learned context-conditioned coordinate transformations, independent evidence lineage, and calibrated abstention) under fixed cost. Any variant developed after seeing P2's holdout must use a fresh, unopened test period or dataset; never retune this test retroactively.

## Provenance and citations

- Primary dataset documentation: https://www.statsmodels.org/stable/datasets/generated/co2.html
- Scripps Mauna Loa historical observations: https://scrippsco2.ucsd.edu/data/atmospheric-co2-data/sampling-station-records/mauna-loa-observatory-hawaii/
- NOAA carbon dioxide observations: https://gmd-prod.cmdl.noaa.gov/ccgg/trends/data.html
- Predecessor public hypothesis (P0): https://github.com/MerluseDan/FACO9000/blob/main/research/srde/portal-hypothesis-2026-11-02/README.md
- Preregistered research protocol: `PREREGISTRATION.md` (also committed to GitHub before validation/test)

**Boundary:** A computational structure that models certain observable patterns is not proof of how human consciousness works, a measure of personal intelligence, or a universal predictive law.
'''
(P/'REPORT.md').write_text(report,encoding='utf-8')

# PDF designed as a concise, readable 3-4 page report
styles=getSampleStyleSheet()
styles.add(ParagraphStyle(name='BigTitleSR',parent=styles['Title'],fontName='Helvetica-Bold',fontSize=20,leading=24,textColor=colors.HexColor('#15263e'),spaceAfter=10))
styles.add(ParagraphStyle(name='SubSR',parent=styles['Normal'],fontName='Helvetica',fontSize=9,leading=13,textColor=colors.HexColor('#536273'),spaceAfter=10))
styles.add(ParagraphStyle(name='HeadSR',parent=styles['Heading2'],fontName='Helvetica-Bold',fontSize=12,leading=17,spaceBefore=13,spaceAfter=6,textColor=colors.HexColor('#173f69')))
styles.add(ParagraphStyle(name='BodySR',parent=styles['BodyText'],fontSize=9,leading=13,spaceAfter=8))
styles.add(ParagraphStyle(name='FineSR',parent=styles['BodyText'],fontSize=8,leading=11,textColor=colors.HexColor('#405064'),spaceAfter=6))

from xml.sax.saxutils import escape
pdf=P/'SRDE_P2_Research_Report.pdf'
doc=SimpleDocTemplate(str(pdf),pagesize=letter,rightMargin=48,leftMargin=48,topMargin=53,bottomMargin=49,title='SRDE-P2 Real-Observation Portal Forecasting',author='Dan Merluse / AI-assisted Blackbird Intelligence')
story=[]
def para(t,kind='BodySR'):story.append(Paragraph(t,styles[kind]))
def head(t):para(escape(t),'HeadSR')
para('BLACKBIRD INTELLIGENCE <font color="#3171ad">/</font> PROTO ALPHA','SubSR')
para('SRDE-P2 | Real-Observation Portal Forecasting','BigTitleSR')
para('November 3, 2026  ·  Preregistered  ·  Independently audited  ·  Historical CO2 events','SubSR')
para('<b>Outcome:</b> The SRDE portal prototype learned useful predictive structure, but did <b>not</b> outperform the strongest conventional baselines on the held-out observations.','BodySR')
head('Measured results · 1995–2001 holdout')
table_data=[['Method','Valid. Brier','Test Brier','Test AUC']]
for z in sorted(rows,key=lambda z:z['holdout']):table_data.append([z['method'],f"{z['validation']:.5f}",f"{z['holdout']:.5f}",f"{z['auc']:.4f}"])
tab=Table(table_data,colWidths=[180,86,86,85],repeatRows=1)
tab.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e8edf3')),('TEXTCOLOR',(0,0),(-1,0),colors.HexColor('#15263e')),('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),('FONTSIZE',(0,0),(-1,-1),8.6),('LEADING',(0,0),(-1,-1),12),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7),('LINEBELOW',(0,-1),(-1,-1),.8,colors.HexColor('#c8d3df')),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f8fafc')])]))
story.append(tab);story.append(Spacer(1,8))
para(f"<b>Primary paired difference:</b> portal minus gradient booster = <b>+{b['portal_minus_booster_brier_mean']:.6f}</b>; year-block 95% interval [{b['ci95_year_resample'][0]:+.6f}, {b['ci95_year_resample'][1]:+.6f}]. The interval includes zero. Random forest had the lowest test Brier at {m('random_forest')['brier']:.6f}.",'FineSR')
story.append(Image(str(P/'holdout_brier.png'),width=500,height=230))
story.append(PageBreak())
head('What was tested and what was held out')
para('Historical Mauna Loa weekly CO2 (1958-2001) from the fixed statsmodels 0.14.6 dataset. Forecast: is concentration four weeks in the future greater than today? Predictors contain only historical changes and annual phase. Training: 1,320 observations ending 1988; validation: 309 ending 1994; test: 361 issued in 1995-2001. Rows whose labels crossed date boundaries were excluded.','BodySR')
para(f"The portal model learns recursively gated local probability models in a three-coordinate space (annual sine, cosine, recent CO2 change). <b>Depth cap = 100; actual depth = {r['models']['srde_portal']['max_observed_depth']}; nodes = {r['models']['srde_portal']['fitted_nodes']}.</b> It is similar to a model tree, not proof of exotic geometry.",'BodySR')
para('ROBUSTNESS AND FAILURE MODES','SubSR');para('A negative result is still a result','BigTitleSR')
story.append(Image(str(P/'holdout_predictions.png'),width=500,height=142));story.append(Spacer(1,6))
head('Control checks')
para(f"<b>Shuffled-label control:</b> Brier = {r['portal_label_shuffle_negative_control']['metrics']['brier']:.6f}, near the constant no-information score {m('constant')['brier']:.6f}. <b>Reverse inference:</b> a conventional Bayesian diagnostic inferred prior trend from a known later outcome (Brier {r['reverse_bayesian_diagnostic']['test_brier']:.6f} versus prior baseline {r['reverse_bayesian_diagnostic']['test_baseline_prevalence_brier']:.6f}); this is not retrocausality.")
para(f"<b>Audit:</b> all 361 raw events and dates were checked independently against the source; all model Brier, log-loss and accuracy scores recomputed within 1e-7; protocol and source file checksums matched the preregistered validation lock.")
story.append(Image(str(P/'yearwise_brier.png'),width=500,height=112))
head('Scientific boundary')
para('The model uses no emotion or feeling measurements, and provides no evidence about subconscious processes, human intelligence, universal meaning, or real-world causation. Model forecasts are retrospective, from an archival data snapshot. Only seven holdout years support the bootstrap uncertainty estimate; serial dependence remains.','BodySR')
para('Project origin: Dan Merluse. Formalization, implementation, and auditing: AI-assisted. Source scripts, full per-date forecasts, preregistration, negative controls, package versions and SHA-256 manifest are in the accompanying archive.','FineSR')

def footer(canvas,doc):
    canvas.setFont('Helvetica',7.5);canvas.setFillColor(colors.HexColor('#5c6b7d'))
    canvas.drawString(48,30,'PROTO ALPHA  ·  BLACKBIRD INTELLIGENCE  ·  SRDE-P2')
    canvas.drawRightString(letter[0]-48,30,str(doc.page))

doc.build(story,onFirstPage=footer,onLaterPages=footer)
print('REPORT.md, 3 PNG charts, and PDF generated')
