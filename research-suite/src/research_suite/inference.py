"""Batch scoring with locally trained artifacts. Never load untrusted joblib files."""
from pathlib import Path
import json
import joblib
import numpy as np
import pandas as pd
from .common import environment


def save_artifact(path, model, columns, threshold, project, dataset_hash, **extra):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({'model': model, 'columns': columns, 'threshold': threshold, 'project': project,
                 'training_data_sha256': dataset_hash, 'environment': environment(), **extra}, path)


def predict(artifact_path, input_path, output_path, trusted=False):
    if not trusted:
        raise ValueError('Use --trust-local-model only for artifacts you trained; joblib can execute code')
    artifact = joblib.load(artifact_path)
    project = artifact['project']
    if project == 'phishing':
        X = pd.read_csv(input_path)
        if set(X.columns) != set(artifact['columns']):
            raise ValueError('CSV must contain exactly the training feature columns, with no labels')
        X = X[artifact['columns']].astype(float)
        if np.isinf(X.to_numpy()).any() or not X.stack().isin([-1, 0, 1]).all():
            raise ValueError('UCI features must be -1, 0, 1, or missing')
        ids = np.arange(len(X))
    elif project == 'checkpoints':
        from .checkpoints import features
        records = json.loads(Path(input_path).read_text())
        if not isinstance(records, list) or not records:
            raise ValueError('Citation input must be a nonempty JSON list of sentence objects')
        X = np.array([features(r) for r in records])
        ids = np.arange(len(X))
    elif project == 'transients':
        from .transients import early_features
        X = early_features(pd.read_csv(input_path), artifact['horizon'])[artifact['columns']]
        ids = X.index.to_numpy()
    else:
        raise ValueError('Unsupported artifact')
    probabilities = artifact['model'].predict_proba(X)[:, 1]
    frame = pd.DataFrame({'record_id': ids, 'risk_or_priority_score': probabilities,
                          'flag_at_training_threshold': probabilities >= artifact['threshold']})
    if project == 'transients':
        frame = frame.sort_values('risk_or_priority_score', ascending=False)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(output_path, index=False)
    return frame
