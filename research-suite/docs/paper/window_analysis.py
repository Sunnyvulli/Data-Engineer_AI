"""Reconcile fresh full-window inference before interpreting exploratory factorial rankings."""
import json
import hashlib
from pathlib import Path
import numpy as np
from sklearn.metrics import average_precision_score,roc_auc_score
from validation_extension import paired_bootstrap

ROOT=Path(__file__).resolve().parents[2];D=ROOT/'results/validation'

def run():
    fresh=json.loads((D/'window-diagnostic.json').read_text())
    old=json.loads((D/'ragtruth-coverage-risks.json').read_text())
    base=json.loads((D/'external-support-scores.json').read_text())
    assert fresh['status']=='complete' and len(fresh['rows'])==900
    assert fresh['pair_sha256']==old['pair_sha256']
    for a,b in zip(fresh['rows'],base['records']):
        assert (a['id'],a['source_id'])==(b['id'],b['source_id'])
    scores={k:np.array([r['risks'][k] for r in fresh['rows']]) for k in fresh['rows'][0]['risks']}
    reference='e_all_c_all_max'
    error=float(np.max(np.abs(scores[reference]-old['risk'])))
    assert error<1e-5,f'Full-window score mismatch: {error}'
    y=np.array(base['labels']);groups=np.array([r['source_id'] for r in base['records']])
    report={'status':'exposed-target exploratory controlled window diagnostic','n':900,'groups':150,
            'reference':reference,'reference_max_absolute_difference':error,
            'reencoding_truncations':sum(r['audit']['reencoding_truncations'] for r in fresh['rows']),
            'inference_pairs':sum(r['audit']['inference_pairs'] for r in fresh['rows']),
            'metrics':{k:{'ap':float(average_precision_score(y,s)), 'roc_auc':float(roc_auc_score(y,s))} for k,s in scores.items()},
            'uncertainty':paired_bootstrap(y,scores,groups,{k+'_minus_reference':(k,reference) for k in scores if k!=reference}),
            'input_sha256':{f:hashlib.sha256((D/f).read_bytes()).hexdigest() for f in ['window-diagnostic.json','ragtruth-coverage-risks.json','external-support-scores.json']},
            'limitations':['Exploratory on previously exposed outcomes; no selected winner or confirmatory significance.',
                          'Conditional on fixed model, window boundaries and supplied evidence.',
                          'First-window policy is not the original bounded policy.',
                          'Aggregation changes may reflect length sensitivity; no general causal claim.']}
    (D/'window-analysis.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__':run()
