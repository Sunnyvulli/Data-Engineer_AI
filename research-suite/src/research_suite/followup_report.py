"""Generate a technical report from actual follow-up output files."""
import json
from pathlib import Path


def value(x):
    return 'not estimable' if x is None else f'{x:.4f}'


def ci(x):
    return 'not estimable' if x is None else f'[{x[0]:.4f}, {x[1]:.4f}]'


def generate(output):
    root = Path(output)
    p = json.loads((root/'phishing-followup.json').read_text())
    c = json.loads((root/'citation-transfer.json').read_text())
    a = json.loads((root/'independent-transients.json').read_text())
    remainder = root/'independent-transients-remainder.json'
    b = json.loads(remainder.read_text()) if remainder.exists() else None
    text = '''# Validation limits in three inexpensive ML workflows

Engineering research report, October 2026. Project owner: Hanumantha Rao Vulli. This is an unreviewed technical report, not an accepted paper, a claim of scientific novelty, or production validation.

## Purpose and protocol

The first release established reproducible baselines. This follow-up asks how results change under different input representations, corpus transfer, and independent simulation objects. Protocols were committed before the new outcomes were inspected: `304fbdb56b33bef05c90ec4cd6db0a74c19802aa`, with pre-execution clarification `b74e5ae0fd8542e76b0c21ccc41dec63990427a9`. The astronomy pilot's lack of target events led to a separately committed adaptive stage-two protocol `f5b950ffb2bbdf9a106cbc2678e3171a727de85f`; it must not be described as the original fixed test.

Intervals below are 95% percentile cluster bootstrap intervals from 300 resamples (seed 20261018), conditional on the fitted model. They do not correct sample selection, collection bias, benchmark exposure, or training uncertainty. Related work and unexecuted specialised baselines are listed in `docs/followup/RELATED_WORK.md`.

## 1. Phishing: the score depends on representation and corpus construction

'''
    text += f"The primary PhiUSIIL archive contains {p['audit']['raw_rows']:,} rows. The audit found {p['audit']['exact_url_duplicate_rows']} exact duplicate URL rows and excluded {p['audit']['conflicting_urls_excluded']} conflicting URL groups. A fixed SHA-256-ranked subset of {p['selected_rows']:,} unique URLs was split by exact normalized hostname. This is not campaign, registered-domain, or temporal separation. Only raw text was used; precomputed similarity/probability fields were excluded.\n\n"
    text += '| Representation | AP | AP interval | Recall at validation-selected threshold | Test FPR |\n| --- | ---: | --- | ---: | ---: |\n'
    for r in p['experiments']:
        text += f"| {r['representation']} | {value(r['average_precision'])} | {ci(r['uncertainty']['ap_percentile_95'])} | {value(r['recall'])} | {value(r['false_positive_rate'])} |\n"
    text += f"\nPaired host-cluster interval for AP(full URL) minus AP(hostname): {ci(p['paired_full_minus_host_ap']['paired_ap_difference_percentile_95'])}.\n\n"
    for label, group in p['audit']['collection_by_class'].items():
        text += f"Class {'phishing' if label == '1' else 'legitimate'}: HTTPS {group['https_fraction']:.2%}; leading www. {group['www_fraction']:.2%}; nonempty path {group['nonempty_path_fraction']:.2%}; query {group['query_fraction']:.2%}.\n\n"
    text += '''Interpretation: the representation gap and class-dependent URL formatting create a serious collection-artifact risk. Removing paths/schemes also removes potentially useful real signals, so this ablation cannot causally attribute the entire score gap to artifacts. It does show why the near-perfect full-URL result should not be promoted as current-world effectiveness. Prior public engineering work reports related PhiUSIIL concerns and is credited; these observations are not claimed as a first discovery. This experiment is a second-corpus model, not external validation of the incompatible UCI-327 engineered-feature detector.

## 2. Citation support: a source recall target does not ensure target recall

Source-domain validation selects thresholds targeting at least 90% unsupported-sentence recall. All answers and sentences for a question stay together. The other corpus supplies the test set; target labels do not enter fitting or threshold choice.

| Source → target | Policy | AP (continuous policies only) | Unsupported recall | Recall interval | Review fraction |
| --- | --- | ---: | ---: | --- | ---: |
'''
    for r in c['experiments']:
        ap = value(r['average_precision']) if r['policy'] in ('learned_lexical', 'lexical') else 'binary/constant scores'
        text += f"| {r['source']} → {r['target']} | {r['policy']} | {ap} | {value(r['recall'])} | {ci(r['uncertainty']['recall_percentile_95'])} | {value(r['review_fraction'])} |\n"
    text += '''
The released automatic policy uses the historical ALCE binary support judgments, not a newly executed current entailment model. Binary-score AP is not compared with continuous ranking AP as a superiority claim. Review fractions and thresholds differ; this is a descriptive operating-point comparison, not matched-cost proof. Lexical overlap still cannot establish truth or detect all contradictions. Corpus transfer within ALCE does not establish performance across all disciplines, modern models, or actual student workflows.

## 3. Astronomy: retain the feasibility failure

'''
    text += f"The originally fixed first {a['selection']['selected_complete_objects']:,} independent objects yielded {a['metrics']['positives']} kilonova targets among {a['eligible_detected_objects']:,} detected objects. Status: **{a['evaluation_status']}**. AP: {value(a['metrics']['average_precision'])}; rare-event recall: {value(a['budget']['recall_at_budget'])}. No artificial zero or perfect rare-event score is substituted.\n\n"
    if b is None:
        text += 'The separately specified remaining-object stage has not finished. No result is inferred.\n\n'
    else:
        text += f"The adaptive second stage excluded the exposed first 5,000 objects and the shard's final object. It evaluated {b['eligible_detected_objects']:,} detected objects containing {b['metrics']['positives']} kilonova targets, with no original-training ID overlap. The three-day forest was frozen: no fitting or threshold selection used these target labels. Status: **{b['evaluation_status']}**.\n\n"
        text += f"AP: {value(b['metrics']['average_precision'])}; top-5% precision: {value(b['budget']['precision_at_budget'])}; top-5% recall: {value(b['budget']['recall_at_budget'])}.\n\n"
        if 'ap_percentile_95' in b['uncertainty']:
            text += f"AP interval: {ci(b['uncertainty']['ap_percentile_95'])}; budget-precision interval: {ci(b['uncertainty']['precision_at_budget_percentile_95'])}; budget-recall interval: {ci(b['uncertainty']['recall_at_budget_percentile_95'])}.\n\n"
    if b is not None and b['metrics']['positives'] > 0:
        diagnostic = b.get('recall_binomial_diagnostic')
        if diagnostic:
            text += f"Only {diagnostic['positive_events']} positive events were observed. The recall bootstrap can be degenerate when every observed event is missed; its zero-width interval must not be read as certainty. A post-outcome Clopper-Pearson diagnostic gives {ci(diagnostic['clopper_pearson_95'])} under independent, exchangeable positive-event assumptions. These assumptions may not hold across shared simulations. No stable rare-event generalisation claim follows.\n\n"
    text += '''This remains PLAsTiCC simulation-to-simulation testing. It does not validate performance on observed Rubin alerts, gravitational-wave triggers, a robotic telescope, or actual discoveries. The adaptive second stage and the shard's selection properties limit interpretation. Specialised time-series models such as RAPID have not been rerun under a matched protocol.

## Reproduction

From the research-suite directory, install the documented baseline dependencies, fetch the baseline data, and generate the frozen three-day model using the unchanged seed-42 baseline implementation. The additional public-data download is approximately 321 MB.

```bash
research-suite fetch followup
python -m research_suite.followup phishing
python -m research_suite.followup citations
python -m research_suite.followup transients --trust-local-model
python -m research_suite.followup transients --trust-local-model --remaining-shard
python -m research_suite.followup_report
```

Only load joblib artifacts that you trained and trust. URL strings are never visited. Raw datasets are not committed. Input hashes, model hash, environment versions, split sizes, class counts, and per-policy metrics are in adjacent JSON files. The fetch command checks fixed hashes.

## Four-perspective self-review

| Perspective | Decision from the evidence |
| --- | --- |
| Researcher/student | New runs are reproducible, and the zero-target pilot is retained. The owner must reproduce and explain the results before presenting the work. |
| Supervisor | Corpus-transfer and interval reporting improve the baseline package, but a contemporary specialised comparison and a demonstrated new contribution are still missing. |
| Industry user | Collection artifacts, domain-transfer loss, historical labels, and simulation limits prevent claims of deployment readiness. |
| Critical reviewer | No scores or missing events were invented. Adaptive changes, binary/continuous comparison limits, prior work, and limitations are explicitly disclosed. |

These perspectives are structured self-review, not external review or expert endorsement. No publication submission, external message, live payment, or paid model call was performed.
'''
    (root/'REPORT.md').write_text(text)
    return root/'REPORT.md'


if __name__ == '__main__':
    print(generate('results/followup'))
