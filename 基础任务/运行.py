"""从此目录启动基础页面；默认不调用付费API。"""
from pathlib import Path
import argparse
import subprocess
import sys

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--check',action='store_true',help='核对已有实验记录，不启动页面')
args=parser.parse_args()
root=Path(__file__).resolve().parents[1]
script='scripts/audit_improvement.py' if args.check else 'scripts/serve_v2.py'
raise SystemExit(subprocess.call([sys.executable,str(root/script)],cwd=root))
