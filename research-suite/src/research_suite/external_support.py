"""Frozen independent RAGTruth QA validation, with explicit answer-level labels.

No target training/tuning. RAGTruth/MS MARCO texts stay local; see protocol.
"""

from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import time
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import average_precision_score
from .common import sha256, split_groups, write_json, environment
from .checkpoints import features, recall_threshold, policy_metrics
from .followup import alce_transfer_data
from .entailment import FILES, MODEL, REVISION, infer, input_pair, unsupported_risk

RAG_HASHES = {
    "dataset_source_info.jsonl": "0dffc26ea9f3c1c3d7c7e8336b56ef1646e3cec876edffcca3c9c624d12d578b",
    "dataset_response.jsonl": "e4c2e4ac24fff676d8984cc61c35d791612fadc58015335d97dd632375e18073",
}


def normalize_question(text):
    return " ".join(text.lower().split())


def target_record(source, response):
    """Strict allowlist: model input never contains annotations/prompt/generator."""
    info = source["source_info"]
    if source["task_type"] != "QA" or not isinstance(info, dict):
        raise ValueError("QA source required")
    if not isinstance(info["passages"], str) or not isinstance(
        response["response"], str
    ):
        raise ValueError("Expected source and response text")
    return {
        "text": response["response"],
        "citations": [{"title": "", "text": info["passages"]}],
    }


def load_target(directory, alce_path):
    directory = Path(directory)
    for file, expected in RAG_HASHES.items():
        if sha256(directory / file) != expected:
            raise ValueError("RAGTruth hash mismatch: " + file)
    alce = json.loads(Path(alce_path).read_text())
    known = set()
    for models in alce.values():
        for items in models.values():
            for qid, item in items.items():
                if qid != "overall_results":
                    known.add(normalize_question(item["question"]))
    sources = {
        r["source_id"]: r
        for r in map(
            json.loads,
            (directory / "dataset_source_info.jsonl").read_text().splitlines(),
        )
    }
    records, labels, groups, metadata = [], [], [], []
    excluded = set()
    eligible = 0
    for response in map(
        json.loads, (directory / "dataset_response.jsonl").read_text().splitlines()
    ):
        source = sources[response["source_id"]]
        if response["split"] != "test" or source["task_type"] != "QA":
            continue
        eligible += 1
        if normalize_question(source["source_info"]["question"]) in known:
            excluded.add(source["source_id"])
            continue
        records.append(target_record(source, response))
        labels.append(int(bool(response["labels"])))
        groups.append(source["source_id"])
        metadata.append(
            {
                "id": response["id"],
                "source_id": source["source_id"],
                "generator": response["model"],
                "quality": response["quality"],
            }
        )
    if not records or len(np.unique(labels)) != 2:
        raise ValueError("Target requires both annotated classes")
    return (
        records,
        np.array(labels),
        np.array(groups),
        metadata,
        {
            "eligible_test_qa_responses": eligible,
            "exact_alce_question_groups_excluded": len(excluded),
            "retained_responses": len(records),
            "retained_source_groups": len(set(groups)),
        },
    )


def window_ranges(length, width, stride):
    if width <= 0 or stride <= 0 or stride > width or length < 0:
        raise ValueError("Invalid covering window configuration")
    if length <= width:
        return [(0, length)]
    starts = list(range(0, length - width + 1, stride))
    if starts[-1] + width < length:
        starts.append(length - width)
    return [(start, min(start + width, length)) for start in starts]


