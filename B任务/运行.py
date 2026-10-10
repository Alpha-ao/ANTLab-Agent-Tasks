"""从此目录启动B题页面；只进行离线重放。"""
from pathlib import Path
import argparse
import subprocess
import sys

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--check',action='store_true',help='核对已有实验记录，不启动页面')
args=parser.parse_args()
root=Path(__file__).resolve().parents[1]
script='scripts/audit_b.py' if args.check else 'scripts/serve_b.py'
raise SystemExit(subprocess.call([sys.executable,str(root/script)],cwd=root))
