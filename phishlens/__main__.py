import argparse,json,sys
from pathlib import Path
from .model import ROOT,TextModel
from .engine import analyze

def main():
    p=argparse.ArgumentParser(description='PhishLens AI investigation lab');sub=p.add_subparsers(dest='command',required=True)
    for name in ['fetch','challenge']:sub.add_parser(name)
    t=sub.add_parser('train');t.add_argument('--baseline',action='store_true')
    s=sub.add_parser('serve');s.add_argument('--port',type=int,default=8765)
    a=sub.add_parser('analyze');a.add_argument('email');a.add_argument('--output',default='reports/investigation.json')
    args=p.parse_args()
    if args.command=='fetch':
        from .data import fetch
        fetch()
    elif args.command=='train':
        from .train import train
        train(args.baseline)
    elif args.command=='serve':
        from .web import serve
        serve(args.port)
    elif args.command=='analyze':
        m=TextModel() if (ROOT/'models'/'text_model.json').exists() else None
        r=analyze(Path(args.email).read_bytes(),m);out=Path(args.output);out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(r,indent=2),encoding='utf-8');print('Saved',out)
    elif args.command=='challenge':
        m=TextModel();manifest=json.loads((ROOT/'samples'/'manifest.json').read_text());results=[]
        for item in manifest:
            r=analyze((ROOT/'samples'/item['file']).read_bytes(),m);results.append({**item,'ml_score':r['ml']['score'],'rule_score':r['rule_score'],'verdict':r['verdict'],'ml_detected_at_0_5':r['ml']['score']>=.5})
        out={'note':'AI-authored synthetic challenge set, excluded from training. Illustrative cases, not population accuracy.','cases':results};(ROOT/'reports'/'challenge.json').write_text(json.dumps(out,indent=2),encoding='utf-8');print(json.dumps(out,indent=2))
if __name__=='__main__':
    try:main()
    except (OSError,ValueError) as e:print('PhishLens:',e,file=sys.stderr);sys.exit(1)
