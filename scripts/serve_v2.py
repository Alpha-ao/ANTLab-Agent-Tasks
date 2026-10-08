"""Local UI with dynamic inputs, persisted evidence, and shared budget guard."""
import argparse
import json
import pathlib
import secrets
import threading
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs
from explore import ROOT, request, save, runner, student_v2, stamp

class Handler(BaseHTTPRequestHandler):
    def reply(self,status,obj):
        raw=json.dumps(obj,ensure_ascii=False).encode()
        self.send_response(status);self.send_header('Content-Type','application/json; charset=utf-8')
        self.send_header('Content-Length',str(len(raw)));self.send_header('Cache-Control','no-store')
        self.end_headers();self.wfile.write(raw)
    def records(self):
        return [json.loads(p.read_text(encoding='utf-8')) for p in (ROOT/'runs').rglob('*.json')]
    def do_GET(self):
        path=urlparse(self.path)
        if path.path=='/':
            raw=(ROOT/'web/index.html').read_text(encoding='utf-8').replace('__TOKEN__',self.server.token).encode()
            self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8')
            self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
        elif path.path=='/api/cases':self.reply(200,runner.cases())
        elif path.path=='/api/status':self.reply(200,{'paid_remaining':self.server.paid_remaining,'arm':self.server.arm})
        elif path.path=='/api/results':
            self.reply(200,[{k:r.get(k) for k in ['run_id','case_id','condition','variant','arm','experiment','utc','status']} for r in self.records()])
        elif path.path=='/api/result':
            rid=parse_qs(path.query).get('id',[''])[0]
            r=next((r for r in self.records() if r['run_id']==rid),None)
            self.reply(200 if r else 404,r or {'error':'记录不存在'})
        else:self.reply(404,{'error':'路径不存在'})
    def do_POST(self):
        if self.path!='/api/run':return self.reply(404,{'error':'路径不存在'})
        if self.headers.get('X-Assessment-Session')!=self.server.token:return self.reply(403,{'error':'会话不匹配'})
        try:
            n=int(self.headers.get('Content-Length','0'))
            if not 0<n<=100000:raise ValueError('输入长度不合法')
            body=json.loads(self.rfile.read(n));q=body.get('question');ps=body.get('passages')
            if not isinstance(q,str) or not q.strip() or len(q)>4000:raise ValueError('问题不能为空或过长')
            if not isinstance(ps,list) or not 1<=len(ps)<=30:raise ValueError('需1至30个证据段落')
            for p in ps:
                if not isinstance(p,dict) or set(p)!={'id','source','text'} or any(not isinstance(v,str) or not v for v in p.values()):
                    raise ValueError('每段需要非空id/source/text字符串')
            if len({p['id'] for p in ps})!=len(ps):raise ValueError('证据ID重复')
            mode=body.get('mode');variant=body.get('variant')
            if mode not in ('dry','paid') or variant not in ('baseline','improved'):raise ValueError('未知模式')
            case={'id':'UI-'+uuid.uuid4().hex[:8],'split':'ui','question':q,'passages':ps,'conditions':{'R0':[p['id'] for p in ps]}}
            if mode=='dry':
                chosen=student_v2.improve(q,ps) if variant=='improved' else ps
                result={'run_id':str(uuid.uuid4()),'utc':stamp(),'case_id':case['id'],'condition':'R0','variant':variant,
                        'mode':'dry','run_kind':'dry_run','status':'dry_run','messages':student_v2.prepare_messages(q,chosen),
                        'selected_passage_ids':[p['id'] for p in chosen],'response':None}
                save(ROOT/'runs/ui-preview'/(result['run_id']+'.json'),result)
            else:
                with self.server.lock:
                    if self.server.paid_remaining<=0:raise ValueError('当前网页付费次数已用完；可继续预览和回放')
                    self.server.paid_remaining-=1
                    result=request(case,'R0',variant,self.server.arm,'ui_v2',ROOT/'runs/ui_v2')
            self.reply(200,result)
        except (ValueError,TypeError,KeyError,RuntimeError) as e:self.reply(400,{'error':str(e)})
        except Exception as e:self.reply(500,{'error':type(e).__name__})
    def log_message(self,*args):pass

def main():
    p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=8768);p.add_argument('--paid-limit',type=int,default=0)
    p.add_argument('--arm',choices=['v2','v2_thinking'],default='v2_thinking')
    a=p.parse_args()
    if not 0<=a.paid_limit<=5:raise SystemExit('paid-limit must be 0..5')
    s=ThreadingHTTPServer(('127.0.0.1',a.port),Handler);s.token=secrets.token_urlsafe(24)
    s.lock=threading.Lock();s.paid_remaining=a.paid_limit;s.arm=a.arm
    print(f'http://127.0.0.1:{a.port} paid-limit={a.paid_limit}',flush=True)
    try:s.serve_forever()
    finally:s.server_close()
if __name__=='__main__':main()
