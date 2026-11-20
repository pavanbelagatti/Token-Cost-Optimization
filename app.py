"""ContextCost Lab — richer Streamlit UI, real API measurements + labeled synthetic fixtures."""
import json
import os
from collections import Counter

import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from context import load_data, local_context, raw_context
from smart_retrieval import retrieve, smart_context
from engine import QUESTIONS, run_one

load_dotenv()
st.set_page_config(page_title='AI Context Efficiency Lab | Port.io + OpenAI', page_icon='🧭', layout='wide', initial_sidebar_state='expanded')
st.markdown('''<style>
.block-container {padding-top:1.6rem;max-width:1450px}
[data-testid="stMetric"] {background:#111b2c0a;border:1px solid #7e94ad35;border-radius:14px;padding:14px 17px}
[data-testid="stMetricLabel"] {font-size:.88rem}
h1,h2,h3 {letter-spacing:-.025em}
.hero {padding:24px 28px;border-radius:20px;background:linear-gradient(110deg,#112e43,#174c67 70%,#136e7c);color:#fff;margin-bottom:16px}
.hero h1 {color:#fff;margin:0;font-size:2rem}.hero p {color:#d4e7f1;margin:8px 0 0}
.small-note {font-size:.82rem;color:#74849a}
</style>''',unsafe_allow_html=True)
services, logs, incident = load_data()
logdf = pd.DataFrame(logs)
service_ids = [s['identifier'] for s in services]
health_counts = Counter(s.get('health','unknown') for s in services)
error_logs = [l for l in logs if l.get('severity') == 'ERROR']

st.markdown('<div class="hero"><h1>AI Context Efficiency Lab</h1><p>Powered by Port.io + OpenAI · From scattered engineering data to structured AI-ready context</p></div>',unsafe_allow_html=True)
st.markdown('**Smarter AI Agents Start with Better Context**')
st.write('See how structured organizational context from Port.io helps AI agents retrieve relevant engineering data, reduce unnecessary token consumption, and investigate incidents more efficiently.')
with st.sidebar:
    st.header('Experiment controls')
    question_choice = st.selectbox('Investigation scenario', QUESTIONS)
    question = st.text_area('Question to ask the agent', value=question_choice, height=105)
    st.markdown('**Main comparison: Without Port vs With Port**')
    main_modes = st.multiselect('Main comparison', ['Raw','Port structured'],default=['Raw','Port structured'])
    advanced = st.checkbox('Show advanced retrieval baselines',value=False)
    extra_modes = st.multiselect('Additional controls', ['Smart retrieval','Local structured'],default=['Smart retrieval']) if advanced else []
    modes = main_modes + extra_modes
    model = st.text_input('OpenAI model', value=os.getenv('OPENAI_MODEL','gpt-4o-mini'))
    st.caption('Runs invoke OpenAI and incur actual API charges. Port mode also reads your catalog.')
    run = st.button('▶ Run selected comparison', type='primary', use_container_width=True)
    st.divider()
    st.caption('Port catalog: contextcost_service · 12 demo entities')
    st.caption('Advanced: Smart retrieval searches source documents directly, without Port. Local structured is retained as a reproducibility control.')
    st.caption('No synthetic logs or incident data are live production telemetry.')

if run:
    if not os.getenv('OPENAI_API_KEY'):
        st.error('Add OPENAI_API_KEY to .env before running a benchmark.')
    elif not modes:
        st.warning('Select at least one strategy.')
    else:
        rows=[]
        for mode in modes:
            with st.spinner('Calling OpenAI for '+mode+'...'):
                try:
                    rows.append(run_one(question,mode,model))
                except Exception as exc:
                    st.error('{} failed: {}'.format(mode,exc))
        if rows:
            st.session_state['last_results']=rows

rows = st.session_state.get('last_results',[])
tab1,tab2,tab3,tab4,tab5 = st.tabs(['📊 Executive overview','🧪 Benchmark & answers','🗂️ Service catalog','🔎 Incident evidence','🔄 Context freshness'])

