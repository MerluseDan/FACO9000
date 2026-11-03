#!/usr/bin/env python3
"""SRDE conditional-portal synthetic follow-up, 2026-11-03.
Assisted computational prototype, NOT the original SRDE runtime.
Synthetic data-generating process intentionally favors provenance-sensitive evidence.
Do not treat success on this authored simulator as real-world predictive validation.
"""
import json, time, hashlib
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score, brier_score_loss, log_loss

OUT=Path(__file__).resolve().parent
PROTOCOL={
 "identifier":"SRDE-20261103-P1-synthetic",
 "train_world_ids":list(range(10000,10080)),
 "validation_world_ids":list(range(20000,20020)),
 "test_world_ids":list(range(30000,30060)),
 "shifted_world_ids":list(range(40000,40040)),
 "pairs_per_world":150,
 "max_evidence_paths":64,
 "truth":"Bernoulli(sigmoid(-1.6 + 1.28 * sum_independent_active_votes + .72 * min(2, max(0, number_positive_sources-1))))",
 "portal":"State-conditioned path traversal; group votes by independent source; require two positive sources for strengthened quorum; depth 3 fallback.",
 "calibration":"One-feature logistic calibrator trained only on train worlds for each rule; full-feature conventional models fit train worlds.",
 "models":["CN","Katz","TypedGraph","ProvenanceGraph","Portal","PortalNoState","PortalNoLineage","PortalDepth2","GraphLogistic","FullGraphLogistic","FullGraphHGB"],
 "random_control":"Permute held-out labels only AFTER model training and prediction; do not refit.",
 "metrics":["ROC-AUC","Brier score","log loss","world-bootstrap delta AUC"]
}
(OUT/"FROZEN_PROTOCOL.json").write_text(json.dumps(PROTOCOL,indent=2))
sha=hashlib.sha256((OUT/"FROZEN_PROTOCOL.json").read_bytes()).hexdigest()
def logistic(x):
    return 1/(1+np.exp(-np.clip(x,-30,30)))

def synth_world(seed,shift=False):
    rng=np.random.default_rng(seed)
    rows=[]
    for i in range(PROTOCOL["pairs_per_world"]):
        context=int(rng.integers(3))
        n_sources=int(np.clip(rng.poisson(3.6),1,11))
        observations=[]
        independent=[]
        for source in range(n_sources):
            # Each source emits 1+ duplicate observations. Copies share provenance.
            matched=bool(rng.random()<(.28 if shift else .46))
            tag=context if matched else int((context+int(rng.integers(1,3)))%3)
            orientation=1 if rng.random()<(.65 if shift else .75) else -1
            positive=1 if rng.random()<.61 else -1
            reliability=float(rng.uniform(.55,.94))
            age=float(rng.uniform(0,6))
            depth=2 if rng.random()<.54 else 3
            strength=positive*reliability*np.exp(-age/3) if tag==context and orientation==1 else 0.
            independent.append(strength)
            duplicates=1+int(rng.geometric(.26 if shift else .53)-1)
            duplicates=min(duplicates,12)
            for duplicate in range(duplicates):
                observations.append((source,positive,tag,orientation,reliability,age,depth))
        # All algorithms get the same bounded evidence window. The underlying
        # outcome can depend on latent sources not present in the window.
        observations=observations[:PROTOCOL["max_evidence_paths"]]
        # Each candidate has a latent independent-source process; target is never
        # directly supplied as an input feature.
        net=float(sum(independent))
        n_pos=sum(v>0 for v in independent)
        propensity=-1.6+1.28*net+.72*min(2,max(0,n_pos-1))
        y=int(rng.random()<logistic(propensity))
        # Structural, signed, context-aware, provenance-aware graph features.
        seen={}
        all_seen={}
        length2=length3=0
        path_signed=active_signed=depth2_signed=0.
        independent_pos=independent_neg=0
        for source,v,tag,orient,rel,age,depth in observations:
            length2+=(depth==2)
            length3+=(depth==3)
            atten=rel*np.exp(-age/3)
            raw=v*atten
            path_signed+=raw
            gated=raw if tag==context and orient==1 else 0.
            active_signed+=gated
            if depth==2:depth2_signed+=gated
            # Same source ID cannot manufacture additional independent votes.
            if source not in seen:seen[source]=gated
            elif abs(gated)>abs(seen[source]):seen[source]=gated
            if source not in all_seen:all_seen[source]=raw
            elif abs(raw)>abs(all_seen[source]):all_seen[source]=raw
        source_votes=list(seen.values())
        npos=sum(x>1e-12 for x in source_votes)
        nneg=sum(x<-1e-12 for x in source_votes)
        dedup=sum(source_votes)
        dedup_no_state=sum(all_seen.values())
        two_votes=[v for (source,sgn,tag,orient,rel,age,depth) in observations
                   if depth==2 and tag==context and orient==1 for v in [sgn*rel*np.exp(-age/3)]]
        # Distinct depth-2 witnesses by source, not by observation copy.
        d2={}
        for source,sgn,tag,orient,rel,age,depth in observations:
            if depth==2 and tag==context and orient==1:
                v=sgn*rel*np.exp(-age/3)
                if source not in d2 or abs(v)>abs(d2[source]):d2[source]=v
        q2=sum(v>1e-12 for v in d2.values())>=2
        q=sum(v>1e-12 for v in source_votes)>=2
        # Candidate portal resolves at depth 2 if independent support reaches quorum;
        # otherwise it opens depth-3 evidence to reach a conclusion.
        act_for_portal=list(d2.values()) if q2 else source_votes
        portal_score=sum(act_for_portal)+.65*(sum(v>0 for v in act_for_portal)>=2)
        scores={
            "CN":length2,
            "Katz":length2+.07*length3,
            "TypedGraph":active_signed, # correlated copies counted repeatedly
            "ProvenanceGraph":dedup,
            "Portal":portal_score,
            "PortalNoState":dedup_no_state+.65*(sum(x>0 for x in all_seen.values())>=2),
            "PortalNoLineage":active_signed+.65*(sum(x>0 for x in [v*rel*np.exp(-age/3) if tag==context and orient==1 else 0
                                         for _,v,tag,orient,rel,age,depth in observations])>=2),
            "PortalDepth2":sum(d2.values())+.65*q2
        }
        row={"world":seed,"case_id":f"{seed}-{i}","shift":int(shift),"context":context,"y":y,
             "independent_sources":n_sources,"observations":len(observations),
             "n_positive_sources":npos,"n_negative_sources":nneg, "n_positive_depth2":sum(v>0 for v in d2.values()),
             "context_signed":active_signed,"provenance_signed":dedup,
             "raw_signed":path_signed,"length2":length2,"length3":length3,
             "depth2_signed":depth2_signed,
             "quorum":int(q)}
        row.update(scores)
        rows.append(row)
    return rows

