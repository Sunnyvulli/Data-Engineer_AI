"""Reconcile immutable rows and compute exposed-target, paired cluster diagnostics."""
from pathlib import Path
import hashlib
import json
import math
import numpy as np
from sklearn.metrics import average_precision_score, roc_auc_score
from research_suite.checkpoints import recall_threshold, policy_metrics
from research_suite.common import split_groups
from research_suite.followup import alce_transfer_data
from research_suite.entailment import input_pair

ROOT = Path(__file__).resolve().parents[2]
D = ROOT/'results/validation'
SEED = 20261025
REPEATS = 5000

def threshold_fast(y, scores):
    p = np.sort(np.asarray(scores)[np.asarray(y)==1])
    if not len(p):
        raise ValueError('No positive examples')
    return float(p[len(p)-math.ceil(.9*len(p))])

def interval(values):
    return np.percentile(values,[2.5,97.5]).tolist()

def paired_bootstrap(y, scores, groups, contrasts, repeats=REPEATS):
    """Complete question sampling with replacement; retain all paired rows and ties."""
    y, groups = np.asarray(y), np.asarray(groups)
    clusters = [np.flatnonzero(groups==g) for g in np.unique(groups)]
    rng = np.random.default_rng(SEED)
    differences = {name: [] for name in contrasts}
    ap_values = {name: [] for name in scores}
    for _ in range(repeats):
        ix = np.concatenate([clusters[i] for i in rng.integers(0,len(clusters),len(clusters))])
        if len(np.unique(y[ix]))<2:
            continue
        ap = {k:float(average_precision_score(y[ix],np.asarray(s)[ix])) for k,s in scores.items()}
        for k in scores: ap_values[k].append(ap[k])
        for k,(a,b) in contrasts.items(): differences[k].append(ap[a]-ap[b])
    return {'requested':repeats,'valid':len(next(iter(ap_values.values()))),'seed':SEED,
            'resampling_unit':'complete question source_id; identical sampled rows for every score',
            'ap_95':{k:interval(v) for k,v in ap_values.items()},
            'paired_ap_difference_95':{k:interval(v) for k,v in differences.items()}}

def materialize_calibration():
    path=ROOT/'data/raw/alce_annotations.json'
    expected='cfed9293752413d7c7631f36524dd4ee9ef58b209cdf9c63f6fc1e280b43cca6'
    assert hashlib.sha256(path.read_bytes()).hexdigest()==expected
    _,y,g,domains,_=alce_transfer_data(path)
    pairs=[]
    for models in json.loads(path.read_text()).values():
        for items in models.values():
            for qid,item in items.items():
                if qid!='overall_results': pairs.extend(input_pair(s) for s in item['sentences'])
    materialized={}
    for domain in ['asqa','eli5']:
        source=np.flatnonzero(domains==domain)
        _,va,_=split_groups(y[source],g[source],42)
        ix=source[va]
        cache=json.loads((D/f'{domain}-coverage-validation.json').read_text())
        digest=hashlib.sha256(json.dumps([pairs[i] for i in ix],ensure_ascii=False).encode()).hexdigest()
        assert digest==cache['pair_sha256'], 'Source validation pair identity mismatch'
        risks=np.asarray(cache['risk']);labels=y[ix];groups=g[ix]
        assert len(risks)==len(ix)
        materialized[domain]={'labels':labels.tolist(),'groups':groups.tolist(),'risk':risks.tolist(),
                              'pair_sha256':digest,'alce_sha256':expected}
    (D/'extension-calibration-rows.json').write_text(json.dumps(materialized,indent=2)+'\n')
    return materialized