with tab1:
    a,b,c,d = st.columns(4)
    a.metric('Catalog services',len(services))
    b.metric('Degraded services',health_counts.get('degraded',0))
    c.metric('Synthetic error events',len(error_logs))
    d.metric('Dependency links',sum(len(s.get('dependencies',[])) for s in services))
    left,right = st.columns([1.35,1])
    with left:
        st.subheader('Measured token consumption')
        if rows:
            df=pd.DataFrame(rows)
            st.bar_chart(df.set_index('mode')[['input_tokens','output_tokens']],stack=False)
            raw=next((r for r in rows if r['mode']=='Raw'),None)
            port=next((r for r in rows if r['mode']=='Port structured'),None)
            if raw and port and raw['input_tokens']:
                saving=100*(raw['input_tokens']-port['input_tokens'])/raw['input_tokens']
                st.metric('Port vs raw · input token reduction','{:.2f}%'.format(saving))
                st.caption('Single-run observation, not a production savings guarantee.')
        else:
            st.info('Run a benchmark to populate this chart with actual OpenAI token usage.')
    with right:
        st.subheader('Service health · fixture')
        healthdf=pd.DataFrame([{'Status':k,'Services':v} for k,v in health_counts.items()])
        st.bar_chart(healthdf.set_index('Status'))
        st.caption('Health statuses come from fictional service records, not live monitoring.')
    st.subheader('Estimated monthly input token economics')
    qcol,pcol=st.columns(2)
    with qcol: volume=st.slider('Agent investigations per month',1000,100000,10000,1000)
    with pcol: input_price=st.number_input('Input price · USD per million tokens',min_value=0.0,value=float(os.getenv('INPUT_PRICE_PER_M','0.15')),step=0.05,format='%.3f')
    raw=next((r for r in rows if r['mode']=='Raw'),None)
    structured=next((r for r in rows if r['mode']=='Port structured'),None) or next((r for r in rows if r['mode']=='Local structured'),None)
    if raw and structured:
        before=raw['input_tokens']*volume*input_price/1e6
        after=structured['input_tokens']*volume*input_price/1e6
        ca,cb,cc=st.columns(3)
        ca.metric('Raw · monthly input cost','${:,.2f}'.format(before))
        cb.metric('Structured · monthly input cost','${:,.2f}'.format(after))
        cc.metric('Scenario difference','${:,.2f}'.format(before-after))
        st.caption('Projection assumes every future question has the same token usage as this single run. Excludes output tokens, caching, retrieval, infrastructure and Port licensing.')
    else:
        st.info('Run raw and a structured strategy to unlock scenario projections.')

with tab2:
    st.subheader('Without Port vs With Port')
    st.write('Main comparison: raw context vs live Port catalog context. Enable advanced baselines in the sidebar to compare source-document search and a local structured control.')
    if rows and any(r['mode']=='Smart retrieval' for r in rows):
        with st.expander('Inspect smart retrieval source documents'):
            st.dataframe(pd.DataFrame([{'source':d['source'],'kind':d['kind'],'relevance_score':d['score'],'characters':len(d['text'])} for d in retrieve(question)]),hide_index=True,use_container_width=True)
    st.subheader('Model usage & performance')
    if rows:
        columns=['mode','input_tokens','output_tokens','total_tokens','model_cost_usd','retrieval_seconds','latency_seconds','end_to_end_seconds','context_characters']
        st.dataframe(pd.DataFrame([{k:r.get(k) for k in columns} for r in rows]),hide_index=True,use_container_width=True)
        st.caption('Model latency and context preparation/retrieval latency are reported separately. End-to-end includes both, excluding UI rendering. Costs use .env pricing assumptions.')
        for r in rows:
            with st.expander(r['mode']+' · response & evaluation',expanded=True):
                st.markdown(r['answer'])
                checks=r.get('heuristic_grade',{}).get('checks',{})
                st.write('Keyword-based checks:',checks)
                st.caption('Heuristic score is NOT independently verified factual accuracy.')
        st.download_button('⬇ Export benchmark JSON',json.dumps(rows,indent=2),file_name='contextcost_benchmark.json',mime='application/json')
        st.download_button('⬇ Export benchmark CSV',pd.DataFrame(rows).drop(columns=['heuristic_grade'],errors='ignore').to_csv(index=False),file_name='contextcost_benchmark.csv',mime='text/csv')
    else:
        st.info('Choose your strategies in the sidebar and run the benchmark.')
    with st.expander('Methodology & fairness notes'):
        st.markdown('''- **Raw:** supplies all local service, log and incident fixture data.\n- **Smart retrieval (advanced):** uses lexical top-k search over raw service records, log entries and the incident file; does not use Port or prebuilt structured context. This is a simple search baseline, not an enterprise RAG implementation.\n- **Local structured (advanced):** selects relevant local service records and a small log sample.\n- **Port structured:** reads catalog service records from the Port API; logs and incident text still come from local fixtures.\n- **Caution:** local and Port strategies may send identical compact payloads. Port is the governed source of catalog context, not a token compression algorithm.\n- **Retrieval timings:** measured separately from OpenAI call time, including Port API retrieval where selected.\n- **Not measured:** data ingestion costs, total system operating cost, repeated-run confidence intervals or independently verified answer correctness.''')

with tab3:
    st.subheader('Engineering service inventory')
    selected=st.selectbox('Inspect service',service_ids)
    inventory=pd.DataFrame([{'Service':s['identifier'],'Owner':s.get('team','—'),'Health':s.get('health','—'),'Environment':s.get('environment','—'),'Dependencies':', '.join(s.get('dependencies',[])) or 'None','Latest version':s.get('latest_deployment',{}).get('version','—')} for s in services])
    st.dataframe(inventory,hide_index=True,use_container_width=True)
    svc=next(s for s in services if s['identifier']==selected)
    c1,c2,c3=st.columns(3)
    c1.metric('Owner',svc.get('team','Unknown'))
    c2.metric('Service health',svc.get('health','Unknown'))
    c3.metric('Direct dependencies',len(svc.get('dependencies',[])))
    st.markdown('**Latest deployment change**')
    st.write(svc.get('latest_deployment',{}).get('change','Unknown'))
    st.markdown('**Runbook**')
    st.write(svc.get('runbook','Not available'))
    st.markdown('**Service notes**')
    st.write(svc.get('notes','Not available'))
    st.caption('Inventory shown here is the local seeded fixture; benchmark Port mode independently retrieves Port entities.')

