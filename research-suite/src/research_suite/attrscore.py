"""Bounded official AttrScore comparator; no training or calibrated probabilities."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import resource
import time

MODEL_REVISION = '282eb2ab5d537f5badf5fa33008d96abff34607b'
WEIGHT_HASH = '163ba0ad32e03ce021207b4f9ac63654cdaa99beb644467dafc0016b9bb92125'
POLICY = 'official_instruction_claim120_reference_fill512_greedy8_v1'
INSTRUCTION = ('As an Attribution Validator, your task is to verify whether a given reference can support '
 'the given claim. A claim can be either a plain sentence or a question followed by its answer. '
 'Specifically, your response should clearly indicate the relationship: Attributable, Contradictory '
 'or Extrapolatory. A contradictory error occurs when you can infer that the answer contradicts '
 'the fact presented in the context, while an extrapolatory error means that you cannot infer '
 'the correctness of the answer based on the information provided in the context.')

def parse_label(text):
    return {'attributable': 0., 'contradictory': 1., 'extrapolatory': 1.}.get(text.strip().lower())

def bounded_input(tokenizer, evidence, claim):
    prefix = tokenizer.encode(INSTRUCTION + '\n\nClaim: ', add_special_tokens=False)
    claim_ids = tokenizer.encode(claim, add_special_tokens=False)
    reference = tokenizer.encode('\nReference: ', add_special_tokens=False)
    evidence_ids = tokenizer.encode(evidence, add_special_tokens=False)
    cc = claim_ids[:120]
    budget = 511 - len(prefix) - len(cc) - len(reference)
    if budget < 0:
        raise ValueError('Instruction and claim exceed fixed budget')
    selected = prefix + cc + reference + evidence_ids[:budget] + [tokenizer.eos_token_id]
    assert len(selected) <= 512
    return selected, {'claim_tokens': len(claim_ids), 'evidence_tokens': len(evidence_ids),
                     'claim_truncated': len(claim_ids)>120, 'evidence_truncated': len(evidence_ids)>budget,
                     'input_tokens': len(selected)}

def run(data, model_dir, output, max_seconds=3600):
    import torch
    from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
    from .external_support import load_target
    from .entailment import input_pair
    from .common import sha256
    torch.set_num_threads(4)
    started = time.monotonic()
    model_dir, output = Path(model_dir), Path(output)
    manifest = json.loads((model_dir/'manifest.json').read_text())
    assert manifest['revision'] == MODEL_REVISION
    assert sha256(model_dir/'pytorch_model.bin') == WEIGHT_HASH
    for name, entry in manifest['files'].items():
        assert sha256(model_dir/name) == entry['sha256']
    tokenizer = AutoTokenizer.from_pretrained(model_dir, local_files_only=True, use_fast=False)
    model = AutoModelForSeq2SeqLM.from_pretrained(model_dir, local_files_only=True,
                                                trust_remote_code=False).eval()
    records, labels, groups, meta, _ = load_target(Path(data)/'ragtruth', Path(data)/'alce_annotations.json')
    pairs = [input_pair(x) for x in records]
    digest = hashlib.sha256(json.dumps(pairs,ensure_ascii=False).encode()).hexdigest()
    state = {'model_revision': MODEL_REVISION, 'policy': POLICY, 'pair_sha256': digest,
             'weight_sha256': WEIGHT_HASH, 'rows': [], 'status': 'partial', 'sessions': [],
             'model_manifest': manifest, 'fixtures': []}
    if output.exists():
        old = json.loads(output.read_text())
        for k in ['model_revision','policy','pair_sha256','weight_sha256']:
            if old[k] != state[k]: raise ValueError('Cache identity mismatch: '+k)
        state = old
    def infer(evidence,claim):
        ids,audit = bounded_input(tokenizer,evidence,claim)
        with torch.inference_mode():
            tokens = model.generate(torch.tensor([ids]),max_new_tokens=8,do_sample=False,num_beams=1)
        text = tokenizer.decode(tokens[0],skip_special_tokens=True)
        return text,parse_label(text),audit
    if not state['fixtures']:
        for expected,e,c in [('Attributable','The capital of France is Paris.','The capital of France is Paris.'),
                             ('Contradictory','The capital of France is Paris.','The capital of France is London.'),
                             ('Extrapolatory','The capital of France is Paris.','Paris has two million residents.')]:
            text,risk,audit = infer(e,c)
            state['fixtures'].append({'expected':expected,'output':text,'risk':risk,'audit':audit})
        print(json.dumps({'fixtures':state['fixtures']}),flush=True)
    initial = len(state['rows'])
    for i in range(initial,len(pairs)):
        if time.monotonic()-started >= max_seconds: break
        if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss > 8*1024*1024:
            state['stop_reason']='RSS cap';break
        e,c = pairs[i]
        text,risk,audit = infer(e,c)
        state['rows'].append({'id':meta[i]['id'],'source_id':meta[i]['source_id'],
                              'output':text,'risk':risk,'audit':audit})
        if (i+1)%10==0:
            output.parent.mkdir(parents=True,exist_ok=True)
            tmp=output.with_suffix('.tmp');tmp.write_text(json.dumps(state,indent=2)+'\n');tmp.replace(output)
            print(json.dumps({'completed':i+1,'total':len(pairs),'elapsed':round(time.monotonic()-started,2),
                              'rss_mib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024}),flush=True)
    state['status']='complete' if len(state['rows'])==len(pairs) else 'partial'
    state['sessions'].append({'new_rows':len(state['rows'])-initial,'wall_seconds':time.monotonic()-started,
                              'peak_rss_mib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024})
    output.write_text(json.dumps(state,indent=2)+'\n')
    return state

if __name__ == '__main__':
    p=argparse.ArgumentParser();p.add_argument('--data',default='data/raw');p.add_argument('--models',required=True)
    p.add_argument('--output',default='results/validation/attrscore-generation.json');p.add_argument('--max-seconds',type=int,default=3600)
    a=p.parse_args();run(a.data,a.models,a.output,a.max_seconds)
