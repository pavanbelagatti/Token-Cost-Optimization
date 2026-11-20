"""Three ways to package the same underlying engineering facts."""
import json
from pathlib import Path
ROOT = Path(__file__).parent

def load_data():
    services = json.loads((ROOT / 'data/services.json').read_text())
    logs = json.loads((ROOT / 'data/logs.json').read_text())
    incident = (ROOT / 'data/incident.md').read_text()
    return services, logs, incident

def raw_context(question):
    services, logs, incident = load_data()
    return json.dumps({'services':services,'logs':logs,'incident':incident},indent=2)

def relevant_services(question, services):
    q=question.lower()
    names=[s['identifier'] for s in services]
    matched=[n for n in names if n in q]
    if not matched:
        matched=['checkout'] # default incident under study; explicit demo fallback
    selected=set(matched)
    for s in services:
        if s['identifier'] in matched:
            selected.update(s.get('dependencies',[]))
    return [s for s in services if s['identifier'] in selected]

def compact_record(s):
    return {k:s[k] for k in ('identifier','team','dependencies','latest_deployment','health','runbook','notes') if k in s}

def local_context(question):
    services, logs, incident=load_data()
    chosen=relevant_services(question,services)
    ids={s['identifier'] for s in chosen}
    # Keep a small recent sample of matching service errors; no facts invented.
    errors=[l for l in logs if l['service'] in ids and l['severity']=='ERROR'][-6:]
    return json.dumps({'services':[compact_record(s) for s in chosen], 'recent_errors':errors,'incident':incident},separators=(',',':'))

def port_context(question, client):
    services=client.list_services()
    chosen=relevant_services(question,services)
    # Port stores catalog facts; incident/log evidence stays in the source system.
    _,logs,incident=load_data()
    ids={s['identifier'] for s in chosen}
    errors=[l for l in logs if l['service'] in ids and l['severity']=='ERROR'][-6:]
    return json.dumps({'services':[compact_record(s) for s in chosen], 'recent_errors':errors,'incident':incident},separators=(',',':'))
