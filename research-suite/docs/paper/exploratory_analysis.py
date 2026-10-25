"""Execute the immutable exposed-target plan; never a confirmation study."""
from pathlib import Path
import argparse
import gzip
import hashlib
import importlib.metadata
import json
import subprocess
import warnings
import numpy as np
from scipy.stats import rankdata
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import KFold
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / "results/validation"
SEED, REPEATS = 20261025, 5000
PLAN_COMMIT = "9002e048b42cec344165f8f8e4fe94f59a0e8bd6"
INPUTS = {
    "external-support-scores.json": "793cc7f33161783a4fab6324e7fbeca3415f627d6b976fbfba106122874b1526",
    "ragtruth-coverage-risks.json": "d04c1bd89769f12833a99591a5729579ef72e678d5c47839ba57c059f9f928d3",
    "review-diagnostics.json": "54348715337cc8af4f3caeaa2b85c3de5b662e78bb288c02d338cdfb8cb4c84a",
}


def metrics(y, score):
    """Tie-aware sklearn AP and pair-count AUC definitions, without call overhead."""
    y, score = np.asarray(y), np.asarray(score)
    positives = y.sum()
    if not 0 < positives < len(y):
        return np.full(2, np.nan)
    order = np.argsort(-score, kind="stable")
    sy, ss = y[order], score[order]
    ends = np.r_[np.flatnonzero(np.diff(ss)), len(sy)-1]
    tp = np.cumsum(sy)[ends]
    fp = ends + 1 - tp
    increments = np.diff(np.r_[0, tp])
    ap = np.sum(increments * tp / (ends+1)) / positives
    auc = np.sum(increments * (len(y)-positives - fp + .5*np.diff(np.r_[0, fp])))
    auc /= positives * (len(y)-positives)
    return np.array([ap, auc])


def ranks(values, generators):
    out = np.empty(len(values))
    for name in np.unique(generators):
        mask = generators == name
        out[mask] = rankdata(values[mask], method="average") / mask.sum()
    return out


def folds_for(groups):
    unique = np.unique(groups)
    folds = np.full(len(groups), -1)
    for fold, (_, test) in enumerate(KFold(5, shuffle=True, random_state=SEED).split(unique)):
        folds[np.isin(groups, unique[test])] = fold
    assert (folds >= 0).all()
    return folds


def fit_fold(length, nli, gen, y, folds, fold, augmented):
    train, test = folds != fold, folds == fold
    categories = sorted(set(gen))
    continuous = np.column_stack([np.log1p(length), nli]) if augmented else np.log1p(length)[:, None]
    scaler = StandardScaler().fit(continuous[train])
    indicators = np.column_stack([gen == g for g in categories[1:]])
    x = np.column_stack([scaler.transform(continuous), indicators])
    model = LogisticRegression(C=1., penalty="l2", solver="lbfgs", class_weight=None,
                               tol=1e-8, max_iter=10000, fit_intercept=True)
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=FutureWarning, message=".*penalty.*deprecated.*")
        warnings.simplefilter("error", ConvergenceWarning)
        model.fit(x[train], y[train])
    if max(model.n_iter_) >= 10000:
        raise RuntimeError("Fit did not converge; no parameter adjustment allowed")
    return model.predict_proba(x[test])[:, 1], {
        "fold": fold, "n_train": int(train.sum()), "n_test": int(test.sum()),
        "categories": categories, "scaler_mean": scaler.mean_.tolist(),
        "scaler_scale": scaler.scale_.tolist(), "coefficient": model.coef_[0].tolist(),
        "intercept": float(model.intercept_[0]), "iterations": int(model.n_iter_[0]),
    }


def crossfit(length, nli, gen, y, groups, folds):
    out, fits = {}, {}
    for name, augmented in [("M0", False), ("M1", True)]:
        p = np.full(len(y), np.nan)
        fits[name] = []
        for fold in range(5):
            test = folds == fold
            assert not set(groups[test]) & set(groups[~test])
            p[test], detail = fit_fold(length, nli, gen, y, folds, fold, augmented)
            changed = y.copy()
            changed[test] = 1 - changed[test]
            p_changed, _ = fit_fold(length, nli, gen, changed, folds, fold, augmented)
            assert np.array_equal(p[test], p_changed), "Held-out-label leakage"
            fits[name].append(detail)
        assert np.isfinite(p).all()
        out[name] = p
    return out, fits


def contrasts(y, length, nli, gen, probabilities):
    names = sorted(set(gen))
    result = {
        "raw_length_minus_coverage": metrics(y, length) - metrics(y, nli),
        "rank_length_minus_coverage": metrics(y, ranks(length, gen)) - metrics(y, ranks(nli, gen)),
        "increment_M1_minus_M0": metrics(y, probabilities["M1"]) - metrics(y, probabilities["M0"]),
    }
    bygen = []
    for name in names:
        mask = gen == name
        value = metrics(y[mask], length[mask]) - metrics(y[mask], nli[mask])
        result["generator/" + name] = value
        bygen.append(value)
    result["macro_length_minus_coverage"] = np.mean(bygen, axis=0)
    return result


