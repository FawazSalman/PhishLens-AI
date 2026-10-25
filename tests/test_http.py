import base64,hashlib,json,re,socket,subprocess,sys,time,unittest,urllib.error,urllib.request
from phishlens.model import ROOT

class HTTPTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with socket.socket() as s:s.bind(('127.0.0.1',0));cls.port=s.getsockname()[1]
        cls.proc=subprocess.Popen([sys.executable,'-m','phishlens','serve','--port',str(cls.port)],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        cls.base=f'http://127.0.0.1:{cls.port}';cls.opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
        for i in range(60):
            try:
                with cls.opener.open(cls.base,timeout=2) as r:html=r.read().decode()
                cls.token=re.search(r"X-PhishLens-Token':'([^']+)",html).group(1);break
            except (OSError,AttributeError):time.sleep(.1)
        else:cls.proc.terminate();raise RuntimeError('Local server did not start')
    @classmethod
    def tearDownClass(cls):cls.proc.terminate();cls.proc.wait(timeout=5)
    def post(self,obj,token=None):
        h={'Content-Type':'application/json','X-PhishLens-Token':token or self.token}
        req=urllib.request.Request(self.base+'/api/analyze',data=json.dumps(obj).encode(),headers=h)
        with self.opener.open(req,timeout=10) as r:return json.loads(r.read())
    def test_analysis_api(self):
        r=self.post({'email':(ROOT/'samples'/'01_account_pressure.eml').read_text()});self.assertGreaterEqual(r['rule_score'],30)
    def test_bad_token_rejected(self):
        with self.assertRaises(urllib.error.HTTPError) as c:self.post({'email':'hello'},'bad')
        self.assertEqual(c.exception.code,403)
    def test_empty_rejected(self):
        with self.assertRaises(urllib.error.HTTPError) as c:self.post({'email':''})
        self.assertEqual(c.exception.code,400)
    def test_original_upload_hash(self):
        raw=b'Subject: bytes\r\nContent-Type: text/plain; charset=iso-8859-1\r\n\r\ncaf\xe9'
        r=self.post({'email_b64':base64.b64encode(raw).decode()});self.assertEqual(r['email_sha256'],hashlib.sha256(raw).hexdigest())
    def test_untrusted_host_rejected(self):
        req=urllib.request.Request(self.base,headers={'Host':'attacker.example'})
        with self.assertRaises(urllib.error.HTTPError) as c:self.opener.open(req)
        self.assertEqual(c.exception.code,403)
    def test_unknown_path_not_served(self):
        with self.assertRaises(urllib.error.HTTPError) as c:self.opener.open(self.base+'/data/raw/CEAS_08.csv')
        self.assertEqual(c.exception.code,404)
if __name__=='__main__':unittest.main()
