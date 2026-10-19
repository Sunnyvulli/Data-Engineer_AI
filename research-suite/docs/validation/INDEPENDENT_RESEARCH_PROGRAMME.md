# Independent research programme: data preparation and reliable ML

Started October19,2026 UTC at the user's request. These are independent projects inspired by broad advertised research areas, not university-affiliated work, commissioned supervisor projects, copied proposals or evidence of admission. Existing qualifications remain unchanged. No external submission is authorized by this document.

## One coherent first paper, three technical strands

Working question: how do training-data selection and source-only calibration affect evidence-support triage under distribution and annotation-unit shifts?

1. Responsible data preparation: compare fixed-budget random question selection with input-only diversity selection. Evaluate annotation-row and question budgets, leakage, duplicate controls, ranking and manual-review burden. This aligns with the user's demonstrated data engineering/data quality work.
2. Reliable language models: retain the earlier frozen open NLI comparator and whole-answer coverage diagnostic. Separate supplied-evidence support from universal factual truth. Additional Bayesian calibration is future work, not already implemented or claimed.
3. Reproducible data systems: provenance, deterministic processing, group-preserving splits, runnable pipelines and measured resource costs. No claim of Spark/Kafka expertise, distributed scalability or production deployment without actual implementation and measurements.

Do not force these strands into three thin papers. The first contribution is a bounded empirical audit; additional papers require distinct, defensible questions and evidence.

## Literature and novelty gate

Data selection and coresets are established research areas. Initial primary sources:
- Niu et al.2024, RAGTruth. https://aclanthology.org/2024.acl-long.585/
- Yang et al.2024, Mind the Boundary: Coreset Selection via Reconstructing the Decision Boundary. https://proceedings.mlr.press/v235/yang24b.html
- Xia et al.2024, Refined Coreset Selection: Towards Minimal Coreset Size under Model Performance Constraints. https://proceedings.mlr.press/v235/xia24b.html
- Yang et al.2023, Towards Sustainable Learning: Coresets for Data-efficient Deep Learning. https://proceedings.mlr.press/v202/yang23g.html
- RLSeek2026 primary entry for feasibility/literature follow-up, not a measured baseline: https://aclanthology.org/2026.acl-long.1492/

A broader related-work comparison and accessible matched modern baselines remain needed. Do not call random/diversity selection, window aggregation, calibration or evaluation original inventions. Original implementation does not establish scientific novelty. Do not claim comparison with a paper's trained system merely because its paper was read.

## Frozen training-budget pilot

Freeze before computing any new selector outcomes. ALCE input hash and RAGTruth hashes/revisions remain those in EXTERNAL_SUPPORT_PROTOCOL.md. All earlier target results have already been inspected: this pilot is explicitly exploratory on exposed benchmarks, not a newly untouched confirmatory test.

Use separately ASQA/ELI5 source records, original six lexical features, fixed source folds from split_groups seed42. Source training consists of train plus unused source fold (81 questions), validation19 questions, matching the original transfer policy. Target remains the same900 RAGTruth answers/150 questions; no target examples train or calibrate models. Published MIT annotation terms and underlying MS MARCO noncommercial terms remain in force. Publish only permitted derived outputs, never source text.

For each source choose floor(fraction*N) complete training question groups, minimum2, fractions.25,.50,1.0. Both selectors use identical question-count budgets; report actual training sentences because question sizes differ. Selection seeds17,42,91. Random: seeded NumPy permutation of sorted group IDs. Diversity: train-only standardize six-feature rows, average by question, seeded first group then greedy maximum minimum squared Euclidean distance; stable input order breaks ties. No labels or validation/target outcomes enter selectors. This is an elementary farthest-first diagnostic, not reproduction of sophisticated published coreset methods. At full budget selectors coincide; fit once per source and reuse, never present duplicate identical experiments as independent evidence.

Fit existing balanced logistic regression with StandardScaler, max_iter2000/random_state42. Fix hyperparameters, no tuning. Calibrate threshold only on original source validation using existing >=90% unsupported-recall rule. If a selected set has only one label class, preserve failure, no resampling to manufacture a valid result. Report training questions/sentences, AP/ROC, recall/FPR/review/misses and selection+fit runtime. Report all settings, not a chosen favorable seed. Full-data original thresholds and AP must reproduce before comparison. No inferential significance claim from these three selection seeds; further cluster uncertainty and independent confirmation are required for any final paper.

Integrity tests must establish selector label blindness, deterministic selection and whole-question membership. Save code and measured outputs with this programme. Do not add pilot findings to career documents until tested and published.

## Author and publication responsibilities

Human authors must understand/verify the work and qualify for authorship; AI is not an author. Follow applicable disclosure requirements. Do not invent university affiliations, coauthors, endorsements or acceptances. Existing manuscript is a draft technical report, not an accepted publication. TMLR's primary policy allows assistive LLM use but assigns responsibility to authors and disallows AI authorship: https://www.jmlr.org/tmlr/editorial-policies.html . Follow target-specific rules. GitHub/preprint posting is distinct from peer-reviewed acceptance. Human author review and explicit authorization precede external submission.
