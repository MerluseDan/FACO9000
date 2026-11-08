import unittest,math
import run_la4 as r
class Tests(unittest.TestCase):
 def test_probability_mass(self):
  for a in [.65,.8]:self.assertAlmostEqual(sum(r.likelihood(x,b,l,a) for x in range(8) for b in [0,1] for l in [0,1]),1)
 def test_unlabeled_orientation_symmetry(self):
  for a in [.65,.8]:
   for x in range(8):
    for l in [0,1]:
     w=[sum(r.likelihood(x,y^ori,l,a) for y in [0,1]) for ori in [0,1]]
     self.assertAlmostEqual(w[0],w[1])
 def test_missing_not_false(self):
  ag=r.Agent([7]*8,.8);s=ag.initial();self.assertEqual(ag.orientation(s),(.5,.5))
  s=ag.update(s,0,0);self.assertNotEqual(ag.orientation(s)[0],.5)
 def test_lineage_cannot_orient(self):
  ag=r.Agent([7]*8,.8);s=ag.initial()
  for action in [1,3,9,11]:s=ag.update(s,action,1)
  self.assertEqual(ag.orientation(s),(.5,.5))
 def test_anchor_context_scope(self):
  ag=r.Agent([7]*8,.8);s=ag.update(ag.initial(),0,1)
  self.assertNotEqual(ag.orientation(s)[0],.5);self.assertEqual(ag.orientation(s)[1],.5)
 def test_repeated_query_forbidden(self):
  ag=r.Agent([7]*8,.8);s=ag.update(ag.initial(),0,1)
  self.assertNotIn(0,ag.actions(s))
 def test_outcome_mass(self):
  ag=r.Agent([0,2,7,6,4,1,3,5],.8);s=ag.initial()
  for action in ag.actions(s):self.assertAlmostEqual(sum(p for p,ns in ag.outcomes(s,action)),1.)
 def test_short_lookahead_abstention_trap(self):
  ag=r.Agent([7]*8,.65);s=ag.initial()
  self.assertEqual(ag.greedy(s)[1],-1)
  self.assertEqual(ag.table2(s)[1],-1)
 def test_two_solvers_agree(self):
  ag=r.Agent([7]*8,.65);s=ag.initial()
  self.assertEqual(ag.table2(s)[1],ag.recursive(s,2)[1])
  self.assertAlmostEqual(ag.table2(s)[0],ag.recursive(s,2)[0])
 def test_brier_twin_bound(self):
  for p in [0,.1,.5,.8,1.]:
   for y in [0,1]:
    average=((p-y)**2+(p-(1-y))**2)/2
    self.assertAlmostEqual(average,.25+(p-.5)**2);self.assertGreaterEqual(average,.25)
 def test_pool_coupling(self):
  c=r.conditions()[0];d={**c,'orientation':[1,1]}
  a=r.pool(7,c);b=r.pool(7,d)
  for x,y in zip(a,b):
   for k in ['context','x','proxy_b','lineage','reference_u']:self.assertEqual(x[k],y[k])
   self.assertEqual(x['y'],1-y['y'])
 def test_echo_not_grounded(self):
  c={**r.conditions()[0],'reference':'echo'}
  for row in r.pool(3,c):self.assertEqual(row['anchor_response'],(row['x']>>2)&1)
if __name__=='__main__':unittest.main()
