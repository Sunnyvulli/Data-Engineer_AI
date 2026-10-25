### 4.2. Exploratory paired contrasts and incremental value

All results in this section use the exposed target. The original plan was committed in 9002e048b42cec344165f8f8e4fe94f59a0e8bd6 before these additional calculations; its text remains unchanged. Exactly 5,000 complete-question bootstrap draws, seed 20261025, are shared across scores and populations. Intervals are conditional 95% percentile summaries, uncorrected for multiple contrasts. AP means scikit-learn average precision. Positive length-minus-NLI differences favor length; positive M1-minus-M0 differences favor the augmented model. Every planned contrast, including zero-crossing intervals, is reported.

Table 6. Exploratory exposed-target paired differences. Rank transformations are recomputed within every sampled generator, retaining duplicate-group multiplicity. Macro averages weight generators equally and require every included stratum to contain both classes. Counts show valid/invalid draws; invalid draws are never replaced.

| Population | Contrast | AP diff [95%] | AUC diff [95%] | Valid / invalid |
| --- | --- | --- | --- | --- |
| All six | Raw length - NLI | 0.1045 [0.0255, 0.1848] | 0.0279 [-0.0291, 0.0831] | 5000 / 0 |
| All six | Ranked length - NLI | 0.0594 [0.0005, 0.1214] | 0.0068 [-0.0549, 0.0709] | 5000 / 0 |
| All six | Macro length - NLI | 0.0866 [-0.0083, 0.1786] | -0.1029 [-0.1730, -0.0326] | 3156 / 1844 |
| All six | M1 - M0 | 0.0297 [0.0109, 0.0486] | 0.0170 [0.0036, 0.0307] | 5000 / 0 |
| No GPT-4 | Raw length - NLI | 0.1043 [0.0256, 0.1827] | 0.0486 [-0.0107, 0.1061] | 5000 / 0 |
| No GPT-4 | Ranked length - NLI | 0.0734 [0.0018, 0.1466] | 0.0117 [-0.0525, 0.0772] | 5000 / 0 |
| No GPT-4 | Macro length - NLI | 0.1061 [-0.0059, 0.2160] | -0.0107 [-0.0925, 0.0687] | 4972 / 28 |
| No GPT-4 | M1 - M0 | 0.0285 [0.0105, 0.0470] | 0.0211 [0.0045, 0.0380] | 5000 / 0 |

Raw length has a positive pooled AP difference in this conditional exploratory analysis, whereas both raw and rank-normalized AUC intervals cross zero. The equal-weight macro AUC favors NLI with all generators but crosses zero after GPT-4 is removed. The complete-sample macro interval is conditional on 3,156 valid draws and is particularly unstable because GPT-4 has one positive. These are different estimands, not a basis for selecting a favorable ranking or establishing general superiority or equivalence.

Table 7. Exploratory within-generator length-minus-NLI contrasts. The five retained per-generator contrasts are numerically identical in the GPT-4-excluded sensitivity because their rows and shared question draws are unchanged. Sparse-stratum intervals condition on valid draws; the one-positive GPT-4 interval is not reliable population inference.

| Generator | AP diff [95%] | AUC diff [95%] | Valid | Invalid |
| --- | --- | --- | --- | --- |
| gpt-3.5-turbo-0613 | 0.1515 [-0.2636, 0.6067] | -0.1538 [-0.4257, 0.1164] | 4972 | 28 |
| gpt-4-0613 | -0.0110 [-0.0414, -0.0080] | -0.5638 [-0.6545, -0.4698] | 3174 | 1826 |
| llama-2-13b-chat | 0.1029 [-0.0430, 0.2605] | 0.0837 [-0.0494, 0.2152] | 5000 | 0 |
| llama-2-70b-chat | -0.0157 [-0.1665, 0.1346] | -0.0622 [-0.1950, 0.0707] | 5000 | 0 |
| llama-2-7b-chat | 0.0159 [-0.1250, 0.1608] | -0.0384 [-0.1630, 0.0902] | 5000 | 0 |
| mistral-7B-instruct | 0.2759 [0.0931, 0.4267] | 0.1172 [-0.0144, 0.2427] | 5000 | 0 |

M0 is L2 logistic regression using log1p(answer tokens) and generator indicators; M1 adds continuous coverage-NLI risk. Five fixed question-group folds keep preprocessing and fitting inside training groups. Neither model is a source-only policy: both train on other exposed-target groups. Out-of-fold probabilities are pooled for scoring. The paired bootstrap treats these predictions as fixed and omits refitting, fold-selection and training uncertainty; overlapping fold training sets further limit interpretation.

