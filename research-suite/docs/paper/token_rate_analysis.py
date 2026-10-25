"""Bounded character-span-to-token descriptive extension, with no causal verdict."""
from pathlib import Path
import argparse
import gzip
import hashlib
import importlib.metadata
import json
import warnings
import numpy as np
import statsmodels.api as sm
from statsmodels.tools.sm_exceptions import PerfectSeparationWarning
from tokenizers import Tokenizer
from exploratory_analysis import ROOT, D, load_inputs, summarize

TOKEN_HASH = "5124ef2ead1a10a717703bc436de7f353da76d6340e4587719b42b1693707964"
RAW_HASH = "e4c2e4ac24fff676d8984cc61c35d791612fadc58015335d97dd632375e18073"


def union_spans(spans):
    merged = []
    for lo, hi in sorted(spans):
        if merged and lo <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], hi)
        else:
            merged.append([lo, hi])
    return merged


def annotated_count(offsets, spans):
    merged = union_spans(spans)
    return sum(any(lo < right and hi > left for left, right in merged) for lo, hi in offsets if hi > lo)


def design(length, generators, categories):
    indicator = np.column_stack([generators == g for g in categories]).astype(float)
    return np.column_stack([indicator, indicator*np.log1p(length)[:, None]])


def fit_rate(length, count, gen, categories, locations):
    x = design(length, gen, categories)
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", PerfectSeparationWarning)
            fit = sm.GLM(count/length, x, family=sm.families.Binomial(), var_weights=length).fit(
                method="IRLS", maxiter=100, tol=1e-8, start_params=np.zeros(x.shape[1]), wls_method="lstsq")
        if not fit.converged or not np.isfinite(fit.params).all():
            return None, "nonconvergence_or_nonfinite"
        n = len(categories)
        values = {}
        for i, g in enumerate(categories):
            px = design(np.array(locations[g]), np.array([g]*3), categories)
            values[g] = [float(fit.params[n+i]), *fit.predict(px).tolist()]
        return values, None
    except Exception as exc:
        return None, type(exc).__name__


def run(raw, tokenizer_path):
    s, y, lengths, gen, groups, _ = load_inputs()
    assert hashlib.sha256(raw.read_bytes()).hexdigest() == RAW_HASH
    assert hashlib.sha256(tokenizer_path.read_bytes()).hexdigest() == TOKEN_HASH
    token = Tokenizer.from_file(str(tokenizer_path))
    token.no_padding(); token.no_truncation()
    records = {str(r["id"]):r for r in map(json.loads,raw.read_text().splitlines())}
    counts, spans_seen = [], 0
    for i, metadata in enumerate(s["records"]):
        row = records[metadata["id"]]
        assert str(row["source_id"]) == metadata["source_id"] and row["model"] == gen[i]
        assert bool(row["labels"]) == bool(y[i])
        text = row["response"]
        spans = []
        for label in row["labels"]:
            start, end = label["start"], label["end"]
            assert 0 <= start < end <= len(text), "Invalid annotation character bounds"
            assert text[start:end] == label["text"], "Span text does not match character offsets"
            spans.append((start,end)); spans_seen += 1
        encoded = token.encode(text, add_special_tokens=False)
        assert len(encoded.ids) == lengths[i], "Cached-token length mismatch; block extension"
        assert all(0 <= lo <= hi <= len(text) for lo,hi in encoded.offsets)
        counts.append(annotated_count(encoded.offsets, spans))
    counts = np.array(counts)
    nonempty = lengths > 0
    report = {"status":"exploratory_exposed_target_bounded_annotation_check",
              "amendment_commit":"d57efc0d87aacccd22ee1d51c7edb2118f69b994",
              "raw_sha256": RAW_HASH, "tokenizer_sha256":TOKEN_HASH,
              "script_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "packages":{p:importlib.metadata.version(p) for p in ["numpy","scipy","statsmodels","patsy","tokenizers"]},
              "span_offset_validation":"every retained annotation exactly equals its Unicode [start,end) answer slice",
              "cached_length_mismatches":0,"zero_token_answers":int((~nonempty).sum()),
              "validated_annotation_spans":spans_seen,"generators":{},
              "limitations":["annotation boundaries and guidelines may vary by generator", "flat or rising rates do not settle causal exposure, semantic quality or per-claim errors", "tokens are not treated as independent observations for uncertainty"]}
    categories = sorted(set(gen))
    locations = {g:np.quantile(lengths[(gen==g)&nonempty],[.25,.5,.75],method="linear").tolist() for g in categories}
    for g in categories:
        ix=(gen==g)&nonempty
        report["generators"][g]={"n":int((gen==g).sum()),"nonempty":int(ix.sum()),
            "annotated_tokens":int(counts[ix].sum()),"answer_tokens":int(lengths[ix].sum()),
            "ratio_of_totals":float(counts[ix].sum()/lengths[ix].sum()),
            "mean_answer_fraction":float(np.mean(counts[ix]/lengths[ix])),
            "length_min_median_max":[int(lengths[ix].min()),float(np.median(lengths[ix])),int(lengths[ix].max())],
            "length_quartiles":locations[g]}
    archive=json.loads(gzip.decompress((D/"exploratory-analysis-resamples.json.gz").read_bytes()))
    unique=np.array(archive["group_ids"])
    draws=np.array(archive["draw_indices"])
    estimates, failure = fit_rate(lengths[nonempty],counts[nonempty],gen[nonempty],categories,locations)
    failures={}; samples={g:[] for g in categories}
    clusters=[np.flatnonzero((groups==g)&nonempty) for g in unique]
    for i,draw in enumerate(draws):
        ix=np.concatenate([clusters[j] for j in draw])
        value, why=fit_rate(lengths[ix],counts[ix],gen[ix],categories,locations)
        if why: failures[why]=failures.get(why,0)+1
        for g in categories: samples[g].append(value[g] if value is not None else [None]*4)
        if (i+1)%1000==0: print("token_rate",i+1,flush=True)
    report["point_fit_failure"]=failure
    report["bootstrap_failure_counts"]=failures
    report["requested_draws"]=len(draws)
    for g in categories:
        data=np.array(samples[g],dtype=float);valid=np.isfinite(data).all(axis=1);count=int(valid.sum())
        ci=np.quantile(data[valid],[.025,.975],axis=0,method="linear").tolist() if count>=1000 else None
        report["generators"][g].update({"slope_and_predicted_fractions":estimates[g] if estimates else None,
            "ci95_columns_slope_p25_p50_p75":ci,"valid_draws":count,"invalid_draws":len(draws)-count})
    report["rows"]=[{"id":r["id"],"source_id":r["source_id"],"generator":r["generator"],
                    "answer_tokens":int(n),"annotated_tokens":int(k)} for r,n,k in zip(s["records"],lengths,counts)]
    (D/"token-rate-analysis.json").write_text(json.dumps(report,indent=2,allow_nan=False)+"\n")
    (D/"token-rate-resamples.json.gz").write_bytes(gzip.compress(json.dumps(samples,separators=(",",":"),allow_nan=False).encode(),mtime=0))
    print("Saved bounded token-rate extension",flush=True)


if __name__ == "__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--responses",type=Path,required=True)
    parser.add_argument("--tokenizer",type=Path,required=True)
    args=parser.parse_args()
    run(args.responses,args.tokenizer)