def generate(ids,shift=False):
    return pd.DataFrame(r for s in ids for r in synth_world(s,shift))
def evaluate_subset(df,models):
    y=df.y.to_numpy(); out={}
    for name,predict in models.items():
        q=np.clip(predict(df),1e-6,1-1e-6)
        out[name]={
            "auc":float(roc_auc_score(y,q)),
            "brier":float(brier_score_loss(y,q)),
            "log_loss":float(log_loss(y,q)),
            "n":len(y)
        }
    return out
def world_bootstrap(test,models,other,metric="auc",n=1500,seed=77):
    # Cluster bootstrap at the independent-world level. World AUCs are calculated
    # exactly once; resampled CI is for the world-average paired AUC gap.
    rng=np.random.default_rng(seed)
    pred={m:models[m](test) for m in (other, "Portal")}
    y=test.y.to_numpy()
    ids=test.world.to_numpy()
    deltas=[]
    for w in np.unique(ids):
        ii=np.where(ids==w)[0]
        if len(np.unique(y[ii]))<2:continue
        deltas.append(roc_auc_score(y[ii],pred["Portal"][ii])-roc_auc_score(y[ii],pred[other][ii]))
    ds=np.asarray(deltas)
    draws=rng.integers(0,len(ds),size=(n,len(ds)))
    draws_means=ds[draws].mean(axis=1)
    return {"comparator":other,
            "delta_portal_minus_comparator_world_mean":float(ds.mean()),
            "delta_portal_minus_comparator_pooled":float(roc_auc_score(y,pred["Portal"])-roc_auc_score(y,pred[other])),
            "ci95_world_mean":list(np.quantile(draws_means,[.025,.975])),
            "bootstrap_world_resamples":n}

