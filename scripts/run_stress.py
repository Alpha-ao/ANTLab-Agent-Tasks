"""Predefined long-context and missing-evidence stress checks; no label in request."""
import copy
import hashlib
import json
import random
from explore import ROOT, request, save, stamp

def main():
    folder=ROOT/'runs/exploration/stress_v2_thinking'
    if folder.exists():raise SystemExit('Stress run already exists')
    cases=json.loads((ROOT/'tests/data/holdout.json').read_text(encoding='utf-8'))
    labels=json.loads((ROOT/'tests/data/holdout_labels.json').read_text(encoding='utf-8'))
    filler=(' 记录还保存文件版本、来源页、操作时间和批次号。复核时必须分开当前版本与旧版本，'
            '不得把模拟组、压力组与正式批次的数字混在一起。请求耗时只代表客户端观测，'
            '不能据此推断服务器型号、功率和能耗。拒答与失败均保留，不删除不利结果。')
    tasks=[];new_labels={}
    for c in cases:
        c=copy.deepcopy(c);old=c['id'];c['id']='L'+old[1:];c['split']='stress'
        for p in c['passages']:p['text']+=filler*4
        tasks.append(c);new_labels[c['id']]=labels[old]
    # Drop a necessary operand/rule; existing irrelevant batches must not substitute.
    for i,old in enumerate(['H01','H03','H08'],1):
        c=copy.deepcopy(next(c for c in cases if c['id']==old));c['id']=f'M{i:02d}';c['split']='stress'
        needed=labels[old]['evidence_ids'];remove=needed[0] if old=='H01' else needed[1]
        c['passages']=[p for p in c['passages'] if p['id']!=remove]
        c['conditions']={'R0':[p['id'] for p in c['passages']]}
        tasks.append(c);new_labels[c['id']]={'answer':'证据不足','evidence_ids':[x for x in needed if x!=remove],
          'basis':'Required denominator, comparison operand, or selection rule deliberately removed; irrelevant batch cannot replace it.',
          'human_review':'pending'}
    random.Random(9708).shuffle(tasks)
    save(ROOT/'tests/data/stress.json',tasks);save(ROOT/'tests/data/stress_labels.json',new_labels)
    save(ROOT/'configs/stress_v2_thinking.json',{'utc':stamp(),'prediction':'All full cases retain answers; M01-03 abstain, not borrow other batches.',
      'run_kind':'exploratory stress, not independent benchmark','jobs':[c['id'] for c in tasks],
      'hashes':{n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in ['基础/starter/student_v2.py','scripts/explore.py','tests/data/stress.json']}})
    for c in tasks:request(c,'R0','baseline','v2_thinking','stress_v2_thinking',folder)

if __name__=='__main__':main()
