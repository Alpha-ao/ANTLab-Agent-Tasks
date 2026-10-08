"""New labelled experiments only. Shared 10 CNY budget; no automatic retries."""
import argparse
import copy
import datetime
import hashlib
import json
import pathlib
import random
import sys
import uuid

ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'基础/starter'))
import runner
import student
import student_v2
from provider import call_model
from run_basic import validate

def save(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')

def stamp():return datetime.datetime.now(datetime.timezone.utc).isoformat()

def configuration(arm):
    c=runner.load_config(ROOT/'基础/config.local.json')
    if arm in ('thinking','v2_thinking'):
        c['parameters']={'max_tokens':4096,'thinking':{'type':'enabled'},
                         'reasoning_effort':'low','response_format':{'type':'json_object'}}
        c['timeout_seconds']=120
    return c

def request(case,condition,variant,arm,experiment,folder):
    by_id={p['id']:p for p in case['passages']}
    original=[copy.deepcopy(by_id[x]) for x in case['conditions'][condition]]
    chosen=student.improve(case['question'],original) if variant=='improved' else original
    impl=student_v2 if arm.startswith('v2') else student
    msgs=impl.prepare_messages(case['question'],chosen)
    c=configuration(arm)
    ledger_path=ROOT/'results/budget.json'
    ledger=json.loads(ledger_path.read_text(encoding='utf-8'))
    # All previous rounds count. Unknown-cost calls keep their reservation.
    reserve=((len(json.dumps(msgs,ensure_ascii=False).encode())+4096)*2+c['parameters']['max_tokens']*8)/1e6
    spent=sum(x.get('charge_upper_cny',x['reserved_cny']) for x in ledger['entries'])
    if spent+reserve>ledger['limit_cny']:raise RuntimeError('Budget would exceed 10 CNY')
    rid=str(uuid.uuid4())
    entry={'utc':stamp(),'stage':experiment,'run_id':rid,'case_id':case['id'],'condition':condition,
           'variant':variant,'arm':arm,'reserved_cny':reserve,'state':'reserved'}
    ledger['entries'].append(entry);save(ledger_path,ledger)
    r={'schema_version':2,'run_id':rid,'utc':stamp(),'case_id':case['id'],'split':case['split'],
       'condition':condition,'variant':variant,'arm':arm,'experiment':experiment,'mode':'paid','run_kind':'live_api',
       'config':{k:v for k,v in c.items() if k!='endpoint'},'messages':msgs,
       'original_passage_ids':[p['id'] for p in original],'selected_passage_ids':[p['id'] for p in chosen],
       'input_characters':sum(len(m['content']) for m in msgs)}
    path=folder/(rid+'.json')
    save(path,{**r,'status':'pending'})
    try:r.update(call_model(msgs,c))
    except Exception as e:r.update(status='client_exception',error=type(e).__name__,response=None,usage=None)
    save(path,r)
    entry['state']=r['status'];save(ledger_path,ledger)
    try:
        result=validate(r)
        u=r['usage'];cost=(u['prompt_tokens']*2+u['completion_tokens']*8)/1e6
        entry['charge_upper_cny']=cost
        if cost>reserve:raise ValueError('cost exceeded reservation')
        save(ledger_path,ledger)
    except Exception as e:
        entry['validation_error']=str(e);save(ledger_path,ledger)
        raise RuntimeError('Stopped; preserved attempt '+rid+': '+str(e)) from e
    print(case['id'],condition,variant,arm,result['answer'],result['citations'],flush=True)
    return r

def main():
    p=argparse.ArgumentParser();p.add_argument('experiment');p.add_argument('--stage',choices=['dev','evaluation','holdout'],default='dev')
    p.add_argument('--arms',nargs='+',choices=['original','v2','thinking','v2_thinking'],default=['v2_thinking'])
    p.add_argument('--all-conditions',action='store_true');p.add_argument('--paired',action='store_true')
    a=p.parse_args()
    if not a.experiment.replace('_','').replace('-','').isalnum():raise SystemExit('Invalid experiment name')
    folder=ROOT/'runs/exploration'/a.experiment
    if folder.exists():raise SystemExit('Experiment exists; do not overwrite or silently retry')
    cs=runner.cases() if a.stage!='holdout' else json.loads((ROOT/'tests/data/holdout.json').read_text(encoding='utf-8'))
    jobs=[]
    for c in cs:
        if c['split']!=a.stage:continue
        for arm in a.arms:
            for cond in (['R0','R1','R2','K'] if a.all_conditions else ['R0']):jobs.append((c,cond,'baseline',arm))
            if a.paired:jobs.append((c,'R0','improved',arm))
    random.Random(20261009).shuffle(jobs)
    files=['基础/starter/student.py','基础/starter/student_v2.py','基础/starter/provider.py','scripts/explore.py']
    save(ROOT/'configs'/(a.experiment+'.json'),{'utc':stamp(),'stage':a.stage,
         'notice':'exploratory; original evaluation already observed; not blind validation',
         'hashes':{n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in files},
         'jobs':[(c['id'],cond,v,arm) for c,cond,v,arm in jobs],
         'configs':{arm:{k:v for k,v in configuration(arm).items() if k!='endpoint'} for arm in a.arms}})
    for c,cond,v,arm in jobs:request(c,cond,v,arm,a.experiment,folder)

if __name__=='__main__':main()
