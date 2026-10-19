"""Early kilonova prioritisation using only observations within alert cutoffs."""
from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from .common import binary_metrics, environment, sha256, split_groups, write_json

REQUIRED = {'object_id', 'mjd', 'passband', 'flux', 'flux_err', 'detected_bool'}


def validate(observations):
    if not REQUIRED <= set(observations):
        raise ValueError(f'Missing columns: {sorted(REQUIRED - set(observations))}')
    if not np.isfinite(observations[list(REQUIRED)].to_numpy(dtype=float)).all():
        raise ValueError('Observation values must be finite')
    if (observations.flux_err <= 0).any() or not observations.passband.isin(range(6)).all():
        raise ValueError('Positive uncertainties and passbands 0..5 required')
    if not observations.detected_bool.isin([0, 1]).all():
        raise ValueError('Detection flag must be 0 or 1')


def early_features(observations, horizon):
    validate(observations)
    if horizon < 0:
        raise ValueError('Horizon must be nonnegative')
    first = observations.loc[observations.detected_bool == 1].groupby('object_id').mjd.min()
    eligible = observations.join(first.rename('first_detection'), on='object_id', how='inner')
    # Cut BEFORE aggregation; no peak time, future observation count, truth redshift, or true flux.
    early = eligible[(eligible.mjd >= eligible.first_detection) &
                     (eligible.mjd <= eligible.first_detection + horizon)].copy()
    early['snr'] = early.flux / early.flux_err
    rows = []
    for oid, group in early.groupby('object_id', sort=True):
        record = {'object_id': oid, 'n_observations': len(group),
                  'elapsed': float(group.mjd.max() - group.first_detection.iloc[0]),
                  'n_bands': group.passband.nunique()}
        for band in range(6):
            selected = group[group.passband == band].sort_values('mjd')
            record[f'b{band}_n'] = len(selected)
            for stat in ('mean', 'std', 'min', 'max'):
                record[f'b{band}_{stat}'] = float(getattr(selected.flux, stat)()) if len(selected) > (stat == 'std') else np.nan
            record[f'b{band}_snr'] = float(selected.snr.max()) if len(selected) else np.nan
            record[f'b{band}_slope'] = (float((selected.flux.iloc[-1] - selected.flux.iloc[0]) /
                                             (selected.mjd.iloc[-1] - selected.mjd.iloc[0]))
                                       if len(selected) > 1 and selected.mjd.iloc[-1] > selected.mjd.iloc[0] else np.nan)
        rows.append(record)
    if not rows:
        raise ValueError('No detected objects available')
    return pd.DataFrame(rows).set_index('object_id')


def budget_metrics(y, p, budget=.05):
    if not 0 < budget <= 1:
        raise ValueError('Budget must be in (0,1]')
    k = max(1, int(np.ceil(len(y) * budget)))
    order = np.argsort(-p, kind='stable')[:k]
    tp = int(np.sum(y[order]))
    return {'selected': k, 'rare_found': tp, 'precision_at_budget': tp / k,
            'recall_at_budget': tp / int(np.sum(y)) if np.sum(y) else 0.}


def run(data, output, seeds=(17, 42, 91)):
    data = Path(data)
    observations = pd.read_csv(data / 'plasticc_train_lightcurves.csv.gz')
    metadata = pd.read_csv(data / 'plasticc_train_metadata.csv.gz')
    if metadata.object_id.duplicated().any():
        raise ValueError('Metadata object IDs must be unique')
    rows, split_log = [], []
    for horizon in (1, 3, 7):
        X = early_features(observations, horizon)
        aligned = metadata.set_index('object_id').loc[X.index]
        y = (aligned.target == 64).astype(int).to_numpy()
        # All metadata except object_id and target is deliberately excluded.
        for seed in seeds:
            tr, va, te = split_groups(y, X.index.to_numpy(), seed)
            split_log.append({'horizon_days': horizon, 'seed': seed, 'train': len(tr), 'validation': len(va),
                              'test': len(te), 'test_kilonovae': int(y[te].sum()), 'object_overlap_count': 0})
            for name in ('logistic', 'forest'):
                estimator = (LogisticRegression(max_iter=2000, class_weight='balanced', random_state=seed)
                             if name == 'logistic' else RandomForestClassifier(n_estimators=150, min_samples_leaf=2,
                                                                              class_weight='balanced', random_state=seed, n_jobs=2))
                model = make_pipeline(SimpleImputer(strategy='median', add_indicator=True, keep_empty_features=True),
                                      StandardScaler(), estimator)
                model.fit(X.iloc[tr], y[tr])
                p = model.predict_proba(X.iloc[te])[:, 1]
                rows.append({'horizon_days': horizon, 'seed': seed, 'model': name,
                             **binary_metrics(y[te], p), **budget_metrics(y[te], p)})
                if seed == 42 and name == 'forest':
                    from .inference import save_artifact
                    save_artifact(Path(output) / f'models/transients-{horizon}d.joblib', model, list(X.columns),
                                  .5, 'transients', sha256(data / 'plasticc_train_lightcurves.csv.gz'), horizon=horizon)
                    ranking = pd.DataFrame({'object_id': X.index[te], 'kilonova_score': p,
                                            'heldout_label': y[te]}).sort_values('kilonova_score', ascending=False)
                    Path(output).mkdir(parents=True, exist_ok=True)
                    ranking.to_csv(Path(output) / f'transient-ranking-{horizon}d.csv', index=False)
            # Expected random baseline uses held-out prevalence, no lucky sampled ranking.
            rows.append({'horizon_days': horizon, 'seed': seed, 'model': 'random_expected',
                         'average_precision': float(y[te].mean()), 'precision_at_budget': float(y[te].mean()),
                         'recall_at_budget': max(1, int(np.ceil(len(te)*.05))) / len(te), 'n': len(te)})
    result = {'status': 'simulated PLAsTiCC training-sample benchmark; not live telescope validation',
              'target_class': '64: kilonova', 'environment': environment(),
              'input_sha256': {name: sha256(data / name) for name in ['plasticc_train_metadata.csv.gz', 'plasticc_train_lightcurves.csv.gz']},
              'split_policy': 'object-disjoint train/validation/test; validation reserved, no hyperparameter search',
              'cutoff_policy': 'observations from first detected_bool=1 through first detection+horizon, inclusive',
              'followup_budget': .05, 'n_observations': len(observations), 'n_metadata_objects': len(metadata),
              'splits': split_log, 'experiments': rows}
    write_json(Path(output) / 'transients.json', result)
    pd.json_normalize(rows).to_csv(Path(output) / 'transients.csv', index=False)
    return result
