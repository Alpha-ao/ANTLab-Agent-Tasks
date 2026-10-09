"""Malformed JSON values must return a useful error instead of disconnecting."""
import importlib.util
import json
import pathlib
import threading
import unittest
import urllib.error
import urllib.request

ROOT=pathlib.Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('b_http_under_test',ROOT/'scripts/serve_b.py')
server_module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(server_module)

class HTTPBoundaryTests(unittest.TestCase):
    def test_nonobject_json_returns_400_and_server_remains_available(self):
        server=server_module.HTTPServer(('127.0.0.1',0),server_module.Handler)
        worker=threading.Thread(target=server.serve_forever,daemon=True);worker.start()
        url='http://127.0.0.1:'+str(server.server_port)
        try:
            for payload in ([],None,'text',42):
                with self.subTest(payload=payload):
                    req=urllib.request.Request(url+'/api/run',data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'})
                    with self.assertRaises(urllib.error.HTTPError) as caught:
                        urllib.request.urlopen(req)
                    self.assertEqual(caught.exception.code,400)
                    with caught.exception as response:
                        self.assertIn('body_must_be_object',json.load(response)['error'])
            for request in ({},{'query':42,'doc_ids':['alpha'],'snapshot':'v1','k':1}):
                payload={'mode':'original','request':request,'draft':{'answer':'test','citations':[]}}
                req=urllib.request.Request(url+'/api/run',data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'})
                with self.assertRaises(urllib.error.HTTPError) as caught:
                    urllib.request.urlopen(req)
                self.assertEqual(caught.exception.code,400)
                with caught.exception as response:
                    self.assertIn('invalid_input',json.load(response)['error'])
            with urllib.request.urlopen(url+'/api/data') as response:
                self.assertEqual(len(json.load(response)['cases']),7)
        finally:server.shutdown();server.server_close();worker.join()
