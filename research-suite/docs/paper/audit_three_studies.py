"""Reconcile astronomy scores and expose phishing positive-component support.

No fitting, new outcome selection, or raw third-party data required.
"""
from pathlib import Path
import collections
import gzip
import hashlib
import json
import math
import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, roc_auc_score

ROOT = Path(__file__).resolve().parents[2]


def audit():
    result = json.loads((ROOT / 'results/followup/recurrent-comparison.json').read_text())
    checks, inputs = [], []
    ids = []
    for split in ['source', 'independent']:
        path = ROOT / f'results/followup/recurrent-{split}-scores.csv'
        inputs.append(path)
        frame = pd.read_csv(path).sort_values('object_id', kind='stable')
        assert frame.object_id.is_unique
        ids.append(set(frame.object_id))
        y = frame.label.to_numpy()
        for name, column in [('rapid_inspired_gru', 'gru_score'), ('frozen_forest', 'forest_score')]:
            row = next(x for x in result[f'{split}_results'] if x['model'] == name)
            metrics = row['metrics'] if split == 'independent' else row
            budget = row['budget'] if split == 'independent' else row
            score = frame[column].to_numpy()
            for key, value in [('average_precision', average_precision_score(y, score)), ('roc_auc', roc_auc_score(y, score))]:
                assert np.isclose(value, metrics[key], rtol=0, atol=1e-12), (split, name, key)
            selected = np.argsort(-score, kind='stable')[:math.ceil(.05 * len(y))]
            assert len(selected) == budget['selected']
            assert int(y[selected].sum()) == budget['rare_found']
            checks.append(f'{split}/{name}: AP, ROC, top-5% count and positives')
    assert not ids[0] & ids[1]
    path = ROOT / 'results/validation/visual-phishing-scores.json.gz'
    inputs.append(path)
    packed = json.loads(gzip.decompress(path.read_bytes()))
    support = []
    for split in packed['splits']:
        groups = collections.defaultdict(list)
        for group, label in zip(split['groups'], split['labels']):
            groups[group].append(label)
        positives = [dict(group=g, rows=len(y), positives=sum(y)) for g, y in groups.items() if sum(y)]
        support.append(dict(seed=split['seed'], test_rows=len(split['labels']),
                            test_components=len(groups), positive_components=len(positives),
                            positive_component_details=positives))
    report = dict(status='passed', astronomy_checks=checks, source_external_id_overlap=0,
                  phishing_support=support,
                  interpretation='All test positives lie in one component per seed. Conditional bootstrap intervals do not measure generalization across independent phishing components.',
                  scope='Saved-score audit, not a raw-data reproduction, fresh test, or independent peer review.',
                  sha256={str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs})
    (ROOT / 'results/validation/three-study-audit.json').write_text(json.dumps(report, indent=2)+'\n')
    return report


if __name__ == '__main__':
    print(json.dumps(audit(), indent=2))
