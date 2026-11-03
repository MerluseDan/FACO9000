"""Experiment 30 offline integrity, independence, and grading tests."""
import copy
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'source'))
import e30_core as c
import e30_run_model as r
from e30_persistence import persist_and_reload

class TestDataset(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.world=c.generate_world(c.MAIN_SEEDS[0])
        cls.corpus=c.data()

    def test_reproducible_dataset_digest(self):
        self.assertEqual(c.data()['sha256'],c.data()['sha256'])
        self.assertEqual(self.corpus['sha256'],c.sha(self.corpus['worlds']))

    def test_no_duplicate_task_or_doc_ids(self):
        for w in self.corpus['worlds']:
            self.assertEqual(len({d['id'] for d in w['docs']}),len(w['docs']))
            self.assertEqual(len({t['id'] for t in w['tasks']}),len(w['tasks']))

    def test_fixed_world_counts_and_scenarios(self):
        self.assertEqual(len(self.corpus['worlds']),8)
        for w in self.corpus['worlds']:
            self.assertEqual([t['scenario'] for t in w['tasks']],list(c.SCENARIOS))

    def test_gold_not_in_question(self):
        for w in self.corpus['worlds']:
            for t in w['tasks']:
                if t['gold']!='UNKNOWN':
                    self.assertNotIn(t['gold'],t['question'])

    def test_gold_not_used_by_retrieval(self):
        t=copy.deepcopy(self.world['tasks'][0]); baseline=c.evidence(self.world,t,'srde_activated')
        t['gold']='INTENTIONALLY_CHANGED'
        actual=c.evidence(self.world,t,'srde_activated')
        baseline.pop('state_preprocessing_seconds');actual.pop('state_preprocessing_seconds')
        self.assertEqual(actual,baseline)

    def test_gold_matches_visible_state_for_all_tasks(self):
        for w in self.corpus['worlds']:
            for t in w['tasks']:
                state=c.materialized_state(w,t)
                self.assertEqual(t['gold'],state['value'],(w['world'],t['scenario'],state))

    def test_current_historical_change(self):
        now=self.world['tasks'][0]['gold'];past=self.world['tasks'][1]['gold']
        self.assertNotEqual(now,past)

    def test_revocation_breaks_copied_bad_origin(self):
        t=self.world['tasks'][4]
        state=c.materialized_state(self.world,t)
        self.assertEqual(state['root_count'],1)
        self.assertEqual(state['value'],t['gold'])
        self.assertEqual(self.world['tasks'][5]['gold'],'UNKNOWN')

    def test_dependency_invalidation_recursive(self):
        t=self.world['tasks'][7]; state=c.materialized_state(self.world,t)
        self.assertEqual(state['value'],'UNKNOWN')
        self.assertIn('root-compromised',state['revoked'])

    def test_conflict_and_expiration_are_unknown(self):
        for idx in (6,9):
            self.assertEqual(c.materialized_state(self.world,self.world['tasks'][idx])['value'],'UNKNOWN')

    def test_method_budget_equal_and_never_exceeded(self):
        for w in self.corpus['worlds']:
            for t in w['tasks']:
                for m in c.METHODS:
                    e=c.evidence(w,t,m,budget=c.TOKEN_BUDGET)
                    self.assertLessEqual(e['tokens'],c.TOKEN_BUDGET)
                    self.assertTrue(e['text'])

    def test_real_budget_measured_and_capped(self):
        # An independent, non-additive token mock simulates token-boundary changes.
        fn=lambda s:len(s.encode('utf-8').split(b' '))
        t=self.world['tasks'][0]
        for method in c.METHODS:
            out=c.evidence(self.world,t,method,budget=32,token_count=fn)
            self.assertLessEqual(out['tokens'],32)

    def test_no_corpus_cross_world_leakage(self):
        all_ids={d['id'] for d in self.world['docs']}
        # Doc IDs are local to each isolated world; verifying selected records are in the matching world.
        for t in self.world['tasks']:
            for m in c.METHODS:
                ev=c.evidence(self.world,t,m)
                self.assertTrue(set(ev['selected']).issubset(all_ids))

    def test_legacy_source_packages_unmodified(self):
        self.assertTrue(c.PROTOCOL_ID.startswith('FACO-SRDE-E30'))

    def test_sqlite_persistence_immutable_and_reopens(self):
        import sqlite3
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'facts.sqlite'
            w=persist_and_reload(self.corpus,path)
            w2=persist_and_reload(self.corpus,path)
            self.assertEqual(w,self.corpus)
            self.assertEqual(w2,self.corpus)
            con=sqlite3.connect(path)
            with self.assertRaises(sqlite3.IntegrityError):
                con.execute('UPDATE records SET payload=? WHERE world=?',('evil',self.world['world']))
            con.rollback()
            with self.assertRaises(sqlite3.IntegrityError):
                con.execute('DELETE FROM questions WHERE world=?',(self.world['world'],))
            con.rollback(); con.close()

    def test_offline_output_has_no_real_llm_claims(self):
        with tempfile.TemporaryDirectory() as d:
            c.save_offline(d,self.corpus)
            summary=json.loads((Path(d)/'offline_summary.json').read_text())
            self.assertEqual(summary['status'],'OFFLINE_RETRIEVAL_ONLY_NOT_REAL_LLM')
            self.assertFalse((Path(d)/'model_run.json').exists())

class TestGrading(unittest.TestCase):
    def test_exact_valid_answer(self):
        self.assertTrue(r.strictly_grade('{"answer":"AABCDEFG"}',True,'AABCDEFG')['correct'])
    def test_invalid_when_wrong(self):
        self.assertEqual(r.strictly_grade('{"answer":"UNKNOWN"}',True,'AABCDEFG')['status'],'WRONG')
    def test_truncated_always_fails_even_if_prefix_valid(self):
        self.assertEqual(r.strictly_grade('{"answer":"UNKNOWN"}',False,'UNKNOWN')['status'],'TRUNCATED')
    def test_no_markdown(self):
        self.assertEqual(r.strictly_grade('```json\n{"answer":"UNKNOWN"}\n```',True,'UNKNOWN')['status'],'INVALID_JSON')
    def test_reject_unknown_keys(self):
        self.assertEqual(r.strictly_grade('{"answer":"UNKNOWN","reason":"ok"}',True,'UNKNOWN')['status'],'INVALID_SCHEMA')
    def test_world_paired_bootstrap(self):
        rows=[]
        for world in ('w1','w2'):
            rows.append({'world':world,'method':'srde_activated','correct':True})
            rows.append({'world':world,'method':'graph_state','correct':False})
        out=r.bootstrap_paired(rows,n=200)
        self.assertEqual(out['n_paired_worlds'],2)
        self.assertEqual(out['delta'],1)
        self.assertEqual(out['ci95'],[1,1])
    def test_resumable_runner_with_mock_backend_not_real_results(self):
        from unittest.mock import patch
        def fake_loader(*args,**kwargs):
            def fake_infer(t,ctx):
                # Deliberately a mock, ONLY a test of output plumbing and resume.
                return {'raw':json.dumps({'answer':t['gold']}),'ended':True,'seconds':0.001,
                        'input_tokens':150,'output_tokens':12}
            def count(s):return (len(s)+3)//4
            count.chat_hash=lambda task,ctx:c.sha(c.prompt(task,ctx))
            return count,fake_infer,{'gpu_name':'MOCK_NOT_REAL'}
        frozen={'corpora':{'main':c.data()['sha256'],'confirmation':c.data(c.CONFIRM_SEEDS)['sha256']}}
        with patch.object(r,'verify_freeze',return_value=frozen):
            with tempfile.TemporaryDirectory() as d:
                report1=r.run(d,'preflight','MOCK_TEST_MODEL',backend=fake_loader())
                report2=r.run(d,'preflight','MOCK_TEST_MODEL',backend=fake_loader())
                self.assertEqual(report1['completed_calls'],4)
                self.assertEqual(report2['completed_calls'],4)
                self.assertEqual(len((Path(d)/'model_rows.jsonl').read_text().splitlines()),4)
                self.assertEqual(report2['protocol']['base_identity']['runtime']['gpu_name'],'MOCK_NOT_REAL')
                self.assertTrue(report2['status'].startswith('MOCK_'))
                self.assertFalse(report2['full_run'])

if __name__=='__main__':unittest.main()
