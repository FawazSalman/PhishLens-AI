import csv,hashlib,json,time,urllib.request
from pathlib import Path
from .model import ROOT,normalize
FILES={'CEAS_08.csv':'1f0d59191eec892a709995d48cd8decb','Nazario.csv':'4022d055bb7cf8602f30f768f652e91e','Nigerian_5.csv':'edfbbb89c40e7447f47867bcc82e72f9'}

def fetch():
    folder=ROOT/'data'/'raw';folder.mkdir(parents=True,exist_ok=True)
    manifest=[]
    for name,md5 in FILES.items():
        path=folder/name;url='https://zenodo.org/records/8339691/files/'+name+'?download=1'
        if not path.exists() or hashlib.md5(path.read_bytes()).hexdigest()!=md5:
            for attempt in range(3):
                try:
                    print('Downloading',name,flush=True)
                    with urllib.request.urlopen(url,timeout=120) as response: data=response.read(100_000_001)
                    if len(data)>100_000_000 or hashlib.md5(data).hexdigest()!=md5: raise ValueError('Dataset checksum mismatch: '+name)
                    path.with_suffix('.part').write_bytes(data);path.with_suffix('.part').replace(path);break
                except Exception:
                    if attempt==2: raise
                    time.sleep(2)
        manifest.append({'name':name,'md5':md5,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'url':url,'license':'CC BY 4.0 per Zenodo record'})
        print(name,'checksum verified',flush=True)
    (ROOT/'data'/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')

def load(name):
    csv.field_size_limit(10_000_000)
    out=[]
    with (ROOT/'data'/'raw'/name).open(encoding='utf-8-sig',errors='replace',newline='') as f:
        reader=csv.DictReader(f)
        if not {'subject','body','label'}.issubset(reader.fieldnames or []): raise ValueError('Unexpected dataset schema: '+name)
        for row in reader:
            text=normalize((row.get('subject') or '')+'\n'+(row.get('body') or ''))
            if len(text)<20 or "folder internal data" in text: continue
            label=str(row['label']).strip()
            if label not in ('0','1'): raise ValueError('Unexpected label: '+label)
            out.append((text[:100000],int(label)))
    return out

def deduplicate(rows):
    groups={};conflicts=set()
    for text,label in rows:
        key=hashlib.sha256(text.encode()).hexdigest()
        if key in groups and groups[key][1]!=label: conflicts.add(key)
        groups[key]=(text,label)
    return [v for k,v in groups.items() if k not in conflicts],len(rows)-len(groups),len(conflicts)
