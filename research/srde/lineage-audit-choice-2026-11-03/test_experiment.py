import unittest,itertools
from run_experiment import *
class ContractTests(unittest.TestCase):
    def test_initial_independent_odds(self):
        m=Model(pi=0.);p=probability(initial(7),m)
        self.assertAlmostEqual(p,.8**3/(.8**3+.2**3))
    def test_initial_copied_odds(self):
        self.assertAlmostEqual(probability(initial(7),Model(pi=1.)),.8**2/(.8**2+.2**2))
    def test_impossible_copy_disagreement(self):
        self.assertIsNone(belief(initial(2),Model(pi=1.)))
    def test_fallback_abstains(self):
        self.assertEqual(terminal(initial(2),Model(pi=1.)),(.15,.5,True))
    def test_atom_mass(self):
        for m in [Model(),Model(q=.5),Model(pi=1.)]:self.assertAlmostEqual(sum(p for c,p in atoms(m)),1.)
    def test_uninformative_audit_has_no_value(self):
        m=Model(q=.5);p=TablePlanner(m)
        self.assertTrue(all(a!='A' for s,(v,a) in p.table.items()))
    def test_late_audit_never_selected(self):
        p=TablePlanner(Model(delay=4))
        self.assertTrue(all(a!='A' for s,(v,a) in p.table.items()))
    def test_delay_guard(self):
        m=Model(delay=2);s=initial(6)
        nxt=transition(s,'A',m)
        self.assertTrue(all(ns[3]==-1 and ns[4]==2 for p,ns in nxt))
        self.assertTrue(all(ns[3]!=-1 for p,s1 in nxt for p2,ns in transition(s1,'W',m)))
    def test_budget_cap(self):
        self.assertEqual(actions((3,7,(),-1,-1,False)),())
        self.assertNotIn('F',actions((1,7,(1,0),-1,-1,False)))
        self.assertNotIn('A',actions((1,7,(),-1,2,True)))
    def test_backward_recursive_equivalence(self):
        m=Model();a=TablePlanner(m);b=RecursivePlanner(m)
        for s,(v,act) in a.table.items():self.assertAlmostEqual(v,b.solve(s)[0]);self.assertEqual(act,b.choose(s))
    def test_audit_option_weakly_improves_model_value(self):
        m=Model();a=TablePlanner(m);b=TablePlanner(m,False)
        for x in range(8):self.assertLessEqual(a.table[initial(x)][0],b.table[initial(x)][0]+1e-12)
    def test_perfect_audit_recovers_lineage(self):
        m=Model(q=1.)
        for z in [0,1]:
            s=(1,7,(),z,-1,True);b=belief(s,m)
            self.assertAlmostEqual(sum(b[i] for i in range(4) if i%2==z),1.)
    def test_label_swap_symmetry(self):
        m=Model()
        for x in range(8):self.assertAlmostEqual(probability(initial(x),m)+probability(initial(7-x),m),1.)
    def test_audit_first_can_wait_for_response(self):
        m=Model(delay=2);pl=build(m);r=rollout((1,1,6,1,1,1),'AuditFirst',m,pl)
        self.assertTrue(r['trace'].startswith('A'));self.assertIn(r['audit_seen'],[-1,1])
if __name__=='__main__':unittest.main()
