# Training-data selection pilot: all settings and skeptical review

October19,2026 UTC. Protocol committed before new selector outcomes at1fe44e3ec5ef94889516e72a28291f3f7ed1fb79. This is an exploratory extension on the already-exposed RAGTruth target, not an untouched confirmation, a new coreset algorithm or a separate accepted paper.

26 actual fitted policies and10 reused full-data references; both full-data policies reproduced prior ALCE thresholds and AP to1e-12 before comparison.26 saved prediction vectors independently reconciled for AP/ROC/recall/FPR/review to1e-12.58 integrity tests passed locally. No one-class selected-set failures occurred.

The budget is training question count, not sentence count, annotation time or total compute. Selectors may examine all source-training features without labels; train-pool preprocessing is allowed by protocol. Sentence counts differ between selected questions, so this does not establish equal annotation cost. No target rows/labels enter training or threshold calibration. Original source validation has only19 questions; uncertain thresholds can transfer poorly.

| Source | Question budget | Selector | Seed | Training questions / sentences | Target AP | Recall | FPR | Review |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| asqa | 25% | random | 17 | 20 / 167 | 0.4529 | 1.000 | 1.000 | 1.000 |
| asqa | 25% | random | 42 | 20 / 167 | 0.4298 | 1.000 | 0.993 | 0.994 |
| asqa | 25% | random | 91 | 20 / 161 | 0.1352 | 0.050 | 0.143 | 0.127 |
| asqa | 25% | diversity | 17 | 20 / 156 | 0.4328 | 1.000 | 1.000 | 1.000 |
| asqa | 25% | diversity | 42 | 20 / 140 | 0.3114 | 1.000 | 0.995 | 0.996 |
| asqa | 25% | diversity | 91 | 20 / 159 | 0.4349 | 1.000 | 1.000 | 1.000 |
| asqa | 50% | random | 17 | 40 / 338 | 0.2068 | 0.950 | 0.823 | 0.846 |
| asqa | 50% | random | 42 | 40 / 317 | 0.3258 | 1.000 | 0.991 | 0.992 |
| asqa | 50% | random | 91 | 40 / 311 | 0.2181 | 0.906 | 0.750 | 0.778 |
| asqa | 50% | diversity | 17 | 40 / 335 | 0.2410 | 1.000 | 0.986 | 0.989 |
| asqa | 50% | diversity | 42 | 40 / 318 | 0.2788 | 1.000 | 1.000 | 1.000 |
| asqa | 50% | diversity | 91 | 40 / 337 | 0.2809 | 1.000 | 0.993 | 0.994 |
| asqa | 100% | random | 17 | 81 / 639 | 0.2808 | 1.000 | 0.986 | 0.989 |
| eli5 | 25% | random | 17 | 20 / 353 | 0.2019 | 0.825 | 0.686 | 0.711 |
| eli5 | 25% | random | 42 | 20 / 328 | 0.3170 | 1.000 | 0.930 | 0.942 |
| eli5 | 25% | random | 91 | 20 / 349 | 0.1636 | 0.200 | 0.235 | 0.229 |
| eli5 | 25% | diversity | 17 | 20 / 341 | 0.3056 | 1.000 | 0.964 | 0.970 |
| eli5 | 25% | diversity | 42 | 20 / 364 | 0.1550 | 0.200 | 0.268 | 0.256 |
| eli5 | 25% | diversity | 91 | 20 / 299 | 0.2327 | 0.881 | 0.709 | 0.740 |
| eli5 | 50% | random | 17 | 40 / 704 | 0.2049 | 0.863 | 0.732 | 0.756 |
| eli5 | 50% | random | 42 | 40 / 683 | 0.2833 | 0.994 | 0.901 | 0.918 |
| eli5 | 50% | random | 91 | 40 / 705 | 0.1657 | 0.356 | 0.374 | 0.371 |
| eli5 | 50% | diversity | 17 | 40 / 679 | 0.2758 | 0.994 | 0.835 | 0.863 |
| eli5 | 50% | diversity | 42 | 40 / 692 | 0.2023 | 0.812 | 0.661 | 0.688 |
| eli5 | 50% | diversity | 91 | 40 / 666 | 0.2009 | 0.681 | 0.519 | 0.548 |
| eli5 | 100% | random | 17 | 81 / 1430 | 0.2180 | 0.819 | 0.641 | 0.672 |

## Interpretation

There is no consistently dominant selector. Some smaller-data models rank better than the full-data lexical reference on this exposed target, but choosing one after observing outcomes would bias a final claim. Retain every seed. At25% budget one ASQA random setting catches only5% of target positives; several other settings achieve100% recall while reviewing effectively every answer. These settings therefore demonstrate sensitivity and workload tradeoffs, not a reliable data-efficiency improvement. Three selection seeds are insufficient for significance claims and do not capture source-fold or dataset-selection uncertainty.

## Four-perspective self-review

- Student/reproducer: scripts record selected whole-question IDs, source-only calibration, exact budgets and full derived risks. Tests check deterministic label-blind selection and group membership. Understand and reproduce the run before claiming authorship.
- Professor: farthest-first diversity is an established elementary method. Current literature already studies coresets extensively. The pilot does not reproduce those sophisticated systems, prove novelty or validate Bayesian calibration. A meaningful claim needs broader matched baselines and confirmation.
- Industry user: lower label count is not necessarily lower cost or safe triage. Actual sentences vary; most high-recall settings impose large review burdens. No deployment performance, saved money or production scalability is measured.
- Critical reviewer: previous target exposure is disclosed; no favorable seed was removed; full-data duplicates are references, not independent experiments. Target-independent protocol freezing does not erase earlier benchmark exposure. Independent human review has not happened.

## Next research gate

Before calling this a publishable contribution: establish a precise gap against the cited coreset/selection literature; use matched cost budgets and stronger feasible baselines; reserve a genuinely unexposed, permissioned target for confirmation; report question-cluster uncertainty and source-fold variability. Any new protocol must state which previous outcomes were exposed. Integrate useful results into one coherent manuscript rather than generating three overlapping papers.

Use python -m research_suite.data_selection --data data/raw --output results/validation from the suite root. Compressed data-selection-scores.json.gz contains IDs/groups/labels/risks only, no restricted text. The JSON aggregates and audit accompany the original code. Human author verification and explicit external-submission authorization remain required. No university affiliation is claimed.
