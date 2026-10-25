"""Offline integrity audit of derived extension scores; no raw text/model required."""
import hashlib
import json
from pathlib import Path
import numpy as np
from sklearn.metrics import average_precision_score,roc_auc_score
from research_suite.attrscore import parse_label
from research_suite.checkpoints import policy_metrics

D=Path(__file__).resolve().parents[2]/'results/validation'

def run():
    extension=json.loads((D/'validation-extension.json').read_text())
    windows=json.loads((D/'window-analysis.json').read_text())
    base=json.loads((D/'external-support-scores.json').read_text())
    attr=json.loads((D/'attrscore-generation.json').read_text())
    diag=json.loads((D/'review-diagnostics.json').read_text())
    fresh=json.loads((D/'window-diagnostic.json').read_text())
    old=json.loads((D/'ragtruth-coverage-risks.json').read_text())
    assert attr['status']==fresh['status']=='complete'
    assert len(attr['rows'])==len(fresh['rows'])==len(base['records'])==900
    for report in [extension,windows]:
        for file,digest in report['input_sha256'].items():
            assert hashlib.sha256((D/file).read_bytes()).hexdigest()==digest
    for i,(a,w,b) in enumerate(zip(attr['rows'],fresh['rows'],base['records'])):
        assert (a['id'],a['source_id'])==(w['id'],w['source_id'])==(b['id'],b['source_id'])
        assert parse_label(a['output'])==a['risk']
        assert a['audit']['input_tokens']<=512
        assert abs(w['risks']['e_all_c_all_max']-old['risk'][i])<1e-5
    mask=np.array([r['risk'] is not None for r in attr['rows']]);y=np.array(base['labels'])[mask]
    arrays={'attrscore':np.array([r['risk'] if r['risk'] is not None else np.nan for r in attr['rows']]),
            'length':np.array([r['answer_tokens'] for r in diag['rows']]),'coverage':np.array(base['coverage_nli']),
            'asqa_lexical':np.array(base['lexical_by_source']['asqa']),'eli5_lexical':np.array(base['lexical_by_source']['eli5']),
            'length_within_generator':np.array([r['length_within_generator_rank'] for r in diag['rows']]),
            'coverage_within_generator':np.array([r['coverage_within_generator_rank'] for r in diag['rows']])}
    for k,s in arrays.items():
        for metric,fn in [('ap',average_precision_score),('roc_auc',roc_auc_score)]:
            assert np.isclose(extension['metrics'][k][metric],fn(y,s[mask]),atol=1e-12)
    assert extension['attrscore_fixed_rule']==policy_metrics(y,arrays['attrscore'][mask],.5)
    assert extension['n']==int(mask.sum()) and extension['failed_outputs']==int((~mask).sum())
    assert extension['paired_uncertainty']['requested']==5000
    for k,m in windows['metrics'].items():
        s=[r['risks'][k] for r in fresh['rows']]
        assert np.isclose(m['ap'],average_precision_score(base['labels'],s),atol=1e-12)
        assert np.isclose(m['roc_auc'],roc_auc_score(base['labels'],s),atol=1e-12)
    print('Extension: 900 row IDs, model labels, score metrics, fixed operating rule, input hashes and full-window reconciliation pass.')

if __name__=='__main__':run()
