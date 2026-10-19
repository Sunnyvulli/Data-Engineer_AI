"""Citation-support triage: lexical baselines evaluated against human labels.
A triage score is NOT a factual verdict or an entailment judgment.
"""
from __future__ import annotations
import json
import re
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from .common import binary_metrics, environment, sha256, split_groups, write_json

STOP = set('the a an is are was were of in on to for and or by with as from that this it its be has have had at'.split())


def tokens(text):
    return set(re.findall(r"[a-z0-9]+", re.sub(r'\[\d+\]', '', text.lower()))) - STOP


def features(sentence):
    claim = sentence.get('text', '')
    citations = sentence.get('citations', [])
    if not isinstance(claim, str) or not isinstance(citations, list):
        raise ValueError('Sentence requires text and a list of citations')
    evidence = ' '.join(c.get('text', '') for c in citations)
    ct, et = tokens(claim), tokens(evidence)
    overlap = len(ct & et) / max(len(ct), 1)
    numbers = set(re.findall(r'\b\d+(?:\.\d+)?\b', re.sub(r'\[\d+\]', '', claim)))
    evidence_numbers = set(re.findall(r'\b\d+(?:\.\d+)?\b', evidence))
    return np.array([overlap, len(citations), len(ct), len(et),
                     len(numbers - evidence_numbers) / max(len(numbers), 1), float(not citations)], dtype=float)


def triage(sentence, threshold=.5):
    f = features(sentence)
    # Explicitly simple deterministic baseline, no factual verification claim.
    risk = max(1 - f[0], f[4], f[5])
    return {'risk': float(risk), 'review_required': bool(risk >= threshold),
            'reasons': [name for name, flag in [('missing_citation', f[5]),
                         ('unmatched_numbers', f[4]), ('low_lexical_coverage', f[0] < .5)] if flag],
            'warning': 'Lexical triage only: high overlap can still conceal contradictions.'}


def load(path):
    data = json.loads(Path(path).read_text())
    rows, labels, groups, domains = [], [], [], []
    for dataset, models in data.items():
        for model, examples in models.items():
            for qid, item in examples.items():
                if qid == 'overall_results':
                    continue
                if 'sentences' not in item:
                    raise ValueError(f'Missing sentences for {dataset}/{model}/{qid}')
                for sentence in item['sentences']:
                    label = sentence.get('sentence_recall_score')
                    if label not in (0, 1):
                        raise ValueError('Human sentence-support label must be 0 or 1')
                    rows.append(features(sentence))
                    labels.append(1 - int(label))  # unsupported is the positive class
                    groups.append(f'{dataset}:{qid}')
                    domains.append(dataset)
    return np.array(rows), np.array(labels), np.array(groups), np.array(domains)


def recall_threshold(y, risk, target=.9):
    """Highest validation threshold retaining at least target unsupported recall."""
    candidates = np.unique(np.r_[0., risk])
    positives = risk[np.asarray(y) == 1]
    if not len(positives):
        raise ValueError('Validation requires unsupported examples')
    return float(max(t for t in candidates if np.mean(positives >= t) >= target))


def policy_metrics(y, risk, threshold):
    flagged = risk >= threshold
    return {**binary_metrics(y, risk, threshold), 'review_fraction': float(flagged.mean()),
            'missed_unsupported': int(np.sum((y == 1) & ~flagged)),
            'unsupported_fraction_among_unflagged': float(np.mean(y[~flagged])) if (~flagged).any() else None}


def run(data, output, seeds=(17, 42, 91)):
    path = Path(data) / 'alce_annotations.json'
    X, y, groups, domains = load(path)
    rows, split_log = [], []
    for seed in seeds:
        tr, va, te = split_groups(y, groups, seed)
        split_log.append({'seed': seed, 'train': len(tr), 'validation': len(va), 'test': len(te),
                          'question_overlap_count': 0})
        model = make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000, class_weight='balanced', random_state=seed))
        model.fit(X[tr], y[tr])
        learned_val = model.predict_proba(X[va])[:, 1]
        learned_test = model.predict_proba(X[te])[:, 1]
        lexical = lambda Z: np.maximum.reduce([1-Z[:, 0], Z[:, 4], Z[:, 5]])
        for name, v, t in [('lexical', lexical(X[va]), lexical(X[te])),
                           ('learned_lexical', learned_val, learned_test)]:
            threshold = recall_threshold(y[va], v)
            if seed == 42 and name == 'learned_lexical':
                from .inference import save_artifact
                save_artifact(Path(output) / 'models/checkpoints.joblib', model, list(range(X.shape[1])),
                              threshold, 'checkpoints', sha256(path))
            rows.append({'seed': seed, 'policy': name, **policy_metrics(y[te], t, threshold)})
            for domain in sorted(set(domains)):
                mask = domains[te] == domain
                rows.append({'seed': seed, 'policy': name, 'domain': domain,
                             **policy_metrics(y[te][mask], t[mask], threshold)})
        rows.append({'seed': seed, 'policy': 'review_all', **policy_metrics(y[te], np.ones(len(te)), 0.5)})
        rows.append({'seed': seed, 'policy': 'review_none', **policy_metrics(y[te], np.zeros(len(te)), 0.5)})
    result = {'status': 'offline support-triage baseline; no educational or factual-verification validation',
              'dataset_sha256': sha256(path), 'n_sentences': len(y), 'n_questions': len(set(groups)),
              'positive_label': 'human sentence_recall_score=0 (not fully supported by cited documents)',
              'threshold_policy': 'validation target unsupported recall >=0.90; test untouched',
              'split_policy': 'all model outputs and sentences for a question stay in the same split',
              'environment': environment(), 'splits': split_log, 'experiments': rows}
    write_json(Path(output) / 'checkpoints.json', result)
    pd.json_normalize(rows).to_csv(Path(output) / 'checkpoints.csv', index=False)
    return result
