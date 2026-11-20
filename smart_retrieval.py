"""Source-document search baseline, independent of Port and local_context().

Builds a lightweight lexical retrieval index over raw fixture documents.
This is a reproducible search baseline, not a production vector database.
"""
import json
import math
import re
from collections import Counter
from context import load_data

STOP = {'the','and','for','what','who','why','how','does','are','was','with','from','this','that','which','should','could','into','about','have','latest','production','service','services','incident','first'}
def terms(s):
    return [x for x in re.findall(r'[a-z0-9]+',s.lower()) if len(x)>2 and x not in STOP]

def documents():
    services,logs,incident=load_data()
    docs=[{'source':'incident.md','kind':'incident','text':incident}]
    for s in services:
        docs.append({'source':'services.json:'+s['identifier'],'kind':'service','text':json.dumps(s,ensure_ascii=False)})
    # Index individual log events so relevant records can be retrieved, rather than dumping the whole log file.
    for i,log in enumerate(logs):
        docs.append({'source':'logs.json:'+str(i),'kind':'log','text':json.dumps(log,ensure_ascii=False)})
    return docs

def retrieve(question,k=10):
    docs=documents()
    query=Counter(terms(question))
    corpus=[Counter(terms(d['text'])) for d in docs]
    df=Counter(t for c in corpus for t in c)
    N=len(docs)
    scored=[]
    for doc,c in zip(docs,corpus):
        score=sum((1+math.log(1+c[t])) * math.log(1+(N-df[t]+0.5)/(df[t]+0.5)) * n for t,n in query.items() if c[t])
        # Incidents are operationally relevant for incident questions, but still subject to scoring.
        if score>0: scored.append((score,doc))
    scored.sort(key=lambda x:(-x[0],x[1]['source']))
    return [{'source':d['source'],'kind':d['kind'],'score':round(score,3),'text':d['text']} for score,d in scored[:k]]

def smart_context(question,k=10):
    return json.dumps({'retrieval':'lexical top-k over raw service records, logs and incident file','documents':retrieve(question,k)},separators=(',',':'))
