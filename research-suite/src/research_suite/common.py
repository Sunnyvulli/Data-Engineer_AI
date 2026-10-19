"""Shared validation, audit records, and held-out evaluation."""
from __future__ import annotations
import hashlib
import json
import platform
from pathlib import Path
import numpy as np
import pandas as pd
import sklearn
from sklearn.metrics import average_precision_score, brier_score_loss, confusion_matrix, f1_score, roc_auc_score
from sklearn.model_selection import StratifiedGroupKFold


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')


def environment():
    return {'python': platform.python_version(), 'numpy': np.__version__,
            'pandas': pd.__version__, 'scikit_learn': sklearn.__version__}


def split_groups(y, groups, seed=42):
    """Three disjoint group sets: approx 60% train, 20% validation, 20% test."""
    y, groups = np.asarray(y), np.asarray(groups)
    folds = list(StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=seed).split(np.zeros(len(y)), y, groups))
    test = folds[0][1]
    val = folds[1][1]
    train = np.setdiff1d(np.arange(len(y)), np.concatenate([test, val]))
    for a, b in [(train, val), (train, test), (val, test)]:
        if set(groups[a]) & set(groups[b]):
            raise ValueError('Group leakage')
    for indices in (train, val, test):
        if len(np.unique(y[indices])) < 2:
            raise ValueError('Each split must contain at least two classes; supply more groups')
    return train, val, test


def threshold_at_fpr(y, probabilities, max_fpr=0.01):
    """Choose the lowest threshold meeting an empirical validation FPR budget."""
    y, probabilities = np.asarray(y), np.asarray(probabilities, dtype=float)
    if not 0 <= max_fpr <= 1 or not np.isfinite(probabilities).all():
        raise ValueError('Invalid FPR or scores')
    negatives = probabilities[y == 0]
    if not len(negatives):
        raise ValueError('Validation requires negative examples')
    candidates = np.r_[np.unique(probabilities), np.nextafter(probabilities.max(), np.inf)]
    return float(next(t for t in np.sort(candidates) if np.mean(negatives >= t) <= max_fpr))


def binary_metrics(y, p, threshold=0.5):
    y, p = np.asarray(y, dtype=int), np.asarray(p, dtype=float)
    if set(np.unique(y)) != {0, 1} or not np.isfinite(p).all() or np.any((p < 0) | (p > 1)):
        raise ValueError('Metrics require both binary classes and finite probabilities')
    pred = p >= threshold
    tn, fp, fn, tp = confusion_matrix(y, pred, labels=[0, 1]).ravel()
    return {'n': len(y), 'positives': int(y.sum()), 'average_precision': float(average_precision_score(y, p)),
            'roc_auc': float(roc_auc_score(y, p)), 'brier': float(brier_score_loss(y, p)),
            'f1': float(f1_score(y, pred, zero_division=0)), 'recall': float(tp / (tp + fn)),
            'precision': float(tp / (tp + fp)) if tp + fp else 0.0,
            'false_positive_rate': float(fp / (fp + tn)), 'threshold': threshold,
            'confusion': {'tn': int(tn), 'fp': int(fp), 'fn': int(fn), 'tp': int(tp)}}
