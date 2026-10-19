"""Exploratory, precommitted question-budget pilot on exposed support benchmarks."""

import argparse
import json
from pathlib import Path
import time
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import average_precision_score
from .common import split_groups, write_json, environment
from .checkpoints import features, recall_threshold, policy_metrics
from .external_support import load_target
from .followup import alce_transfer_data


def select_groups(X, groups, count, seed, method):
    """No label parameter. Selection uses training inputs and group membership only."""
    names = np.unique(groups)
    if count < 1 or count > len(names):
        raise ValueError("Invalid group budget")
    rng = np.random.default_rng(seed)
    if method == "random":
        return names[rng.permutation(len(names))[:count]]
    if method != "diversity":
        raise ValueError("Unknown selector")
    z = StandardScaler().fit_transform(X)
    means = np.array([z[groups == g].mean(0) for g in names])
    chosen = [int(rng.integers(len(names)))]
    distance = np.full(len(names), np.inf)
    while len(chosen) < count:
        distance = np.minimum(distance, ((means - means[chosen[-1]]) ** 2).sum(1))
        distance[chosen] = -1
        chosen.append(int(np.argmax(distance)))
    return names[chosen]


def run(data, output):
    data = Path(data)
    records, y, groups, meta, selection = load_target(
        data / "ragtruth", data / "alce_annotations.json"
    )
    targetX = np.array([features(r) for r in records])
    X, sy, sg, domains, _ = alce_transfer_data(data / "alce_annotations.json")
    original = json.loads(
        (Path(output).parent / "followup/citation-transfer.json").read_text()
    )
    rows = []
    predictions = []
    for source in ["asqa", "eli5"]:
        ix = np.flatnonzero(domains == source)
        tr, va, unused = split_groups(sy[ix], sg[ix], 42)
        train = ix[np.r_[tr, unused]]
        val = ix[va]
        names = np.unique(sg[train])
        full = None
        for fraction in [0.25, 0.5, 1.0]:
            for method in ["random", "diversity"]:
                for seed in [17, 42, 91]:
                    if fraction == 1.0 and full is not None:
                        rows.append(
                            dict(
                                source=source,
                                fraction=fraction,
                                selector=method,
                                seed=seed,
                                reused_full_policy=full,
                            )
                        )
                        continue
                    start = time.perf_counter()
                    chosen = select_groups(
                        X[train],
                        sg[train],
                        max(2, int(fraction * len(names))),
                        seed,
                        method,
                    )
                    selected = train[np.isin(sg[train], chosen)]
                    row = dict(
                        source=source,
                        fraction=fraction,
                        selector=method,
                        seed=seed,
                        training_questions=len(chosen),
                        training_sentences=len(selected),
                        selected_groups=chosen.tolist(),
                    )
                    if len(np.unique(sy[selected])) < 2:
                        row["status"] = "failed: one selected training label class"
                        rows.append(row)
                        continue
                    model = make_pipeline(
                        StandardScaler(),
                        LogisticRegression(
                            max_iter=2000, class_weight="balanced", random_state=42
                        ),
                    )
                    model.fit(X[selected], sy[selected])
                    cut = recall_threshold(sy[val], model.predict_proba(X[val])[:, 1])
                    p = model.predict_proba(targetX)[:, 1]
                    row.update(
                        status="completed",
                        **policy_metrics(y, p, cut),
                        selection_fit_score_seconds=time.perf_counter() - start,
                    )
                    if fraction == 1.0:
                        prior = next(
                            r
                            for r in original["experiments"]
                            if r["source"] == source
                            and r["policy"] == "learned_lexical"
                        )
                        other = np.flatnonzero(domains != source)
                        if not np.isclose(
                            cut, prior["threshold"], rtol=0, atol=1e-12
                        ) or not np.isclose(
                            average_precision_score(
                                sy[other], model.predict_proba(X[other])[:, 1]
                            ),
                            prior["average_precision"],
                            rtol=0,
                            atol=1e-12,
                        ):
                            raise ValueError("Full-data reproduction failed")
                        full = f"{source}/full"
                    key = f"{source}/{fraction}/{method}/{seed}"
                    row["prediction_key"] = key
                    rows.append(row)
                    predictions.append(dict(key=key, risk=p.tolist()))
    write_json(
        Path(output) / "data-selection-scores.json",
        dict(
            ids=[m["id"] for m in meta],
            groups=groups.tolist(),
            labels=y.tolist(),
            predictions=predictions,
        ),
    )
    result = dict(
        status="completed exploratory pilot on previously exposed target; not untouched confirmation or novel coreset algorithm",
        environment=environment(),
        selection=selection,
        settings=rows,
        limits=[
            "question budgets differ in sentence/annotation costs",
            "target outcomes had been exposed before this protocol",
            "six lexical features only; not a general deep-learning coreset comparison",
            "three selector seeds do not establish statistical significance",
            "source-only calibration does not guarantee target recall",
            "additional independent validation required before final scientific claims",
        ],
    )
    write_json(Path(output) / "data-selection.json", result)
    return result


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--data", default="data/raw")
    p.add_argument("--output", default="results/validation")
    a = p.parse_args()
    run(a.data, a.output)
