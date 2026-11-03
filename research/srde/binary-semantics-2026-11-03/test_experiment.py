import copy, itertools, json, unittest
import numpy as np
from pathlib import Path
import run_experiment as r

def case(v=1,**changes):
    e=dict(lineage=0,copy=0,age=0,context=0,reliability=.8,leaf=v,edges=[1],active=True)
    e.update(changes)
    return dict(context=0,F=.8,reports=[e])
class Semantics(unittest.TestCase):
    def test_four_states(self):
        self.assertEqual({r.evidence_state(a,b) for a,b in itertools.product([0,1],repeat=2)},{'true_only','false_only','both','neither'})
    def test_unknown_is_not_false(self):
        self.assertEqual(r.score(dict(context=0,reports=[])),.5)
        self.assertLess(r.score(case(-1)),.5)
    def test_inactive_is_not_negative(self):
        self.assertEqual(r.score(case(-1,active=False)),.5)
    def test_duplicate_invariance(self):
        c=case(); p=r.score(c);c['reports']*=4
        self.assertEqual(r.score(c),p)
        self.assertGreater(r.score(c,lineage=False),p)
    def test_independent_corroboration(self):
        c=case();p=r.score(c);e=copy.deepcopy(c['reports'][0]);e['lineage']=1;c['reports'].append(e)
        self.assertGreater(r.score(c),p)
    def test_staleness_tends_unknown(self):
        self.assertAlmostEqual(r.score(case(1,age=100)),.5,places=10)
    def test_wrong_context_unknown(self):
        self.assertEqual(r.score(case(context=1)),.5)
    def test_affect_independence(self):
        c=case();p=r.score(c);c['F']=0;self.assertEqual(p,r.score(c))
    def test_signed_paths_exhaustive(self):
        for n in [1,2,3]:
            for edges in itertools.product([-1,1],repeat=n):
                for leaf in [-1,1]:self.assertEqual(r.decode_recursive(leaf,list(edges)),leaf*np.prod(edges))
    def test_contradiction_cancels_equal_likelihood(self):
        c=case();e=copy.deepcopy(c['reports'][0]);e.update(lineage=1,leaf=-1);c['reports'].append(e)
        self.assertEqual(r.score(c),.5)
    def test_fde_demorgan_exhaustive(self):
        states=list(itertools.product([0,1],repeat=2))
        for a,b in itertools.product(states,repeat=2):self.assertEqual(r.fde_not(r.fde_and(a,b)),r.fde_or(r.fde_not(a),r.fde_not(b)))
    def test_fde_no_explosion(self):
        # Both P and not-P may be designated while unrelated Q lacks truth support.
        p=(1,1); q=(0,0)
        self.assertTrue(p[0] and r.fde_not(p)[0]);self.assertFalse(q[0])
    def test_symbol_permutation(self):
        y=np.array([0,1,0,1]);p=np.array([.1,.8,.3,.7])
        a=r.metrics(y,p);b=r.metrics(1-y,1-p)
        for k in ['auc','accuracy','brier','logloss','coverage80']:self.assertAlmostEqual(a[k],b[k])
    def test_generator_replay(self):
        self.assertEqual(r.generate(44,'test',1),r.generate(44,'test',1))
    def test_recursive_iterative_cases(self):
        for c in r.generate(81,'shift',2):self.assertEqual(r.score(c),r.score(c,recursive=True))
    def test_splits_no_row_leakage(self):
        f=Path(__file__).parent/'results/digits_splits.json'
        for s in json.loads(f.read_text()):
            a,b,c=map(set,[s['train'],s['calibration'],s['test']]);self.assertFalse(a&b or a&c or b&c)
            self.assertEqual(len(a|b|c),360)
    def test_graph_query_independence(self):
        x=np.arange(24).reshape(12,2)/24;y=np.arange(12)%2;q=np.array([[.2,.3],[.8,.9]])
        self.assertAlmostEqual(r.graph_probs(x,y,q,3)[0],r.graph_probs(x,y,q[:1],3)[0])
    def test_probability_bounds(self):
        for c in r.generate(55,'test',1):self.assertTrue(0<=r.score(c)<=1)
if __name__=='__main__':unittest.main(verbosity=2)