Table 8. Exploratory pooled out-of-fold model scores. The paired gains and all intervals appear in Table 6.

| Population | M0 AP | M1 AP | M0 AUC | M1 AUC |
| --- | --- | --- | --- | --- |
| All six | 0.3948 | 0.4245 | 0.7747 | 0.7917 |
| No GPT-4 | 0.3981 | 0.4265 | 0.7238 | 0.7449 |

NLI contributes a positive conditional incremental signal under these fixed specifications, including after GPT-4 removal. That observation prevents a blanket conclusion that evidence reading adds nothing beyond length and generator. It is a hypothesis for genuinely fresh confirmation, not an established general finding or a source-transfer improvement. No configuration was tuned after these outcomes.

### 4.3. Bounded annotation-token exposure check

The pinned RAGTruth response file and coverage tokenizer were hash-verified. All 235 retained annotation spans exactly matched Unicode character slices, and all 900 full-answer token lengths matched cached counts. Overlapping spans were merged; a non-special answer token counted once if its offsets overlapped any annotated character span. No answers had zero tokens. This is annotated token coverage, not per-claim error or a certificate of semantic correctness.

Table 9. Exploratory generator-specific rates and length-adjusted binomial-logit slopes. Total rate is annotated tokens divided by all answer tokens; mean rate averages answer fractions. The interaction model uses a separate intercept and log1p(length) slope per generator. Predicted fractions are at that generator's observed length quartiles. Full predicted-fraction intervals, token totals, length distributions, row counts and every saved fit are released in token-rate-analysis.json and token-rate-resamples.json.gz.

| Generator | Total rate | Mean rate | Length slope [95%] | Predicted Q1 / Q2 / Q3 | Accepted draws |
| --- | --- | --- | --- | --- | --- |
| gpt-3.5-turbo-0613 | 1.211% | 0.703% | 3.7392 [-1.0407, 13.7289] | 0.024% / 0.187% / 0.658% | 5000 |
| gpt-4-0613 | 0.111% | 0.204% | -2.3550 [-3.9183, 0.0000] | 0.136% / 0.078% / 0.050% | 5000 |
| llama-2-13b-chat | 6.332% | 5.529% | 0.9522 [-0.0737, 2.1350] | 4.001% / 5.310% / 6.859% | 5000 |
| llama-2-70b-chat | 7.317% | 5.726% | 2.1824 [-0.1413, 4.2142] | 2.356% / 4.262% / 6.894% | 5000 |
| llama-2-7b-chat | 7.486% | 6.987% | 0.6803 [-0.3080, 1.6951] | 5.895% / 6.875% / 8.027% | 5000 |
| mistral-7B-instruct | 6.845% | 4.736% | 1.8760 [0.2603, 3.5291] | 2.002% / 3.826% / 6.242% | 5000 |

All 5,000 token-model fits met the fixed numerical acceptance criteria, with no reported fit failures; four exponential-overflow runtime warnings were retained in the execution notes. Numerical acceptance does not establish identification. In 1,826 draws GPT-4 had no annotated token; its stratum parameters approach a boundary despite finite convergence. The analogous GPT-3.5 count was 28. GPT-4 slope intervals are therefore unreliable numerical summaries, and GPT-3.5 is also sparse. No retrospective boundary exclusion or replacement fit was performed. The dated execution notes document this limitation separately from the unchanged plan.

The point slopes are positive for five generators and negative for GPT-4, with broad intervals. These differences do not prove or refute the exposure explanation. Span boundaries and annotation conventions can differ across generators; conditioning on answer length does not remove those differences or unmeasured confounding. Question-group refitting supplies descriptive uncertainty, not independent-token standard errors or causal inference.

The token implementation details were fixed in a separate dated amendment before token outcomes; the primary analysis plan remains intact. Runtime notes and boundary diagnostics were added after the run and are labeled as such. Passing tests and numerical convergence check implementation behavior; they do not validate statistical conclusions.

Contrast inventory: original source-only threshold transfer and the frozen coverage representation belong to the earlier external protocol; historical 300-draw comparisons remain unchanged. Raw, rank-normalized and macro length contrasts, within-generator intervals, the GPT-4-excluded sensitivity, cross-fitted incremental value and annotated-token rates are all exposed-target exploratory extensions. No confirmatory contrast or equivalence margin has been tested.
