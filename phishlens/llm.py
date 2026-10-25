"""Local evidence selection: raw email is never passed to the LLM."""
import json,urllib.request

def prioritize(report,model='qwen2.5:1.5b'):
    signals=[{'id':e['id'],'kind':e['kind'],'weight':e['weight']} for e in report['evidence']]
    if not signals:return {'status':'no_evidence','selected':[]}
    schema={'type':'object','properties':{'evidence_ids':{'type':'array','items':{'type':'string','enum':[e['id'] for e in signals]},'maxItems':5}},'required':['evidence_ids'],'additionalProperties':False}
    payload={'model':model,'stream':False,'format':schema,'options':{'temperature':0,'num_predict':160,'num_ctx':2048},'messages':[{'role':'system','content':'Select up to five strongest evidence IDs for a defensive email reviewer. Input contains fixed detector categories only. Do not infer maliciousness. Return only JSON with evidence_ids.'},{'role':'user','content':json.dumps(signals)}]}
    req=urllib.request.Request('http://127.0.0.1:11434/api/chat',data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'})
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open(req,timeout=120) as r:result=json.loads(r.read(100000))
    ids=json.loads(result['message']['content']).get('evidence_ids');allowed={e['id']:e for e in report['evidence']}
    if not isinstance(ids,list) or len(ids)>5 or any(not isinstance(i,str) or i not in allowed for i in ids):raise ValueError('Invalid evidence IDs')
    return {'status':'ok','model':model,'selected':[allowed[i] for i in dict.fromkeys(ids)],'note':'LLM prioritizes evidence only. Explanations are copied from detector evidence; AI cannot change scores or verdict.'}
