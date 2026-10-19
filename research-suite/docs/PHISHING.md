# Phishing feature-block robustness

## Question and implementation

How does detection at a fixed validation-selected operating threshold degrade when page or URL feature blocks become unavailable? `src/research_suite/phishing.py` implements this experiment on the primary UCI Phishing Websites archive, using logistic regression and random forests.

Positive label: UCI `Result=-1` (phishing). The alternate `.old.arff` archive member is not used. All 30 original engineered features enter the baseline. A median imputer is fitted on training rows only. Exact feature-vector duplicates, including rows whose labels conflict, share a group and cannot cross splits. Five stratified group folds supply approximately 60/20/20 train/validation/test partitions.

The threshold is the lowest score satisfying <=1% empirical false-positive rate on clean validation data. It stays fixed for every test corruption. Validation control does not guarantee <=1% test or deployment false positives. Page and URL feature groups are explicitly listed in the source before evaluation. Removing them simulates feature-extractor outages, not adversarially generated websites. Remaining features, including some correlated signals, stay available. Median imputation can hide an outage; no claim of missingness-aware training is made.

## Outputs

Clean, missing-page, missing-URL, and randomly masked-20% conditions are evaluated for both classifiers across three seeds. Average precision is reported, not trapezoidal PR-AUC. Confusion counts, operating-point recall, FPR, Brier score, and fit/inference times are recorded. Timing is an indicative batch measurement, not a production latency benchmark.

## Deployment boundary

The CLI supports offline scoring of the same feature schema. It does not fetch websites, collect credentials, or claim to detect current phishing campaigns. No domains or campaign dates are present in this dataset, so exact duplicate grouping is not a substitute for campaign-disjoint or temporal testing. High scores on this historical benchmark do not establish current-world effectiveness.

## Next research gate

Obtain permissioned raw URL/text/screenshot data, audit near-duplicates and campaign provenance, add domain/time-separated evaluation, and compare feature-only with actual multimodal models. Existing systems such as PhishIntention and PhishLLM establish substantial prior work; multimodal detection itself is not a new contribution. A defensible paper needs an additional, demonstrated contribution and stronger datasets.
