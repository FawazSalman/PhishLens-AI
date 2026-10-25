import json,unittest
from unittest.mock import patch
from phishlens.engine import analyze,parse_email,MAX_BYTES
from phishlens.data import deduplicate
from phishlens.model import ROOT,TextModel
from phishlens.llm import prioritize

class EngineTests(unittest.TestCase):
    def sample(self,n):return next((ROOT/'samples').glob(n+'*.eml')).read_bytes()
    def test_pressure_and_ip(self):
        r=analyze(self.sample('01'));k={e['kind'] for e in r['evidence']}
        self.assertTrue({'Reply-To mismatch','Pressure language','Credential theme','IP address URL'}<=k)
        self.assertTrue(all('http://' not in u for u in r['urls']))
    def test_html_alternative_links(self):
        m=parse_email(self.sample('05'));self.assertIn('http://192.0.2.30/payroll',m['urls']);self.assertNotIn('<script>',m['body'])
    def test_attachment_not_body(self):
        m=parse_email(self.sample('11'));self.assertEqual(m['attachments'][0]['name'],'invoice.pdf.js');self.assertNotIn('INERT',m['body'])
    def test_untrusted_auth(self):
        r=analyze(b'Authentication-Results: attacker; spf=fail\n\nhello');self.assertIn('Unverified header',{e['kind'] for e in r['evidence']})
    def test_limit(self):
        with self.assertRaises(ValueError):parse_email(b'x'*(MAX_BYTES+1))
    def test_dedup_conflicts(self):
        rows,dups,conflicts=deduplicate([('a',0),('a',1),('b',0),('b',0)]);self.assertEqual(rows,[('b',0)]);self.assertEqual(conflicts,1)
    def test_injection_rule(self):self.assertIn('Prompt injection signal',{e['kind'] for e in analyze(self.sample('04'))['evidence']})
    def test_benign_low_rules(self):self.assertEqual(analyze(self.sample('07'))['rule_score'],0)
    def test_llm_receives_only_categories(self):
        report=analyze(self.sample('01'))
        class Response:
            def __enter__(self):return self
            def __exit__(self,*a):pass
            def read(self,*a):return json.dumps({'message':{'content':'{"evidence_ids":["E1"]}'}}).encode()
        class Opener:
            def open(self,req,timeout):
                data=req.data.decode();assert '192.0.2' not in data;assert 'support@' not in data;return Response()
        with patch('urllib.request.build_opener',return_value=Opener()):self.assertEqual(prioritize(report)['selected'][0]['id'],'E1')
    def test_llm_rejects_unknown_ids(self):
        class Response:
            def __enter__(self):return self
            def __exit__(self,*a):pass
            def read(self,*a):return b'{"message":{"content":"{\\"evidence_ids\\":[\\"E999\\"]}"}}'
        with patch('urllib.request.OpenerDirector.open',return_value=Response()):
            with self.assertRaises(ValueError):prioritize(analyze(self.sample('01')))
    @unittest.skipUnless((ROOT/'models'/'text_model.json').exists(),'Train model first')
    def test_model_and_split(self):
        m=TextModel();r=m.predict('Hello, the project meeting is on Thursday.');self.assertTrue(0<=r['score']<=1)
        p=ROOT/'data'/'split_hashes.json'
        if p.exists():
            split=json.loads(p.read_text());self.assertFalse(set(split['train'])&set(split['test']))
if __name__=='__main__':unittest.main()
