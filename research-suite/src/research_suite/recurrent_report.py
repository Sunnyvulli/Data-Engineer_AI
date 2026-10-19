"""Generate an auditable adaptation/observed-readiness report from saved outputs."""

import json
from pathlib import Path


def report(root="results/followup"):
    root = Path(root)
    result = json.loads((root / "recurrent-comparison.json").read_text())
    observed = json.loads((root / "observed-readiness.json").read_text())
    rows = [
        "# RAPID-inspired recurrent comparison and observed-data readiness",
        "",
        "Original implementation/analysis by Hanumantha Rao Vulli. Measured October 19, 2026 UTC. This is a bounded adaptation experiment, not scientific novelty, an accepted publication, a RAPID paper/package reproduction or real-event validation.",
        "",
        "## Fixed comparison and attribution",
        "",
        "The [protocol](../../docs/followup/RECURRENT_PROTOCOL.md) was committed before training (`b2a590a36d5f3a2e265309b15273e81500e54697`). The model adapts the two unidirectional 100-unit GRUs described by [Muthukrishna et al. (2019)](https://arxiv.org/html/1904.00014v2). It changes the input grid, six-band representation, binary endpoint target and training budget. The current astrorapid repository uses a TCN and released ZTF/Pan-STARRS filters; those weights were not relabelled as LSST weights.",
        "",
        "Both methods receive only observations between first detected_bool=1 and three days later, inclusive. GRU uses a causal 13-point grid with latest observed flux/error/mask per band and source-training-only scales. Forest uses its original summary features. Thus allowed observations, object split, target and ranking budget match, while representation and computational/selection resources differ. The GRU retains only its best source-validation AP checkpoint; forest had no analogous checkpoint search. Exposed simulated test outcomes are reused and are not a fresh blind holdout.",
        "",
        "| Split | Objects | Kilonova targets |",
        "|---|---:|---:|",
    ]
    for name, info in result["split"].items():
        rows.append(f"| {name} | {info['objects']} | {info['positives']} |")
    rows += [
        "",
        f"One seed 42, exactly 25 epochs. Selected epoch {result['selected_epoch']} by source-validation AP {result['selected_validation_ap']:.4f}. Network parameters: {result['parameter_count']:,}. Model revision decisions were not based on test results. Class-weighted scores are not calibrated probabilities.",
        "",
        "## Measured results",
        "",
        "| Evaluation | Model | Objects | Positives | AP | ROC AUC | Top-5% selected | Targets found | Budget recall |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for r in result["source_results"]:
        rows.append(
            f"| Source held-out | {r['model']} | {r['n']} | {r['positives']} | {r['average_precision']:.6f} | {r['roc_auc']:.4f} | {r['selected']} | {r['rare_found']} | {r['recall_at_budget']:.1%} |"
        )
    for r in result["independent_results"]:
        m, b = r["metrics"], r["budget"]
        rows.append(
            f"| Independent simulated remainder | {r['model']} | {m['n']} | {m['positives']} | {m['average_precision']:.6f} | {m['roc_auc']:.4f} | {b['selected']} | {b['rare_found']} | {b['recall_at_budget']:.1%} |"
        )
    rows += [
        "",
        "On the source held-out split, GRU has lower AP but selects one additional target at the same budget (8 versus 7). On the independent remainder its AP is higher, but both models miss both targets within the budget. These differing metric directions and sparse targets do not establish overall superiority or useful deployment sensitivity.",
        "",
    ]
    source_gru = result["source_results"][0]
    source_forest = result["source_results"][1]
    independent_gru = result["independent_results"][0]
    independent_forest = result["independent_results"][1]
    rows += [
        "",
        "Paired AP differences (GRU minus forest), with 300 complete-object bootstrap resamples conditional on the fitted models:",
        "",
        f"- Source held-out: {source_gru['average_precision']-source_forest['average_precision']:.6f}; 95% interval {source_gru['uncertainty']['paired_ap_difference_percentile_95']}.",
        f"- Independent remainder: {independent_gru['metrics']['average_precision']-independent_forest['metrics']['average_precision']:.6f}; 95% interval {independent_gru['paired_ap_interval']}.",
        "",
        "The independent remainder contains only two positive events. This is insufficient for a reliable population sensitivity claim. Budget recall intervals from sparse-event bootstraps can be degenerate; the exact-binomial diagnostics below require independent exchangeable positive events and do not remove selection/domain bias:",
        "",
    ]
    for r in result["independent_results"]:
        rows.append(
            f"- {r['model']}: {r['budget']['rare_found']}/2 targets selected; illustrative Clopper–Pearson 95% recall interval {r['recall_binomial_diagnostic']['clopper_pearson_95']}."
        )
    rows += [
        "",
        "Detailed default 0.5 diagnostics and uncertainty are retained in `recurrent-comparison.json`. Default0.5 is not the operational budget policy. `recurrent-source-scores.csv` and `recurrent-independent-scores.csv` preserve aligned IDs, simulated labels and both scores. Original forest AP and independent population size were checked against the earlier release; source/external ID overlap is rejected.",
        "",
        "## Failure, recovery and compute",
        "",
        "The initial evaluation stopped after training on a JSON-schema lookup error: the old independent AP was nested under metrics, not at top level. All 25 validation records and the already selected model were retained. Evaluation resumed from the recorded model SHA-256 using safe-mode Keras loading; no retraining, new checkpoint selection or parameter change occurred. `recurrent-recovery.json` records the error, selected-artifact hash and source hashes. The artifact hash must match the final result.",
        "",
        f"Recovery evaluation wall time: {result['wall_seconds']:.1f} seconds; peak recovery-process RSS {result['peak_process_rss_kib']/1024:.1f} MiB. Original training duration/RSS were not separately persisted before the error and are not fabricated. TensorFlow {result['tensorflow']}, Keras {result['keras']}, four CPU intra-op threads and deterministic operations. Exact installed versions are in `requirements-recurrent-runtime-lock.txt`. The retained dependency scan reported no advisories at that scan, not a security guarantee.",
        "",
        "## Observed-data readiness: no classifier scores",
        "",
        "The [readiness protocol](../../docs/followup/OBSERVED_READINESS_PROTOCOL.md) was committed before CSV sampling/query (`a90e35460fc03513d9ca3bb77433db7a7751526f`). Source: [official BTS Sample Explorer](https://sites.astro.caltech.edu/ztf/bts/explorer.php?format=csv), which requests citation of its research paper. Public visibility is not asserted to provide a blanket redistribution license; the full source table is not redistributed. IRSA public-data terms and acknowledgments are linked in the output manifest.",
        "",
        f"The default-query snapshot had {observed['selection']['frame_rows']:,} records, including {observed['selection']['eligible_unique_ids']:,} unique eligible provider-classified SN records. The 20 lowest SHA-256 ZTF identifiers were selected as a negative-control frame. Provider classifications were not independently adjudicated; this is not a kilonova-positive or representative alert sample.",
        "",
        f"The fixed first selected object, {observed['first_object_archive_query']['object_id']}, returned HTTP {observed['first_object_archive_query'].get('http_status')} and {observed['first_object_archive_query'].get('rows')} photometry rows for the frozen 1.5 arcsec public DR24 g/r cone. That outcome is retained; no replacement object was chosen after seeing it. The earlier 724-row documentation-example query is not substituted for this sampling result.",
        "",
        "Direct model admission was rejected. Verified gaps include no returned rows for the preselected cone, ZTF-versus-LSST filter response, catalog magnitudes rather than verified difference-flux inputs, absent broker detection history and unestablished source crossmatch. No flux, uncertainty, alert flags or model results were invented. Sampling/query/hash/schema details and selected factual identifiers are in `observed-readiness.json`; raw source tables remain local. A cached query must match its recorded URL and SHA-256 before reuse.",
        "",
        "A follow-on observed study would need a new frozen access/coverage protocol, compatible difference-alert photometry and physical passband/unit mapping, verified source identities and an independently labelled evaluation frame. These are not closed by this access audit. The failure of this direct mapping does not prove all observed astronomy comparisons impossible.",
        "",
        "## Four-perspective self-review",
        "",
        "- Researcher: report every measured ranking and missed event; one seed and reused simulations cannot establish broad model superiority.",
        "- Supervisor: source validation selected the checkpoint; the schema failure was recovered without retraining. Require fresh evaluation for any outcome-driven revision.",
        "- Industry user: a shared 5% follow-up budget exposes resource cost, while sparse positives and absent observed-data admission prevent deployment claims.",
        "- Critical reviewer: this is a credited GRU adaptation with differing representations/resources, not a reproduction. Zero-row archive access and provider-label sampling are explicit limitations, not fabricated validation.",
        "",
        "These are structured self-review perspectives, not independent expert endorsements.",
        "",
        "## Reproduction",
        "",
        "```bash",
        "python -m pip install -r requirements-lock.txt",
        "python -m pip install -r requirements-recurrent-runtime-lock.txt",
        "PYTHONPATH=src python -m research_suite.recurrent --trust-local-model",
        "PYTHONPATH=src python -m research_suite.observed_readiness",
        "PYTHONPATH=src python -m research_suite.recurrent_report",
        "python -m unittest discover -s tests -v",
        "```",
        "",
        "Fetch the original/follow-up data and reproduce the original trusted seed 42 forest artifact first. Never load someone else’s joblib model. Optional `--resume-selected-model` requires the locally generated selected artifact, full training progress and matching recovery manifest; ordinary runs train from scratch under the fixed protocol. The changing BTS snapshot is cached locally with hashes; a new snapshot is a new dated readiness audit.",
        "",
    ]
    (root / "RECURRENT_REPORT.md").write_text("\n".join(rows))


if __name__ == "__main__":
    report()
