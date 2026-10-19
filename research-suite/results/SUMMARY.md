# Measured baseline results

Generated from the committed experiment JSON, not manually entered scores. Each cell is **mean [minimum, maximum]** over seeds 17, 42, and 91. These are overlapping split repetitions, not confidence intervals. Average precision is the non-interpolated AP metric. Scores refer only to the documented datasets and policies.

## Phishing robustness

11,055 records; 5,785 unique feature-vector groups. Exact feature duplicates do not cross partitions. Positive class is phishing. Threshold targets validation FPR <=1%, without guaranteeing that test FPR stays below that value.

| model | condition | average_precision | recall | false_positive_rate |
| --- | --- | --- | --- | --- |
| forest | clean | 0.9887 [0.9849, 0.9909] | 0.8331 [0.8049, 0.8718] | 0.0108 [0.0065, 0.0154] |
| forest | missing_page | 0.9533 [0.9423, 0.9642] | 0.4817 [0.4077, 0.6256] | 0.0086 [0.0049, 0.0121] |
| forest | missing_url | 0.9812 [0.9786, 0.9833] | 0.8308 [0.8094, 0.8637] | 0.0141 [0.0114, 0.0162] |
| forest | random_20pct | 0.9646 [0.9619, 0.9678] | 0.6683 [0.6432, 0.7040] | 0.0124 [0.0057, 0.0187] |
| logistic | clean | 0.9756 [0.9743, 0.9770] | 0.6904 [0.6384, 0.7355] | 0.0070 [0.0016, 0.0138] |
| logistic | missing_page | 0.9148 [0.9017, 0.9299] | 0.3209 [0.1716, 0.4435] | 0.0097 [0.0041, 0.0211] |
| logistic | missing_url | 0.9670 [0.9666, 0.9674] | 0.6326 [0.5761, 0.6755] | 0.0049 [0.0008, 0.0073] |
| logistic | random_20pct | 0.9508 [0.9442, 0.9543] | 0.5093 [0.4586, 0.5605] | 0.0062 [0.0024, 0.0121] |

Interpretation: page-feature loss substantially reduces operating-point recall. The high clean average precision does not establish current-campaign generalisation, multimodal performance, or deployment readiness. The feature-block definitions leave other correlated features available.

## Citation-support triage

2,604 human-labelled sentences from 200 questions. All model outputs for a question remain in one partition. Unsupported means not fully supported by the provided citations, not necessarily false.

| policy | average_precision | recall | review_fraction | unsupported_fraction_among_unflagged |
| --- | --- | --- | --- | --- |
| learned_lexical | 0.9081 [0.9039, 0.9139] | 0.9253 [0.9188, 0.9356] | 0.6589 [0.6453, 0.6853] | 0.0983 [0.0920, 0.1038] |
| lexical | 0.8957 [0.8939, 0.8970] | 0.9254 [0.9103, 0.9389] | 0.6686 [0.6415, 0.6965] | 0.1007 [0.0897, 0.1135] |
| review_all | 0.4496 [0.4455, 0.4535] | 1.0000 [1.0000, 1.0000] | 1.0000 [1.0000, 1.0000] | N/A |
| review_none | 0.4496 [0.4455, 0.4535] | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 0.4496 [0.4455, 0.4535] |

Interpretation: selective policies reduce the number of flagged sentences relative to review-all, but leave unsupported sentences in the unflagged set. Review fraction is a count proxy: no reviewer time or student-learning improvement was measured. Even a low-risk sentence may contain a contradiction. Review-all/none AP reflects constant-score prevalence and is not evidence of ranking quality.

## Early kilonova prioritisation

1,421,705 simulated observations and 7,848 labelled metadata objects. Eligible test objects require an actual simulated detection flag; see split logs for evaluated counts. No simulation truth metadata enters predictors. Follow-up budget is top 5% by candidate count.

| horizon_days | model | average_precision | precision_at_budget | recall_at_budget |
| --- | --- | --- | --- | --- |
| 1 | forest | 0.0424 [0.0336, 0.0562] | 0.0422 [0.0127, 0.0633] | 0.1595 [0.0500, 0.2381] |
| 1 | logistic | 0.0254 [0.0182, 0.0321] | 0.0253 [0.0127, 0.0380] | 0.0960 [0.0500, 0.1429] |
| 1 | random_expected | 0.0132 [0.0127, 0.0134] | 0.0132 [0.0127, 0.0134] | 0.0503 [0.0503, 0.0503] |
| 3 | forest | 0.0896 [0.0551, 0.1459] | 0.0675 [0.0506, 0.0886] | 0.2571 [0.2000, 0.3333] |
| 3 | logistic | 0.0322 [0.0237, 0.0372] | 0.0253 [0.0000, 0.0506] | 0.0952 [0.0000, 0.1905] |
| 3 | random_expected | 0.0132 [0.0127, 0.0134] | 0.0132 [0.0127, 0.0134] | 0.0503 [0.0503, 0.0503] |
| 7 | forest | 0.1560 [0.1238, 0.2198] | 0.1013 [0.0886, 0.1139] | 0.3865 [0.3500, 0.4286] |
| 7 | logistic | 0.0291 [0.0198, 0.0438] | 0.0338 [0.0127, 0.0633] | 0.1278 [0.0500, 0.2381] |
| 7 | random_expected | 0.0132 [0.0127, 0.0134] | 0.0132 [0.0127, 0.0134] | 0.0503 [0.0503, 0.0503] |

Interpretation: forest ranking benefits from longer observation windows in these runs. Most selected candidates are still not kilonovae, and many kilonovae remain unselected. The expected-random comparison uses held-out prevalence. These are simulated light curves and retrospective rankings, not discoveries or a real telescope scheduling trial.

## Validation and review

- Integrity checks cover grouped splitting, label direction, thresholds with tied scores, invalid inputs, human-label exclusion, alert cutoffs, and future-observation invariance.
- Offline batch prediction is smoke-tested with locally trained artifacts for all three projects.
- Source-data hashes, software versions, split counts, and complete per-seed metrics are in adjacent JSON files.
- No claim of statistical significance, new state of the art, publication acceptance, production certification, or external peer review is made.
- Human owner review, contemporary specialised baselines, out-of-domain evaluation, and a demonstrated new contribution are still needed before a paper submission.
