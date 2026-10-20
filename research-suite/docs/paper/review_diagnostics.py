"""Post-hoc confounding diagnostics; never a source-only detector comparison."""
from pathlib import Path
import hashlib
import json
import numpy as np
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.model_selection import KFold
from scipy.stats import rankdata

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


def within_generator_ranks(values, generators):
    """Average tied ranks / stratum n; no outcome labels, transductive target ranks."""
    values, generators = np.asarray(values), np.asarray(generators)
    if values.ndim != 1 or generators.ndim != 1 or len(values) != len(generators):
        raise ValueError("Aligned one-dimensional scores and generators required")
    if not len(values) or not np.isfinite(values).all():
        raise ValueError("Nonempty finite scores required")
    ranks = np.zeros(len(values), dtype=float)
    for name in np.unique(generators):
        ix = generators == name
        ranks[ix] = rankdata(values[ix], method="average") / ix.sum()
    return ranks


def self_check():
    # Ties retain their mean rank; unrelated generator scales cannot affect ranks.
    values = np.array([1., 1., 3., 10., 20., 20.])
    gen = np.array(['a', 'a', 'a', 'b', 'b', 'b'])
    rank = within_generator_ranks(values, gen)
    assert np.allclose(rank, [.5, .5, 1., 1/3, 5/6, 5/6])
    changed_scale = np.where(gen == 'a', values * 100 + 50, values - 1000)
    assert np.array_equal(rank, within_generator_ranks(changed_scale, gen))
    permutation = np.array([5, 1, 3, 0, 4, 2])
    assert np.array_equal(rank[permutation], within_generator_ranks(values[permutation], gen[permutation]))
    for bad, bad_gen in [([], []), ([float('nan')], ['a']), ([1, 2], ['a'])]:
        try:
            within_generator_ranks(bad, bad_gen)
        except ValueError:
            pass
        else:
            raise AssertionError("Invalid diagnostic input accepted")
    # Independent pair-count oracle for AUC with tied scores.
    y_tied = np.array([0, 1, 0, 1])
    score_tied = np.array([1., 1., 2., 3.])
    pos, neg = score_tied[y_tied == 1], score_tied[y_tied == 0]
    oracle = sum(float(a > b) + .5 * float(a == b) for a in pos for b in neg) / (len(pos)*len(neg))
    assert np.isclose(metrics(y_tied, score_tied)['roc_auc'], oracle)
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
    length_ranks = within_generator_ranks(lengths, generators)
    coverage_ranks = within_generator_ranks(saved["coverage_nli"], generators)
    strata = []
    for name in sorted(set(generators)):
        ix = generators == name
        strata.append({'generator': name, 'n': int(ix.sum()), 'positives': int(y[ix].sum()),
                       'prevalence': float(y[ix].mean()), 'mean_answer_tokens': float(lengths[ix].mean()),
                       'length_longer_risk': metrics(y[ix], lengths[ix]),
                       'length_shorter_risk': metrics(y[ix], -lengths[ix]),
                       'sparse_positive_warning': int(y[ix].sum()) < 10,
                       'detectors': {name: metrics(y[ix], np.asarray(scores)[ix]) for name, scores in
                         [('asqa_lexical', saved['lexical_by_source']['asqa']),
                          ('eli5_lexical', saved['lexical_by_source']['eli5']),
                          ('bounded_nli', saved['bounded_nli']), ('coverage_nli', saved['coverage_nli'])]}})
    report = {'status': 'post_hoc_exploratory', 'seed': 20261020, 'n': len(y),
              'prevalence': float(y.mean()), 'length_longer_risk': metrics(y, lengths),
              'length_shorter_risk': metrics(y, -lengths),
              'length_within_generator_rank': metrics(y, length_ranks),
              'coverage_within_generator_rank': metrics(y, coverage_ranks),
              'rank_policy': 'average tied rank divided by generator n; all six generators; target-distribution transductive; label-free',
              'generator_prior_target_supervised': metrics(y, prior), 'strata': strata,
              'source_calibration': aggregate['validation'],
              'limitations': ['target outcomes previously exposed',
                'generator prior trains on target labels in other question groups; not source-only',
                'within-generator samples include only 1 or 5 positives in some strata',
                'within-generator ranks use the unlabeled target distribution and generator metadata',
                'point estimates do not establish equivalence, superiority or causal decomposition',
                'cached lengths aligned only after exact risk-vector and row-count reconciliation',
                'no causal attribution to length, generator, coverage or corpus'],
              'inputs_sha256': {name: hashlib.sha256((D/name).read_bytes()).hexdigest() for name in
                ['external-support-scores.json', 'ragtruth-coverage-risks.json', 'external-support.json']},
              'rows': [{'id': x['id'], 'source_id': x['source_id'], 'answer_tokens': int(length),
                        'fold': int(fold), 'generator_prior': float(score),
                        'length_within_generator_rank': float(length_ranks[i]),
                        'coverage_within_generator_rank': float(coverage_ranks[i])}
                       for i, (x, length, fold, score) in enumerate(zip(saved['records'], lengths, folds, prior))]}
    (D / 'review-diagnostics.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k not in ['rows', 'strata']}, indent=2))
    print([(s['generator'], s['positives'], s['n']) for s in strata])


if __name__ == '__main__':
    run()
