"""Fixed follow-up protocols: corpus shift, cluster uncertainty, independent simulations."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from urllib.parse import urlsplit
import zipfile
import numpy as np
import pandas as pd
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from .common import binary_metrics, environment, sha256, split_groups, threshold_at_fpr, write_json
from .checkpoints import features, recall_threshold, policy_metrics
from .transients import early_features, budget_metrics


def cluster_interval(y, scores, groups, threshold=.5, other_scores=None, repetitions=300, budget=None):
    """Percentile intervals conditional on fitted models, resampling complete clusters."""
    from sklearn.metrics import average_precision_score
    y, scores, groups = np.asarray(y), np.asarray(scores), np.asarray(groups)
    other_scores = None if other_scores is None else np.asarray(other_scores)
    unique = np.unique(groups)
    members = [np.flatnonzero(groups == group) for group in unique]
    rng = np.random.default_rng(20261018)
    aps, recalls, differences, budget_precisions, budget_recalls = [], [], [], [], []
    for _ in range(repetitions):
        idx = np.concatenate([members[i] for i in rng.integers(0, len(unique), len(unique))])
        target = y[idx]
        if len(np.unique(target)) != 2:
            continue
        ap = average_precision_score(target, scores[idx])
        aps.append(float(ap))
        recalls.append(float(np.mean(scores[idx][target == 1] >= threshold)))
        if budget is not None:
            bm = budget_metrics(target, scores[idx], budget)
            budget_precisions.append(bm['precision_at_budget'])
            budget_recalls.append(bm['recall_at_budget'])
        if other_scores is not None:
            differences.append(float(ap-average_precision_score(target, other_scores[idx])))
    def interval(values):
        return np.quantile(values, [.025, .975]).tolist() if values else None
    return {'resampling_unit': 'complete supplied cluster', 'clusters': len(unique),
            'requested_resamples': repetitions, 'valid_resamples': len(aps),
            'ap_percentile_95': interval(aps), 'recall_percentile_95': interval(recalls),
            'paired_ap_difference_percentile_95': interval(differences),
            'precision_at_budget_percentile_95': interval(budget_precisions),
            'recall_at_budget_percentile_95': interval(budget_recalls),
            'limitation': 'conditional on fitted model; does not account for corpus bias or model-selection uncertainty'}


def host(url):
    if not isinstance(url, str) or not url.strip():
        raise ValueError('A nonempty URL string is required')
    try:
        parsed = urlsplit(url.strip() if '://' in url else 'https://' + url.strip())
        value = parsed.hostname
    except ValueError as exc:
        raise ValueError('Malformed URL hostname') from exc
    if not value:
        raise ValueError('URL must contain a hostname')
    value = value.rstrip('.').lower()
    return value[4:] if value.startswith('www.') else value


def raw_url_data(path):
    with zipfile.ZipFile(path) as archive:
        names = [n for n in archive.namelist() if n.endswith('.csv')]
        if len(names) != 1:
            raise ValueError('Expected one PhiUSIIL CSV')
        frame = pd.read_csv(archive.open(names[0]), usecols=['URL', 'label'])
    if frame.URL.isna().any() or not frame.label.isin([0, 1]).all():
        raise ValueError('Unexpected raw URL or label schema')
    frame.URL = frame.URL.str.strip()  # Path/query case remains intact.
    conflicts = frame.groupby('URL').label.nunique()
    bad_urls = set(conflicts[conflicts > 1].index)
    audit = {'raw_rows': len(frame), 'exact_url_duplicate_rows': int(frame.URL.duplicated().sum()),
             'conflicting_urls_excluded': len(bad_urls)}
    frame = frame[~frame.URL.isin(bad_urls)].drop_duplicates('URL').copy()
    frame['hostname'] = frame.URL.map(host)
    frame['positive'] = 1-frame.label  # phishing is positive
    audit['collection_by_class'] = {}
    for label, group in frame.groupby('positive'):
        parsed = group.URL.map(lambda u: urlsplit(u if '://' in u else 'https://'+u))
        audit['collection_by_class'][str(label)] = {
            'rows': len(group), 'https_fraction': float(parsed.map(lambda u: u.scheme == 'https').mean()),
            'www_fraction': float(parsed.map(lambda u: (u.hostname or '').startswith('www.')).mean()),
            'nonempty_path_fraction': float(parsed.map(lambda u: u.path not in ('', '/')).mean()),
            'query_fraction': float(parsed.map(lambda u: bool(u.query)).mean())}
    frame['order_hash'] = frame.URL.map(lambda u: hashlib.sha256(u.encode()).hexdigest())
    return frame.sort_values('order_hash').head(30000).reset_index(drop=True), audit


def phishing_transfer(data, output):
    path = Path(data)/'phiusiil.zip'
    frame, audit = raw_url_data(path)
    y = frame.positive.to_numpy()
    groups = frame.hostname.to_numpy()
    tr, va, te = split_groups(y, groups, 42)
    scores, rows = {}, []
    for name, column in [('full_url', 'URL'), ('hostname', 'hostname')]:
        model = make_pipeline(TfidfVectorizer(analyzer='char', ngram_range=(3, 5), max_features=30000, min_df=2),
                              LogisticRegression(solver='liblinear', max_iter=2000, class_weight='balanced', random_state=42))
        model.fit(frame[column].iloc[tr], y[tr])
        val = model.predict_proba(frame[column].iloc[va])[:, 1]
        test = model.predict_proba(frame[column].iloc[te])[:, 1]
        threshold = threshold_at_fpr(y[va], val)
        scores[name] = test
        rows.append({'representation': name, **binary_metrics(y[te], test, threshold),
                     'uncertainty': cluster_interval(y[te], test, groups[te], threshold)})
    paired = cluster_interval(y[te], scores['full_url'], groups[te], other_scores=scores['hostname'])
    result = {'status': 'second-corpus raw-URL benchmark; not external validation of UCI-327 model',
              'input_sha256': sha256(path), 'environment': environment(), 'audit': audit,
              'selection': '30,000 smallest SHA-256 hashes of outer-whitespace-trimmed unique URLs; conflicting URLs excluded',
              'selected_rows': len(frame), 'unique_hosts': frame.hostname.nunique(),
              'split': {'train': len(tr), 'validation': len(va), 'test': len(te), 'hostname_overlap': 0},
              'host_limit': 'exact normalized hostname grouping; not eTLD+1, campaign, or temporal separation',
              'experiments': rows, 'paired_full_minus_host_ap': paired}
    write_json(Path(output)/'phishing-followup.json', result)
    return result


def alce_transfer_data(path):
    raw = json.loads(Path(path).read_text())
    X, y, groups, domains, automatic = [], [], [], [], []
    for domain, models in raw.items():
        for model, examples in models.items():
            for qid, item in examples.items():
                if qid == 'overall_results':
                    continue
                sentences = item['sentences']
                auto = item['automatic_recall_scores']
                if len(auto) != len(sentences) or any(s not in [0, 1] for s in auto):
                    raise ValueError('Released automatic scores are not aligned binary scores')
                for sentence, score in zip(sentences, auto):
                    X.append(features(sentence));y.append(1-int(sentence['sentence_recall_score']))
                    groups.append(domain+':'+qid);domains.append(domain);automatic.append(1-score)
    return np.array(X), np.array(y), np.array(groups), np.array(domains), np.array(automatic)


def citation_transfer(data, output):
    path = Path(data)/'alce_annotations.json'
    X, y, groups, domains, automatic = alce_transfer_data(path)
    rows, splits = [], []
    lexical = np.maximum.reduce([1-X[:, 0], X[:, 4], X[:, 5]])
    for source, target in [('asqa', 'eli5'), ('eli5', 'asqa')]:
        source_idx, te = np.flatnonzero(domains == source), np.flatnonzero(domains == target)
        tr0, va0, unused0 = split_groups(y[source_idx], groups[source_idx], 42)
        # All source folds except the validation fold are training. No target labels are used.
        tr = source_idx[np.r_[tr0, unused0]];va = source_idx[va0]
        model = make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000, class_weight='balanced', random_state=42))
        model.fit(X[tr], y[tr])
        val_p = model.predict_proba(X[va])[:, 1];test_p = model.predict_proba(X[te])[:, 1]
        threshold = recall_threshold(y[va], val_p)
        lexical_threshold = recall_threshold(y[va], lexical[va])
        splits.append({'source': source, 'target': target, 'train': len(tr), 'validation': len(va), 'test': len(te),
                       'train_questions': len(set(groups[tr])), 'test_questions': len(set(groups[te])), 'question_overlap': 0})
        for name, risk, cutoff in [('learned_lexical', test_p, threshold), ('lexical', lexical[te], lexical_threshold),
                                   ('released_automatic', automatic[te], .5), ('review_all', np.ones(len(te)), .5),
                                   ('review_none', np.zeros(len(te)), .5)]:
            rows.append({'source': source, 'target': target, 'policy': name,
                         **policy_metrics(y[te], risk, cutoff), 'uncertainty': cluster_interval(y[te], risk, groups[te], cutoff)})
    result = {'status': 'ALCE domain-transfer evaluation; no new factual-truth or learning-outcome trial',
              'input_sha256': sha256(path), 'environment': environment(), 'splits': splits,
              'released_automatic_note': 'Uses already-released automatic_recall_scores; evaluator was not rerun or newly trained',
              'experiments': rows}
    write_json(Path(output)/'citation-transfer.json', result)
    return result


def first_complete_objects(path, maximum=5000):
    """Read a sorted shard through the first row of the next object, then stop."""
    pieces, selected = [], []
    previous = None
    for chunk in pd.read_csv(path, chunksize=100000):
        ids = chunk.object_id.to_numpy()
        if previous is not None and ids[0] < previous or np.any(ids[1:] < ids[:-1]):
            raise ValueError('Shard must be sorted by object_id')
        previous = ids[-1]
        for oid in pd.unique(ids):
            if oid not in selected:
                selected.append(oid)
                if len(selected) > maximum:
                    boundary = selected[maximum]
                    pieces.append(chunk[chunk.object_id < boundary])
                    result = pd.concat(pieces, ignore_index=True)
                    return result, {'selected_complete_objects': maximum, 'last_id': int(selected[maximum-1])}
        pieces.append(chunk)
    return pd.concat(pieces, ignore_index=True), {'selected_complete_objects': len(selected), 'last_id': int(selected[-1])}


def independent_outcome(y, p, object_ids):
    y, p = np.asarray(y), np.asarray(p)
    if not np.isfinite(p).all() or np.any((p < 0) | (p > 1)):
        raise ValueError('Independent scores must be finite probabilities')
    if len(np.unique(y)) < 2:
        metrics = {'n': len(y), 'positives': int(y.sum()), 'average_precision': None, 'roc_auc': None,
                   'recall': None, 'false_positive_rate': float(np.mean(p >= .5)) if np.sum(y) == 0 else None}
        budget = budget_metrics(y, p)
        budget['recall_at_budget'] = None
        return {'evaluation_status': 'rare-event discrimination not estimable: selected sample lacks both classes',
                'metrics': metrics, 'budget': budget, 'uncertainty': {'reason': 'No valid two-class resampling distribution'}}
    from scipy.stats import beta
    budget = budget_metrics(y, p)
    positives, found = int(y.sum()), budget['rare_found']
    exact = [0. if found == 0 else float(beta.ppf(.025, found, positives-found+1)),
             1. if found == positives else float(beta.ppf(.975, found+1, positives-found))]
    return {'evaluation_status': 'two-class evaluation completed', 'metrics': binary_metrics(y, p),
            'budget': budget, 'uncertainty': cluster_interval(y, p, object_ids, budget=.05),
            'recall_binomial_diagnostic': {'clopper_pearson_95': exact, 'positive_events': positives,
                'assumption': 'independent exchangeable positive events; illustrative diagnostic, not a guarantee',
                'note': 'Added as a post-outcome diagnostic because a rare-event bootstrap can be degenerate'}}


def independent_transients(data, output, model_path, trusted=False, remaining=False):
    if not trusted:
        raise ValueError('Only use locally trained joblib artifacts with explicit trust')
    data, output = Path(data), Path(output)
    if remaining:
        pieces = []
        for chunk in pd.read_csv(data/'plasticc_test_lightcurves_01.csv.gz', chunksize=100000):
            pieces.append(chunk[chunk.object_id > 53125])
        obs = pd.concat(pieces, ignore_index=True)
        final_id = obs.object_id.max()
        obs = obs[obs.object_id < final_id]
        selection = {'policy': 'stage-two remaining objects after pilot; final object excluded',
                     'excluded_pilot_through_id': 53125, 'excluded_final_id': int(final_id),
                     'selected_complete_objects': obs.object_id.nunique()}
    else:
        obs, selection = first_complete_objects(data/'plasticc_test_lightcurves_01.csv.gz')
    ids = set(obs.object_id)
    original = pd.read_csv(data/'plasticc_train_metadata.csv.gz', usecols=['object_id'])
    if ids & set(original.object_id):
        raise ValueError('Independent simulation IDs overlap original training metadata')
    metadata = []
    for chunk in pd.read_csv(data/'plasticc_test_metadata.csv.gz', chunksize=100000, usecols=['object_id', 'true_target']):
        metadata.append(chunk[chunk.object_id.isin(ids)])
    metadata = pd.concat(metadata).set_index('object_id')
    if metadata.index.duplicated().any() or set(metadata.index) != ids:
        raise ValueError('Evaluation metadata alignment failed')
    artifact = joblib.load(model_path)
    if artifact['project'] != 'transients' or artifact['horizon'] != 3:
        raise ValueError('Protocol requires the frozen three-day transient model')
    X = early_features(obs, 3)[artifact['columns']]
    y = (metadata.loc[X.index].true_target == 64).astype(int).to_numpy()
    p = artifact['model'].predict_proba(X)[:, 1]
    result = {'status': 'independent simulated objects; no real-world external validation',
              'selection': selection, 'eligible_detected_objects': len(X), 'excluded_without_detection': len(ids)-len(X),
              'original_metadata_id_overlap': 0, 'frozen_model_sha256': sha256(model_path),
              'environment': environment(), **independent_outcome(y, p, X.index.to_numpy()),
              'expected_random_precision': float(y.mean()),
              'input_sha256': {name: sha256(data/name) for name in ['plasticc_test_metadata.csv.gz', 'plasticc_test_lightcurves_01.csv.gz']}}
    write_json(output/('independent-transients-remainder.json' if remaining else 'independent-transients.json'), result)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('project', choices=['phishing', 'citations', 'transients'])
    parser.add_argument('--data', default='data/raw')
    parser.add_argument('--output', default='results/followup')
    parser.add_argument('--model', default='results/models/transients-3d.joblib')
    parser.add_argument('--trust-local-model', action='store_true')
    parser.add_argument('--remaining-shard', action='store_true')
    args = parser.parse_args()
    if args.project == 'phishing':result = phishing_transfer(args.data, args.output)
    elif args.project == 'citations':result = citation_transfer(args.data, args.output)
    else:result = independent_transients(args.data, args.output, args.model, args.trust_local_model, args.remaining_shard)
    print(json.dumps({'project': args.project, 'status': result['status'], 'output': args.output}))


if __name__ == '__main__':
    main()
