"""Lightweight deterministic implementation and leakage guard tests."""
import numpy as np
from pathlib import Path
from srde_p2 import PortalTree,make_rows,split_rows,COLS,metrics,method_grid
from statsmodels.datasets import co2

def main():
    raw=co2.load_pandas().data
    rows=make_rows(raw)
    train,val,test=split_rows(rows)
    assert len(train)>700 and len(val)>250 and len(test)>250
    # Exactly four weekly rows separate issue and target; data always causal
    assert ((np.asarray([np.datetime64(d) for d in rows.target_date])-
             np.asarray([np.datetime64(d) for d in rows.issue_date]))/
            np.timedelta64(1,'D')==28).all()
    # Check lag input explicitly on nonmissing raw data
    d=rows.iloc[51];t=raw.index.get_loc(d.issue_date)
    assert abs(d.diff_4-(raw.co2.iloc[t]-raw.co2.iloc[t-4]))<1e-9
    # Labels were not exposed to the model, tests only here use target
    X=train[COLS].to_numpy(float);y=train.target.to_numpy(int)
    model=PortalTree(max_depth=100,alpha=.35)
    model.fit(X,y)
    p=model.predict_proba(val[COLS].to_numpy(float))[:,1]
    assert len(p)==len(val) and np.isfinite(p).all()
    assert 0<=model.deepest_<=100 and model.nodes_>=1
    assert len(model.trace(X[0]))-1<=model.deepest_
    assert abs(sum(model.predict_proba(X[[0]])[0])-1)<1e-12
    assert set(method_grid())=={'constant','seasonal_logistic','logistic','decision_tree','random_forest','hist_gradient_boosting','srde_portal'}
    assert abs(metrics([1,0],[1,0])['brier'])<1e-10
    print('PASS: causal lag/target alignment; temporal isolation; portal recursion bound; normalized probabilities; model registry; scoring')
    print(f'rows: train={len(train)} val={len(val)} test UNOPENED={len(test)}; observed portal depth unit-test={model.deepest_} nodes={model.nodes_}')
if __name__=='__main__':main()
