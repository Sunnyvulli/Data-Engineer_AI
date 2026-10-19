"""Offline feature-block robustness baseline. Does not browse suspect websites."""
from __future__ import annotations
import io
import time
import zipfile
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.io import arff
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.impute import SimpleImputer
from sklearn.pipeline import make_pipeline
from .common import binary_metrics, environment, sha256, split_groups, threshold_at_fpr, write_json

# Fixed before evaluation; these are feature blocks, NOT raw modalities.
BLOCKS = {'url': ['having_IP_Address', 'URL_Length', 'Shortining_Service', 'having_At_Symbol',
                  'double_slash_redirecting', 'Prefix_Suffix', 'having_Sub_Domain', 'HTTPS_token'],
          'page': ['Favicon', 'Request_URL', 'URL_of_Anchor', 'Links_in_tags', 'SFH',
                   'Submitting_to_email', 'Redirect', 'on_mouseover', 'RightClick', 'popUpWidnow', 'Iframe']}


def load(path):
    with zipfile.ZipFile(path) as archive:
        raw = archive.read('Training Dataset.arff').decode('utf-8')
    records, _ = arff.loadarff(io.StringIO(raw))
    frame = pd.DataFrame(records).astype(float)
    if 'Result' not in frame or not set(frame.Result.unique()) <= {-1, 1}:
        raise ValueError('Unexpected UCI label encoding')
    X = frame.drop(columns='Result')
    if not np.isfinite(X.to_numpy()).all():
        raise ValueError('Original input must contain finite numeric features')
    # UCI -1 means phishing, +1 legitimate. Positive class is phishing here.
    y = (frame.Result == -1).astype(int).to_numpy()
    groups = pd.util.hash_pandas_object(X, index=False).to_numpy()
    return X, y, groups


def corrupt(X, condition, seed):
    X = X.copy()
    if condition in ('missing_page', 'missing_url'):
        X.loc[:, BLOCKS[condition.removeprefix('missing_')]] = np.nan
    elif condition == 'random_20pct':
        X = X.mask(np.random.default_rng(seed).random(X.shape) < .2)
    elif condition != 'clean':
        raise ValueError('Unknown corruption condition')
    return X


def run(data, output, seeds=(17, 42, 91)):
    path = Path(data) / 'phishing.zip'
    X, y, groups = load(path)
    rows, splits = [], []
    for seed in seeds:
        tr, va, te = split_groups(y, groups, seed)
        splits.append({'seed': seed, 'train': len(tr), 'validation': len(va), 'test': len(te),
                       'test_positive_count': int(y[te].sum()), 'group_intersection_count': 0,
                       'test_row_index_sha256': __import__('hashlib').sha256(te.tobytes()).hexdigest()})
        for name in ('logistic', 'forest'):
            classifier = (LogisticRegression(max_iter=2000, class_weight='balanced', random_state=seed)
                          if name == 'logistic' else RandomForestClassifier(n_estimators=150, min_samples_leaf=2,
                                                                          class_weight='balanced', random_state=seed, n_jobs=2))
            model = make_pipeline(SimpleImputer(strategy='median', add_indicator=True), classifier)
            start = time.perf_counter()
            model.fit(X.iloc[tr], y[tr])
            fit_seconds = time.perf_counter() - start
            threshold = threshold_at_fpr(y[va], model.predict_proba(X.iloc[va])[:, 1])
            if seed == 42 and name == 'forest':
                from .inference import save_artifact
                save_artifact(Path(output) / 'models/phishing.joblib', model, list(X.columns), threshold,
                              'phishing', sha256(path))
            for condition in ('clean', 'missing_page', 'missing_url', 'random_20pct'):
                evaluation = corrupt(X.iloc[te], condition, seed)
                start = time.perf_counter()
                p = model.predict_proba(evaluation)[:, 1]
                inference_seconds = time.perf_counter() - start
                rows.append({'seed': seed, 'model': name, 'condition': condition,
                             'fit_seconds': fit_seconds, 'inference_seconds': inference_seconds,
                             **binary_metrics(y[te], p, threshold)})
    result = {'status': 'historical-engineered-feature benchmark; not multimodal or deployment validation',
              'dataset_sha256': sha256(path), 'rows': len(X), 'unique_feature_groups': len(set(groups)),
              'split_policy': 'identical feature vectors grouped, stratified five-fold partition; no campaign/date metadata',
              'threshold_policy': 'lowest threshold with validation FPR <= 0.01; unchanged during corruption tests',
              'environment': environment(), 'splits': splits, 'experiments': rows}
    write_json(Path(output) / 'phishing.json', result)
    flat = pd.json_normalize(rows)
    flat.to_csv(Path(output) / 'phishing.csv', index=False)
    return result
