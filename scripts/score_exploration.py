"""Recompute all exploratory results with disclosed, source-based labels."""
import collections
import csv
import json
import pathlib
import re
import statistics
from decimal import Decimal, InvalidOperation
from analyze_basic import LABELS
ROOT=pathlib.Path(__file__).resolve().parents[1]

def matches(actual,expected):
    a=actual.strip().replace('％','%').rstrip('。')
    if expected=='证据不足':return a.startswith(expected)
    if expected=='方案丙':return a in ('丙','方案丙')
    if expected in ('甲','乙','丙'):return a in (expected,'方案'+expected,'配置'+expected,expected+'方案')
    if a==expected:return True
    # Only numeric values with an optional explicit seconds suffix; never substrings.
    if re.fullmatch(r'-?\d+(?:\.\d+)?',expected) and re.fullmatch(r'-?\d+(?:\.\d+)?(?:秒)?',a):
        return Decimal(a.removesuffix('秒'))==Decimal(expected)
    return False

def main():
    labels={cid:{'answer':v[0],'evidence_ids':v[1]} for cid,v in LABELS.items()}
    for d in json.loads((ROOT/'基础/data/dev_answers.json').read_text(encoding='utf-8')):labels[d['id']]=d
    labels['D02']['evidence_ids']=['P406170','P562395']
    labels.update(json.loads((ROOT/'tests/data/holdout_labels.json').read_text(encoding='utf-8')))
    if (ROOT/'tests/data/stress_labels.json').exists():
        labels.update(json.loads((ROOT/'tests/data/stress_labels.json').read_text(encoding='utf-8')))
    if (ROOT/'tests/data/missing_labels.json').exists():
        labels.update(json.loads((ROOT/'tests/data/missing_labels.json').read_text(encoding='utf-8')))
    rows=[]
    for p in sorted((ROOT/'runs/exploration').glob('*/*.json')):
        r=json.loads(p.read_text(encoding='utf-8'));lab=labels[r['case_id']]
        a={'answer':'','citations':[]}
        try:a=json.loads(r['response']['choices'][0]['message']['content'])
        except (KeyError,TypeError,ValueError):pass
        correct=matches(a['answer'],lab['answer'])
        cited=set(a['citations']);necessary=set(lab['evidence_ids'])
        valid=bool(cited) and cited<=set(r['selected_passage_ids'])
        rows.append({'experiment':r['experiment'],'case_id':r['case_id'],'condition':r['condition'],'variant':r['variant'],
          'arm':r['arm'],'run_id':r['run_id'],'answer':a['answer'],'expected_candidate':lab['answer'],
          'correct_candidate':correct,'citation_valid':valid,'necessary_citations_covered':necessary<=cited,
          'answer_and_evidence_candidate':correct and valid and necessary<=cited,
          'extra_citations':';'.join(cited-necessary),'human_review':'pending',
          'test_validity':'ambiguous_negative_control' if r['case_id']=='M01' else 'candidate_valid',
          'elapsed_seconds':r.get('elapsed_seconds'),
          'completion_tokens':(r.get('usage') or {}).get('completion_tokens'),
          'raw_path':str(p.relative_to(ROOT)).replace('\\','/')})
    with (ROOT/'results/exploration.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    groups=collections.defaultdict(list)
    for r in rows:groups[(r['experiment'],r['arm'],r['condition'],r['variant'])].append(r)
    summary=[]
    for key,rs in sorted(groups.items()):
        summary.append(dict(zip(['experiment','arm','condition','variant'],key),n=len(rs),
            correct_candidate=sum(r['correct_candidate'] for r in rs),
            valid_test_n=sum(r['test_validity']=='candidate_valid' for r in rs),
            valid_test_correct=sum(r['correct_candidate'] and r['test_validity']=='candidate_valid' for r in rs),
            answer_and_evidence_candidate=sum(r['answer_and_evidence_candidate'] for r in rs),
            citation_valid=sum(r['citation_valid'] for r in rs),
            median_elapsed_seconds=statistics.median(r['elapsed_seconds'] for r in rs if r['elapsed_seconds'] is not None),
            total_completion_tokens=sum(r['completion_tokens'] or 0 for r in rs)))
    (ROOT/'results/exploration_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    for s in summary:print(s['experiment'],s['arm'],s['condition'],s['variant'],str(s['correct_candidate'])+'/'+str(s['n']),
                           'answer+evidence',s['answer_and_evidence_candidate'],'median sec',round(s['median_elapsed_seconds'],3))

if __name__=='__main__':main()