def summarize(observed, samples):
    result = {}
    for name, point in observed.items():
        data = np.array(samples[name], dtype=float)
        valid = np.isfinite(data).all(axis=1)
        count = int(valid.sum())
        ci = np.quantile(data[valid], [.025, .975], axis=0, method="linear") if count >= 1000 else None
        result[name] = {
            "ap_difference": float(point[0]) if np.isfinite(point[0]) else None,
            "auc_difference": float(point[1]) if np.isfinite(point[1]) else None,
            "ap_ci95": ci[:, 0].tolist() if ci is not None else None,
            "auc_ci95": ci[:, 1].tolist() if ci is not None else None,
            "valid_draws": count, "invalid_draws": len(data)-count,
        }
    return result


def load_inputs():
    for name, expected in INPUTS.items():
        assert hashlib.sha256((D/name).read_bytes()).hexdigest() == expected, name
    s = json.loads((D/"external-support-scores.json").read_text())
    cache = json.loads((D/"ragtruth-coverage-risks.json").read_text())
    diag = json.loads((D/"review-diagnostics.json").read_text())
    y = np.array(s["labels"])
    length = np.array([row["claim_tokens"] for row in cache["audit"]])
    gen = np.array([row["generator"] for row in s["records"]])
    groups = np.array([row["source_id"] for row in s["records"]])
    nli = np.array(s["coverage_nli"])
    assert len(y) == len(length) == len(gen) == len(groups) == len(nli) == 900
    assert len(np.unique(groups)) == 150 and y.sum() == 160 and len(set(gen)) == 6
    assert np.array_equal(nli, cache["risk"])
    assert len({r["id"] for r in s["records"]}) == 900
    for i, row in enumerate(s["records"]):
        assert all(row[k] == diag["rows"][i][k] for k in ["id", "source_id"])
        assert length[i] == diag["rows"][i]["answer_tokens"]
    for g in set(groups):
        assert len(set(gen[groups == g])) == 6 and (groups == g).sum() == 6
    return s, y, length, gen, groups, nli


def run():
    s, y, length, gen, groups, nli = load_inputs()
    unique = np.unique(groups)
    folds = folds_for(groups)
    draws = np.random.default_rng(SEED).integers(0, len(unique), size=(REPEATS, len(unique)))
    report = {
        "status": "exploratory_exposed_target", "plan_commit": PLAN_COMMIT,
        "plan_sha256": hashlib.sha256((ROOT/"docs/paper/EXPLORATORY_ANALYSIS_PLAN.md").read_bytes()).hexdigest(),
        "code_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "inputs_sha256": INPUTS, "seed": SEED, "requested_draws": REPEATS,
        "packages": {p: importlib.metadata.version(p) for p in ["numpy", "scipy", "scikit-learn"]},
        "limitations": ["exposed target; exploratory uncorrected intervals", "fixed OOF prediction intervals omit training and fold uncertainty", "sparse-stratum intervals conditional on valid draws", "passing tests cannot validate statistical conclusions", "not equivalence, causal inference or general superiority"],
        "populations": {},
    }
    packed = {"group_ids": unique.tolist(), "draw_indices": draws.tolist(), "populations": {}}
    for pop, mask in [("all_generators", np.ones(len(y), dtype=bool)), ("without_gpt4", gen != "gpt-4-0613")]:
        py, pl, pn, pg, pq, pf = [x[mask] for x in (y, length, nli, gen, groups, folds)]
        probabilities, fits = crossfit(pl, pn, pg, py, pq, pf)
        observed = contrasts(py, pl, pn, pg, probabilities)
        samples = {name: [] for name in observed}
        clusters = [np.flatnonzero(pq == g) for g in unique]
        for i, draw in enumerate(draws):
            ix = np.concatenate([clusters[j] for j in draw])
            values = contrasts(py[ix], pl[ix], pn[ix], pg[ix], {k:v[ix] for k,v in probabilities.items()})
            for name in samples:
                samples[name].append(values[name].tolist())
            if (i+1) % 1000 == 0:
                print(pop, i+1, flush=True)
        report["populations"][pop] = {
            "n": len(py), "positives": int(py.sum()), "contrasts": summarize(observed, samples),
            "model_metrics": {k: dict(zip(["ap", "auc"], metrics(py, v).tolist())) for k,v in probabilities.items()},
            "fits": fits,
        }
        packed["populations"][pop] = {
            "rows": [{"id": row["id"], "source_id": row["source_id"], "generator": row["generator"], "label": int(label),
                      "length": int(l), "nli": float(n), "fold": int(f), "M0": float(p0), "M1": float(p1)}
                     for row,label,l,n,f,p0,p1 in zip(np.array(s["records"],dtype=object)[mask],py,pl,pn,pf,probabilities["M0"],probabilities["M1"])],
            "bootstrap_contrasts": samples,
        }
    (D/"exploratory-analysis.json").write_text(json.dumps(report, indent=2, allow_nan=False)+"\n")
    # NaNs represent explicitly invalid draws in the compact archive as JSON null.
    def clean(obj):
        if isinstance(obj, float) and not np.isfinite(obj): return None
        if isinstance(obj, list): return [clean(x) for x in obj]
        if isinstance(obj, dict): return {k:clean(v) for k,v in obj.items()}
        return obj
    (D/"exploratory-analysis-resamples.json.gz").write_bytes(gzip.compress(json.dumps(clean(packed),separators=(",",":"),allow_nan=False).encode(), mtime=0))
    print("Saved every planned contrast and both populations", flush=True)


if __name__ == "__main__":
    run()
