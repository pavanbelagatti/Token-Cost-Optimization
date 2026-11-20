"""Run real OpenAI calls, record provider token usage, and grade factual coverage."""
import os,time
from context import raw_context,local_context,port_context
from port_client import PortClient
from smart_retrieval import smart_context

SYSTEM='You are an engineering incident analyst. Use only supplied context. State the owner, dependencies, recent change, and next checks. If evidence is missing, say unknown. Be concise; do not invent facts.'
QUESTIONS=[
 'Why is checkout failing in production? Who owns it, what does it depend on, and what changed?',
 'Who owns checkout and what should we investigate first?',
 'Which dependencies could explain checkout 502 errors?',
 'What was the latest checkout deployment change and which runbook applies?',
 'Does the available evidence show checkout data loss?',
]

def grade(question,answer):
    # Lightweight transparent checks, NOT a substitute for expert accuracy review.
    a=answer.lower()
    checks={'mentions_checkout':'checkout' in a,'mentions_payments':'payment' in a}
    if 'owns' in question.lower() or 'owner' in question.lower():checks['owner_commerce']='commerce' in a
    if 'change' in question.lower() or 'deployment' in question.lower():checks['timeout_change']='800' in a or 'timeout' in a
    return {'checks':checks,'coverage':sum(checks.values())/len(checks)}

def run_one(question,mode,model=None,client=None):
    overall_start=time.perf_counter()
    if mode=='Raw':context=raw_context(question)
    elif mode=='Local structured':context=local_context(question)
    elif mode=='Port structured':context=port_context(question,client or PortClient())
    elif mode=='Smart retrieval':context=smart_context(question)
    else:raise ValueError('Unknown mode')
    retrieval_elapsed=time.perf_counter()-overall_start
    model=model or os.getenv('OPENAI_MODEL','gpt-4o-mini')
    start=time.perf_counter()
    from openai import OpenAI
    response=OpenAI().chat.completions.create(model=model,temperature=0,messages=[{'role':'system','content':SYSTEM},{'role':'user','content':'QUESTION:\n'+question+'\n\nCONTEXT:\n'+context}])
    elapsed=time.perf_counter()-start
    usage=response.usage
    answer=response.choices[0].message.content or ''
    inp=usage.prompt_tokens;out=usage.completion_tokens
    ip=os.getenv('INPUT_PRICE_PER_M');op=os.getenv('OUTPUT_PRICE_PER_M')
    cost=(inp*float(ip)+out*float(op))/1e6 if ip and op else None
    return {'question':question,'mode':mode,'model':model,'answer':answer,'input_tokens':inp,'output_tokens':out,'total_tokens':usage.total_tokens,'model_cost_usd':cost,'latency_seconds':round(elapsed,3),'retrieval_seconds':round(retrieval_elapsed,3),'end_to_end_seconds':round(elapsed+retrieval_elapsed,3),'context_characters':len(context),'heuristic_grade':grade(question,answer)}