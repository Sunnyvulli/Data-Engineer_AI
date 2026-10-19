"""Bounded CPU NLI comparator. Protocol: docs/followup/NLI_PROTOCOL.md.

Optional ONNX/tokenizers dependencies are imported only for actual inference.
Pretrained model credit: cross-encoder authors; no new model training claimed.
"""

from __future__ import annotations
import argparse
import hashlib
import json
import re
import resource
import time
from pathlib import Path
import urllib.request
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from .common import environment, sha256, split_groups, write_json
from .checkpoints import recall_threshold, policy_metrics
from .followup import alce_transfer_data, cluster_interval

MODEL = "cross-encoder/nli-deberta-v3-small"
REVISION = "fa2804872c3b4bd748f38c0185cc85775361e735"
FILES = {
    "README.md": "a9aa108025ad1984374c5e80365406bafe331aea5abc30239e1796ec0a7c267d",
    "config.json": "885d0dceae8fa5c136da9209121ec9eb11160488e840de3bc1f29353674e5712",
    "tokenizer.json": "5124ef2ead1a10a717703bc436de7f353da76d6340e4587719b42b1693707964",
    "tokenizer_config.json": "f3eecd07c370ef0bf7dd3780d3cd68cf9c8b00c267e21a208ddcd8f82bfec1a6",
    "special_tokens_map.json": "ed7c099c988dbb414b18a6980d20cb57b91b7cd119f6f6941eb364b0e892e712",
    "onnx/model.onnx": "59fd8dd78926e15907ab419303179e4196bdedd710e888773e2f0143fe430897",
}


def fetch_model(directory):
    """Immutable official artifacts only; atomic checked downloads; no remote code."""
    directory = Path(directory)
    for name, expected in FILES.items():
        path = directory / name
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists() and sha256(path) == expected:
            continue
        temporary = path.with_suffix(path.suffix + ".part")
        urllib.request.urlretrieve(
            f"https://huggingface.co/{MODEL}/resolve/{REVISION}/{name}", temporary
        )
        if sha256(temporary) != expected:
            raise ValueError(f"Hash mismatch: {name}")
        temporary.replace(path)
    return directory


def input_pair(sentence):
    """Strict allowlist: annotation scores never enter NLI input."""
    claim = re.sub(r"\[\d+\]", "", sentence["text"]).strip()
    evidence = "\n\n".join(
        (c.get("title", "") + "\n" + c.get("text", "")).strip()
        for c in sentence.get("citations", [])
    )
    return evidence, claim


def sentences(path):
    result = []
    for domain, models in json.loads(Path(path).read_text()).items():
        for model, examples in models.items():
            for qid, item in examples.items():
                if qid != "overall_results":
                    result.extend(input_pair(s) for s in item["sentences"])
    return result


def unsupported_risk(logits):
    logits = np.asarray(logits, dtype=float)
    if logits.ndim != 2 or logits.shape[1] != 3 or not np.isfinite(logits).all():
        raise ValueError("Expected finite contradiction/entailment/neutral logits")
    exponent = np.exp(logits - logits.max(axis=1, keepdims=True))
    return 1 - exponent[:, 1] / exponent.sum(axis=1)


def infer(pairs, model_directory, batch_size=4):
    import onnxruntime as ort
    from tokenizers import Tokenizer

    directory = Path(model_directory)
    for name, expected in FILES.items():
        if sha256(directory / name) != expected:
            raise ValueError(f"Hash mismatch: {name}")
    config = json.loads((directory / "config.json").read_text())
    if config["id2label"] != {"0": "contradiction", "1": "entailment", "2": "neutral"}:
        raise ValueError("Unrecognized model label order")
    tokenizer = Tokenizer.from_file(str(directory / "tokenizer.json"))
    tokenizer.no_truncation()
    tokenizer.no_padding()
    options = ort.SessionOptions()
    options.intra_op_num_threads = 4
    session = ort.InferenceSession(
        str(directory / "onnx/model.onnx"),
        sess_options=options,
        providers=["CPUExecutionProvider"],
    )
    risks = np.ones(len(pairs))
    audit = []
    pending = []

    def flush():
        if not pending:
            return
        length = max(len(enc.ids) for _, enc in pending)
        ids = np.zeros((len(pending), length), dtype=np.int64)
        mask = np.zeros_like(ids)
        for row, (_, enc) in enumerate(pending):
            ids[row, : len(enc.ids)] = enc.ids
            mask[row, : len(enc.ids)] = enc.attention_mask
        output = session.run(["logits"], {"input_ids": ids, "attention_mask": mask})[0]
        for (idx, _), risk in zip(pending, unsupported_risk(output)):
            risks[idx] = risk
        pending.clear()

    for idx, (evidence, original_claim) in enumerate(pairs):
        tokenizer.no_truncation()
        claim_ids = tokenizer.encode(original_claim, add_special_tokens=False).ids
        evidence_count = len(tokenizer.encode(evidence, add_special_tokens=False).ids)
        claim = (
            tokenizer.decode(claim_ids[:120])
            if len(claim_ids) > 120
            else original_claim
        )
        retained_claim_count = len(
            tokenizer.encode(claim, add_special_tokens=False).ids
        )
        if retained_claim_count > 120:
            raise ValueError("Decoded claim exceeds frozen token cap")
        truncated = evidence_count + retained_claim_count + 3 > 512
        tokenizer.enable_truncation(
            max_length=512, strategy="only_first", direction="right"
        )
        enc = tokenizer.encode(evidence, claim)
        audit.append(
            {
                "row": idx,
                "evidence_tokens_original": evidence_count,
                "claim_tokens_original": len(claim_ids),
                "claim_truncated": len(claim_ids) > 120,
                "evidence_truncated": truncated,
                "input_tokens": len(enc.ids),
                "missing_evidence": not bool(evidence.strip()),
            }
        )
        if evidence.strip():
            pending.append((idx, enc))
        if len(pending) == batch_size:
            flush()
        if (idx + 1) % 100 == 0:
            print(f"Prepared {idx+1}/{len(pairs)} pairs", flush=True)
    flush()
    return (
        risks,
        audit,
        {
            "onnxruntime": ort.__version__,
            "tokenizers": __import__("tokenizers").__version__,
            "providers": session.get_providers(),
            "intra_op_threads": 4,
            "batch_size": batch_size,
        },
    )


