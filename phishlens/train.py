import hashlib,json,platform
from datetime import datetime,timezone
import sklearn,numpy,scipy
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report,confusion_matrix,average_precision_score,roc_auc_score
from .model import ROOT
from .data import load,deduplicate,fetch

def train(baseline=False):
    fetch();rows,dupes,conflicts=deduplicate(load('CEAS_08.csv')+([] if baseline else load('Nazario.csv')))
    texts,labels=zip(*rows)
    tr,te=train_test_split(list(range(len(rows))),test_size=.2,random_state=42,stratify=labels)
    v=TfidfVectorizer(ngram_range=(1,2),max_features=30000,min_df=2,sublinear_tf=True)
    x=v.fit_transform([texts[i] for i in tr]);y=[labels[i] for i in tr]
    clf=LogisticRegression(max_iter=500,class_weight='balanced',random_state=42)
    print('Training text baseline...',flush=True);clf.fit(x,y)
    def evaluate(indices):
        xt=v.transform([texts[i] for i in indices]);yt=[labels[i] for i in indices];p=clf.predict_proba(xt)[:,1];pred=(p>=.5).astype(int)
        return {'classification_report':classification_report(yt,pred,output_dict=True,zero_division=0),'confusion_matrix':confusion_matrix(yt,pred,labels=[0,1]).tolist(),'average_precision':average_precision_score(yt,p),'roc_auc':roc_auc_score(yt,p)}
    report={'created_utc':datetime.now(timezone.utc).isoformat(),'seed':42,'threshold':.5,'training_rows':len(tr),'test_rows':len(te),'exact_normalized_duplicates_removed':dupes,'conflicting_text_groups_removed':conflicts,'label_meaning':'Upstream 0/1 labels; positive class may include spam, not exclusively verified phishing.','held_out_mixed':evaluate(te),'training_sources':['CEAS_08.csv'] if baseline else ['CEAS_08.csv','Nazario.csv'],'limitations':['Historical English-heavy corpora; not a production accuracy estimate.','Exact normalized duplicates removed before splitting; near-duplicate templates/campaigns may cross split.','No campaign-grouped or temporal split.','Text model excludes sender, receiver, date and upstream URL flag to reduce metadata leakage.','Source overlap is removed by exact normalized text; remaining near duplicates can inflate results.']}
    seen={hashlib.sha256(t.encode()).hexdigest() for t in texts}
    external_name='Nazario.csv' if baseline else 'Nigerian_5.csv'
    external,ext_dupes,ext_conflicts=deduplicate(load(external_name))
    before=len(external)
    external=[(t,y) for t,y in external if hashlib.sha256(t.encode()).hexdigest() not in seen]
    ext_p=clf.predict_proba(v.transform([t for t,y in external]))[:,1]
    ext_y=[y for t,y in external];ext_pred=(ext_p>=.5).astype(int)
    report['external']={'source':external_name,'rows':len(external),'overlapping_rows_removed':before-len(external),'class_counts':{'0':ext_y.count(0),'1':ext_y.count(1)},'classification_report':classification_report(ext_y,ext_pred,output_dict=True,zero_division=0),'confusion_matrix':confusion_matrix(ext_y,ext_pred,labels=[0,1]).tolist(),'note':'Source-shift benchmark; not a temporal or campaign-independent guarantee. Missing classes do not support accuracy claims.'}
    report['versions']={'python':platform.python_version(),'sklearn':sklearn.__version__,'numpy':numpy.__version__,'scipy':scipy.__version__}
    model={'vocabulary':{k:int(i) for k,i in v.vocabulary_.items()},'idf':v.idf_.tolist(),'coef':clf.coef_[0].tolist(),'intercept':float(clf.intercept_[0])}
    (ROOT/'models').mkdir(exist_ok=True);(ROOT/'reports').mkdir(exist_ok=True)
    (ROOT/'models'/('baseline_text_model.json' if baseline else 'text_model.json')).write_text(json.dumps(model),encoding='utf-8')
    (ROOT/'reports'/('baseline_ceas_only.json' if baseline else 'evaluation.json')).write_text(json.dumps(report,indent=2),encoding='utf-8')
    split={'train':[hashlib.sha256(texts[i].encode()).hexdigest() for i in tr],'test':[hashlib.sha256(texts[i].encode()).hexdigest() for i in te]}
    (ROOT/'data'/('baseline_split_hashes.json' if baseline else 'split_hashes.json')).write_text(json.dumps(split),encoding='utf-8')
    failures=[]
    for i,p in zip(te,clf.predict_proba(v.transform([texts[i] for i in te]))[:,1]):
        if int(p>=.5)!=labels[i]: failures.append({'sha256':hashlib.sha256(texts[i].encode()).hexdigest(),'label':labels[i],'score':float(p),'length':len(texts[i])})
    (ROOT/'reports'/('baseline_errors.json' if baseline else 'held_out_errors.json')).write_text(json.dumps(failures,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))
