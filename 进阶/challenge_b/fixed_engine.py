"""Version-safe offline replay. Draft content remains untrusted and unchanged."""
import copy
import hashlib
import json
import time
import uuid

VERSION = 'b-fixed-1'

def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                    separators=(',', ':')).encode()).hexdigest()

class Engine:
    def __init__(self, use_cache=True):
        self.cache = {}
        self.use_cache = use_cache

    def evaluate(self, request, corpus, draft):
        start = time.perf_counter()
        rid = str(uuid.uuid4())
        trace = []
        result = dict(request_id=rid, request=copy.deepcopy(request), cache_hit=False,
                      run_kind='offline_replay', answer=None, citations=[], evidence=[],
                      locator_status='absent', support_status='not_checked',
                      judgment_source='unverified', locator_judgment_source='rule',
                      support_reason='未实现独立语义核验；引用有效不等于支持答案。',
                      actual_scope=[], origin_request_id=rid, trace=trace,
                      engine_version=VERSION)
        def finish(status):
            result['status'] = status
            result['elapsed_ms'] = (time.perf_counter()-start)*1000
            return copy.deepcopy(result)

        if not isinstance(request, dict) or not isinstance(corpus, list) or not isinstance(draft, dict):
            return finish('invalid_input')
        q, docs, snap, k = (request.get(x) for x in ('query','doc_ids','snapshot','k'))
        if (not isinstance(q,str) or not q.strip() or not isinstance(docs,list) or not docs
            or any(not isinstance(d,str) or not d for d in docs)
            or not isinstance(snap,str) or not snap or type(k) is not int or not 1 <= k <= 100
            or not isinstance(draft.get('answer'),str) or not isinstance(draft.get('citations'),list)
            or any(not isinstance(c,str) for c in draft['citations'])):
            return finish('invalid_input')
        required = ('id','doc_id','snapshot','text','tags','page')
        if any(not isinstance(b,dict) or any(x not in b for x in required)
               or any(not isinstance(b[x],str) for x in ('id','doc_id','snapshot','text'))
               or not isinstance(b['tags'],list) or any(not isinstance(t,str) for t in b['tags'])
               or type(b['page']) is not int or b['page']<1 for b in corpus):
            return finish('invalid_corpus')
        if len({b['id'] for b in corpus}) != len(corpus):
            return finish('invalid_corpus')
        available = {(b['doc_id'],b['snapshot']) for b in corpus}
        missing = sorted(d for d in set(docs) if (d,snap) not in available)
        trace.append({'stage':'scope_validation','missing_documents':missing})
        if missing:
            return finish('invalid_scope')
        scoped = [b for b in corpus if b['doc_id'] in docs and b['snapshot']==snap]
        norm = copy.deepcopy(request)
        norm['doc_ids'] = sorted(set(docs))
        key = digest({'request':norm,'corpus':sorted(corpus,key=lambda b:b['id']),
                      'draft':draft,'version':VERSION})
        trace.append({'stage':'cache_lookup','key':key,'enabled':self.use_cache})
        if self.use_cache and key in self.cache:
            cached = copy.deepcopy(self.cache[key])
            cached.update(request_id=rid, request=copy.deepcopy(request), cache_hit=True,
                          elapsed_ms=(time.perf_counter()-start)*1000,
                          trace=trace+[{'stage':'reuse','origin_request_id':cached['origin_request_id']}])
            return cached
        terms = set(q.strip().lower().split())
        ranked = sorted(scoped,key=lambda b:(-len(terms & set(b['tags'])),b['id']))
        scored = [{'id':b['id'],'score':len(terms & set(b['tags']))} for b in ranked]
        evidence = [copy.deepcopy(b) for b in ranked if terms & set(b['tags'])][:k]
        trace.append({'stage':'scoped_ranking','candidates':scored,'selected':[b['id'] for b in evidence]})
        for b in evidence:
            b['block_id'] = b['id']
            b['locator'] = {'page':b['page'],'bbox':None,'reason':'合成文本没有PDF区域坐标'}
        cites = copy.deepcopy(draft['citations'])
        outside = sorted(set(cites)-{b['id'] for b in evidence})
        locator = 'absent' if not cites else 'invalid' if outside else 'valid'
        trace.append({'stage':'citation_check','outside':outside,'locator_status':locator})
        result.update(answer=draft['answer'], citations=cites, evidence=evidence,
                      locator_status=locator, actual_scope=[{'doc_id':d,'snapshot':s} for d,s in
                          sorted({(b['doc_id'],b['snapshot']) for b in evidence})], cache_key=key)
        output = finish('ok')
        if self.use_cache:
            self.cache[key] = copy.deepcopy(output)
        return output
