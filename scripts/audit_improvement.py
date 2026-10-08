"""Completion checks against actual saved runs, not report text."""
import hashlib
import json
import pathlib
import re
from score_exploration import matches
from analyze_basic import LABELS
ROOT=pathlib.Path(__file__).resolve().parents[1]

def read(p):return json.loads(p.read_text(encoding='utf-8'))
def runs(name):return [read(p) for p in (ROOT/'runs/exploration'/name).glob('*.json')]
def answer(r):return json.loads(r['response']['choices'][0]['message']['content'])

def main():
    checks={}
    f=read(ROOT/'configs/frozen.json')
    checks['first_round_frozen_files_unchanged']=all(hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==h for n,h in f['hashes'].items())
    first=[read(p) for p in (ROOT/'runs/basic/evaluation').glob('*.json')]
    checks['first_round_40_unique_main_attempts']=len(first)==40 and len({(r['case_id'],r['condition'],r['variant']) for r in first})==40
    dev=[r for r in runs('dev_factorial_v2') if r['arm']=='v2_thinking']
    dl={r['id']:r for r in read(ROOT/'基础/data/dev_answers.json')}
    checks['recommended_development_4_of_4']=len(dev)==4 and all(matches(answer(r)['answer'],dl[r['case_id']]['answer']) for r in dev)
    full=[r for r in runs('evaluation_v2_thinking') if r['condition']!='K']
    checks['four_full_context_groups_complete']=len(full)==32 and len({(r['case_id'],r['condition'],r['variant']) for r in full})==32
    checks['full_context_answers_and_evidence']=all(matches(answer(r)['answer'],LABELS[r['case_id']][0]) and set(LABELS[r['case_id']][1])<=set(answer(r)['citations']) for r in full)
    labels=read(ROOT/'tests/data/stress_labels.json');labels.update(read(ROOT/'tests/data/missing_labels.json'))
    stress=runs('stress_v2_thinking')+runs('missing_v2_thinking')
    valid=[r for r in stress if r['case_id']!='M01']
    checks['stress_16_clear_cases_pass']=len(valid)==16 and all(matches(answer(r)['answer'],labels[r['case_id']]['answer']) and set(labels[r['case_id']]['evidence_ids'])<=set(answer(r)['citations']) for r in valid)
    checks['ambiguous_negative_control_retained']=len(stress)==17 and any(r['case_id']=='M01' and answer(r)['answer']=='70%' for r in stress) and labels['M01']['answer']=='证据不足'
    cs={c['id']:c for c in read(ROOT/'基础/data/cases.json')}
    checks['actual_inputs_match_original_passages']=all(
        sorted(json.loads(r['messages'][1]['content'])['passages'],key=lambda p:p['id'])==sorted(cs[r['case_id']]['passages'],key=lambda p:p['id']) for r in full)
    ui=[read(p) for p in (ROOT/'runs/ui_v2').glob('*.json')]
    checks['one_real_ui_request_record']=len(ui)==1 and ui[0]['status']=='ok' and answer(ui[0])=={'answer':'80%','citations':['P312446','P898100']}
    budget=read(ROOT/'results/budget.json');entries=budget['entries'];cost=sum(e.get('charge_upper_cny',e['reserved_cny']) for e in entries)
    checks['all_calls_under_budget']=len(entries)==186 and cost<=10 and all(e['state']=='ok' for e in entries)
    checks['no_credential_patterns_in_deliverables']=not any(re.search(r'sk-[A-Za-z0-9]{20,}',p.read_text(encoding='utf-8-sig')) for d in ['runs','results','configs','versions'] for p in (ROOT/d).rglob('*') if p.is_file() and p.suffix in ['.json','.csv','.md','.py'])
    out={'checks':checks,'cny_peak_upper':cost,'live_requests':len(entries),
         'scope':'basic implementation improvement; provisional rule labels, not independent human review',
         'known_limitations':['K retrieval errors remain','M01 negative control ambiguous','T01 source ambiguity','No unseen independent human benchmark']}
    (ROOT/'results/completion_audit.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(out,ensure_ascii=False,indent=2))
    if not all(checks.values()):raise SystemExit('Audit incomplete')

if __name__=='__main__':main()
