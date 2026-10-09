"""Nine frozen diagnosis requests, serial, no retries. Not autonomous repair."""
import argparse
import datetime
import hashlib
import json
import pathlib
import random
import sys
import uuid

ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'基础/starter'))
from provider import call_model
import runner

def save(p,v):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8')

def prepare():
    baseline=json.loads((ROOT/'runs/advanced_b/baseline.json').read_text(encoding='utf-8'))
    runs=json.loads((ROOT/'runs/advanced_b/verification/raw.json').read_text(encoding='utf-8'))
    trace=next(x['output']['trace'] for x in runs if x['name']=='original/cold_v2_k1')
    cases=[
        dict(id='version',symptom='先查第一版，再查第二版同一问题，网页仍返回30秒。',category='请求与资料版本一致性',
             evidence=[dict(id='E1',text=json.dumps(baseline[0]['input'],ensure_ascii=False)),
                       dict(id='E2',text=json.dumps(baseline[1]['input'],ensure_ascii=False)),
                       dict(id='E3',text=json.dumps(baseline[1]['output'],ensure_ascii=False))]),
        dict(id='retrieval',symptom='当前版本明明存在匹配资料，但k=1时返回空证据。',category='检索范围与截取顺序',
             evidence=[dict(id='E1',text='本次请求alpha/v2，query=timeout request threshold，k=1。使用全新实例，cache_hit=false。'),
                       dict(id='E2',text=json.dumps(trace,ensure_ascii=False)),
                       dict(id='E3',text='b01属于alpha/v1，tags为timeout request threshold 30；b02属于alpha/v2，tags为timeout request threshold 12。最终evidence为空。')]),
        dict(id='support',symptom='页面显示supported，但用户认为答案超出了原文依据。',category='引用定位与语义支持混淆',
             evidence=[dict(id='E1',text=json.dumps(baseline[3]['input'],ensure_ascii=False)),
                       dict(id='E2',text=json.dumps(baseline[3]['output'],ensure_ascii=False))])]
    jobs=[]
    for c in cases:
        for arm in ('symptom','category','evidence'):
            payload={'symptom':c['symptom']}
            if arm!='symptom':payload['human_supplied_category']=c['category']
            if arm=='evidence':payload['external_observations']=c['evidence']
            messages=[{'role':'system','content':'你是文档查证系统的故障诊断助手。只根据所给观察判断，区分已知和假设；没有日志就不要编造日志或断言唯一原因。输出JSON对象，字段恰为diagnosis（字符串）、evidence_ids（字符串数组，只能引用提供的E编号，无则空数组）、proposed_check（一个可以区分原因的具体检查，字符串）、repair_direction（字符串）。不要输出代码。这里是离线合成样机，不能声称已经运行修复或测量GPU。'},
                      {'role':'user','content':json.dumps(payload,ensure_ascii=False)}]
            jobs.append({'case_id':c['id'],'arm':arm,'messages':messages,'allowed_ids':[x['id'] for x in c['evidence']] if arm=='evidence' else []})
    random.Random(20261009).shuffle(jobs)
    plan=json.loads((ROOT/'configs/advanced_b_plan.json').read_text(encoding='utf-8'))
    conf=runner.load_config(ROOT/'基础/config.local.json')
    conf.update(model='deepseek-flash',parameters=plan['model_experiment']['parameters'],timeout_seconds=120)
    freeze={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'jobs':jobs,
            'config':{k:v for k,v in conf.items() if k!='endpoint'},
            'hashes':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [pathlib.Path(__file__),ROOT/'configs/advanced_b_plan.json',ROOT/'基础/starter/provider.py']},
            'notice':'diagnosis only, known hand-selected faults, no automatic code repair; category labels supplied by experiment author'}
    return conf,freeze

def main():
    p=argparse.ArgumentParser();p.add_argument('--run',action='store_true');a=p.parse_args()
    conf,freeze=prepare();path=ROOT/'configs/advanced_b_feedback.json'
    if not a.run:
        if path.exists():raise SystemExit('freeze already exists')
        save(path,freeze);print('Frozen 9 jobs; no calls');return
    saved=json.loads(path.read_text(encoding='utf-8'))
    if any(saved[k]!=freeze[k] for k in ('jobs','config','hashes')):raise SystemExit('freeze mismatch')
    folder=ROOT/'runs/advanced_b/live_feedback'
    if folder.exists():raise SystemExit('attempts exist; no retry')
    folder.mkdir()
    # Prevent another copy of this paid batch; do not run other paid scripts concurrently.
    lock=ROOT/'results/advanced_b/paid.lock'
    lock.parent.mkdir(exist_ok=True)
    with lock.open('x') as f:f.write('serial batch; remove only after terminal state verified')
    try:
        for job in saved['jobs']:
            lp=ROOT/'results/budget.json';ledger=json.loads(lp.read_text(encoding='utf-8'))
            reserve=(2*(len(json.dumps(job['messages'],ensure_ascii=False).encode())+4096)+8*4096)/1e6
            spent=sum(e.get('charge_upper_cny',e['reserved_cny']) for e in ledger['entries'])
            if spent+reserve>min(ledger['limit_cny'],10):raise RuntimeError('budget stop')
            rid=str(uuid.uuid4());entry=dict(run_id=rid,stage='advanced_b_feedback',case_id=job['case_id'],arm=job['arm'],reserved_cny=reserve,state='reserved')
            ledger['entries'].append(entry);save(lp,ledger)
            record={**job,'run_id':rid,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'config':saved['config'],'run_kind':'live_api','attempt':1,'status':'pending'}
            rp=folder/(rid+'.json');save(rp,record)
            try:record.update(call_model(job['messages'],conf))
            except Exception as e:record.update(status='client_exception',error=type(e).__name__)
            save(rp,record);entry['state']=record['status'];save(lp,ledger)
            try:
                if record['status']!='ok':raise ValueError(record['status'])
                choice=record['response']['choices'][0]
                if choice['finish_reason']!='stop':raise ValueError('truncated')
                obj=json.loads(choice['message']['content'])
                if set(obj)!= {'diagnosis','evidence_ids','proposed_check','repair_direction'}:raise ValueError('schema')
                if any(not isinstance(obj[k],str) or not obj[k].strip() for k in ('diagnosis','proposed_check','repair_direction')):raise ValueError('empty text')
                if not isinstance(obj['evidence_ids'],list) or any(x not in job['allowed_ids'] for x in obj['evidence_ids']):raise ValueError('invalid evidence ids')
                u=record['usage']
                if any(type(u.get(k)) is not int or u[k]<0 for k in ('prompt_tokens','completion_tokens')):raise ValueError('unknown usage')
                cost=(u['prompt_tokens']*2+u['completion_tokens']*8)/1e6
                if cost>reserve:raise ValueError('reservation exceeded')
                entry['charge_upper_cny']=cost;save(lp,ledger)
            except Exception as e:
                entry['validation_error']=str(e);save(lp,ledger)
                raise RuntimeError('STOP saved attempt '+rid+': '+str(e)) from e
            print(job['case_id'],job['arm'],rid,flush=True)
    finally:lock.unlink(missing_ok=True)

if __name__=='__main__':main()
