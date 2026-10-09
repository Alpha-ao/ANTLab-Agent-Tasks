"""Recompute B output tables and costs without network calls."""
import json
import pathlib
import statistics

ROOT=pathlib.Path(__file__).resolve().parents[1]
def load(p):return json.loads(p.read_text(encoding='utf-8'))
def main():
    pairs=load(ROOT/'runs/advanced_b/verification/paired.json')
    observations={
        ('version','symptom'):'把答案中的30秒误读为响应耗时；原始现象表述有歧义，不能只归因模型。',
        ('version','category'):'区分版本问题并列出多个原因，未获得具体日志，不能确认原因。',
        ('version','evidence'):'结合v2请求、b01和cache_hit提出清缓存对照；E1实际为输入草稿，不能称其为独立执行结果。',
        ('retrieval','symptom'):'已提出先截取再过滤的候选解释；因此有证据组不能被说成首次发现原因。',
        ('retrieval','category'):'提出候选阶段日志与较大k对照，但仍有多个假设。',
        ('retrieval','evidence'):'结合b01/b02与中间选择轨迹，给出k=2检查与筛选顺序修复方向。',
        ('support','symptom'):'建议逐句核对证据；无法凭现象确定引用和语义是否混淆。',
        ('support','category'):'明确区分定位与语义，建议分开检查。',
        ('support','evidence'):'指出原文未测量GPU释放，不能支持保证释放；未测量也不能证明现实中绝不释放。'
    }
    rows=[]
    for p in sorted((ROOT/'runs/advanced_b/live_feedback').glob('*.json')):
        r=load(p);o=json.loads(r['response']['choices'][0]['message']['content'])
        rows.append({k:r[k] for k in ('case_id','arm','run_id','status','elapsed_seconds','usage')}|
                    {'output':o,'review':observations[(r['case_id'],r['arm'])],'review_source':'Codex source-based qualitative review; not independent human gold'})
    ledger=load(ROOT/'results/budget.json');entries=ledger['entries'];b=[e for e in entries if e.get('stage')=='advanced_b_feedback']
    summary={'live_requests':len(rows),'b_cost_upper_cny':sum(e.get('charge_upper_cny',e['reserved_cny']) for e in b),
             'project_cost_upper_cny':sum(e.get('charge_upper_cny',e['reserved_cny']) for e in entries),
             'project_live_requests':len(entries),'diagnosis_reviews':rows,
             'latency_medians_seconds':{arm:statistics.median(r['elapsed_seconds'] for r in rows if r['arm']==arm) for arm in ('symptom','category','evidence')},
             'caveat':'Three paired known faults, nine outputs, unequal input information and length. Version symptom ambiguous. No measured automatic repair success.'}
    out=ROOT/'results/advanced_b';out.mkdir(exist_ok=True)
    (out/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    lines=['# B题逐例结果','', '来源：runs/advanced_b/verification/paired.json；复算：python scripts/summarize_b.py。', '',
           '| 案例 | 原版证据 / 状态 | 修复版证据 / 状态 | 原版请求ID | 修复版请求ID |','|---|---|---|---|---|']
    for x in pairs:
        b,f=x['before'],x['after']
        lines.append('| '+ ' | '.join([x['case_id'],','.join(z['id'] for z in b['evidence'])+' / '+b['support_status'],','.join(z['id'] for z in f['evidence'])+' / '+f['status']+' / '+f['support_status'],b['request_id'],f['request_id']])+' |')
    lines+=['','语义状态全部未核验不等于答案全部正确。修复保持固定draft不变。','','## DeepSeek外部信息诊断（AI定性复核）','']
    for r in rows:lines+=['- '+r['case_id']+' / '+r['arm']+' / '+r['run_id']+'：'+r['review']]
    (out/'paired.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in summary.items() if k not in ('diagnosis_reviews',)},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
