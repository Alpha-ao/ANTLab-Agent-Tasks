"""Append-only causal check of two mechanisms yielding the SAME empty evidence."""
import copy
import datetime
import hashlib
import json
import pathlib
import sys

ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'进阶/challenge_b'))
from challenge import Engine as Original
from diagnostic_engine import Engine as Intervention
from fixed_engine import Engine as Fixed

def save(p,x):
    p.write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf-8')

def main():
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument('--label',default='same_symptom');a=ap.parse_args()
    if not a.label.replace('_','').isalnum():raise SystemExit('invalid label')
    folder=ROOT/'runs/advanced_b'/a.label
    if folder.exists():raise SystemExit('refuse overwrite')
    folder.mkdir(parents=True)
    planpath=ROOT/'configs/advanced_b_same_symptom_plan.json'
    plan=json.loads(planpath.read_text(encoding='utf-8'))
    sources=[planpath,pathlib.Path(__file__),*[ROOT/'进阶/challenge_b'/n for n in ('challenge.py','diagnostic_engine.py','fixed_engine.py','data.json')]]
    save(folder/'before_run.json',{'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'plan':plan,
        'sha256':{p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}})
    data=json.loads((ROOT/'进阶/challenge_b/data.json').read_text(encoding='utf-8'))
    corpus=data['corpus'];warmup=copy.deepcopy(data['cases'][2]);target=copy.deepcopy(data['cases'][1]);target['request']['k']=1
    records=[]
    def call(name,engine,case):
        before=copy.deepcopy(engine.cache)
        output=engine.evaluate(copy.deepcopy(case['request']),copy.deepcopy(corpus),copy.deepcopy(case['draft']))
        records.append({'name':name,'input':copy.deepcopy(case),'corpus':copy.deepcopy(corpus),'cache_before':before,'output':copy.deepcopy(output)})
        save(folder/'raw.json',records)
        return output
    original=Original();primed=call('original_warmup',original,warmup);seed=copy.deepcopy(original.cache)
    save(folder/'starting_cache.json',seed)
    baseline=call('original_target',original,target)
    rows=[];checks=[]
    def check(name,ok):checks.append({'name':name,'passed':bool(ok)})
    check('natural_empty_cache',primed['evidence']==[] and bool(seed))
    check('original_same_symptom',baseline['cache_hit'] and baseline['evidence']==[])
    for name,cf,sf in [('original',False,False),('cache_only',True,False),('scope_only',False,True),('both',True,True)]:
        engine=Intervention(cf,sf);engine.cache=copy.deepcopy(seed)
        out=call(name,engine,target)
        observation={'cache_hit':out['cache_hit'],'evidence_ids':[b['id'] for b in out['evidence']]}
        rows.append({'arm':name,**observation,'run_id':out['request_id']})
        check('prediction/'+name,observation==plan['predictions'][name])
    for name,scope in [('original',False),('scope_only',True)]:
        out=call('cold/'+name,Intervention(False,scope),target)
        check('cold/'+name,[b['id'] for b in out['evidence']]==plan['cold_controls'][name] and not out['cache_hit'])
    k2=copy.deepcopy(target);k2['request']['k']=2
    for name,cf,expected in [('original',False,[]),('cache_only',True,['b02'])]:
        engine=Intervention(cf,False);engine.cache=copy.deepcopy(seed)
        out=call('negative_k2/'+name,engine,k2)
        check('negative_k2/'+name,[b['id'] for b in out['evidence']]==expected)
    fixed=Fixed();call('fixed_warmup',fixed,warmup);out=call('fixed_target',fixed,target)
    check('delivered_fix',out['answer']==target['draft']['answer'] and [b['id'] for b in out['evidence']]==['b02'] and not out['cache_hit'])
    check('identical_main_input_and_state',all(r['input']==target and r['cache_before']==seed and r['corpus']==corpus for r in records if r['name'] in plan['predictions']))
    summary={'checks':checks,'passed':sum(c['passed'] for c in checks),'total':len(checks),'rows':rows,
             'conclusion':'Two mechanisms can yield the same empty evidence. Warm cache hides the remaining scope-order defect; both fixes are required for this starting state.'}
    save(folder/'summary.json',summary)
    print(json.dumps(summary,ensure_ascii=False,indent=2))
    if not all(c['passed'] for c in checks):raise SystemExit('prediction mismatch; preserved, stop')

if __name__=='__main__':main()
