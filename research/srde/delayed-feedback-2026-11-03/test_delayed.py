import unittest,copy,json
import numpy as np
import run_delayed as r
def case():return dict(context=0,time=170,target_time=171,reports=[dict(source=i,age=0,observed_time=170,active=True,context=0,leaf=1 if i%2 else -1,edges=[1],copy=0) for i in range(5)])
def model(n='ResetGraph4'):return r.Learner(n,np.full((8,4),.7),(1.,0.),.3)
def event(p,now,y=1):return dict(available_time=now,y=y,forecast=p)
class DelayedTests(unittest.TestCase):
 def test_future_feedback_rejected(self):
  m=model();p=m.predict(case(),170)
  with self.assertRaises(AssertionError):m.feedback(event(p,178),177)
 def test_gold_input_rejected(self):
  c=case();c['y']=1
  with self.assertRaises(AssertionError):model().predict(c,170)
 def test_max_four_votes(self):self.assertLessEqual(len(model().predict(case(),170)['evidence']),4)
 def test_duplicate_invariance(self):
  c=case();a=model().predict(c,170);c['reports']*=4;self.assertEqual(a,model().predict(c,170))
 def test_recursion_sequential_replay(self):
  a=model('ResetPortal');b=model('ResetSequential')
  for t in range(170,1070,9):
   c=case();c['time']=t
   x=a.predict(c,t);y=b.predict(c,t);self.assertEqual(x,y)
   a.feedback(event(x,t+8,t%2),t+8);b.feedback(event(y,t+8,t%2),t+8)
  self.assertEqual(a.alarms,b.alarms)
 def test_warmup_unknown(self):
  a=model();a.ready=0;a.epoch=170
  self.assertEqual(a.predict(case(),170)['p'],.5)
 def test_old_regime_feedback_not_relearned_after_reset(self):
  a=model();p=a.predict(case(),170);a.epoch=175;a.ready=0;s=a.s.copy();a.feedback(event(p,178),178);self.assertTrue(np.array_equal(s,a.s));self.assertEqual(a.ready,0)
 def test_reset_requires_observed_errors(self):
  a=model();bad=dict(p=1.,raw_p=1.,evidence=[],issue_time=0)
  for t in range(31):a.feedback(event(bad,t,0),t)
  self.assertEqual(a.alarms,[]);a.feedback(event(bad,31,0),31);self.assertEqual(a.alarms,[31])
 def test_frozen_does_not_update_weights(self):
  a=model('FrozenGraph4');w=a.weights().copy();p=a.predict(case(),170);a.feedback(event(p,178,0),178);self.assertTrue(np.array_equal(w,a.weights()))
 def test_window_and_decay_finite(self):
  for name in ['Window128Graph4','ExpDecayGraph4']:
   a=model(name)
   for t in range(200):
    p=a.predict(case(),170+9*t);a.feedback(event(p,178+9*t,t%2),178+9*t)
   self.assertTrue(np.isfinite(a.weights()).all())
 def test_generator_replay_and_causal_reports(self):
  p=json.loads((r.ROOT/'PROTOCOL.json').read_text());p['worlds']=2
  a,g=r.generate(711,p);b,h=r.generate(711,p);self.assertEqual(a,b);self.assertEqual(g,h)
  self.assertTrue(all(e['observed_time']<=c['time']<c['target_time'] for rows in a.values() for c in rows for e in c['reports']))
 def test_no_event_flag_required(self):
  c=case();a=model().predict(c,170);c['unread_hidden_change_flag']=True
  self.assertEqual(a,model().predict(c,170))
if __name__=='__main__':unittest.main(verbosity=2)
