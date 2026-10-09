"""Factorial interventions: preserve original behavior except named factors."""
import copy
import time
import uuid
from fixed_engine import digest

class Engine:
    def __init__(self, cache_fix=False, scope_fix=False):
        self.cache = {}
        self.cache_fix, self.scope_fix = cache_fix, scope_fix

    def evaluate(self, request, corpus, draft):
        start=time.perf_counter()
        query=request['query'].strip().lower()
        key=digest([request,corpus,draft]) if self.cache_fix else query
        hit=key in self.cache
        if hit:
            result=copy.deepcopy(self.cache[key])
        else:
            terms=set(query.split())
            pool=[b for b in corpus if b['doc_id'] in request['doc_ids'] and b['snapshot']==request['snapshot']] if self.scope_fix else corpus
            ranked=sorted(pool,key=lambda b:(-len(terms & set(b['tags'])),b['id']))
            selected=[b for b in ranked[:request['k']] if terms & set(b['tags'])]
            evidence=[b for b in selected if b['doc_id'] in request['doc_ids'] and b['snapshot']==request['snapshot']]
            valid=bool(draft['citations']) and set(draft['citations']).issubset({b['id'] for b in evidence})
            result=dict(answer=draft['answer'],citations=draft['citations'],evidence=evidence,
                        locator_status='valid' if valid else 'invalid',support_status='supported' if valid else 'not_checked',
                        judgment_source='rule',status='ok',
                        trace={'ranked':[b['id'] for b in ranked],'selected_before_final_scope':[b['id'] for b in selected]})
            self.cache[key]=copy.deepcopy(result)
        result.update(request_id=str(uuid.uuid4()),request=copy.deepcopy(request),cache_hit=hit,
                      elapsed_ms=(time.perf_counter()-start)*1000,run_kind='offline_replay')
        return copy.deepcopy(result)
