import json
from pathlib import Path
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
ROOT=Path(__file__).resolve().parents[1]

def normalize(text):
    import re
    return re.sub(r'\s+',' ',text).strip().lower()

class TextModel:
    """Numeric JSON persistence avoids loading executable pickle/joblib objects."""
    def __init__(self,path=None):
        p=Path(path or ROOT/'models'/'text_model.json')
        d=json.loads(p.read_text(encoding='utf-8'))
        self.vectorizer=TfidfVectorizer(vocabulary=d['vocabulary'],ngram_range=(1,2),sublinear_tf=True)
        self.vectorizer.idf_=np.asarray(d['idf'])
        self.coef=np.asarray(d['coef']);self.intercept=float(d['intercept'])
    def predict(self,text):
        row=self.vectorizer.transform([normalize(text)])
        z=float((row@self.coef)[0]+self.intercept)
        score=float(1/(1+np.exp(-np.clip(z,-700,700))))
        names=self.vectorizer.get_feature_names_out()
        contributions=[{'term':str(names[i]),'contribution':round(float(v*self.coef[i]),5)} for i,v in zip(row.indices,row.data)]
        return {'score':round(score,5),'label':'positive benchmark class' if score>=.5 else 'negative benchmark class','supporting_terms':sorted([x for x in contributions if x['contribution']>0],key=lambda x:-x['contribution'])[:8],'opposing_terms':sorted([x for x in contributions if x['contribution']<0],key=lambda x:x['contribution'])[:8],'note':'Uncalibrated model score; term contributions describe this linear model, not causal evidence.'}
