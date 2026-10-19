"""Original RAPID-inspired GRU adaptation, not a published-model reproduction.

Conceptual source: Muthukrishna et al. 2019, doi:10.1088/1538-3873/ab1609.
Frozen protocol: docs/followup/RECURRENT_PROTOCOL.md.
"""

from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import resource
import time
import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score
from .common import binary_metrics, environment, sha256, split_groups, write_json
from .followup import cluster_interval, independent_outcome
from .transients import early_features, budget_metrics, validate

GRID = np.arange(13, dtype=float) / 4


def prefix(observations):
    """Cut before any fitted scale, representation or aggregation."""
    validate(observations)
    alerts = (
        observations.loc[observations.detected_bool == 1].groupby("object_id").mjd.min()
    )
    joined = observations.join(alerts.rename("alert"), on="object_id", how="inner")
    result = joined[
        (joined.mjd >= joined.alert) & (joined.mjd <= joined.alert + 3)
    ].copy()
    result["relative_time"] = result.mjd - result.alert
    return result


def fit_scales(allowed_prefix, training_ids):
    selected = allowed_prefix[allowed_prefix.object_id.isin(training_ids)]
    return np.array(
        [
            (
                max(
                    float(
                        np.median(np.abs(selected.loc[selected.passband == b, "flux"]))
                    ),
                    1.0,
                )
                if (selected.passband == b).any()
                else 1.0
            )
            for b in range(6)
        ]
    )


def encode(allowed_prefix, scales):
    """Causal latest-observation grid; missing bands stay zero with mask zero."""
    scales = np.asarray(scales, dtype=float)
    if scales.shape != (6,) or not np.isfinite(scales).all() or (scales < 1).any():
        raise ValueError("Expected six finite training scales >=1")
    ids = np.sort(allowed_prefix.object_id.unique())
    values = np.zeros((len(ids), len(GRID), 18), dtype=np.float32)
    positions = {oid: i for i, oid in enumerate(ids)}
    for (oid, band), group in allowed_prefix.groupby(
        ["object_id", "passband"], sort=True
    ):
        # Same-time observations combine without using observations at another time.
        weight = 1 / group.flux_err.to_numpy() ** 2
        compressed = (
            pd.DataFrame(
                {
                    "t": group.relative_time.to_numpy(),
                    "w": weight,
                    "fw": group.flux.to_numpy() * weight,
                }
            )
            .groupby("t")
            .sum()
            .sort_index()
        )
        times = compressed.index.to_numpy()
        flux = (compressed.fw / compressed.w).to_numpy()
        error = np.sqrt(1 / compressed.w.to_numpy())
        latest = np.searchsorted(times, GRID, side="right") - 1
        available = latest >= 0
        row = positions[oid]
        column = int(band) * 3
        values[row, available, column] = np.arcsinh(
            flux[latest[available]] / scales[int(band)]
        )
        values[row, available, column + 1] = np.log1p(
            error[latest[available]] / scales[int(band)]
        )
        values[row, available, column + 2] = 1
    if not np.isfinite(values).all():
        raise ValueError("Nonfinite recurrent inputs")
    return ids, values


def build_model(tf):
    layers = tf.keras.layers
    return tf.keras.Sequential(
        [
            tf.keras.Input(shape=(13, 18)),
            layers.GRU(100, return_sequences=True),
            layers.BatchNormalization(),
            layers.Dropout(0.2),
            layers.GRU(100),
            layers.BatchNormalization(),
            layers.Dropout(0.2),
            layers.Dense(2, activation="softmax"),
        ]
    )


def score(model, X):
    result = np.concatenate(
        [
            model(X[i : i + 128], training=False).numpy()[:, 1]
            for i in range(0, len(X), 128)
        ]
    )
    if not np.isfinite(result).all() or (result < 0).any() or (result > 1).any():
        raise ValueError("Invalid model probabilities")
    return result


