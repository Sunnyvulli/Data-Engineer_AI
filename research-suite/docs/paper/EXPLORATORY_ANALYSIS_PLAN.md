# Exploratory length and evidence-score analysis plan

Frozen 25 October 2026, against repository base `52e616a`. Commit this plan before implementing or running the additional analyses below. Prior target labels, scores, length diagnostics and reviewer comments have already been inspected. This is an auditable post-exposure plan, not preregistration, independent confirmation, or a repair of earlier outcome exposure. Existing 300-draw intervals remain historical results.

## Inputs and alignment

Use exactly the retained 900 RAGTruth QA answers, 150 `source_id` question groups and six generators; positive means at least one released hallucination span. Reconcile record identifiers/order, labels, groups, generators, saved coverage risks and cached `claim_tokens` before computing new results. Length is the existing full-answer token count, with no new tokenizer or direction selection. Assert the published sample/positive counts and exact cached risk-vector agreement. Record package versions, input hashes, code commit and plan commit with outputs. Abort on unexpected mismatch; document any amendment in a separate commit before rerunning.

| Input | SHA-256 |
| --- | --- |
| `results/validation/external-support-scores.json` | `793cc7f33161783a4fab6324e7fbeca3415f627d6b976fbfba106122874b1526` |
| `results/validation/ragtruth-coverage-risks.json` | `d04c1bd89769f12833a99591a5729579ef72e678d5c47839ba57c059f9f928d3` |
| `results/validation/review-diagnostics.json` | `54348715337cc8af4f3caeaa2b85c3de5b662e78bb288c02d338cdfb8cb4c84a` |

## Fixed contrasts and resampling

For both scikit-learn average precision (AP, not trapezoidal PR area) and ROC AUC, use these fixed exploratory contrasts, with positive differences favoring length:

1. Raw longer-answer length minus raw coverage NLI on all rows.
2. Within-generator average tied rank divided by generator sample size, pooled across rows: normalized length minus identically normalized coverage NLI. Recompute both rank transformations within every bootstrap sample, counting duplicate sampled rows. This is a transductive diagnostic, not a source-only policy.
3. Equal-weight mean of the six within-generator metric differences. Report each generator separately as well. Macro AP mixes strata with different prevalence and is descriptive; it is not a standardized deployment AP.

Use exactly 5,000 draws from `numpy.random.default_rng(20261025)`. Sort unique question IDs lexicographically and draw 150 IDs with replacement per draw, retaining every answer and duplicate-group multiplicity. Apply each draw to all compared scores; never bootstrap answers independently. Save the draw indices. Report observed differences and the 2.5th/97.5th percentiles using NumPy's linear quantile method. No significance-driven increase in draws, seed search, preferred contrast selection, or multiplicity-adjusted significance claim.

Define both AP and AUC contrasts as unavailable on a one-class sample/stratum. A macro draw requires valid paired metrics in every included generator; otherwise mark it unavailable. Report valid/invalid draw counts per contrast, do not replace invalid draws, and do not silently average fewer generators. GPT-4's single positive will make many six-generator macro draws unavailable: label those intervals conditional on valid draws and especially unstable. Report percentile intervals as unavailable if fewer than 1,000 valid draws remain.

The primary descriptive population retains GPT-4 (`gpt-4-0613`). The one fixed sensitivity removes every GPT-4 answer, retains all 150 question groups, and repeats all three contrasts using the same saved group draws and five remaining generators. Present both populations regardless of direction or interval width. Do not exclude other generators or select a preferred sensitivity result. Shorter-is-riskier historical metrics remain available but are not an alternative selected hypothesis.

## Incremental-value comparison

These are target-supervised exploratory diagnostics, never source-only deployment results. Predict the same binary answer label using two fixed L2-penalized logistic regressions:

- M0: intercept + `log1p(claim_tokens)` + generator indicators.
- M1: M0 + raw continuous coverage-NLI risk.

