import hashlib
import ipaddress
import re
from email import policy
from email.parser import BytesParser
from email.utils import parseaddr
from html.parser import HTMLParser
from urllib.parse import urlsplit

MAX_BYTES = 2_000_000

def defang(s):
    return s.replace('https://', 'hxxps://').replace('http://', 'hxxp://').replace('.', '[.]')

class HTMLText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.text=[]; self.links=[]; self.hidden=0
    def handle_starttag(self, tag, attrs):
        if tag in ('script','style'): self.hidden+=1
        if tag=='a':
            for k,v in attrs:
                if k=='href' and v: self.links.append(v)
    def handle_endtag(self, tag):
        if tag in ('script','style'): self.hidden=max(0,self.hidden-1)
    def handle_data(self, data):
        if not self.hidden: self.text.append(data)

def parse_email(raw):
    if len(raw)>MAX_BYTES: raise ValueError('Email exceeds 2 MB limit.')
    msg=BytesParser(policy=policy.default).parsebytes(raw)
    plain=[]; html=[]; links=[]; attachments=[]
    for part in msg.walk():
        if part.is_multipart(): continue
        name=part.get_filename()
        if name or part.get_content_disposition()=='attachment':
            attachments.append({'name': name or '(unnamed)', 'type':part.get_content_type()}); continue
        if part.get_content_type() not in ('text/plain','text/html'): continue
        try: text=part.get_content()
        except (LookupError,ValueError,UnicodeError): text=(part.get_payload(decode=True) or b'').decode('utf-8',errors='replace')
        if not isinstance(text,str): continue
        if part.get_content_type()=='text/html':
            parser=HTMLText(); parser.feed(text); html.append(' '.join(parser.text)); links.extend(parser.links)
        else: plain.append(text)
    body='\n'.join(plain or html)[:100000]
    # Include HTML alternative links even when a plain alternative exists.
    links.extend(re.findall(r'https?://[^\s<>"\x27]+',body,re.I))
    links=list(dict.fromkeys(u.rstrip('.,;)') for u in links if u.lower().startswith(('http://','https://'))))[:100]
    headers={k:str(msg.get(k,''))[:2000] for k in ['From','To','Reply-To','Return-Path','Subject','Date','Authentication-Results','Message-ID']}
    return {'sha256':hashlib.sha256(raw).hexdigest(),'headers':headers,'body':body,'urls':links,'attachments':attachments,'parser_defects':[type(d).__name__ for d in msg.defects]}

def evidence(mail):
    items=[]
    def add(kind,detail,weight): items.append({'id':f'E{len(items)+1}','kind':kind,'detail':detail,'weight':weight})
    h=mail['headers']; body=mail['body']; text=h['Subject']+' '+body
    sender=parseaddr(h['From'])[1].lower(); reply=parseaddr(h['Reply-To'])[1].lower()
    domain=lambda s:s.rsplit('@',1)[-1] if '@' in s else ''
    if domain(sender) and domain(reply) and domain(sender)!=domain(reply): add('Reply-To mismatch','From and Reply-To domains differ; may also occur in legitimate services.',15)
    auth=h['Authentication-Results']
    if auth: add('Unverified header','Authentication-Results is supplied message text; its origin is not trusted by this lab.',0)
    if re.search(r'\b(spf|dkim|dmarc)\s*=\s*fail\b',auth,re.I): add('Claimed authentication failure','Message header claims SPF, DKIM or DMARC failure; verify with trusted mail gateway.',15)
    if re.search(r'\b(urgent|immediately|suspend(?:ed)?|within \d+ hours|final warning)\b',text,re.I): add('Pressure language','Urgency or account pressure language detected.',10)
    if re.search(r'\b(password|verify your|sign in|log in|credentials)\b',text,re.I): add('Credential theme','Text discusses credentials or account verification.',10)
    if re.search(r'ignore (all |previous |prior )*(instructions|rules)|system prompt|classify.*(?:safe|benign)',text,re.I): add('Prompt injection signal','Text appears to instruct an automated reviewer; treated as untrusted evidence.',15)
    for u in mail['urls']:
        try:
            p=urlsplit(u); host=p.hostname or ''
            if p.username is not None: add('URL userinfo',defang(u),15)
            try: ipaddress.ip_address(host); add('IP address URL',defang(u),15)
            except ValueError: pass
            if 'xn--' in host.lower(): add('Internationalized hostname',defang(host)+'; punycode alone is not malicious.',5)
            if p.scheme.lower()=='http': add('Unencrypted URL',defang(u),5)
        except ValueError: add('Malformed URL',defang(u),5)
    for a in mail['attachments']:
        if re.search(r'\.(exe|js|vbs|scr|bat|cmd|ps1|iso|lnk|docm|xlsm)$',a['name'],re.I): add('Risky attachment extension',a['name']+'; payload was not extracted or executed.',20)
    return items

def analyze(raw,model=None):
    mail=parse_email(raw); ev=evidence(mail)
    rule_score=min(100,sum(e['weight'] for e in ev))
    ml=model.predict(mail['headers']['Subject']+'\n'+mail['body']) if model else None
    verdict='Elevated signals' if rule_score>=30 or (ml and ml['score']>=0.7) else 'Review recommended' if rule_score>=10 or (ml and ml['score']>=0.3) else 'Few detected signals'
    return {'email_sha256':mail['sha256'],'verdict':verdict,'rule_score':rule_score,'ml':ml,'evidence':ev,'headers':{k:defang(v) for k,v in mail['headers'].items()},'urls':[defang(u) for u in mail['urls']],'attachments':mail['attachments'],'body_preview':defang(mail['body'][:15000]),'limitations':['Scores are research signals, not a safety verdict.','SPF/DKIM/DMARC are not independently verified.','No DNS, URL reputation, live browsing, attachment scanning or detonation.','Text-only historical benchmark may include spam under the positive label.'],'next_steps':['Verify the request through a known separate channel.','Check original headers and gateway logs in a trusted mail system.','If exposure occurred, preserve evidence and follow your incident response process.']}