with tab4:
    st.subheader('Incident context & diagnostic signals')
    st.markdown(incident)
    st.caption('Fictional incident narrative used in both raw and structured model prompts.')
    service_filter=st.selectbox('Filter log events', ['All services']+service_ids)
    filtered=logdf if service_filter=='All services' else logdf[logdf['service']==service_filter]
    st.markdown('**Log severity distribution · synthetic**')
    if not filtered.empty:
        sev=filtered.groupby('severity').size().rename('Events')
        st.bar_chart(sev)
        st.dataframe(filtered.tail(35).iloc[::-1],hide_index=True,use_container_width=True)
    st.markdown('**Context payload comparison**')
    raw_text=raw_context(question)
    local_text=local_context(question)
    st.write('Raw characters: {:,} · Selected context characters: {:,}'.format(len(raw_text),len(local_text)))
    with st.expander('Inspect selected context sent to the model'):
        st.code(json.dumps(json.loads(local_text),indent=2),language='json')

st.divider()
with st.expander('About this demo and its data sources'):
    st.caption('This reproducible tutorial uses fictional services, incidents and log records. When enabled, Port catalog retrieval and OpenAI token measurements use real APIs. Fixture health and logs are not live production telemetry.')


with tab5:
    st.subheader('Experiment 4 · Context freshness')
    st.write('Change a demo service owner in the live Port catalog, then compare it with the unchanged local JSON snapshot. This tests data freshness, not token savings.')
    st.caption('Safety: this experiment updates a real entity in your Port organization. Use only the isolated contextcost_service demo blueprint. It does not modify your local data files.')
    freshness_service = st.selectbox('Demo service to inspect', service_ids, key='freshness_service')
    fixture = next(s for s in services if s['identifier'] == freshness_service)
    local_owner = fixture.get('team', 'Unknown')
    st.metric('Local snapshot owner', local_owner)
    if st.button('🔎 Read live owner from Port', key='fresh_read'):
        try:
            from port_client import PortClient
            entity = PortClient().get_service_entity(freshness_service)
            st.session_state['fresh_entity'] = entity
            st.session_state['fresh_id'] = freshness_service
        except Exception as exc:
            st.error('Unable to read Port: {}'.format(exc))
    entity = st.session_state.get('fresh_entity') if st.session_state.get('fresh_id') == freshness_service else None
    if entity:
        port_owner = entity.get('properties', {}).get('team', 'Unknown')
        x,y = st.columns(2)
        x.metric('Local snapshot', local_owner)
        y.metric('Live Port owner · last fetched', port_owner)
        if port_owner != local_owner:
            st.success('Freshness difference detected: Port has a different owner from the local snapshot.')
        else:
            st.info('Both sources currently agree. Update the demo owner below, then refresh the Port read.')
        st.caption('Port value is a snapshot of the last successful read. Click Read live owner from Port to refresh.')
    else:
        st.info('Read the Port entity to begin the experiment.')

    st.markdown('#### Optional live catalog change')
    st.write('For a controlled demonstration, change the Port owner only. Your local JSON will intentionally stay unchanged.')
    new_owner = st.text_input('New demo owner', value='payments-platform', key='fresh_new_owner', max_chars=80)
    confirmed = st.checkbox('I understand this will change a real entity in my Port demo blueprint.', key='fresh_confirm')
    if st.button('Update owner in Port', disabled=not confirmed or not new_owner.strip(), key='fresh_update'):
        try:
            from port_client import PortClient
            PortClient().update_demo_owner(freshness_service, new_owner.strip())
            st.session_state.pop('fresh_entity', None)
            st.success('Port owner updated. Click Read live owner from Port to verify the change.')
        except Exception as exc:
            st.error('Port update failed: {}'.format(exc))
    if st.button('Restore Port owner from local snapshot', key='fresh_restore'):
        try:
            from port_client import PortClient
            PortClient().update_demo_owner(freshness_service, local_owner)
            st.session_state.pop('fresh_entity', None)
            st.success('Restore request succeeded. Read the Port owner again to verify.')
        except Exception as exc:
            st.error('Restore failed: {}'.format(exc))
    st.markdown('#### What this proves')
    st.write('A local snapshot can become stale when the organizational catalog changes. Port can supply the newer owner to agents that retrieve it at query time. This is a freshness demonstration; it does not prove that Port automatically synchronizes external source systems.')
    st.caption('After testing, restore the original owner. Any model answers generated before the change are historical results and do not refresh automatically.')