def compare(data, output, model_directory):
    started = time.monotonic()
    path = Path(data) / "alce_annotations.json"
    pairs = sentences(path)
    risks, audit, runtime = infer(pairs, model_directory)
    # Persist completed inference before metric computation, allowing deterministic recovery.
    write_json(
        Path(output) / "nli-scores.json",
        {
            "input_sha256": sha256(path),
            "model": MODEL,
            "revision": REVISION,
            "risk": risks.tolist(),
            "context_audit": audit,
        },
    )
    X, y, groups, domains, _ = alce_transfer_data(path)
    if len(risks) != len(y):
        raise ValueError("Score/annotation alignment failure")
    rows, splits = [], []
    for source, target in [("asqa", "eli5"), ("eli5", "asqa")]:
        source_idx = np.flatnonzero(domains == source)
        test = np.flatnonzero(domains == target)
        tr0, va0, unused = split_groups(y[source_idx], groups[source_idx], 42)
        train = source_idx[np.r_[tr0, unused]]
        validation = source_idx[va0]
        lexical = make_pipeline(
            StandardScaler(),
            LogisticRegression(max_iter=2000, class_weight="balanced", random_state=42),
        )
        lexical.fit(X[train], y[train])
        lp = lexical.predict_proba(X[test])[:, 1]
        lt = recall_threshold(y[validation], lexical.predict_proba(X[validation])[:, 1])
        nt = recall_threshold(y[validation], risks[validation])
        splits.append(
            {
                "source": source,
                "target": target,
                "train": len(train),
                "validation": len(validation),
                "test": len(test),
                "question_overlap": len(set(groups[validation]) & set(groups[test])),
            }
        )
        for name, score, cutoff in [
            ("open_nli", risks[test], nt),
            ("learned_lexical", lp, lt),
            ("nli_default", risks[test], 0.5),
            ("review_all", np.ones(len(test)), 0.5),
            ("review_none", np.zeros(len(test)), 0.5),
        ]:
            rows.append(
                {
                    "source": source,
                    "target": target,
                    "policy": name,
                    **policy_metrics(y[test], score, cutoff),
                    "uncertainty": cluster_interval(
                        y[test],
                        score,
                        groups[test],
                        cutoff,
                        other_scores=lp if name == "open_nli" else None,
                    ),
                }
            )
    result = {
        "status": "completed bounded NLI comparison on previously exposed ALCE benchmark",
        "model": MODEL,
        "revision": REVISION,
        "declared_license": "Apache-2.0",
        "model_sha256": FILES,
        "input_sha256": sha256(path),
        "environment": environment(),
        "runtime": runtime,
        "wall_seconds": time.monotonic() - started,
        "peak_process_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "context": {
            "rows": len(audit),
            "evidence_truncated": sum(a["evidence_truncated"] for a in audit),
            "claim_truncated": sum(a["claim_truncated"] for a in audit),
            "missing_evidence": sum(a["missing_evidence"] for a in audit),
        },
        "splits": splits,
        "experiments": rows,
        "limits": [
            "512-token first context can discard support; human labels use complete evidence",
            "benchmark reuse; no new blind holdout; pretrained contamination not excluded",
            "not an original ALCE evaluator reproduction or a factual truth test",
            "conditional question bootstrap does not cover collection bias or model selection",
        ],
    }
    write_json(Path(output) / "nli-comparison.json", result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["fetch", "run"])
    parser.add_argument("--model-directory", default="data/models/nli-deberta-v3-small")
    parser.add_argument("--data", default="data/raw")
    parser.add_argument("--output", default="results/followup")
    args = parser.parse_args()
    if args.action == "fetch":
        fetch_model(args.model_directory)
    else:
        compare(args.data, args.output, args.model_directory)


if __name__ == "__main__":
    main()