Use `StandardScaler` for continuous features, fitted only on the training fold; one-hot generator indicators with the alphabetically first generator as reference and a fixed sorted category list. Use `LogisticRegression(C=1.0, penalty="l2", solver="lbfgs", class_weight=None, tol=1e-8, max_iter=10000, fit_intercept=True)`. No interactions, splines, length-transform alternatives, hyperparameter tuning, class balancing or outcome-selected feature changes. Stop and report convergence failure instead of changing settings after seeing performance.

Assign the sorted 150 unique question IDs using `KFold(n_splits=5, shuffle=True, random_state=20261025)` exactly once. Keep all six answers to a question together and save group/fold assignments. Each held-out prediction must come from a model fitted exclusively on the other question groups. Preprocessing also stays inside each training fold. Check held-out-label perturbations cannot alter that fold's predictions. Score pooled out-of-fold probabilities, not averages of fold metrics.

Report M0 and M1 AP/AUC and paired gains M1 minus M0, with the same 5,000 saved group draws and percentile rules. The bootstrap resamples fixed out-of-fold predictions; it does not refit models and does not estimate training or fold-selection uncertainty. Fold training sets overlap, so these conditional intervals are not full repeated-sample learning-procedure inference. Do not present them as a definitive incremental-value test. As the fixed GPT-4 sensitivity, refit both models without GPT-4 using the same question-fold assignments, the remaining sorted categories and otherwise identical settings. Report it alongside, never instead of, the complete sample.

## Bounded annotation-exposure check

This check is planned, not executed by committing this document. Use only the pinned RAGTruth release already specified in the external protocol; verify its hashes, offset convention and the coverage tokenizer's immutable revision before analysis. Validate every character span against its answer, including Unicode boundaries. Merge overlapping character spans. Count an answer token as annotated when its non-special-token character offsets have positive overlap with that merged union; count each token once. The denominator is all non-special answer tokens from that same pinned tokenizer, without truncation. Reconcile it with cached length and report discrepancies; do not silently substitute a tokenizer. If reliable offset mapping cannot be recovered, report this check blocked. Do not download a different tokenizer or benchmark to improvise a result.

Retain zero-span answers. Report per generator: number of answers, annotated-token total, answer-token total, ratio of totals, mean answer-level fraction, and answer-length distribution. Zero-token answers, if any, stay in the inventory but have undefined rates; report their count. Fit one exploratory grouped-rate model to nonempty answers: binomial-logit GLM of annotated/total token count with token-count trial weights, `log1p(answer_tokens)`, generator indicators and generator-by-log-length interactions. No outcome-selected terms. Report each generator's log-length slope and predicted fraction at that generator's observed 25th/50th/75th length percentiles. Use the same saved question draws, refitting that GLM in each draw for descriptive percentile intervals; report fitting failures without replacement. Do not treat tokens as independent evidence for standard errors. Freeze exact library/version and implementation details in a committed amendment before this extension runs if not supported by the existing environment.

Character-span annotations and their boundaries can vary by generator or guideline interpretation. A flat or rising token-rate trend cannot settle semantic quality, per-claim error, causal exposure or annotation bias. No claim-level rate will be fabricated without valid segmentation. The model conditions on length; it does not remove all confounding.

## Reporting and next gates

Every new table, figure and contrast is labeled **exploratory, exposed target**. Report all fixed comparisons, failures, valid draws and sensitivities, with no equivalence/non-inferiority or general superiority claim. A zero-crossing interval is not evidence of equivalence; a nonzero interval is still a conditional exploratory finding. Preserve the historical output files; write new analyses separately. Add a contrast inventory distinguishing the original frozen protocol from these post-exposure analyses.

Before the stronger comparator runs, verify AttrScore checkpoint suitability, labels/risk mapping, license/revisions, training overlap, context/window policy and source-only calibration under `REVIEW_RESPONSE_PROTOCOL.md`. Resolve the exact checkpoint rather than assuming parameter count establishes suitability. No paid judge or API is authorized by this plan. Fresh confirmation requires a genuinely unexamined compatible dataset and a new frozen hypothesis/margin before opening outcomes. Independent human review requires an actual advisor/domain-expert read and a double-annotated subsample with agreement reporting; generated review perspectives do not meet that requirement.