def calibration():
    materialized=json.loads((D/'extension-calibration-rows.json').read_text())
    report={}
    for domain,row in materialized.items():
        cache=json.loads((D/f'{domain}-coverage-validation.json').read_text())
        assert row['pair_sha256']==cache['pair_sha256'] and row['risk']==cache['risk']
        risks=np.asarray(row['risk']); labels=np.asarray(row['labels']);groups=np.asarray(row['groups'])
        assert threshold_fast(labels,risks)==recall_threshold(labels,risks)
        clusters=[np.flatnonzero(groups==group) for group in np.unique(groups)]
        rng=np.random.default_rng(SEED);values=[]
        for _ in range(REPEATS):
            sample=np.concatenate([clusters[i] for i in rng.integers(0,len(clusters),len(clusters))])
            if labels[sample].sum(): values.append(threshold_fast(labels[sample],risks[sample]))
        report[domain]={'n':len(labels),'groups':len(clusters),'positives':int(labels.sum()),
                        'original_threshold':threshold_fast(labels,risks),'threshold_95':interval(values),
                        'valid':len(values),'requested':REPEATS,'pair_sha256':row['pair_sha256'],
                        'seed':SEED,'conditional_on_fixed_model_and_source_sample':True}
    return report

def run():
    base=json.loads((D/'external-support-scores.json').read_text())
    diag=json.loads((D/'review-diagnostics.json').read_text())
    attr=json.loads((D/'attrscore-generation.json').read_text())
    coverage=json.loads((D/'ragtruth-coverage-risks.json').read_text())
    assert attr['status']=='complete' and len(attr['rows'])==900
    assert attr['pair_sha256']==coverage['pair_sha256']
    for expected,actual,d in zip(base['records'],attr['rows'],diag['rows']):
        assert expected['id']==actual['id']==d['id']
        assert expected['source_id']==actual['source_id']==d['source_id']
    y=np.asarray(base['labels']);groups=np.array([x['source_id'] for x in base['records']])
    mask=np.array([x['risk'] is not None for x in attr['rows']])
    scores={'attrscore':np.array([x['risk'] if x['risk'] is not None else np.nan for x in attr['rows']]),
            'length':np.array([x['answer_tokens'] for x in diag['rows']]),
            'coverage':np.array(base['coverage_nli']),
            'asqa_lexical':np.array(base['lexical_by_source']['asqa']),
            'eli5_lexical':np.array(base['lexical_by_source']['eli5']),
            'length_within_generator':np.array([x['length_within_generator_rank'] for x in diag['rows']]),
            'coverage_within_generator':np.array([x['coverage_within_generator_rank'] for x in diag['rows']])}
    comparisons={f'attrscore_minus_{k}':('attrscore',k) for k in ['length','coverage','asqa_lexical','eli5_lexical']}
    comparisons.update(length_minus_coverage=('length','coverage'),
                       within_generator_length_minus_coverage=('length_within_generator','coverage_within_generator'))
    subset={k:v[mask] for k,v in scores.items()}
    report={'status':'exposed-target exploratory; no fresh confirmation or human peer review',
            'n':int(mask.sum()),'failed_outputs':int((~mask).sum()),'groups':len(set(groups[mask])),
            'positives':int(y[mask].sum()),'metrics':{k:{'ap':float(average_precision_score(y[mask],s)),
                'roc_auc':float(roc_auc_score(y[mask],s))} for k,s in subset.items()},
            'attrscore_fixed_rule':policy_metrics(y[mask],subset['attrscore'],.5),
            'paired_uncertainty':paired_bootstrap(y[mask],subset,groups[mask],comparisons),
            'source_threshold_uncertainty':calibration(),
            'truncation':{k:sum(bool(row['audit'][k]) for row in attr['rows']) for k in ['claim_truncated','evidence_truncated']},
            'input_sha256':{name:hashlib.sha256((D/name).read_bytes()).hexdigest() for name in
               ['external-support-scores.json','review-diagnostics.json','attrscore-generation.json','ragtruth-coverage-risks.json']},
            'limitations':['All target outcomes were previously exposed; intervals descriptive and not multiplicity corrected.',
                          'AttrScore outputs are discrete labels, not calibrated probabilities.',
                          'Coverage and AttrScore use different tokenizers and context policies.',
                          'Within-generator ranks are transductive and label-free; no causal decomposition.',
                          'Source threshold intervals condition on the fitted model; no retraining uncertainty.',
                          'Unknown training overlap; no independent fresh-data confirmation or external reviewer.']}
    (D/'validation-extension.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__': run()
