"""Refresh categorized result copies without changing original run records."""
import hashlib
import argparse
import json
from pathlib import Path
import shutil

ROOT=Path(__file__).resolve().parents[1]

def digest(path):
    data=path.read_bytes()
    if path.suffix in {'.md','.json','.csv'}:
        data=data.replace(b'\r\n',b'\n')
    return hashlib.sha256(data).hexdigest()

GROUPS={
    '基础任务':{
        'report-basic-v1.md':'报告/首轮记录.md',
        'report-v2.md':'报告/改进记录.md',
        'research.md':'资料/阅读记录.md',
        'results/results.csv':'结果/首轮逐题结果.csv',
        'results/exploration.csv':'结果/改进逐题结果.csv',
        'results/summary.json':'结果/首轮汇总.json',
        'results/exploration_summary.json':'结果/改进汇总.json',
        'results/completion_audit.json':'结果/检查记录.json',
        'results/ui-verified.jpg':'结果/页面截图.jpg',
    },
    'B任务':{
        'results/advanced_b/review-followup.md':'报告/修正记录.md',
        'results/advanced_b/paired.md':'结果/逐例说明.md',
        'results/advanced_b/summary.json':'结果/模型诊断记录.json',
        'runs/advanced_b/same_symptom/summary.json':'结果/同症状对照.json',
        'results/advanced_b/retest-20261009.json':'结果/最近复测.json',
        'results/advanced_b/linux-review.json':'结果/Linux检查.json',
        'results/advanced_b/completion_audit.json':'结果/检查记录.json',
        'results/advanced_b/ui-retest-20261009.png':'结果/页面截图.png',
        'results/advanced_b/ui-retest-20261009.json':'结果/页面复测记录.json',
    }
}

def main():
    parser=argparse.ArgumentParser(description='更新分类副本，或检查副本是否与原文件一致。')
    parser.add_argument('--check',action='store_true',help='只检查，不修改文件')
    args=parser.parse_args()
    for group,mapping in GROUPS.items():
        entries=[]
        for src,dst in mapping.items():
            source=ROOT/src;destination=ROOT/group/dst
            if not args.check:
                destination.parent.mkdir(parents=True,exist_ok=True)
                shutil.copyfile(source,destination)
            sha=digest(source)
            if not destination.is_file() or digest(destination)!=sha:
                raise SystemExit('副本缺失或内容不同：'+str(destination))
            entries.append({'source':src,'copy':dst,'sha256':sha,
                            'hash_mode':'CRLF to LF' if source.suffix in {'.md','.json','.csv'} else 'raw bytes'})
        manifest=ROOT/group/'文件来源.json'
        if args.check:
            if json.loads(manifest.read_text(encoding='utf-8'))!=entries:
                raise SystemExit('来源记录与当前文件不一致：'+str(manifest))
        else:
            manifest.write_text(json.dumps(entries,ensure_ascii=False,indent=2),encoding='utf-8')
        print(group+': '+str(len(entries))+' files checked')

if __name__=='__main__':main()