class CoverageNLI:
    def __init__(self, directory):
        import onnxruntime as ort
        from tokenizers import Tokenizer

        directory = Path(directory)
        for file, expected in FILES.items():
            if sha256(directory / file) != expected:
                raise ValueError("Model hash mismatch")
        self.tokenizer = Tokenizer.from_file(str(directory / "tokenizer.json"))
        self.tokenizer.no_truncation()
        self.tokenizer.no_padding()
        options = ort.SessionOptions()
        options.intra_op_num_threads = 4
        self.session = ort.InferenceSession(
            str(directory / "onnx/model.onnx"),
            sess_options=options,
            providers=["CPUExecutionProvider"],
        )

    def one(self, evidence, claim):
        t = self.tokenizer
        t.no_truncation()
        evidence_ids = t.encode(evidence, add_special_tokens=False).ids
        claim_ids = t.encode(claim, add_special_tokens=False).ids
        audit = {
            "evidence_tokens": len(evidence_ids),
            "claim_tokens": len(claim_ids),
            "inference_pairs": 0,
            "reencoding_truncations": 0,
        }
        if not evidence.strip():
            return 1.0, audit
        ew = [
            t.decode(evidence_ids[a:b])
            for a, b in window_ranges(len(evidence_ids), 384, 320)
        ]
        cw = [
            t.decode(claim_ids[a:b]) for a, b in window_ranges(len(claim_ids), 120, 100)
        ]
        encodings = []
        owners = []
        for c, part in enumerate(cw):
            for chunk in ew:
                t.no_truncation()
                full = t.encode(chunk, part)
                audit["reencoding_truncations"] += int(len(full.ids) > 512)
                t.enable_truncation(
                    max_length=512, strategy="only_first", direction="right"
                )
                encodings.append(t.encode(chunk, part))
                owners.append(c)
        best = np.zeros(len(cw))
        for start in range(0, len(encodings), 4):
            batch = encodings[start : start + 4]
            length = max(len(x.ids) for x in batch)
            ids = np.zeros((len(batch), length), dtype=np.int64)
            mask = np.zeros_like(ids)
            for row, enc in enumerate(batch):
                ids[row, : len(enc.ids)] = enc.ids
                mask[row, : len(enc.ids)] = enc.attention_mask
            risk = unsupported_risk(
                self.session.run(
                    ["logits"], {"input_ids": ids, "attention_mask": mask}
                )[0]
            )
            for j, value in enumerate(1 - risk):
                best[owners[start + j]] = max(best[owners[start + j]], float(value))
        audit["inference_pairs"] = len(encodings)
        return float(np.max(1 - best)), audit

    def cached(self, pairs, path):
        path = Path(path)
        digest = hashlib.sha256(
            json.dumps(pairs, ensure_ascii=False).encode()
        ).hexdigest()
        state = {
            "pair_sha256": digest,
            "model_revision": REVISION,
            "policy_version": "e384s320_c120s100_maxmin_v1",
            "risk": [],
            "audit": [],
        }
        if path.exists():
            state = json.loads(path.read_text())
            if (
                state["pair_sha256"] != digest
                or state["model_revision"] != REVISION
                or state.get("policy_version") != "e384s320_c120s100_maxmin_v1"
            ):
                raise ValueError("Cached inference provenance changed")
        for i in range(len(state["risk"]), len(pairs)):
            risk, audit = self.one(*pairs[i])
            state["risk"].append(risk)
            state["audit"].append(audit)
            if (i + 1) % 50 == 0:
                write_json(path, state)
                print(f"Coverage {path.name}: {i+1}/{len(pairs)}", flush=True)
        write_json(path, state)
        return np.array(state["risk"]), state["audit"]


def uncertainty(y, p, groups, threshold, other=None, *, unit="complete RAGTruth source_id"):
    unique = np.unique(groups)
    members = [np.flatnonzero(groups == g) for g in unique]
    rng = np.random.default_rng(20261019)
    values = {
        k: []
        for k in [
            "ap",
            "unsupported_recall",
            "supported_fpr",
            "review_fraction",
            "paired_ap_difference",
        ]
    }
    for _ in range(300):
        ix = np.concatenate(
            [members[i] for i in rng.integers(0, len(unique), len(unique))]
        )
        yy = y[ix]
        if len(np.unique(yy)) < 2:
            continue
        pp = p[ix]
        flags = pp >= threshold
        ap = float(average_precision_score(yy, pp))
        values["ap"].append(ap)
        values["unsupported_recall"].append(float(flags[yy == 1].mean()))
        values["supported_fpr"].append(float(flags[yy == 0].mean()))
        values["review_fraction"].append(float(flags.mean()))
        if other is not None:
            values["paired_ap_difference"].append(
                ap - float(average_precision_score(yy, other[ix]))
            )
    return {
        "unit": unit,
        "clusters": len(unique),
        "requested": 300,
        "valid": len(values["ap"]),
        "percentile_95": {
            k: np.quantile(v, [0.025, 0.975]).tolist() if v else None
            for k, v in values.items()
        },
        "limits": "conditional on fitted policies; no corpus, annotation or selection-bias guarantee",
    }


