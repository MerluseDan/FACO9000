import unittest,math,json,hashlib
import run_la3 as r
class Tests(unittest.TestCase):
 def test_predictive_mass(self):
  j=r.predictive([(.65,.8,.5,.4),(.8,.2,1.,.6)])
  self.assertAlmostEqual(sum(map(sum,j)),1.)
 def test_condition_after_integrating(self):
  weighted=[(.55,.8,1.,.5),(.95,.1,.5,.5)]
  j=r.predictive(weighted);p=r.Planner(j);x=1
  expected=sum(j[x][i] for i,(y,l,z) in enumerate(r.HIDDEN) if y)/sum(j[x])
  self.assertAlmostEqual(p.prob(p.start(x)),expected)
 def test_single_model_matches_core(self):
  m=r.core.Model(pi=.35,q=.8,acc=.7);p=r.Planner(r.predictive([(.7,.35,.8,1.)]))
  old=r.core.build(m)
  for case,w in r.core.atoms(m):
   a=p.run(case);b=r.core.rollout(case,'GraphFullDP',m,old)
   self.assertAlmostEqual(a['p'],b['p']);self.assertAlmostEqual(a['loss'],b['loss']);self.assertEqual(a['trace'],b['trace'])
 def test_recursive_table_equality(self):
  p=r.Planner(r.predictive([(.55,.8,.75,.5),(.95,.1,.5,.5)]))
  for s in p.table:
   self.assertAlmostEqual(p.table[s][0],p.recursive(s)[0]);self.assertEqual(p.table[s][1],p.recursive(s)[1])
 def test_no_audit_action(self):
  p=r.Planner(r.predictive([(.8,.2,1.,1.)]),False)
  self.assertTrue(all('A' not in p.actions(s) for s in p.table))
 def test_delayed_packet_sanitized(self):
  raw,p=r.calibration(9,r.conditions()[0])
  self.assertEqual(sum(x['y_observed'] is not None for x in p),124)
  self.assertTrue(all(x['lineage_observed'] is None for x in p[112:]))
  self.assertNotIn('y',p[127]);self.assertNotIn('lineage',p[127])
  self.assertLessEqual(sum(x['reference_requested'] for x in p),32)
 def test_noaudit_training_ignores_audit(self):
  _,p=r.calibration(11,r.conditions()[0])
  other=[{**x,'audit':1-x['audit'],'lineage_observed':1 if x['lineage_observed']==0 else 0} for x in p]
  self.assertEqual(r.fit(p,'noaudit'),r.fit(other,'noaudit'))
 def test_posterior_normalized(self):
  _,p=r.calibration(11,r.conditions()[0])
  for k in ['joint','qonly','noaudit']:self.assertAlmostEqual(sum(x[3] for x in r.fit(p,k)),1.)
 def test_empty_uniform_prior(self):
  p=r.fit([],'joint')
  self.assertTrue(all(abs(v[3]-1/len(r.THETA))<1e-14 for v in p))
 def test_impossible_observation_abstains(self):
  p=r.Planner(r.predictive([(.8,.2,1.,1.)]))
  s=(1,2,(),1) # first pair disagree: L=0; q=1 cannot report Z=1
  self.assertEqual(p.prob(s),.5);self.assertEqual(p.terminal(s)[2],1)
 def test_source_identity(self):
  P=json.loads((r.R/'PROTOCOL.json').read_text())
  self.assertEqual(hashlib.sha256((r.R/'decision_core.py').read_bytes()).hexdigest(),P['source_core_sha256'])
if __name__=='__main__':unittest.main()