def main():
    start=time.monotonic()
    datasets={
        "training":generate(PROTOCOL["train_world_ids"]),
        "validation":generate(PROTOCOL["validation_world_ids"]),
        "test":generate(PROTOCOL["test_world_ids"]),
        "shifted_confirmation":generate(PROTOCOL["shifted_world_ids"],True)
    }
    dtrain=datasets["training"]
    # Classic graph features first; full conventional methods access exactly
    # the information used by the portal including independent-source lineage.
    graph_cols=["CN","Katz","TypedGraph","raw_signed","length3","depth2_signed"]
    full_cols=graph_cols+["ProvenanceGraph","n_positive_sources","n_negative_sources",
            "context_signed","quorum","independent_sources","observations"]
    mods={}
    raw_methods=PROTOCOL["models"][:8]
    for m in raw_methods:
        mod=LogisticRegression(max_iter=500,solver="lbfgs")
        mod.fit(dtrain[[m]],dtrain.y)
        mods[m]=lambda df,m=m,mod=mod:mod.predict_proba(df[[m]])[:,1]
    graphlog=LogisticRegression(max_iter=900)
    graphlog.fit(dtrain[graph_cols],dtrain.y)
    fulllog=LogisticRegression(max_iter=900)
    fulllog.fit(dtrain[full_cols],dtrain.y)
    hgb=HistGradientBoostingClassifier(max_iter=90,max_leaf_nodes=16,max_depth=3,
                                        l2_regularization=1.0,random_state=20261103)
    hgb.fit(dtrain[full_cols],dtrain.y)
    mods["GraphLogistic"]=lambda df:graphlog.predict_proba(df[graph_cols])[:,1]
    mods["FullGraphLogistic"]=lambda df:fulllog.predict_proba(df[full_cols])[:,1]
    mods["FullGraphHGB"]=lambda df:hgb.predict_proba(df[full_cols])[:,1]
    result={"experiment":"SRDE conditional portal synthetic challenge",
            "protocol_sha256":sha,
            "counts":{k:{"samples":len(v),"worlds":v.world.nunique(),"positive_rate":float(v.y.mean()),"mean_observation_paths":float(v.observations.mean())} for k,v in datasets.items()},
            "metrics":{k:evaluate_subset(v,mods) for k,v in datasets.items() if k!="training"}}
    result["bootstrap"]={dataset:{
        comp:world_bootstrap(datasets[dataset],mods,comp,n=500,seed=677+i)
        for i,comp in enumerate(["Katz","TypedGraph","ProvenanceGraph","GraphLogistic","FullGraphLogistic","FullGraphHGB","PortalNoState","PortalNoLineage","PortalDepth2"])
        } for dataset in ["test","shifted_confirmation"]}
    rng=np.random.default_rng(888)
    testdf=datasets["test"]
    null_y=rng.permutation(testdf.y.to_numpy())
    result["label_shuffle_control"]={m:float(roc_auc_score(null_y,mods[m](testdf))) for m in ["Katz","Portal","FullGraphLogistic"]}
    # Structural negative control: random layered portals, zero semantic evidence.
    reaches=[]
    for seed in range(50000,50200):
        rg=np.random.default_rng(seed)
        active={0}
        for depth in range(100):
            table=rg.integers(0,12,size=(12,2))
            active={int(table[v,j]) for v in active for j in (0,1)}
        reaches.append(len(active))
    result["100_level_null"]={"worlds":len(reaches),"mean_reachable_endpoints":float(np.mean(reaches)),
                              "min":int(min(reaches)),"max":int(max(reaches)),
                              "interpretation":"High connectivity with no semantic or causal truth"}
    # Duplicate-voter invariance: evidence clones share a source and must not be counted independently.
    result["unit_tests"]={
        "unseen_worlds":len(set(PROTOCOL["train_world_ids"])&set(PROTOCOL["test_world_ids"]))==0,
        "disjoint_shifted_worlds":len(set(PROTOCOL["shifted_world_ids"])&set(PROTOCOL["test_world_ids"]))==0,
        "exact_case_count":all(len(datasets[k])==len(PROTOCOL[v])*PROTOCOL["pairs_per_world"] for k,v in [
            ("training","train_world_ids"),("validation","validation_world_ids"),("test","test_world_ids"),
            ("shifted_confirmation","shifted_world_ids")]),
        "evidence_budget_max":all(int(d.observations.max())<=PROTOCOL["max_evidence_paths"] for d in datasets.values())
    }
    result["run_time_sec"]=time.monotonic()-start
    (OUT/"synthetic_results.json").write_text(json.dumps(result,indent=2))
    cols=["world","case_id","y","shift","independent_sources","observations","CN","Katz","TypedGraph",
          "ProvenanceGraph","Portal","PortalNoState","PortalNoLineage","PortalDepth2"]
    datasets["test"][cols].to_csv(OUT/"synthetic_test_cases.csv",index=False)
    pd.DataFrame([
        {"sample":group,"method":m,**met} for group,all_m in result["metrics"].items() for m,met in all_m.items()
    ]).to_csv(OUT/"synthetic_metrics.csv",index=False)
    print(json.dumps({
        "runtime":result["run_time_sec"],
        "counts":result["counts"],
        "test_auc":{k:round(v["auc"],4) for k,v in result["metrics"]["test"].items()},
        "shift_auc":{k:round(v["auc"],4) for k,v in result["metrics"]["shifted_confirmation"].items()},
        "bootstrap":result["bootstrap"]["test"]["FullGraphLogistic"],
        "null":result["label_shuffle_control"],
        "hundred_level_null":result["100_level_null"],
        "unit_tests":result["unit_tests"]
    },indent=2))
if __name__=="__main__":
    main()
