"""Repair a flawed negative control, without rewriting its original record."""
import copy
import json
from explore import ROOT,request,save,stamp

def main():
    folder=ROOT/'runs/exploration/missing_v2_thinking'
    if folder.exists():raise SystemExit('Already run')
    source=json.loads((ROOT/'tests/data/stress.json').read_text(encoding='utf-8'))
    c=copy.deepcopy(next(x for x in source if x['id']=='M01'));c['id']='M04'
    target=next(p for p in c['passages'] if p['source']=='新构造/补记录')
    target['text']='AZ91复核有56项完全支持；总任务数以及其他类别数量都没有记录，不能从当前资料推算分母。'
    d=copy.deepcopy(c);d['id']='M05'
    d['passages'].append({'id':'OLD-VERSION','source':'归档旧版','text':'石桥项目R11在2026-09批次AZ90有100项，92项完全支持；这是旧版，不能替代R12当前批次。'})
    d['conditions']={'R0':[p['id'] for p in d['passages']]}
    save(ROOT/'tests/data/missing.json',[c,d])
    save(ROOT/'tests/data/missing_labels.json',{x['id']:{'answer':'证据不足','evidence_ids':[target['id']],
         'basis':'Current denominator and all other-category counts explicitly absent; obsolete version is not admissible.'} for x in [c,d]})
    save(ROOT/'configs/missing_v2_thinking.json',{'utc':stamp(),'prediction':'M04 and M05 both abstain; no current denominator can be recovered.',
         'reason':'M01 was not clean: 56+14+10 supplies a possible denominator. Retain as ambiguous instead of calling model wrong.'})
    for x in [c,d]:request(x,'R0','baseline','v2_thinking','missing_v2_thinking',folder)
if __name__=='__main__':main()
