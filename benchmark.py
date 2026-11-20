"""CLI benchmark: python benchmark.py --repeat 2 --port"""
import argparse,csv,json,time
from pathlib import Path
from dotenv import load_dotenv
from engine import QUESTIONS,run_one

def main():
    load_dotenv()
    parser=argparse.ArgumentParser()
    parser.add_argument('--repeat',type=int,default=1)
    parser.add_argument('--port',action='store_true')
    args=parser.parse_args()
    modes=['Raw','Smart retrieval','Local structured']+(['Port structured'] if args.port else [])
    out=Path('results');out.mkdir(exist_ok=True)
    rows=[]
    for question in QUESTIONS:
        for mode in modes:
            for trial in range(args.repeat):
                print(f'Running: {mode} | trial {trial+1} | {question[:35]}')
                r=run_one(question,mode);r['trial']=trial+1;rows.append(r)
    stamp=time.strftime('%Y%m%d-%H%M%S')
    (out/f'benchmark-{stamp}.json').write_text(json.dumps(rows,indent=2))
    fields=['question','mode','trial','model','input_tokens','output_tokens','total_tokens','model_cost_usd','latency_seconds','retrieval_seconds','end_to_end_seconds','context_characters']
    with (out/f'benchmark-{stamp}.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows([{k:r[k] for k in fields} for r in rows])
    print('Saved results to',out)

if __name__=='__main__':main()
