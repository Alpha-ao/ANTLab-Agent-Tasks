"""Local B demonstration: real offline computation and persisted request logs."""
import argparse
import copy
import json
import pathlib
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer

ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'进阶/challenge_b'))
from challenge import Engine as Original
from fixed_engine import Engine as Fixed
DATA=json.loads((ROOT/'进阶/challenge_b/data.json').read_text(encoding='utf-8'))
ENGINES={'original':Original(),'fixed':Fixed()}
LOGS=ROOT/'runs/advanced_b/ui'

class Handler(BaseHTTPRequestHandler):
    def send(self,status,value,mime='application/json; charset=utf-8'):
        raw=value if isinstance(value,bytes) else json.dumps(value,ensure_ascii=False).encode()
        self.send_response(status);self.send_header('Content-Type',mime)
        self.send_header('Cache-Control','no-store');self.send_header('Content-Length',str(len(raw)))
        self.end_headers();self.wfile.write(raw)
    def do_GET(self):
        if self.path=='/':return self.send(200,(ROOT/'web/advanced_b.html').read_bytes(),'text/html; charset=utf-8')
        if self.path=='/api/data':return self.send(200,DATA)
        if self.path=='/api/feedback':
            rows=[]
            for p in sorted((ROOT/'runs/advanced_b/live_feedback').glob('*.json')):
                r=json.loads(p.read_text(encoding='utf-8'))
                content=None
                if r.get('status')=='ok':
                    try:content=json.loads(r['response']['choices'][0]['message']['content'])
                    except (KeyError,ValueError):pass
                rows.append({k:r.get(k) for k in ('run_id','case_id','arm','status','elapsed_seconds')}|{'output':content})
            return self.send(200,rows)
        if self.path.startswith('/api/log/'):
            name=self.path.removeprefix('/api/log/')
            if len(name)==36 and all(c in '0123456789abcdef-' for c in name):
                p=LOGS/(name+'.json')
                if p.exists():return self.send(200,p.read_bytes())
        return self.send(404,{'error':'not_found'})
    def do_POST(self):
        if self.path!='/api/run':return self.send(404,{'error':'not_found'})
        try:
            size=int(self.headers.get('Content-Length','0'))
            if not 0<size<=65536:raise ValueError('invalid_size')
            body=json.loads(self.rfile.read(size))
            if not isinstance(body,dict):raise ValueError('body_must_be_object')
            mode=body.get('mode','fixed')
            if mode not in ENGINES:raise ValueError('invalid_mode')
            req=body['request'];draft=body['draft']
            if not isinstance(req,dict) or not isinstance(draft,dict):raise ValueError('invalid_input')
            if mode=='original' and (
                not isinstance(req.get('query'),str)
                or not isinstance(req.get('doc_ids'),list)
                or any(not isinstance(d,str) for d in req['doc_ids'])
                or not isinstance(req.get('snapshot'),str)
                or type(req.get('k')) is not int
                or not isinstance(draft.get('answer'),str)
                or not isinstance(draft.get('citations'),list)
                or any(not isinstance(c,str) for c in draft['citations'])):
                raise ValueError('invalid_input')
            if body.get('reset'):ENGINES[mode].cache.clear()
            out=ENGINES[mode].evaluate(req,copy.deepcopy(DATA['corpus']),draft)
            record={'mode':mode,'reset':bool(body.get('reset')),'request':req,'draft':draft,'corpus':DATA['corpus'],'output':out}
            LOGS.mkdir(parents=True,exist_ok=True)
            (LOGS/(out['request_id']+'.json')).write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
            return self.send(200,out)
        except (ValueError,KeyError,TypeError) as e:return self.send(400,{'error':type(e).__name__+': '+str(e)})

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=8769);a=p.parse_args()
    print('B demo http://127.0.0.1:'+str(a.port),flush=True)
    HTTPServer(('127.0.0.1',a.port),Handler).serve_forever()
