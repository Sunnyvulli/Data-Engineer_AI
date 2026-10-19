"""Generate a measured Markdown report directly from experiment JSON."""
import json
from pathlib import Path
import pandas as pd


def table(frame, groups, metrics):
    lines = ['| ' + ' | '.join(groups + metrics) + ' |', '| ' + ' | '.join(['---'] * (len(groups)+len(metrics))) + ' |']
    for keys, rows in frame.groupby(groups, dropna=False, sort=True):
        if not isinstance(keys, tuple):keys = (keys,)
        values = [str(k) for k in keys]
        for metric in metrics:
            v = rows[metric].dropna()
            values.append(f'{v.mean():.4f} [{v.min():.4f}, {v.max():.4f}]' if len(v) else 'N/A')
        lines.append('| ' + ' | '.join(values) + ' |')
    return '\n'.join(lines)


def generate(output):
    output = Path(output)
    data = {name: json.loads((output / f'{name}.json').read_text()) for name in ['phishing', 'checkpoints', 'transients']}
    frames = {name: pd.DataFrame(value['experiments']) for name, value in data.items()}
    p, c, t = frames['phishing'], frames['checkpoints'], frames['transients']
    c = c[c.domain.isna()]
    content = '''# Measured baseline results

Generated from the committed experiment JSON, not manually entered scores. Each cell is **mean [minimum, maximum]** over seeds 17, 42, and 91. These are overlapping split repetitions, not confidence intervals. Average precision is the non-interpolated AP metric. Scores refer only to the documented datasets and policies.

## Phishing robustness

'''
    content += f"{data['phishing']['rows']:,} records; {data['phishing']['unique_feature_groups']:,} unique feature-vector groups. Exact feature duplicates do not cross partitions. Positive class is phishing. Threshold targets validation FPR <=1%, without guaranteeing that test FPR stays below that value.\n\n"
    content += table(p, ['model', 'condition'], ['average_precision', 'recall', 'false_positive_rate'])
    content += '''

Interpretation: page-feature loss substantially reduces operating-point recall. The high clean average precision does not establish current-campaign generalisation, multimodal performance, or deployment readiness. The feature-block definitions leave other correlated features available.

## Citation-support triage

'''
    content += f"{data['checkpoints']['n_sentences']:,} human-labelled sentences from {data['checkpoints']['n_questions']} questions. All model outputs for a question remain in one partition. Unsupported means not fully supported by the provided citations, not necessarily false.\n\n"
    content += table(c, ['policy'], ['average_precision', 'recall', 'review_fraction', 'unsupported_fraction_among_unflagged'])
    content += '''

Interpretation: selective policies reduce the number of flagged sentences relative to review-all, but leave unsupported sentences in the unflagged set. Review fraction is a count proxy: no reviewer time or student-learning improvement was measured. Even a low-risk sentence may contain a contradiction. Review-all/none AP reflects constant-score prevalence and is not evidence of ranking quality.

## Early kilonova prioritisation

'''
    content += f"{data['transients']['n_observations']:,} simulated observations and {data['transients']['n_metadata_objects']:,} labelled metadata objects. Eligible test objects require an actual simulated detection flag; see split logs for evaluated counts. No simulation truth metadata enters predictors. Follow-up budget is top 5% by candidate count.\n\n"
    content += table(t, ['horizon_days', 'model'], ['average_precision', 'precision_at_budget', 'recall_at_budget'])
    content += '''

Interpretation: forest ranking benefits from longer observation windows in these runs. Most selected candidates are still not kilonovae, and many kilonovae remain unselected. The expected-random comparison uses held-out prevalence. These are simulated light curves and retrospective rankings, not discoveries or a real telescope scheduling trial.

## Validation and review

- Integrity checks cover grouped splitting, label direction, thresholds with tied scores, invalid inputs, human-label exclusion, alert cutoffs, and future-observation invariance.
- Offline batch prediction is smoke-tested with locally trained artifacts for all three projects.
- Source-data hashes, software versions, split counts, and complete per-seed metrics are in adjacent JSON files.
- No claim of statistical significance, new state of the art, publication acceptance, production certification, or external peer review is made.
- Human owner review, contemporary specialised baselines, out-of-domain evaluation, and a demonstrated new contribution are still needed before a paper submission.
'''
    (output / 'SUMMARY.md').write_text(content)
    return output / 'SUMMARY.md'