def run(data, output, forest_path, trusted=False, resume=False):
    if not trusted:
        raise ValueError(
            "Explicit trust is required for the original locally trained joblib artifact"
        )
    os.environ.setdefault("TF_ENABLE_ONEDNN_OPTS", "0")
    import tensorflow as tf

    tf.config.threading.set_intra_op_parallelism_threads(4)
    tf.config.threading.set_inter_op_parallelism_threads(1)
    tf.keras.utils.set_random_seed(42)
    tf.config.experimental.enable_op_determinism()
    started = time.monotonic()
    data, output = Path(data), Path(output)
    source = pd.read_csv(data / "plasticc_train_lightcurves.csv.gz")
    metadata = pd.read_csv(data / "plasticc_train_metadata.csv.gz").set_index(
        "object_id"
    )
    allowed = prefix(source)
    ids = np.sort(allowed.object_id.unique())
    y = (metadata.loc[ids].target == 64).astype(int).to_numpy()
    train, validation, test = split_groups(y, ids, 42)
    scales = fit_scales(allowed, ids[train])
    encoded_ids, X = encode(allowed, scales)
    if not np.array_equal(ids, encoded_ids):
        raise ValueError("Source alignment failure")
    forest = joblib.load(forest_path)
    if forest["project"] != "transients" or forest["horizon"] != 3:
        raise ValueError("Expected original three-day forest artifact")
    forest_X = early_features(source, 3).loc[ids, forest["columns"]]
    fp = forest["model"].predict_proba(forest_X.iloc[test])[:, 1]
    previous = json.loads((output.parent / "transients.json").read_text())
    row = next(
        r
        for r in previous["experiments"]
        if r["horizon_days"] == 3 and r["seed"] == 42 and r["model"] == "forest"
    )
    if not np.isclose(
        average_precision_score(y[test], fp),
        row["average_precision"],
        atol=1e-12,
        rtol=0,
    ):
        raise ValueError(
            "Original forest held-out AP does not match; stop before neural training"
        )
    model_path = output.parent / "models" / "rapid-inspired-gru.keras"
    if resume:
        recovery = json.loads((output / "recurrent-recovery.json").read_text())
        if sha256(model_path) != recovery["selected_model_sha256"]:
            raise ValueError("Selected recovery artifact changed")
        for filename, expected in recovery["source_sha256"].items():
            if sha256(data / filename) != expected:
                raise ValueError("Source changed before recovery")
        progress = json.loads((output / "recurrent-training-progress.json").read_text())
        history = progress["history"]
        if len(history) != 25:
            raise ValueError("Recovery requires the complete frozen 25-epoch history")
        winner = max(history, key=lambda r: r["source_validation_ap"])
        best, best_epoch = winner["source_validation_ap"], winner["epoch"]
        if best_epoch != progress["best_epoch_so_far"]:
            raise ValueError("Validation checkpoint selection changed")
        model = tf.keras.models.load_model(model_path, compile=False, safe_mode=True)
        class_weights = len(train) / (2 * np.bincount(y[train], minlength=2))
    else:
        model = build_model(tf)
        model.compile(
            optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
            loss="sparse_categorical_crossentropy",
        )
        counts = np.bincount(y[train], minlength=2)
        class_weights = len(train) / (2 * counts)
        rng = np.random.default_rng(42)
        best = -np.inf
        best_weights = None
        history = []
        best_epoch = None
        for epoch in range(1, 26):
            model.reset_metrics()
            order = rng.permutation(train)
            for start in range(0, len(order), 64):
                batch = order[start : start + 64]
                loss = model.train_on_batch(
                    X[batch], y[batch], sample_weight=class_weights[y[batch]]
                )
            val_p = score(model, X[validation])
            ap = float(average_precision_score(y[validation], val_p))
            history.append(
                {
                    "epoch": epoch,
                    "training_loss": float(loss),
                    "source_validation_ap": ap,
                }
            )
            if ap > best:
                best = ap
                best_weights = model.get_weights()
                best_epoch = epoch
            write_json(
                output / "recurrent-training-progress.json",
                {
                    "status": "training; no new test outcomes inspected",
                    "history": history,
                    "best_epoch_so_far": best_epoch,
                },
            )
            print(f"Epoch {epoch}/25 source validation AP={ap:.6f}", flush=True)
        model.set_weights(best_weights)
        model_path = output.parent / "models" / "rapid-inspired-gru.keras"
        model_path.parent.mkdir(parents=True, exist_ok=True)
        model.save(model_path)
    gp = score(model, X[test])
    source_rows = []
    for name, p in [("rapid_inspired_gru", gp), ("frozen_forest", fp)]:
        source_rows.append(
            {
                "model": name,
                **binary_metrics(y[test], p),
                **budget_metrics(y[test], p),
                "uncertainty": cluster_interval(
                    y[test],
                    p,
                    ids[test],
                    budget=0.05,
                    other_scores=fp if name == "rapid_inspired_gru" else None,
                ),
            }
        )
    pd.DataFrame(
        {"object_id": ids[test], "label": y[test], "gru_score": gp, "forest_score": fp}
    ).to_csv(output / "recurrent-source-scores.csv", index=False)
    # Test data are read only after source-validation model selection is final.
    external = pd.read_csv(data / "plasticc_test_lightcurves_01.csv.gz")
    ext = external[(external.object_id > 53125) & (external.object_id != 342868)].copy()
    del external
    independent_metadata = pd.read_csv(
        data / "plasticc_test_metadata.csv.gz", usecols=["object_id", "true_target"]
    ).set_index("object_id")
    eprefix = prefix(ext)
    eids, EX = encode(eprefix, scales)
    if set(eids) & set(metadata.index):
        raise ValueError("Independent/source ID overlap")
    ey = (independent_metadata.loc[eids].true_target == 64).astype(int).to_numpy()
    efeatures = early_features(ext, 3).loc[eids, forest["columns"]]
    ef = forest["model"].predict_proba(efeatures)[:, 1]
    eg = score(model, EX)
    old_external = json.loads(
        (output / "independent-transients-remainder.json").read_text()
    )
    if len(eids) != old_external["eligible_detected_objects"]:
        raise ValueError("Independent population changed")
    if not np.isclose(
        average_precision_score(ey, ef),
        old_external["metrics"]["average_precision"],
        atol=1e-12,
        rtol=0,
    ):
        raise ValueError("Independent forest AP changed")
    independent_rows = []
    for name, p in [("rapid_inspired_gru", eg), ("frozen_forest", ef)]:
        independent_rows.append(
            {
                "model": name,
                **independent_outcome(ey, p, eids),
                "paired_ap_interval": (
                    cluster_interval(ey, p, eids, other_scores=ef)[
                        "paired_ap_difference_percentile_95"
                    ]
                    if name == "rapid_inspired_gru"
                    else None
                ),
            }
        )
    pd.DataFrame(
        {"object_id": eids, "label": ey, "gru_score": eg, "forest_score": ef}
    ).to_csv(output / "recurrent-independent-scores.csv", index=False)
    result = {
        "status": "completed bounded RAPID-inspired adaptation; not paper/package reproduction or real-event validation",
        "seed": 42,
        "epochs": 25,
        "selected_epoch": best_epoch,
        "selected_validation_ap": best,
        "training_history": history,
        "scales_training_only": scales.tolist(),
        "class_weights": class_weights.tolist(),
        "split": {
            name: {"objects": len(ix), "positives": int(y[ix].sum())}
            for name, ix in [
                ("train", train),
                ("validation", validation),
                ("test", test),
            ]
        },
        "environment": environment(),
        "tensorflow": tf.__version__,
        "keras": tf.keras.__version__,
        "wall_seconds": time.monotonic() - started,
        "wall_time_scope": (
            "recovery evaluation only; original training duration not separately persisted"
            if resume
            else "training and evaluation"
        ),
        "recovered_from_bookkeeping_error": resume,
        "peak_process_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "parameter_count": model.count_params(),
        "local_model_sha256": sha256(model_path),
        "frozen_forest_sha256": sha256(forest_path),
        "source_results": source_rows,
        "independent_results": independent_rows,
        "input_sha256": {
            name: sha256(data / name)
            for name in [
                "plasticc_train_lightcurves.csv.gz",
                "plasticc_train_metadata.csv.gz",
                "plasticc_test_lightcurves_01.csv.gz",
                "plasticc_test_metadata.csv.gz",
            ]
        },
        "limits": [
            "one seed; exposed/reused simulated test outcomes",
            "adapted representation, endpoint binary task and training budget differ from RAPID",
            "neural checkpoint uses source validation; original forest has no such checkpoint selection",
            "same allowed observations and ranking budget, different compressed representations",
            "only two independent target events; no population-level assurance",
            "class-weighted scores are not calibrated probabilities",
        ],
    }
    write_json(output / "recurrent-comparison.json", result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", default="data/raw")
    parser.add_argument("--output", default="results/followup")
    parser.add_argument("--forest", default="results/models/transients-3d.joblib")
    parser.add_argument("--trust-local-model", action="store_true")
    parser.add_argument("--resume-selected-model", action="store_true")
    args = parser.parse_args()
    run(
        args.data,
        args.output,
        args.forest,
        args.trust_local_model,
        args.resume_selected_model,
    )


if __name__ == "__main__":
    main()
