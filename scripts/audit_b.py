"""Check actual B deliverables and immutable evidence; no network or paid calls."""
import hashlib
import json
import pathlib
import re
from b_artifacts import matches_hash, text_hash

ROOT=pathlib.Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def main():
    checks={}
    originals=['challenge.py','run_cases.py','server.py','index.html','data.json','spec.md']
    checkout=read(ROOT/'configs/advanced_b_checkout_manifest.json')['files']
    checks['originals_preserved']=all(text_hash((ROOT/'versions/advanced_b'/n).read_bytes())==text_hash((ROOT/'进阶/challenge_b'/n).read_bytes()) for n in originals)
    baseline=read(ROOT/'runs/advanced_b/baseline.json')
    checks['baseline_failure_retained']=len(baseline)==7 and baseline[1]['output']['cache_hit'] and baseline[1]['output']['evidence'][0]['snapshot']=='v1' and baseline[1]['input']['request']['snapshot']=='v2'
    runroot=ROOT/'runs/advanced_b/verification'
    manifest=read(runroot/'manifest.json')
    checks['verified_implementation_unchanged']=all(matches_hash(ROOT,n,v,checkout) for n,v in manifest['hashes'].items())
    cs=read(runroot/'checks.json')
    checks['all_contract_checks_pass']=cs['total']==39 and cs['passed']==39 and all(x['passed'] for x in cs['checks'])
    matrix=read(runroot/'interventions.json');plan=read(ROOT/'configs/advanced_b_plan.json')
    checks['four_interventions_match_predictions']=len(matrix)==4 and all({k:r[k] for k in ('warm_v2_stale','cold_v2_k1_missing')}==plan['predictions'][r['arm']] for r in matrix)
    raw=read(runroot/'raw.json')
    checks['raw_inputs_outputs_saved']=len(raw)==cs['raw_records'] and all(set(('input','corpus','output'))<=set(r) for r in raw)
    freeze=read(ROOT/'configs/advanced_b_feedback.json')
    checks['model_freeze_unchanged']=all(matches_hash(ROOT,n,v,checkout) for n,v in freeze['hashes'].items())
    newroot=ROOT/'runs/advanced_b/same_symptom'
    newplan=read(newroot/'before_run.json');same=read(newroot/'summary.json');samerecords=read(newroot/'raw.json')
    checks['same_symptom_sources_unchanged']=all(matches_hash(ROOT,n,v,checkout) for n,v in newplan['sha256'].items())
    checks['same_symptom_checks_pass']=same['total']==12 and same['passed']==12 and all(x['passed'] for x in same['checks'])
    expected=newplan['plan']['predictions']
    checks['same_symptom_predictions']=len(same['rows'])==4 and all({k:r[k] for k in ('cache_hit','evidence_ids')}==expected[r['arm']] for r in same['rows'])
    seed=read(newroot/'starting_cache.json')
    mainrows=[r for r in samerecords if r['name'] in expected]
    checks['same_symptom_identical_start']=len(mainrows)==4 and all(r['input']==mainrows[0]['input'] and r['cache_before']==seed and r['corpus']==mainrows[0]['corpus'] for r in mainrows)
    calls=[read(p) for p in (ROOT/'runs/advanced_b/live_feedback').glob('*.json')]
    jobs={(j['case_id'],j['arm']):j for j in freeze['jobs']}
    checks['nine_distinct_first_attempts']=len(calls)==9 and len({(r['case_id'],r['arm']) for r in calls})==9 and all(r['attempt']==1 for r in calls)
    checks['paid_inputs_match_freeze']=all(r['messages']==jobs[r['case_id'],r['arm']]['messages'] and r['config']==freeze['config'] for r in calls)
    checks['paid_calls_complete']=all(r['status']=='ok' and r['response']['choices'][0]['finish_reason']=='stop' and r['usage']['prompt_tokens']>0 for r in calls)
    ledger=read(ROOT/'results/budget.json');total=sum(e.get('charge_upper_cny',e['reserved_cny']) for e in ledger['entries'])
    b_entries=[e for e in ledger['entries'] if e.get('stage')=='advanced_b_feedback']
    checks['budget_and_call_ids_match']=total<=10 and len(b_entries)==9 and {e['run_id'] for e in b_entries}=={r['run_id'] for r in calls}
    ui=[read(p) for p in (ROOT/'runs/advanced_b/ui').glob('*.json')]
    checks['ui_original_stale_version']=any(r['mode']=='original' and r['request'].get('snapshot')=='v2' and any(b['snapshot']=='v1' for b in r['output']['evidence']) for r in ui)
    checks['ui_fixed_current_version']=any(r['mode']=='fixed' and r['request'].get('snapshot')=='v2' and r['output']['answer']=='请求超时阈值为12秒。' and r['output']['evidence'] and r['output']['evidence'][0]['id']=='b02' for r in ui)
    checks['ui_dynamic_rejection']=any(r['request'].get('snapshot')=='v999' and r['output']['status']=='invalid_scope' for r in ui)
    uireview=read(ROOT/'results/advanced_b/ui-review-checks.json')['checks']
    checks['ui_error_and_stale_state_checks']=len(uireview)==5 and all(x['passed'] for x in uireview)
    checks['ui_empty_request_logged']=any(r['request']=={} and r['output']['status']=='invalid_input' for r in ui)
    linux=read(ROOT/'results/advanced_b/linux-review.json')
    checks['linux_actual_runs_pass']=len(linux['runs'])==3 and all(r['exit_code']==0 for r in linux['runs'])
    for label,count in [('verification_linux_review',39),('same_symptom_linux_review',12)]:
        name='checks.json' if count==39 else 'summary.json'
        outcome=read(ROOT/'runs/advanced_b'/label/name)
        checks[label]=outcome['passed']==count and outcome['total']==count and all(x['passed'] for x in outcome['checks'])
    checks['ui_screenshot_saved']=(ROOT/'results/advanced_b/ui-result.png').stat().st_size>1000
    checks['required_reports_present']=all((ROOT/n).is_file() for n in ['report.md','report-basic-v1.md','report-v2.md','decisions.md','declaration.md','results/advanced_b/paired.md','results/advanced_b/summary.json'])
    checks['no_credential_patterns']=not any(re.search(r'sk-[A-Za-z0-9]{20,}',p.read_text(encoding='utf-8-sig')) for d in ['runs','results','configs','versions','scripts','web','work'] for p in (ROOT/d).rglob('*') if p.is_file() and p.suffix in ('.json','.md','.py','.html','.csv'))
    result={'scope':'B local implementation, experiment and UI; excludes personal GitHub submission and human review',
            'checks':checks,'project_cost_upper_cny':total,'model_requests':len(calls),
            'limits':['offline replay is not model repair','semantic support remains not_checked','ambiguous version symptom in model comparison','single process only','human review and personal GitHub submission pending']}
    out=ROOT/'results/advanced_b/completion_audit.json';out.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2))
    if not all(checks.values()):raise SystemExit('audit incomplete')

if __name__=='__main__':main()
