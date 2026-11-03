import unittest,math,hashlib,json
from pathlib import Path
import run_la2 as r
class CalibrationTests(unittest.TestCase):
 def test_event_boundary(self):
  a={'issue':123,'y':1,'lineage':0,'initial':0,'audit':1}
  self.assertEqual(r.observed_packet(a,True,True)['y_observed'],1)
  a['issue']=124;self.assertIsNone(r.observed_packet(a,True,True)['y_observed'])
 def test_lineage_boundary(self):
  a={'issue':111,'y':1,'lineage':0,'initial':0,'audit':1}
  self.assertEqual(r.observed_packet(a,True,True)['random_lineage'],0)
  a['issue']=112;self.assertIsNone(r.observed_packet(a,True,True)['random_lineage'])
 def test_hidden_values_excluded(self):
  a={'issue':127,'y':1,'lineage':0,'initial':0,'audit':1}
  p=r.observed_packet(a,False,False)
  self.assertNotIn('y',p);self.assertNotIn('lineage',p)
  self.assertIsNone(p['y_observed']);self.assertIsNone(p['selected_lineage'])
 def test_request_cap_and_latency(self):
  _,p=r.make_calibration(5,r.conditions()[0])
  for k in ['random','selected']:
   self.assertLessEqual(sum(x[k+'_requested'] for x in p),32)
   self.assertTrue(all(x['issue']<=123 for x in p if x[k+'_requested']))
   self.assertTrue(all(x['issue']<=111 for x in p if x[k+'_lineage'] is not None))
 def test_empty_uniform(self):
  f,w=r.infer([],'LatentBayes')
  self.assertAlmostEqual(f['q_mean'],.5);self.assertAlmostEqual(sum(w),1)
 def test_one_verified_likelihood(self):
  p={'initial':7,'audit':1,'y_observed':1,'random_requested':1,'selected_requested':1,'random_lineage':1,'selected_lineage':1}
  f,w=r.infer([p],'MixedSelectedBayes')
  norm=sum(r.GRID)
  for q,ww in zip(r.GRID,w):self.assertAlmostEqual(ww,q/norm)
 def test_reference_replaces_marginal(self):
  p={'initial':0,'audit':1,'y_observed':0,'random_requested':1,'selected_requested':1,'random_lineage':0,'selected_lineage':0}
  _,a=r.infer([p],'MixedSelectedBayes');_,b=r.infer([p],'SelectedVerifiedCounts')
  self.assertEqual(a,b)
 def test_pending_reference_charged(self):
  p={'initial':0,'audit':0,'y_observed':1,'random_requested':1,'selected_requested':1,'random_lineage':None,'selected_lineage':None}
  f,_=r.infer([p],'MixedSelectedBayes')
  self.assertAlmostEqual(f['calibration_cost'],.483);self.assertEqual(f['reference_seen'],0)
 def test_recursive_same_information(self):
  _,p=r.make_calibration(10,r.conditions()[0])
  self.assertEqual(r.infer(p,'MixedSelectedBayes'),r.infer(p,'SRDETypedRecursive'))
 def test_copy_impossible_disagreement(self):
  for x in range(8):
   a,b,c=r.core.bits(x)
   if a!=b:self.assertEqual(r.copy_prob(x,1),0)
 def test_source_core_preserved(self):
  p=r.R;protocol=json.loads((p/'PROTOCOL.json').read_text())
  self.assertEqual(hashlib.sha256((p/'decision_core.py').read_bytes()).hexdigest(),protocol['source_core_sha256'])
 def test_joint_factor_identity(self):
  # Direct summation over latent lineage equals conditional mixture factor.
  for x in range(8):
   for y in [0,1]:
    for z in [0,1]:
     for q in [.0,.3,1.]:
      m=r.core.Model()
      terms=[(m.pi if l else 1-m.pi)*r.core.initial_likelihood(x,y,l,m) for l in [0,1]]
      direct=sum(v*(q if z==l else 1-q) for l,v in enumerate(terms))/sum(terms)
      t=r.copy_prob(x,y) if z else 1-r.copy_prob(x,y)
      self.assertAlmostEqual(direct,q*t+(1-q)*(1-t))
if __name__=='__main__':unittest.main()
