"""Bounded serial experiment. No retries; preserve failures and stop on errors."""
import argparse
import datetime
import hashlib
import json
import pathlib
import random
import sys

ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'基础/starter'))
import runner

def save(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')

def stamp(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def hashes():
    names=['基础/data/cases.json','基础/starter/student.py','基础/starter/runner.py',
           '基础/starter/provider.py','scripts/run_basic.py','基础/config.local.json']
    return {n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in names}

def validate(r):
    if r['status']!='ok': raise ValueError('API failed: '+r['status'])
    choice=r['response']['choices'][0]
    if choice.get('finish_reason')!='stop': raise ValueError('generation not complete')
    obj=json.loads(choice['message']['content'])
    if not isinstance(obj,dict) or set(obj)!={'answer','citations'}: raise ValueError('schema keys')
    if not isinstance(obj['answer'],str) or not obj['answer'].strip(): raise ValueError('empty answer')
    if not isinstance(obj['citations'],list) or any(not isinstance(x,str) for x in obj['citations']):
        raise ValueError('citations schema')
    if any(x not in r['selected_passage_ids'] for x in obj['citations']): raise ValueError('unknown citation')
    u=r['usage']
    if not isinstance(u,dict) or any(not isinstance(u.get(k),int) or u[k]<0 for k in ['prompt_tokens','completion_tokens']):
        raise ValueError('usage unavailable')
    return obj

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('stage',choices=['dev','freeze','evaluation'])
    a=parser.parse_args()
    conf=runner.load_config(ROOT/'基础/config.local.json')
    frozen=ROOT/'configs/frozen.json'
    if a.stage=='freeze':
        if frozen.exists(): raise SystemExit('Already frozen; do not overwrite')
        save(frozen,{'utc':stamp(),'hashes':hashes(),'config':{k:v for k,v in conf.items() if k!='endpoint'},
                     'main_requests':40,'retries':0,'order_seed':20261008})
        print('FROZEN',flush=True); return
    if a.stage=='evaluation':
        if not frozen.exists() or json.loads(frozen.read_text(encoding='utf-8'))['hashes']!=hashes():
            raise SystemExit('Freeze missing or configuration/code changed')
    folder=ROOT/'runs/basic'/a.stage
    if folder.exists() and list(folder.glob('*.json')):
        raise SystemExit('Stage contains attempts; inspect before any separately labelled continuation')
    jobs=[]
    for c in runner.cases():
        if c['split']!=a.stage: continue
        conditions=['R0'] if a.stage=='dev' else ['R0','R1','R2','K']
        jobs.extend((c['id'],cond,'baseline') for cond in conditions)
        jobs.append((c['id'],'R0','improved'))
    random.Random(20261008).shuffle(jobs)
    ledger_path=ROOT/'results/budget.json'
    ledger=json.loads(ledger_path.read_text(encoding='utf-8')) if ledger_path.exists() else {
        'limit_cny':10,'pricing_date':'2026-10-08','price_source':'https://api-docs.deepseek.com/zh-cn/quick_start/pricing/',
        'peak_input_cny_per_million':2,'peak_output_cny_per_million':8,'entries':[]}
    save(ROOT/'results'/f'{a.stage}_schedule.json',{'utc':stamp(),'jobs':jobs,'prediction':'Improved keeps all evidence; grouping may help or have no effect. K may lose cross-record evidence.'})
    for cid,cond,variant in jobs:
        _,_,_,msgs=runner.prepare(cid,cond,variant)
        # Deliberately loose reservation: UTF-8 bytes plus 4096 framing allowance.
        input_bound=len(json.dumps(msgs,ensure_ascii=False).encode('utf-8'))+4096
        reserve=(input_bound*2+conf['parameters']['max_tokens']*8)/1e6
        spent=sum(e.get('charge_upper_cny',e['reserved_cny']) for e in ledger['entries'])
        if spent+reserve>10: raise SystemExit('Budget guard stopped before next request')
        entry={'utc':stamp(),'stage':a.stage,'case_id':cid,'condition':cond,'variant':variant,
               'reserved_cny':reserve,'state':'reserved'}
        ledger['entries'].append(entry);save(ledger_path,ledger)
        r=runner.execute(cid,cond,variant,conf,outdir=folder)
        entry['run_id']=r['run_id'];entry['state']=r['status'];save(ledger_path,ledger)
        try:
            obj=validate(r)
            u=r['usage'];entry['charge_upper_cny']=(u['prompt_tokens']*2+u['completion_tokens']*8)/1e6
            if entry['charge_upper_cny']>reserve: raise ValueError('cost reservation exceeded')
            save(ledger_path,ledger)
        except Exception as e:
            entry['validation_error']=type(e).__name__+': '+str(e);save(ledger_path,ledger)
            raise SystemExit('STOP; raw attempt preserved: '+entry['validation_error'])
        print(cid,cond,variant,obj['answer'],obj['citations'],r['run_id'],flush=True)
    print('Stage complete; peak-price upper estimate CNY',round(sum(e.get('charge_upper_cny',e['reserved_cny']) for e in ledger['entries']),6),flush=True)

if __name__=='__main__': main()
