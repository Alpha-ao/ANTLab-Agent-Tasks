"""Offline evidence, causal interventions and independent contract checks."""
import copy
import datetime
import hashlib
import json
import pathlib
import sys

ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'进阶/challenge_b'))
from challenge import Engine as Original
from fixed_engine import Engine as Fixed
from diagnostic_engine import Engine as Intervention

def save(p,x):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf-8')

def main():
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--label',default='verification');a=p.parse_args()
    if not a.label.replace('_','').replace('-','').isalnum():raise SystemExit('invalid label')
    folder=ROOT/'runs/advanced_b'/a.label
    if folder.exists():raise SystemExit('Refuse overwrite; choose new explicit label')
    data=json.loads((ROOT/'进阶/challenge_b/data.json').read_text(encoding='utf-8'))
    corpus=data['corpus'];cases=data['cases'];records=[];checks=[]
    def call(name,engine,c,material=corpus):
        out=engine.evaluate(copy.deepcopy(c['request']),copy.deepcopy(material),copy.deepcopy(c['draft']))
        records.append(dict(name=name,input=copy.deepcopy(c),corpus=copy.deepcopy(material),output=copy.deepcopy(out)))
        return out
    def check(name,ok,reason):checks.append(dict(name=name,passed=bool(ok),expected_basis=reason))
    ids=lambda r:[b['id'] for b in r['evidence']]
    projections=lambda r:{k:r[k] for k in ('answer','citations','evidence','locator_status','support_status','status')}
    matrix=[]
    plan=json.loads((ROOT/'configs/advanced_b_plan.json').read_text(encoding='utf-8'))
    for name,cf,sf in [('original',False,False),('cache_only',True,False),('scope_only',False,True),('both',True,True)]:
        e=Intervention(cf,sf)
        call(name+'/warmup',e,cases[0]);warm=call(name+'/warm_v2',e,cases[1])
        c=copy.deepcopy(cases[1]);c['request']['k']=1
        cold=call(name+'/cold_v2_k1',Intervention(cf,sf),c)
        row=dict(arm=name,warm_v2_stale=warm['answer']==cases[0]['draft']['answer'],cold_v2_k1_missing='b02' not in ids(cold))
        matrix.append(row)
        check('prediction/'+name,{k:row[k] for k in ('warm_v2_stale','cold_v2_k1_missing')}==plan['predictions'][name], '事前四条件预测')
    original=Original();fixed=Fixed();paired=[]
    for c in cases:
        if c['reset_before']:original=Original();fixed=Fixed()
        before=call(c['id']+'/original',original,c);after=call(c['id']+'/fixed',fixed,c)
        paired.append({'case_id':c['id'],'before':before,'after':after})
    check('R02/version',ids(paired[1]['after'])==['b02'] and paired[1]['after']['answer']==cases[1]['draft']['answer'],'v2原文为12秒，引用b02')
    check('R03/scope_before_topk',ids(paired[2]['after'])==['b03'],'beta/v1唯一正分证据b03')
    check('R04/no_false_verification',paired[3]['after']['support_status']=='not_checked' and paired[3]['after']['locator_status']=='valid','未测量GPU释放，不能凭ID判supported')
    check('R07/invalid_scope',paired[6]['after']['status']=='invalid_scope' and paired[6]['after']['answer'] is None,'不存在文档不得返回合成draft作为正常答案')
    for i in (4,5):
        b,f=paired[i]['before'],paired[i]['after']
        check('normal/'+cases[i]['id'],b['answer']==f['answer'] and ids(b)==ids(f) and f['locator_status']=='valid','保持正常答案与引用；语义状态如实降为未核验')
    # Trace-only instrumented original must preserve baseline behavior across all fixtures.
    o=Original();d=Intervention()
    for c in cases:
        if c['reset_before']:o=Original();d=Intervention()
        check('instrumentation/'+c['id'],projections(o.evaluate(c['request'],corpus,c['draft']))==projections(d.evaluate(c['request'],corpus,c['draft'])),'插桩不改变原样机语义输出')
    # Cache equivalence against no-cache execution across history changes.
    cached=Fixed();uncached=Fixed(False)
    sequence=[]
    for c in cases[:3]+[cases[1],cases[1]]:sequence.append((copy.deepcopy(c),copy.deepcopy(corpus)))
    c=copy.deepcopy(cases[1]);c['request']['k']=1;sequence.append((c,copy.deepcopy(corpus)))
    c=copy.deepcopy(cases[1]);c['draft']['answer']='同样输入的新草稿，不假定语义正确';sequence.append((c,copy.deepcopy(corpus)))
    changed=copy.deepcopy(corpus);changed[1]['text']+=' 新增修订记录。';sequence.append((copy.deepcopy(cases[1]),changed))
    for n,(c,material) in enumerate(sequence):
        x=call('cache_sequence/'+str(n),cached,c,material);y=call('no_cache/'+str(n),uncached,c,material)
        check('cache_equivalence/'+str(n),projections(x)==projections(y),'缓存不能改变同输入无缓存计算结果')
    e=Fixed();first=call('repeat/first',e,cases[1]);second=call('repeat/second',e,cases[1])
    check('repeat/hit',second['cache_hit'] and first['request_id']!=second['request_id'] and second['origin_request_id']==first['request_id'],'重复请求可复用内容但请求ID独立')
    second['evidence'][0]['text']='调用方篡改';third=call('mutation_protection',e,cases[1])
    check('mutation_protection',third['evidence'][0]['text']==corpus[1]['text'],'返回对象修改不能污染缓存')
    # Two semantically equivalent variants, with explicit mappings and expectations.
    base=call('variant/base',Fixed(),cases[1]);rev=call('variant/reversed',Fixed(),cases[1],list(reversed(corpus)))
    check('variant/order',projections(base)==projections(rev),'输入语料逆序不改变规定排序')
    mapping={b['id']:'renamed_'+b['id'] for b in corpus};docmap={'alpha':'doc_x','beta':'doc_y'}
    material=copy.deepcopy(corpus);c=copy.deepcopy(cases[1])
    for b in material:b.update(id=mapping[b['id']],doc_id=docmap[b['doc_id']])
    c['request']['doc_ids']=[docmap[x] for x in c['request']['doc_ids']];c['draft']['citations']=[mapping[x] for x in c['draft']['citations']]
    mapped=call('variant/id_mapping',Fixed(),c,material)
    check('variant/ids',mapped['answer']==base['answer'] and ids(mapped)==[mapping[x] for x in ids(base)] and mapped['locator_status']=='valid','一致重映射保留关系与字典序')
    for label,docs,snap in [('missing_version',['alpha'],'v999'),('partial_scope',['alpha','beta'],'v2')]:
        c=copy.deepcopy(cases[1]);c['request'].update(doc_ids=docs,snapshot=snap)
        out=call('boundary/'+label,Fixed(),c)
        check('boundary/'+label,out['status']=='invalid_scope' and not out['evidence'],'每个指定文档都必须存在该快照')
    c=copy.deepcopy(cases[0]);c['request'].update(doc_ids=['beta','alpha'],k=2)
    out=call('multi_document',Fixed(),c);check('multi_document',ids(out)==['b01','b03'],'多个合法文档均参与范围内排序')
    for label,cites,expect in [('empty',[],'absent'),('outside',['b01'],'invalid')]:
        c=copy.deepcopy(cases[1]);c['draft']['citations']=cites
        out=call('citation/'+label,Fixed(),c);check('citation/'+label,out['locator_status']==expect,'无引用与越界引用分开')
    c=copy.deepcopy(cases[1]);c['request']['query']='no_match'
    out=call('no_match',Fixed(),c);check('no_match',not out['evidence'] and out['locator_status']=='invalid','合法范围内无正分条目不补入不相关资料')
    duplicate=copy.deepcopy(corpus)+[copy.deepcopy(corpus[0])]
    out=call('duplicate_id',Fixed(),cases[1],duplicate);check('duplicate_id',out['status']=='invalid_corpus','引用ID歧义必须拒绝')
    for bad in (0,True,'2'):
        c=copy.deepcopy(cases[1]);c['request']['k']=bad
        check('invalid_k/'+str(bad),call('invalid_k',Fixed(),c)['status']=='invalid_input','k必须是1至100的整数，布尔值不是整数参数')
    manifest={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'hashes':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in
                  list((ROOT/'进阶/challenge_b').glob('*.py'))+[ROOT/'进阶/challenge_b/data.json',ROOT/'configs/advanced_b_plan.json',pathlib.Path(__file__)]}}
    save(folder/'manifest.json',manifest);save(folder/'raw.json',records)
    save(folder/'paired.json',paired);save(folder/'interventions.json',matrix)
    save(folder/'variants.json',{'block_mapping':mapping,'document_mapping':docmap,'order':'reverse corpus','expected':'same answer and corresponding evidence'})
    summary={'checks':checks,'passed':sum(x['passed'] for x in checks),'total':len(checks),'raw_records':len(records),'run_kind':'offline_replay'}
    save(folder/'checks.json',summary)
    print(json.dumps({'passed':summary['passed'],'total':summary['total'],'failed':[x for x in checks if not x['passed']]},ensure_ascii=False))
    if summary['passed']!=summary['total']:raise SystemExit(1)

if __name__=='__main__':main()
