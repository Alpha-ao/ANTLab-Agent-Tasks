"""Offline provisional evaluation; explicit source rules, never used for inference."""
import csv
import json
import pathlib
import statistics
import sys
from decimal import Decimal
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'基础/starter'))
import runner
import student

def save(name,obj):
 p=ROOT/name;p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')

# Transparent, post-run candidate labels with inspectable evidence, not hidden gold.
LABELS={
 'T01':('S24',['P555495','P761989'],'S24完成三项检查；未关闭问题条件存在原文省略，需人工确认'),
 'T02':('76%',['P552476','P169676'],'76/100=76%；部分支持不计完整支持'),
 'T03':('2.6',['P385105','P362285'],'9.4-6.8=2.6秒'),
 'T04':('流程乙',['P758661','P660995'],'错误数甲6、乙2、丙5；<=3只有乙合格'),
 'T05':('证据不足',['P286497','P452207'],'只记录客户端信息，明确未采集功率与能耗'),
 'T06':('25%',['P873502','P721388'],'(8+7)/60=25%'),
 'T07':('方案丙',['P313278','P850395'],'丙86%>=85%且6.8<=7；甲支持率不足、乙超时限'),
 'T08':('K17',['P183430','P223300'],'K17三项检查通过；另两项有失败'),
}

def norm(s):
 return s.strip().replace('％','%').rstrip('。').replace(' ','')

def main():
 records=[json.loads(p.read_text(encoding='utf-8')) for p in (ROOT/'runs/basic/evaluation').glob('*.json')]
 records.sort(key=lambda r:(r['case_id'],r['condition'],r['variant']))
 if len(records)!=40: raise SystemExit('Need exactly 40 main attempts')
 rows=[]
 for r in records:
  expected,needed,reason=LABELS[r['case_id']]
  try: out=json.loads(r['response']['choices'][0]['message']['content'])
  except (KeyError,TypeError,ValueError,IndexError):out={'answer':'','citations':[]}
  answer=norm(out['answer']);ref=out['citations']
  correct=answer.startswith('证据不足') if expected=='证据不足' else answer==expected
  if r['case_id']=='T07':correct=answer in ('方案丙','丙')
  valid=bool(ref) and all(x in r['selected_passage_ids'] for x in ref)
  available=set(needed)<=set(r['selected_passage_ids'])
  # K abstention can be reasonable for the supplied subset even when task is incomplete.
  justified_subset=correct or (answer.startswith('证据不足') and not available)
  support='not_checked'
  if valid and correct and set(needed)<=set(ref):support='supported_candidate'
  elif answer.startswith('证据不足') and not available:support='subset_insufficient_candidate'
  elif available and not correct:support='not_supported_candidate'
  if r['case_id']=='T01':support='ambiguous_requires_human'
  rows.append(dict(run_id=r['run_id'],case_id=r['case_id'],condition=r['condition'],variant=r['variant'],
   attempt='first',api_success=r['status']=='ok',answer=out['answer'],citations=';'.join(ref),
   expected_candidate=expected,task_correct_candidate=correct,input_relative_appropriate_candidate=justified_subset,
   citation_ids_valid=valid,needed_evidence_available=available,support_status_candidate=support,
   extra_citations=';'.join(x for x in ref if x not in needed),reason=reason,
   judgment_source='rule_with_AI_authored_annotation',human_review='pending',
   elapsed_seconds=r['elapsed_seconds'],usage_source='API response.usage',
   raw_path='runs/basic/evaluation/'+r['run_id']+'.json'))
 with (ROOT/'results/results.csv').open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 summary={}
 for name in ['R0','R1','R2','K','improved']:
  group=[r for r in rows if (r['variant']=='improved' if name=='improved' else r['variant']=='baseline' and r['condition']==name)]
  summary[name]={'n':len(group),'task_correct_candidate':sum(r['task_correct_candidate'] for r in group),
   'input_relative_appropriate_candidate':sum(r['input_relative_appropriate_candidate'] for r in group),
   'citation_ids_valid':sum(r['citation_ids_valid'] for r in group),
   'non_abstention':sum(not r['answer'].startswith('证据不足') for r in group),
   'median_elapsed_seconds':statistics.median(r['elapsed_seconds'] for r in group),
   'T01_accept_abstention_sensitivity':sum(r['task_correct_candidate'] or (r['case_id']=='T01' and r['answer'].startswith('证据不足')) for r in group)}
 save('results/summary.json',summary)
 save('results/scoring/candidate_annotations.json',{cid:{'answer':v[0],'evidence_ids':v[1],'reason':v[2],
  'evidence':[p for p in runner.get_case(cid)['passages'] if p['id'] in v[1]],'human_review':'pending'} for cid,v in LABELS.items()})
 pairs=[]
 for cid in LABELS:
  b=next(r for r in rows if r['case_id']==cid and r['condition']=='R0' and r['variant']=='baseline')
  i=next(r for r in rows if r['case_id']==cid and r['variant']=='improved')
  pairs.append({'case_id':cid,'baseline':b,'improved':i,'correct_delta':int(i['task_correct_candidate'])-int(b['task_correct_candidate'])})
 save('results/paired.json',pairs)
 variants=[]
 for c in runner.cases():
  ps=c['passages']; changed=[dict(p,id='RENAMED-'+str(i),source='new/'+str(i)) for i,p in enumerate(reversed(ps))]
  a=student.improve(c['question'],ps);b=student.improve(c['question'],changed)
  variants.append({'case_id':c['id'],'prediction':'same content sequence, all passages retained',
   'input_original':ps,'input_variant':changed,'original_output':[p['id'] for p in a],
   'variant_output':[p['id'] for p in b],'same_content_order':[p['text'] for p in a]==[p['text'] for p in b],
   'preserved':sorted(p['text'] for p in a)==sorted(p['text'] for p in ps),'run_kind':'local_rule'})
 save('results/variants.json',variants)
 t6=[r for r in records if r['case_id']=='T06' and r['condition']=='R0']
 contents=[json.loads(r['messages'][1]['content'])['passages'] for r in t6]
 diagnostic={'prediction_file':'results/diagnostic_plan.md','run_ids':[r['run_id'] for r in t6],
  'same_exact_passage_set':sorted(contents[0],key=lambda p:p['id'])==sorted(contents[1],key=lambda p:p['id']),
  'all_finished':[r['response']['choices'][0]['finish_reason'] for r in t6],
  'independent_arithmetic':str((Decimal(8)+Decimal(7))/Decimal(60)*100)+'%',
  'basis':LABELS['T06'][2],'interpretation':'Saved input loss and output truncation excluded; internal model cause and service variability not resolved.',
  'K_missing_needed':{r['case_id']:not r['needed_evidence_available'] for r in rows if r['condition']=='K'}}
 save('results/diagnostic.json',diagnostic)
 print(json.dumps(summary,ensure_ascii=False,indent=2))
 print('Variants passed',sum(v['same_content_order'] and v['preserved'] for v in variants),'/',len(variants))

if __name__=='__main__': main()
