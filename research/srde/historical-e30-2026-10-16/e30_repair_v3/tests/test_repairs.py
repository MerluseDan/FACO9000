"""Regression coverage for audited preflight, identity and checkpoint failures."""
import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'source'))
import e30_core as c
import e30_integrity as i
import e30_run_model as r

class Repairs(unittest.TestCase):
    def setUp(self):
        def count(s):return (len(s)+3)//4
        count.chat_hash=lambda t,ctx:c.sha(c.prompt(t,ctx))
        self.count=count
        self.expected=r.prepare_expected(r.selected_tasks(c.data(),'preflight'),count)
        self.rows=[]
        for (task_id,method),exp in self.expected.items():
            raw='{"answer":"UNKNOWN"}'
            row={k:exp[k] for k in ('world','scenario','gold','prompt_sha256','input_prompt_sha256','evidence_tokens')}
            row.update(task_id=task_id,method=method,model_output=raw,ended=True,seconds=.1,
                retrieval_seconds=.01,state_preprocessing_seconds=.001,evidence_text=exp['ev']['text'],
                **r.strictly_grade(raw,True,exp['gold']))
            self.rows.append(row)

    def test_wrong_answers_do_not_gate_preflight(self):
        self.assertTrue(all(x['status']=='WRONG' for x in self.rows))
        self.assertTrue(i.preflight_passed(self.rows,self.expected))

    def test_preflight_gate_recomputes_wrong_answers_without_accuracy_threshold(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);base={'immutable':'same'}
            i.atomic_json(root/'run_metadata.json',{'base_identity':base,'mode':'preflight'})
            i.atomic_json(root/'model_run.json',{'status':'PREFLIGHT_STRUCTURAL_PASS','completed_calls':4})
            for row in self.rows:i.append_row(root/'model_rows.jsonl',row)
            self.assertEqual(r.checked_preflight(root,base,self.count),i.file_sha(root/'model_rows.jsonl'))
            with self.assertRaisesRegex(RuntimeError,'identity'):r.checked_preflight(root,{'immutable':'changed'},self.count)

    def test_invalid_and_truncated_preflight_block(self):
        for raw,ended in [('broken',True),('{"answer":"UNKNOWN"}',False),('{"x":"UNKNOWN"}',True),('{"answer":"bad"}',True)]:
            rows=copy.deepcopy(self.rows);rows[0].update(r.strictly_grade(raw,ended,rows[0]['gold']))
            self.assertFalse(i.preflight_passed(rows,self.expected))

    def test_duplicate_json_answer_rejected(self):
        self.assertEqual(r.strictly_grade('{"answer":"UNKNOWN","answer":"UNKNOWN"}',True,'UNKNOWN')['status'],'INVALID_JSON')

    def test_main_without_preflight_never_loads_backend(self):
        with patch.object(r,'load_backend') as loader:
            with self.assertRaisesRegex(RuntimeError,'preflight'):r.run('/unused','standard')
            loader.assert_not_called()

    def test_identity_change_refused_original_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            base={'code_digest':'a','model_revision':'immutable','tokenizer_revision':'immutable',
                'dependencies':{'torch':'x'},'dtype':'float16','device_map':{'':'cuda:0'}}
            i.preserve_identity(tmp,base);original=(Path(tmp)/'run_metadata.json').read_bytes()
            for key in base:
                changed=copy.deepcopy(base);changed[key]='changed'
                with self.assertRaisesRegex(RuntimeError,'identity'):i.preserve_identity(tmp,changed)
                self.assertEqual((Path(tmp)/'run_metadata.json').read_bytes(),original)

    def test_exact_expected_rows_valid(self):
        known=i.validate_rows(self.rows,self.expected,r.strictly_grade)
        i.require_exact_completion(known,self.expected)

    def test_equal_count_wrong_keyset_rejected(self):
        rows=copy.deepcopy(self.rows);rows[0]['task_id']='W999-Q99'
        with self.assertRaisesRegex(RuntimeError,'Unexpected'):i.validate_rows(rows,self.expected,r.strictly_grade)

    def test_duplicate_key_rejected(self):
        with self.assertRaisesRegex(RuntimeError,'Duplicate'):i.validate_rows(self.rows+[self.rows[0]],self.expected,r.strictly_grade)

    def test_prompt_and_grade_tampering_rejected(self):
        for key,value in [('prompt_sha256','bad'),('input_prompt_sha256','bad'),('correct',True),
                          ('gold','UNKNOWN'),('evidence_text','fake'),('ended',False),('seconds',float('nan'))]:
            rows=copy.deepcopy(self.rows);rows[0][key]=value
            with self.assertRaises(RuntimeError,msg=key):i.validate_rows(rows,self.expected,r.strictly_grade)

    def test_missing_row_not_complete(self):
        with self.assertRaisesRegex(RuntimeError,'keyset'):i.require_exact_completion(set(list(self.expected)[1:]),self.expected)

    def test_interrupted_tail_preserved_and_recovery_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'rows.jsonl';raw=b'{"a":1}\n{"interrupted"'
            path.write_bytes(raw)
            self.assertEqual(i.recover_jsonl(path),[{'a':1}])
            self.assertEqual(i.recover_jsonl(path),[{'a':1}])
            backups=list(Path(tmp).glob('*.bak'));self.assertEqual(len(backups),1)
            self.assertEqual(backups[0].read_bytes(),raw)
            self.assertEqual(path.read_bytes(),b'{"a":1}\n')

    def test_valid_unterminated_record_is_uncommitted(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'rows.jsonl';path.write_bytes(b'{"a":1}')
            self.assertEqual(i.recover_jsonl(path),[])
            self.assertEqual(len(list(Path(tmp).glob('*.bak'))),1)

    def test_committed_corruption_is_not_trimmed(self):
        for raw in [b'{"a":1}\nbroken\n',b'broken\n{"tail"']:
            with tempfile.TemporaryDirectory() as tmp:
                path=Path(tmp)/'rows.jsonl';path.write_bytes(raw)
                with self.assertRaisesRegex(RuntimeError,'Corrupt'):i.recover_jsonl(path)
                # Original bytes remain either in original or an immutable backup.
                self.assertTrue(path.read_bytes()==raw or any(p.read_bytes()==raw for p in Path(tmp).glob('*.bak')))

    def test_full_visible_world_cost_recorded_for_both_state_methods(self):
        world=c.generate_world(401);task=world['tasks'][0]
        for m in ('graph_state','srde_activated'):
            ev=c.evidence(world,task,m,budget=32)
            self.assertEqual(ev['state_visible_records'],len(world['docs']))
            self.assertGreater(ev['state_validity_checks'],0)
            self.assertGreater(ev['state_preprocessing_seconds'],0)
            self.assertLessEqual(ev['tokens'],32)
        self.assertIn('full visible world',c.prompt(task,'')['system'])

    def test_corpus_matches_immutable_original(self):
        original=Path(__file__).resolve().parents[1]/'corpora'
        for seeds,name in [(c.MAIN_SEEDS,'main'),(c.CONFIRM_SEEDS,'confirmation')]:
            self.assertEqual(c.data(seeds),json.loads((original/(name+'.json')).read_text()))

    def test_gpu_guard_refuses_other_active_process(self):
        from types import SimpleNamespace
        proc=SimpleNamespace(returncode=0,stdout='0 999 C 96 80 - - - - 9690 0 llama-server\n',stderr='')
        with patch('subprocess.run',return_value=proc):
            with self.assertRaisesRegex(RuntimeError,'Unrelated GPU'):r.gpu_guard()

    def test_cpu_substitution_refused(self):
        with self.assertRaisesRegex(RuntimeError,'CPU'):r.load_backend(i.MODEL_ID,True)

if __name__=='__main__':unittest.main()
