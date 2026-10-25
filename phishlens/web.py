import base64,binascii,json,secrets
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from .model import ROOT,TextModel
from .engine import analyze,MAX_BYTES
from .llm import prioritize

def serve(port=8765):
    model=TextModel() if (ROOT/'models'/'text_model.json').exists() else None
    token=secrets.token_urlsafe(32)
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def respond(self,status,data,kind='application/json'):
            self.send_response(status);self.send_header('Content-Type',kind+'; charset=utf-8');self.send_header('X-Content-Type-Options','nosniff');self.send_header('Cache-Control','no-store');self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'none'; frame-ancestors 'none'; connect-src 'self'");self.end_headers();self.wfile.write(data.encode())
        def valid_host(self):return self.headers.get('Host') in (f'127.0.0.1:{port}',f'localhost:{port}')
        def do_GET(self):
            if not self.valid_host():return self.respond(403,'{}')
            if self.path=='/':return self.respond(200,(ROOT/'phishlens'/'index.html').read_text(encoding='utf-8').replace('__TOKEN__',token),'text/html')
            if self.path=='/api/status':
                p=ROOT/'reports'/'evaluation.json';return self.respond(200,json.dumps({'model_ready':model is not None,'evaluation':json.loads(p.read_text()) if p.exists() else None}))
            if self.path=='/api/samples':return self.respond(200,json.dumps({p.name:p.read_text(encoding='utf-8') for p in sorted((ROOT/'samples').glob('*.eml'))}))
            return self.respond(404,'{}')
        def do_POST(self):
            if not self.valid_host() or self.headers.get('X-PhishLens-Token')!=token:return self.respond(403,json.dumps({'error':'Invalid local session.'}))
            if self.path!='/api/analyze':return self.respond(404,'{}')
            try:
                size=int(self.headers.get('Content-Length','0'))
                if size<=0 or size>MAX_BYTES*3//2+100000:raise ValueError('Size')
                obj=json.loads(self.rfile.read(size));text=obj.get('email','')
                if obj.get('email_b64'):
                    raw=base64.b64decode(obj['email_b64'],validate=True)
                else:
                    if not isinstance(text,str) or not text.strip():raise ValueError('Empty email')
                    raw=text.encode('utf-8')
                result=analyze(raw,model)
                if obj.get('use_llm'):
                    try:result['local_ai']=prioritize(result)
                    except Exception:result['local_ai']={'status':'unavailable','note':'No valid Ollama response. Pull qwen2.5:1.5b and start Ollama. Detector results remain available.'}
                return self.respond(200,json.dumps(result))
            except (ValueError,TypeError,AttributeError,KeyError):return self.respond(400,json.dumps({'error':'Invalid input. Provide an email smaller than 2 MB.'}))
            except Exception:return self.respond(500,json.dumps({'error':'Analysis failed.'}))
    server=ThreadingHTTPServer(('127.0.0.1',port),Handler);print(f'PhishLens AI: http://127.0.0.1:{port} (Ctrl+C to stop)',flush=True)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()