def run(data, output, models):
    started = time.monotonic()
    data, output = Path(data), Path(output)
    output.mkdir(parents=True, exist_ok=True)
    records, y, groups, meta, selection = load_target(
        data / "ragtruth", data / "alce_annotations.json"
    )
    X, ay, ag, domains, _ = alce_transfer_data(data / "alce_annotations.json")
    TX = np.array([features(r) for r in records])
    old_lex = json.loads(
        (output.parent / "followup/citation-transfer.json").read_text()
    )
    old_nli = json.loads((output.parent / "followup/nli-comparison.json").read_text())
    raw = json.loads((data / "alce_annotations.json").read_text())
    apairs = []
    for dm, model_items in raw.items():
        for items in model_items.values():
            for qid, item in items.items():
                if qid != "overall_results":
                    apairs.extend(input_pair(s) for s in item["sentences"])
    policies = {}
    validation_indices = {}
    for source, target in [("asqa", "eli5"), ("eli5", "asqa")]:
        source_ix = np.flatnonzero(domains == source)
        target_ix = np.flatnonzero(domains == target)
        tr, va, unused = split_groups(ay[source_ix], ag[source_ix], 42)
        train = source_ix[np.r_[tr, unused]]
        val = source_ix[va]
        model = make_pipeline(
            StandardScaler(),
            LogisticRegression(max_iter=2000, class_weight="balanced", random_state=42),
        )
        model.fit(X[train], ay[train])
        cut = recall_threshold(ay[val], model.predict_proba(X[val])[:, 1])
        prior = next(
            r
            for r in old_lex["experiments"]
            if r["source"] == source and r["policy"] == "learned_lexical"
        )
        if not np.isclose(
            cut, prior["threshold"], atol=1e-12, rtol=0
        ) or not np.isclose(
            average_precision_score(
                ay[target_ix], model.predict_proba(X[target_ix])[:, 1]
            ),
            prior["average_precision"],
            atol=1e-12,
            rtol=0,
        ):
            raise ValueError("Frozen lexical reproduction failed")
        policies[source] = {
            "lexical": (model.predict_proba(TX)[:, 1], cut),
            "bounded_nli_threshold": next(
                r["threshold"]
                for r in old_nli["experiments"]
                if r["source"] == source and r["policy"] == "open_nli"
            ),
        }
        validation_indices[source] = val
    pairs = [input_pair(r) for r in records]
    bounded_path = output / "ragtruth-bounded-risks.json"
    if bounded_path.exists():
        cached = json.loads(bounded_path.read_text())
        expected = hashlib.sha256(
            json.dumps(pairs, ensure_ascii=False).encode()
        ).hexdigest()
        if (
            cached["pair_sha256"] != expected
            or cached.get("model_revision") != REVISION
            or cached.get("policy") != "bounded512claim120_v1"
        ):
            raise ValueError("Bounded cache changed")
        bounded = np.array(cached["risk"])
        bounded_audit = cached["context_audit"]
    else:
        bounded, bounded_audit, runtime = infer(pairs, models)
        write_json(
            bounded_path,
            {
                "pair_sha256": hashlib.sha256(
                    json.dumps(pairs, ensure_ascii=False).encode()
                ).hexdigest(),
                "risk": bounded.tolist(),
                "context_audit": bounded_audit,
                "runtime": runtime,
                "model_revision": REVISION,
                "policy": "bounded512claim120_v1",
            },
        )
    coverage = CoverageNLI(models)
    cv, coverage_audit = coverage.cached(pairs, output / "ragtruth-coverage-risks.json")
    rows = []
    strata = []
    validation = []
    for source in ["asqa", "eli5"]:
        ix = validation_indices[source]
        vp, vaudit = coverage.cached(
            [apairs[i] for i in ix], output / f"{source}-coverage-validation.json"
        )
        cutoff = recall_threshold(ay[ix], vp)
        validation.append(
            {
                "source": source,
                "rows": len(ix),
                "questions": len(set(ag[ix])),
                "coverage_threshold": cutoff,
            }
        )
        lex, lt = policies[source]["lexical"]
        for name, p, cut in [
            ("learned_lexical", lex, lt),
            ("bounded_nli", bounded, policies[source]["bounded_nli_threshold"]),
            ("coverage_nli", cv, cutoff),
            ("review_all", np.ones(len(y)), 0.5),
            ("review_none", np.zeros(len(y)), 0.5),
        ]:
            rows.append(
                {
                    "source_policy": source,
                    "policy": name,
                    **policy_metrics(y, p, cut),
                    "uncertainty": uncertainty(
                        y, p, groups, cut, lex if name != "learned_lexical" else None
                    ),
                }
            )
            if name in ["learned_lexical", "bounded_nli", "coverage_nli"]:
                for column in ["quality", "generator"]:
                    for value in sorted({m[column] for m in meta}):
                        keep = np.array([m[column] == value for m in meta])
                        yy = y[keep]
                        strata.append(
                            {
                                "source_policy": source,
                                "policy": name,
                                "stratum": column,
                                "value": value,
                                "n": int(keep.sum()),
                                "positives": int(yy.sum()),
                                "metrics": (
                                    policy_metrics(yy, p[keep], cut)
                                    if len(np.unique(yy)) == 2
                                    else None
                                ),
                            }
                        )
    write_json(
        output / "external-support-scores.json",
        {
            "records": meta,
            "labels": y.tolist(),
            "bounded_nli": bounded.tolist(),
            "coverage_nli": cv.tolist(),
            "lexical_by_source": {
                k: v["lexical"][0].tolist() for k, v in policies.items()
            },
        },
    )
    result = {
        "status": "completed independent human-annotated QA benchmark, not deployment or learning-outcome validation",
        "selection": selection,
        "positive_label": "any released annotated hallucination span; supplied-evidence support, not universal truth",
        "annotation_unit": "complete response; differs from ALCE sentences",
        "positives": int(y.sum()),
        "negatives": int((y == 0).sum()),
        "ragtruth_revision": "c103204b9ce28d6bbad859304bf30de72b8ed8fe",
        "input_sha256": RAG_HASHES,
        "alce_sha256": sha256(data / "alce_annotations.json"),
        "model": MODEL,
        "model_revision": REVISION,
        "environment": environment(),
        "wall_seconds": time.monotonic() - started,
        "bounded_context": {
            "evidence_truncated": sum(r["evidence_truncated"] for r in bounded_audit),
            "claims_truncated": sum(r["claim_truncated"] for r in bounded_audit),
        },
        "coverage": {
            "inference_pairs": sum(r["inference_pairs"] for r in coverage_audit),
            "reencoding_truncations": sum(
                r["reencoding_truncations"] for r in coverage_audit
            ),
        },
        "validation": validation,
        "experiments": rows,
        "descriptive_strata": strata,
        "limits": [
            "question exact-match exclusion is not semantic deduplication",
            "pretraining overlap unknown",
            "human labels can be imperfect",
            "answer-level and sentence-level results are not pooled",
            "window aggregation is length-dependent and can lose joint semantics",
            "source threshold recall target has no transfer guarantee",
            "no human educational or deployment trial",
            "no target adaptation after outcomes",
        ],
    }
    write_json(output / "external-support.json", result)
    return result


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--data", default="data/raw")
    p.add_argument("--output", default="results/validation")
    p.add_argument("--models", default="data/models/nli-deberta-v3-small")
    a = p.parse_args()
    run(a.data, a.output, a.models)
