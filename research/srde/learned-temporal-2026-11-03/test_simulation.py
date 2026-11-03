import copy,json,unittest
from pathlib import Path
import numpy as np
import run_simulation as r

class TemporalTests(unittest.TestCase):
 def setUp(self):
  self.proto=json.loads((r.ROOT/'PROTOCOL.json').read_text());self.proto.update(worlds=2,unseen_worlds=1)
  self.data,_=r.generate(917,self.proto)
 def test_deterministic_generator(self):self.assertEqual(self.data,r.generate(917,self.proto)[0])
 def test_no_future_reports(self):
  for a in self.data.values():
   for c in a:self.assertTrue(all(e['observed_time']<=c['time']<c['target_time'] for e in c['reports']))
 def test_temporal_gap(self):
  for a,b in [('train','calibration'),('calibration','chronological'),('chronological','shift')]:self.assertLess(max(c['target_time'] for c in self.data[a]),min(e['observed_time'] for c in self.data[b] for e in c['reports']))
 def test_unseen_worlds_disjoint(self):self.assertFalse({c['world'] for c in self.data['train']}&{c['world'] for c in self.data['unseen']})
 def test_learning_uses_training_only(self):
  w,_=r.fit_weights(self.data['train']);self.data['shift'][0]['y']^=1;w2,_=r.fit_weights(self.data['train']);self.assertTrue(np.array_equal(w,w2))
 def test_duplicate_invariance(self):
  w,_=r.fit_weights(self.data['train']);c=copy.deepcopy(self.data['chronological'][0]);v=r.vector(c,w);c['reports']*=5;self.assertTrue(np.array_equal(v,r.vector(c,w)))
 def test_recursive_sequential(self):
  w,_=r.fit_weights(self.data['train'])
  for c in self.data['shift']:self.assertEqual(r.walk_recursive(r.ordered(c,w),w),r.walk_iterative(r.ordered(c,w),w))
 def test_budget_four(self):
  w,_=r.fit_weights(self.data['train'])
  for c in self.data['chronological']:self.assertLessEqual(len(r.ordered(c,w)),4)
 def test_predictor_does_not_use_gold(self):
  w,_=r.fit_weights(self.data['train']);c=copy.deepcopy(self.data['chronological'][0]);v=r.vector(c,w);c.pop('y');self.assertTrue(np.array_equal(v,r.vector(c,w)))
 def test_unknown_prior(self):self.assertEqual(r.walk_recursive([],np.zeros((8,4))),(.5,0))
 def test_inactive_excluded(self):
  c=copy.deepcopy(self.data['chronological'][0])
  for e in c['reports']:e['active']=False
  self.assertEqual(r.eligible(c),[])
 def test_learned_parameters_finite(self):
  w,a=r.fit_weights(self.data['train']);self.assertTrue(np.isfinite(w).all());self.assertTrue(((a>0)&(a<1)).all())
if __name__=='__main__':unittest.main(verbosity=2)
