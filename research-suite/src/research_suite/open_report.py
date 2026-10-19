"""Generate a technical report from measured open-comparison outputs."""

from pathlib import Path
import json


def report(root="results/followup"):
    root = Path(root)
    nli = json.loads((root / "nli-comparison.json").read_text())
    feed = json.loads((root / "real-feed-probe.json").read_text())
    archive = json.loads((root / "irsa-access-smoke.json").read_text())
    rows = [
        "# Open entailment comparison and independent-source probes",
        "",
        "Measured October 19, 2026 UTC (October 18 in America/Chicago). Original implementation/analysis by Hanumantha Rao Vulli. Pretrained models and data are credited to their creators. No novelty, accepted publication or production validation is claimed.",
        "",
        "## Completed bounded entailment experiment",
        "",
        "Protocol commit before new inference: `356a13eeeb7dad7120cecdd6151280efc5af1a57`. Earlier lexical outcomes were already exposed. Both policies use the same 2,604 ALCE sentences, question groups, seed42 source splits and target rows. Source validation alone sets the >=90% unsupported-recall review threshold. No NLI fine-tuning or target-threshold tuning occurred.",
        "",
        "| Source → target | Policy | Unsupported AP | Unsupported recall | Review fraction | Missed unsupported |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for r in nli["experiments"]:
        if r["policy"] in ("open_nli", "learned_lexical", "nli_default"):
            rows.append(
                f"| {r['source']} → {r['target']} | {r['policy']} | {r['average_precision']:.4f} | {r['recall']:.1%} | {r['review_fraction']:.1%} | {r['missed_unsupported']} |"
            )
    rows += [
        "",
        "NLI ranks unsupported sentences worse by AP in both directions. Its ASQA-source threshold fails the 90% recall target on ELI5. In reverse transfer it catches more unsupported sentences at a much larger review cost; this is not an equal-budget superiority claim. Default 0.5 is a fixed diagnostic.",
        "",
        "| Direction | AP difference: NLI minus lexical | 95% question-cluster interval |",
        "|---|---:|---|",
    ]
    for r in nli["experiments"]:
        if r["policy"] == "open_nli":
            other = next(
                x
                for x in nli["experiments"]
                if x["source"] == r["source"] and x["policy"] == "learned_lexical"
            )
            low, high = r["uncertainty"]["paired_ap_difference_percentile_95"]
            rows.append(
                f"| {r['source']} → {r['target']} | {r['average_precision']-other['average_precision']:.4f} | [{low:.4f}, {high:.4f}] |"
            )
    c = nli["context"]
    rows += [
        "",
        f"Runtime: {nli['wall_seconds']:.1f} seconds, peak process RSS {nli['peak_process_rss_kib']/1024:.1f} MiB; ONNX Runtime {nli['runtime']['onnxruntime']}, tokenizers {nli['runtime']['tokenizers']}, four CPU inference threads, batch four. Of {c['rows']} sentences, {c['evidence_truncated']} evidence contexts and {c['claim_truncated']} claims were truncated; {c['missing_evidence']} had no cited evidence and received risk 1 without inference. Two synthetic wiring checks produced risks 0.0274 for entailment and 0.9999 for contradiction; these are not an accuracy benchmark.",
        "",
        "Model: `cross-encoder/nli-deberta-v3-small`, revision `fa2804872c3b4bd748f38c0185cc85775361e735`, declared Apache-2.0. [Immutable card/config](https://huggingface.co/cross-encoder/nli-deberta-v3-small/tree/fa2804872c3b4bd748f38c0185cc85775361e735) describes SNLI/MultiNLI training. [ALCE source](https://github.com/princeton-nlp/ALCE) supplies annotations. This is not a rerun of its original large-model evaluator. The NLI premise includes cited titles/text; the lexical features use cited text. Context limits, benchmark reuse, possible pretraining overlap and differing training domains constrain interpretation. Intervals condition on fitted models and omit collection/model-selection uncertainty. Support against provided evidence is not universal factual truth.",
        "",
        "Detailed thresholds, metrics and hashes are in `nli-comparison.json`; aligned risks/token audits without passages are in `nli-scores.json`. The optional runtime dependency scan found no reported advisories at scan time (`nli-dependency-audit.json`); this is not a security guarantee.",
        "",
        "## Completed one-snapshot phishing probe",
        "",
        "Protocol commit before fetch/scoring: `f24baa08c79c3a98a14a9aef0164017e99fcb9b0`. The earlier fixed PhiUSIIL model was reconstructed because that raw-URL artifact had not been saved. Source train/validation folds alone determined the fitted model/threshold.",
        "",
        f"OpenPhish Community Feed accessed {feed['provenance']['fetched_utc']}: {feed['selection']['unique_urls']} unique URLs; {feed['selection']['source_host_overlap_excluded']} source-host overlaps and {feed['selection']['invalid_excluded']} malformed URLs excluded. Flagged {feed['provider_reported_phishing_flagged']}/{feed['selection']['retained']} retained entries ({feed['provider_feed_agreement']:.2%}) at threshold {feed['threshold']:.6f}. Source validation FPR was {feed['source_validation_fpr']:.2%}; that is not feed/deployment FPR.",
        "",
        f"Conditional complete-host bootstrap agreement interval: [{feed['uncertainty']['percentile_95'][0]:.2%}, {feed['uncertainty']['percentile_95'][1]:.2%}], {feed['uncertainty']['clusters']} exact hosts, 300 resamples. Labels are provider-reported phishing, not independently adjudicated. There are no benign controls or representative population sampling frame. Do not infer precision, operational FPR, AP, ROC AUC or population phishing sensitivity. Registered-domain/campaign dependence and provider selection/error remain.",
        "",
        "Data provider: [OpenPhish](https://openphish.com/), accessed October 19, 2026 UTC. [Community Feed](https://openphish.com/phishing_feeds.html) and [terms](https://openphish.com/terms.html) govern personal independent research and restrict redistribution. Only non-reconstructive aggregates/provenance are published. Feed URLs, individual predictions and target pages are not redistributed; listed sites were not visited. A changing feed cannot recover this snapshot by its hash alone. Exact rerun needs lawful access to that snapshot; a fresh download is a different experiment.",
        "",
        "## Astronomy access and unfinished comparison",
        "",
        f"The documented public IRSA example query returned HTTP {archive.get('http_status')} and {archive.get('parsed_rows_including_header', 0)-1} CSV records. This is an unlabelled access check, not a scientific sample or event classification. Timestamp, query, hash and schema are retained in `irsa-access-smoke.json`.",
        "",
        "The [astronomy feasibility assessment](../../docs/followup/ASTRONOMY_FEASIBILITY.md) records accessible MIT-licensed RAPID source/weights, filter and preprocessing differences, custom training, IRSA public-data terms and a possible BTS sampling frame. A matched specialised comparison and observed-event performance evaluation remain unfinished. Missing weights and a blanket compute/access blocker are not claimed.",
        "",
        "## Four-perspective self-review",
        "",
        "- Researcher: retain the weaker NLI ranking and transfer failure. Feed agreement is independent-source evidence with substantial label/sampling limits.",
        "- Supervisor: protocols preceded new outputs; thresholds came from source validation. Freeze a matched astronomy protocol before training and use a new holdout for outcome-driven revisions.",
        "- Industry user: review workload is a cost; feed agreement has no benign denominator. Download access establishes no operational latency, live alert reliability or telescope integration.",
        "- Critical reviewer: intervals are conditional, corpus outcomes were previously exposed, training domains differ and feed redistribution is restricted. Passing tests do not establish novelty or acceptance.",
        "",
        "These are structured self-review perspectives, not independent expert endorsements.",
        "",
        "## Reproduce from research-suite",
        "",
        "```bash",
        "python -m pip install -r requirements-lock.txt",
        "python -m pip install -r requirements-nli-runtime-lock.txt",
        "PYTHONPATH=src python -m research_suite.entailment fetch",
        "PYTHONPATH=src python -m research_suite.entailment run",
        "PYTHONPATH=src python -m research_suite.feed_probe",
        "PYTHONPATH=src python -m research_suite.open_report",
        "python -m unittest discover -s tests -v",
        "```",
        "",
        "Fetch original/follow-up datasets first, as documented in README. The feed command reuses a cached local snapshot/provenance; a fresh runtime obtains a different dated snapshot. Models and raw data remain outside source control.",
        "",
    ]
    (root / "OPEN_COMPARISON_REPORT.md").write_text("\n".join(rows))


if __name__ == "__main__":
    report()
