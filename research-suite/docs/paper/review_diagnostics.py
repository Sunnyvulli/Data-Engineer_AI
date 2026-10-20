"""Post-hoc confounding diagnostics; never a source-only detector comparison."""
from pathlib import Path
import hashlib
import json
import numpy as np
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.model_selection import KFold

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / 'results/validation'


def metrics(y, p):
    return {'ap': float(average_precision_score(y, p)),
            'roc_auc': float(roc_auc_score(y, p)) if len(set(y)) == 2 else None}


def generator_prior(y, generators, groups, folds=5, seed=20261020):
    y, generators, groups = map(np.asarray, (y, generators, groups))
    unique = np.unique(groups)
    scores, assignment = np.zeros(len(y)), np.zeros(len(y), dtype=int)
    for fold, (train, test) in enumerate(KFold(folds, shuffle=True, random_state=seed).split(unique)):
        held = np.isin(groups, unique[test])
        fit = np.isin(groups, unique[train])
        assert not set(groups[fit]) & set(groups[held])
        assignment[held] = fold
        for generator in np.unique(generators[held]):
            selected = fit & (generators == generator)
            scores[held & (generators == generator)] = (y[selected].sum() + 1) / (selected.sum() + 2)
    return scores, assignment


def self_check():
    # Identical per-generator counts across complete groups imply a 0.5 prior.
    y = np.tile([0, 1], 10)
    groups = np.repeat(np.arange(10), 2)
    p, fold = generator_prior(y, np.array(['a'] * 20), groups)
    assert np.allclose(p, .5)
    for group in set(groups):
        assert len(set(fold[groups == group])) == 1
    assert metrics([0, 1], [0, 1]) == {'ap': 1., 'roc_auc': 1.}
    # Held-out labels must not alter that fold's predictions.
    changed = y.copy()
    changed[fold == 0] = 1 - changed[fold == 0]
    p2, _ = generator_prior(changed, np.array(['a'] * 20), groups)
    assert np.array_equal(p[fold == 0], p2[fold == 0])


def run():
    self_check()
    saved = json.loads((D / 'external-support-scores.json').read_text())
    cache = json.loads((D / 'ragtruth-coverage-risks.json').read_text())
    aggregate = json.loads((D / 'external-support.json').read_text())
    y = np.array(saved['labels'])
    assert len(y) == len(saved['records']) == len(cache['audit']) == 900
    assert int(y.sum()) == 160
    assert np.array_equal(cache['risk'], saved['coverage_nli'])
    lengths = np.array([x['claim_tokens'] for x in cache['audit']])
    generators = np.array([x['generator'] for x in saved['records']])
    groups = np.array([x['source_id'] for x in saved['records']])
    prior, folds = generator_prior(y, generators, groups)
    strata = []
    for name in sorted(set(generators)):
        ix = generators == name
        strata.append({'generator': name, 'n': int(ix.sum()), 'positives': int(y[ix].sum()),
                       'prevalence': float(y[ix].mean()), 'mean_answer_tokens': float(lengths[ix].mean()),
                       'detectors': {name: metrics(y[ix], np.asarray(scores)[ix]) for name, scores in
                         [('asqa_lexical', saved['lexical_by_source']['asqa']),
                          ('eli5_lexical', saved['lexical_by_source']['eli5']),
                          ('bounded_nli', saved['bounded_nli']), ('coverage_nli', saved['coverage_nli'])]}})
    report = {'status': 'post_hoc_exploratory', 'seed': 20261020, 'n': len(y),
              'prevalence': float(y.mean()), 'length_longer_risk': metrics(y, lengths),
              'length_shorter_risk': metrics(y, -lengths),
              'generator_prior_target_supervised': metrics(y, prior), 'strata': strata,
              'source_calibration': aggregate['validation'],
              'limitations': ['target outcomes previously exposed',
                'generator prior trains on target labels in other question groups; not source-only',
                'within-generator samples include only 1 or 5 positives in some strata',
                'cached lengths aligned only after exact risk-vector and row-count reconciliation',
                'no causal attribution to length, generator, coverage or corpus'],
              'inputs_sha256': {name: hashlib.sha256((D/name).read_bytes()).hexdigest() for name in
                ['external-support-scores.json', 'ragtruth-coverage-risks.json', 'external-support.json']},
              'rows': [{'id': x['id'], 'source_id': x['source_id'], 'answer_tokens': int(length),
                        'fold': int(fold), 'generator_prior': float(score)}
                       for x, length, fold, score in zip(saved['records'], lengths, folds, prior)]}
    (D / 'review-diagnostics.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k not in ['rows', 'strata']}, indent=2))
    print([(s['generator'], s['positives'], s['n']) for s in strata])


if __name__ == '__main__':
    run()
