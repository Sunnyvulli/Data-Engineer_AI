"""Render every frozen contrast and token-rate summary, including null intervals."""
from pathlib import Path
import json

ROOT=Path(__file__).resolve().parents[2]
D=ROOT/'results/validation'

def value_ci(point,ci):
    return f'{point:.4f} [{ci[0]:.4f}, {ci[1]:.4f}]' if ci is not None else f'{point:.4f} [unavailable]'

def render():
    r=json.loads((D/'exploratory-analysis.json').read_text())
    rate=json.loads((D/'token-rate-analysis.json').read_text())
    boundary=json.loads((D/'token-rate-boundary-audit.json').read_text())
    labels={'raw_length_minus_coverage':'Raw length - NLI', 'rank_length_minus_coverage':'Ranked length - NLI',
            'macro_length_minus_coverage':'Macro length - NLI','increment_M1_minus_M0':'M1 - M0'}
    lines=['### 4.2. Exploratory paired contrasts and incremental value',
        '', 'All results in this section use the exposed target. The original plan was committed in 9002e048b42cec344165f8f8e4fe94f59a0e8bd6 before these additional calculations; its text remains unchanged. Exactly 5,000 complete-question bootstrap draws, seed 20261025, are shared across scores and populations. Intervals are conditional 95% percentile summaries, uncorrected for multiple contrasts. AP means scikit-learn average precision. Positive length-minus-NLI differences favor length; positive M1-minus-M0 differences favor the augmented model. Every planned contrast, including zero-crossing intervals, is reported.',
        '', 'Table 6. Exploratory exposed-target paired differences. Rank transformations are recomputed within every sampled generator, retaining duplicate-group multiplicity. Macro averages weight generators equally and require every included stratum to contain both classes. Counts show valid/invalid draws; invalid draws are never replaced.',
        '', '| Population | Contrast | AP diff [95%] | AUC diff [95%] | Valid / invalid |',
        '| --- | --- | --- | --- | --- |']
    for pop,label in [('all_generators','All six'),('without_gpt4','No GPT-4')]:
        for name,description in labels.items():
            x=r['populations'][pop]['contrasts'][name]
            lines.append(f"| {label} | {description} | {value_ci(x['ap_difference'],x['ap_ci95'])} | {value_ci(x['auc_difference'],x['auc_ci95'])} | {x['valid_draws']} / {x['invalid_draws']} |")
    lines.extend(['', 'Raw length has a positive pooled AP difference in this conditional exploratory analysis, whereas both raw and rank-normalized AUC intervals cross zero. The equal-weight macro AUC favors NLI with all generators but crosses zero after GPT-4 is removed. The complete-sample macro interval is conditional on 3,156 valid draws and is particularly unstable because GPT-4 has one positive. These are different estimands, not a basis for selecting a favorable ranking or establishing general superiority or equivalence.',
        '', 'Table 7. Exploratory within-generator length-minus-NLI contrasts. The five retained per-generator contrasts are numerically identical in the GPT-4-excluded sensitivity because their rows and shared question draws are unchanged. Sparse-stratum intervals condition on valid draws; the one-positive GPT-4 interval is not reliable population inference.',
        '', '| Generator | AP diff [95%] | AUC diff [95%] | Valid | Invalid |', '| --- | --- | --- | --- | --- |'])
    for name,x in r['populations']['all_generators']['contrasts'].items():
        if name.startswith('generator/'):
            lines.append(f"| {name.split('/',1)[1]} | {value_ci(x['ap_difference'],x['ap_ci95'])} | {value_ci(x['auc_difference'],x['auc_ci95'])} | {x['valid_draws']} | {x['invalid_draws']} |")
    lines.extend(['', 'M0 is L2 logistic regression using log1p(answer tokens) and generator indicators; M1 adds continuous coverage-NLI risk. Five fixed question-group folds keep preprocessing and fitting inside training groups. Neither model is a source-only policy: both train on other exposed-target groups. Out-of-fold probabilities are pooled for scoring. The paired bootstrap treats these predictions as fixed and omits refitting, fold-selection and training uncertainty; overlapping fold training sets further limit interpretation.', '', 'Table 8. Exploratory pooled out-of-fold model scores. The paired gains and all intervals appear in Table 6.', '', '| Population | M0 AP | M1 AP | M0 AUC | M1 AUC |', '| --- | --- | --- | --- | --- |'])
    for pop,label in [('all_generators','All six'),('without_gpt4','No GPT-4')]:
        m=r['populations'][pop]['model_metrics'];lines.append(f"| {label} | {m['M0']['ap']:.4f} | {m['M1']['ap']:.4f} | {m['M0']['auc']:.4f} | {m['M1']['auc']:.4f} |")
    lines.extend(['', 'NLI contributes a positive conditional incremental signal under these fixed specifications, including after GPT-4 removal. That observation prevents a blanket conclusion that evidence reading adds nothing beyond length and generator. It is a hypothesis for genuinely fresh confirmation, not an established general finding or a source-transfer improvement. No configuration was tuned after these outcomes.',
        '', '### 4.3. Bounded annotation-token exposure check',
        '', 'The pinned RAGTruth response file and coverage tokenizer were hash-verified. All 235 retained annotation spans exactly matched Unicode character slices, and all 900 full-answer token lengths matched cached counts. Overlapping spans were merged; a non-special answer token counted once if its offsets overlapped any annotated character span. No answers had zero tokens. This is annotated token coverage, not per-claim error or a certificate of semantic correctness.',
        '', 'Table 9. Exploratory generator-specific rates and length-adjusted binomial-logit slopes. Total rate is annotated tokens divided by all answer tokens; mean rate averages answer fractions. The interaction model uses a separate intercept and log1p(length) slope per generator. Predicted fractions are at that generator\'s observed length quartiles. Full predicted-fraction intervals, token totals, length distributions, row counts and every saved fit are released in token-rate-analysis.json and token-rate-resamples.json.gz.',
        '', '| Generator | Total rate | Mean rate | Length slope [95%] | Predicted Q1 / Q2 / Q3 | Accepted draws |', '| --- | --- | --- | --- | --- | --- |'])
    for name,x in rate['generators'].items():
        v=x['slope_and_predicted_fractions'];ci=x['ci95_columns_slope_p25_p50_p75']
        lines.append(f"| {name} | {100*x['ratio_of_totals']:.3f}% | {100*x['mean_answer_fraction']:.3f}% | {value_ci(v[0],[ci[0][0],ci[1][0]])} | {' / '.join(f'{100*z:.3f}%' for z in v[1:])} | {x['valid_draws']} |")
    lines.extend(['', f"All 5,000 token-model fits met the fixed numerical acceptance criteria, with no reported fit failures; four exponential-overflow runtime warnings were retained in the execution notes. Numerical acceptance does not establish identification. In {boundary['zero_annotated_token_draws']['gpt-4-0613']:,} draws GPT-4 had no annotated token; its stratum parameters approach a boundary despite finite convergence. The analogous GPT-3.5 count was {boundary['zero_annotated_token_draws']['gpt-3.5-turbo-0613']}. GPT-4 slope intervals are therefore unreliable numerical summaries, and GPT-3.5 is also sparse. No retrospective boundary exclusion or replacement fit was performed. The dated execution notes document this limitation separately from the unchanged plan.",
        '', 'The point slopes are positive for five generators and negative for GPT-4, with broad intervals. These differences do not prove or refute the exposure explanation. Span boundaries and annotation conventions can differ across generators; conditioning on answer length does not remove those differences or unmeasured confounding. Question-group refitting supplies descriptive uncertainty, not independent-token standard errors or causal inference.',
        '', 'The token implementation details were fixed in a separate dated amendment before token outcomes; the primary analysis plan remains intact. Runtime notes and boundary diagnostics were added after the run and are labeled as such. Passing tests and numerical convergence check implementation behavior; they do not validate statistical conclusions.',
        '', 'Contrast inventory: original source-only threshold transfer and the frozen coverage representation belong to the earlier external protocol; historical 300-draw comparisons remain unchanged. Raw, rank-normalized and macro length contrasts, within-generator intervals, the GPT-4-excluded sensitivity, cross-fitted incremental value and annotated-token rates are all exposed-target exploratory extensions. No confirmatory contrast or equivalence margin has been tested.'])
    return '\n'.join(lines)+'\n'

if __name__=='__main__':
    (ROOT/'docs/paper/EXPLORATORY_RESULTS.md').write_text(render())
    print('Rendered all contrasts and bounded token-rate summaries')
