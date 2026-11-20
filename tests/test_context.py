import json
from context import load_data,raw_context,local_context,relevant_services
from engine import grade

def test_data():
    services,logs,incident=load_data()
    assert len(services)==12 and len(logs)>100 and 'INC-1042' in incident

def test_relevant_dependencies():
    services,_,_=load_data()
    names={s['identifier'] for s in relevant_services('checkout is failing',services)}
    assert {'checkout','payments','inventory','pricing'}<=names

def test_compaction():
    q='Why is checkout failing?'
    assert len(local_context(q))<len(raw_context(q))
    assert '800ms' in local_context(q)

def test_grade():
    assert grade('Who owns checkout?','Checkout belongs to commerce and depends on payments')['coverage']==1
