"""Frozen exploratory 2x2 window-coverage / claim-aggregation diagnostic."""
import argparse
import hashlib
import json
from pathlib import Path
import time
import numpy as np
from .external_support import CoverageNLI, load_target, window_ranges
from .entailment import input_pair, unsupported_risk, REVISION

POLICY='e384s320_c120s100_first_all_max_mean_v1'

def aggregate(matrix):
    matrix=np.asarray(matrix,dtype=float)
    if matrix.ndim!=2 or not matrix.size or not np.isfinite(matrix).all():
        raise ValueError('Nonempty finite claim by evidence entailment matrix required')
    if np.any((matrix<0)|(matrix>1)): raise ValueError('Entailment scores must be in [0,1]')
    result={}
    for ev,values in [('first',matrix[:,0]),('all',matrix.max(axis=1))]:
        risk=1-values
        result[f'e_{ev}_c_first']=float(risk[0])
        result[f'e_{ev}_c_all_max']=float(risk.max())
        result[f'e_{ev}_c_all_mean']=float(risk.mean())
    return result

class WindowDiagnostic(CoverageNLI):
    def one(self,evidence,claim):
        t=self.tokenizer;t.no_truncation()
        ei=t.encode(evidence,add_special_tokens=False).ids
        ci=t.encode(claim,add_special_tokens=False).ids
        er=window_ranges(len(ei),384,320);cr=window_ranges(len(ci),120,100)
        audit={'evidence_windows':len(er),'claim_windows':len(cr),'inference_pairs':len(er)*len(cr),
               'reencoding_truncations':0}
        matrix=np.zeros((len(cr),len(er)))
        if not evidence.strip(): return aggregate(matrix),audit
        encodings=[];owners=[]
        for i,(a,b) in enumerate(cr):
            c=t.decode(ci[a:b])
            for j,(s,e) in enumerate(er):
                ev=t.decode(ei[s:e]);t.no_truncation()
                audit['reencoding_truncations']+=int(len(t.encode(ev,c).ids)>512)
                t.enable_truncation(max_length=512,strategy='only_first',direction='right')
                encodings.append(t.encode(ev,c));owners.append((i,j))
        for start in range(0,len(encodings),4):
            batch=encodings[start:start+4];length=max(len(x.ids) for x in batch)
            ids=np.zeros((len(batch),length),dtype=np.int64);mask=np.zeros_like(ids)
            for row,enc in enumerate(batch):
                ids[row,:len(enc.ids)]=enc.ids;mask[row,:len(enc.ids)]=enc.attention_mask
            risk=unsupported_risk(self.session.run(['logits'],{'input_ids':ids,'attention_mask':mask})[0])
            for offset,value in enumerate(1-risk):matrix[owners[start+offset]]=float(value)
        return aggregate(matrix),audit

def run(model_dir,data,output):
    started=time.monotonic()
    model=WindowDiagnostic(model_dir, threads=2)
    model.session.set_providers(['CPUExecutionProvider'])
    records,labels,groups,meta,_=load_target(Path(data)/'ragtruth',Path(data)/'alce_annotations.json')
    pairs=[input_pair(x) for x in records]
    digest=hashlib.sha256(json.dumps(pairs,ensure_ascii=False).encode()).hexdigest()
    output=Path(output)
    state={'model_revision':REVISION,'policy':POLICY,'pair_sha256':digest,'status':'partial','rows':[]}
    if output.exists():
        state=json.loads(output.read_text())
        assert state['model_revision']==REVISION and state['policy']==POLICY and state['pair_sha256']==digest
    for i in range(len(state['rows']),len(pairs)):
        if time.monotonic()-started>1800: break
        risks,audit=model.one(*pairs[i])
        state['rows'].append({'id':meta[i]['id'],'source_id':meta[i]['source_id'],'risks':risks,'audit':audit})
        if (i+1)%25==0:
            output.write_text(json.dumps(state,indent=2)+'\n');print(f'Windows {i+1}/900',flush=True)
    state['status']='complete' if len(state['rows'])==900 else 'partial'
    state['wall_seconds']=time.monotonic()-started
    output.write_text(json.dumps(state,indent=2)+'\n')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--models',required=True);p.add_argument('--data',default='data/raw')
    p.add_argument('--output',default='results/validation/window-diagnostic.json');a=p.parse_args()
    run(a.models,a.data,a.output)
