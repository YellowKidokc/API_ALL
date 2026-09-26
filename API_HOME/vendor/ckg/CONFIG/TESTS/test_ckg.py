import json, tempfile, unittest
from pathlib import Path
from workbench.ckg import Runner, scan, initialize, valid_stage
from workbench.providers import ProviderResult

class Fake:
    name='fixture';model='fixture';calls=0
    def complete(self,prompt,*args,**kwargs):
        self.calls+=1
        if 'Map this document as JSON' in prompt:
            value=dict(title='Test paper',domain='Mathematics',project='Tests',purpose='paper',summary='Test',keywords=['test'],objects=[dict(key='C1',type='CLAIM',register='FORMAL_MATHEMATICAL',quote='True',statement='True',reason='Explicit')],unmapped=['Remainder not deeply opened'])
        else:value=dict(status='AI_PROPOSED',reason='Fixture only',markdown='Fixture analysis; no actual verification.',object_keys=['C1'])
        return ProviderResult(json.dumps(value))

class Tests(unittest.TestCase):
    def test_thirty_and_resume(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);initialize(root);(root/'templates').mkdir()
            (root/'templates/CKG_ATOM_MASTER_TEMPLATE.md').write_text('fixture')
            for i in range(30):(root/'INBOX/03_GENERAL'/f'{i}.md').write_text(f'True {i}')
            (root/'INBOX/00_WAITING_NOT_PROCESSED/wait.md').write_text('True waiting')
            (root/'INBOX/01_PRIORITY/copy.md').write_text('True 0')
            items,_=scan(root);self.assertEqual(len(items),30)
            fake=Fake();r=Runner(root,fake);results=r.batch(items,30)
            self.assertTrue(all(x['status']=='SOURCE_REVIEW_COMPLETE' for x in results))
            self.assertTrue(all(r.completed(x) for x in items))
            calls=fake.calls;r.process(items[0]);self.assertEqual(fake.calls,calls)
            self.assertEqual(len(list((root/'OUTBOX').glob('*.md'))),30)
            self.assertEqual((root/'INBOX/00_WAITING_NOT_PROCESSED/wait.md').read_text(),'True waiting')

    def test_invalid_quote_rejected(self):
        with self.assertRaises(ValueError):
            valid_stage('map',dict(title='x',domain='x',project='x',purpose='x',summary='x',objects=[dict(key='C1',type='CLAIM',quote='invented')],unmapped=[]),'True')

    def test_failure_does_not_stop_other_paper(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);initialize(root);(root/'templates').mkdir();(root/'templates/CKG_ATOM_MASTER_TEMPLATE.md').write_text('fixture')
            (root/'INBOX/03_GENERAL/good.md').write_text('True')
            (root/'INBOX/03_GENERAL/bad.md').write_bytes(b'\xff')
            items,_=scan(root);out=Runner(root,Fake()).batch(items,2)
            self.assertEqual(sorted(x['status'] for x in out),['NEEDS_ATTENTION','SOURCE_REVIEW_COMPLETE'])

if __name__=='__main__':unittest.main()
