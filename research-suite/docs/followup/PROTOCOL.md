# Follow-up evaluation protocol

Protocol fixed October 18, 2026, before inspecting the new evaluation outcomes. This is a protocol record in source control, not an independent preregistration. Existing baseline results have already been inspected and are not treated as a fresh final test.

## Phishing: second corpus and representation artifacts

Use the primary UCI PhiUSIIL archive (dataset 967), interpreting label 0 as phishing and label 1 as legitimate. Load only raw URL and label for predictors. Audit scheme/www/path/query patterns by class; do not feed label-proxy precomputed features to the classifier. Deterministically select the 30,000 lowest SHA-256-ranked unique normalized URLs, retaining duplicate/conflict counts in the audit. Group by normalized full hostname (strip a leading www.) so exact hosts cannot cross partitions; this is not registered-domain or campaign separation. Compare character TF-IDF logistic regression on full URLs versus hostname-only inputs, with max 30,000 features and ngrams 3..5. Use seed 42 and five group folds (60/20/20). Select operating thresholds only on validation at <=1% empirical FPR. Primary metric: test average precision; secondary recall and test FPR. Report paired host-cluster bootstrap intervals for AP difference (300 resamples, seed 20261018). No claim that this is external validation of the incompatible UCI-327 30-feature model. No URLs will be visited or published in outputs.

## Citation support: transfer across domains

Keep the original six lexical features and logistic baseline fixed. Fit on one of ASQA/ELI5 and evaluate on the other, in both directions. Source-domain questions are partitioned into training/validation using a fixed group fold; no target labels enter model fitting or threshold choice. Threshold targets >=90% source validation unsupported recall. Report lexical, learned lexical, review-all, and review-none comparisons. Bootstrap target questions (300 resamples, seed 20261018) and report 95% percentile intervals for AP and unsupported recall. This is corpus transfer, not a new human study or factual-truth benchmark.

## Astronomy: independent simulated objects

Use the frozen seed-42 three-day forest artifact from the baseline release, without refitting or tuning. Fetch the first primary PLAsTiCC test light-curve shard and test metadata from Zenodo record 2539456. Evaluate the first 5,000 sorted complete object IDs in shard 01, chosen without examining labels. The final partially read object must be discarded if streaming stops mid-object. Restrict features to observations from first detection through +3 days, as before. Require no overlap with original training-metadata IDs. Use true_target=64 only as the evaluation label; no truth metadata enters predictors. Compare AP and top-5% precision/recall to expected random performance. Bootstrap object IDs (300 resamples, seed 20261018). All results remain simulation-based and conditional on objects having a detection.

## Reporting

Keep measured negative results, input hashes, split counts, environment, uncertainty assumptions, excluded objects, and unexecuted comparisons. Bootstrap intervals do not correct dataset bias or establish scientific novelty. A contemporary specialised-baseline comparison and real-world external validation remain separate requirements.

## Pre-execution clarification

The citation transfer table also includes the released ALCE `automatic_recall_scores`, aligned by sentence, at the original binary operating point. These are historical released predictions, not a newly executed entailment model. This comparison was added before running or inspecting follow-up outcomes. URL normalization trims only outer whitespace for exact-URL deduplication; path/query case remains intact. Host grouping lowercases the parsed host and strips trailing dot/leading www. No claim of registered-domain separation is made.
