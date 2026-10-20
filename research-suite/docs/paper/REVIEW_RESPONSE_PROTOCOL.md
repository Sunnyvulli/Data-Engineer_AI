# Citation-support review response protocol

20 October 2026. The published target outcomes and the supplied critique have already been seen. Everything below is post hoc and cannot restore a blinded confirmation set. This document precedes the new diagnostic computation; it is not the original external-validation registration.

## Diagnostics on existing predictions

Use all 900 saved rows, retain their source_id groups and labels, and hash the complete inputs. Read answer token lengths and inference-pair counts from the existing coverage audit, checking identical risk vectors and record counts before alignment. Do not obtain or redistribute raw passages.

Report both longer-is-riskier and shorter-is-riskier token-length rankings, with AP and ROC AUC; neither direction is selected as a winner. Report generator counts, positive counts, prevalence and within-generator detector AP/AUC (undefined for a one-class stratum). Also report pooled generator-prior AP/AUC from five complete-question held-out folds, seeded 20261020, with a Beta(1,1) smoothed rate estimated only from the other folds. Keep every response to a question together. This diagnostic uses target labels for training and is therefore NOT a source-only comparator or a deployable hallucination detector. Save folds and derived scores for inspection.

Report source coverage thresholds with their recorded 19-question sample sizes; do not manufacture source-label distributions absent from the cache. The two thresholds are empirical source score quantiles, not comparable probabilities or evidence identifying a causal corpus effect. Fresh source-group uncertainty and a controlled window ablation remain future work.

## Stronger matched comparator: pending execution

AttrScore (Yue et al., Findings EMNLP 2023, DOI 10.18653/v1/2023.findings-emnlp.307) is directly relevant. Use its official OSU-NLP-Group/AttrScore implementation and released checkpoint; verify and record immutable code/weight/tokenizer revisions, licenses and training overlap before downloading or running. The repository advertises Flan-T5 3B/11B and LLaMA/Alpaca 7B variants. No such model has been executed for this manuscript. Do not substitute the paper's headline F1 for AP on our task.

Before inference, fix the specific checkpoint, prompt, allowed maximum context, truncation/window policy, and unsupported-risk mapping for Attributable / Contradictory / Extrapolatory. Test the class mapping on documented fixtures. Where only discrete generation is available, report discrete operating points and tied-score AP; do not invent calibrated class probabilities. Fit any threshold only on the original source validation groups. Report coverage/truncation and failed inputs, wall time and peak memory actually observed; set a local resource cap before execution. No paid API or cloud deployment is authorized here.

Evaluate on exactly the existing 900 rows for exploratory comparability and label it exposed-target analysis. For a confirmatory claim, register a new untouched group-separated selection, check training overlap and annotation-unit compatibility, and freeze model selection before opening its outcomes. Report AP, ROC AUC, recall/FPR/review burden, all predeclared paired contrasts, and complete-question uncertainty. Use a larger fixed bootstrap budget (at least 5,000) for a new run; if making simultaneous inference, predeclare the family and correction. Do not rerun until significance appears.

AttributionBench (Li et al., Findings ACL 2024, DOI 10.18653/v1/2024.findings-acl.886) supplies relevant evaluation context. Its macro-F1 is not directly comparable to this audit's AP. A controlled window study must separately vary coverage and aggregation while holding weights, groups and labels fixed; corpus, generator mixture, annotation unit and label semantics cannot all vary if a causal explanation is claimed.

## Within-generator length extension — 20 October 2026

The owner supplied within-generator calculations after viewing the original diagnostics. This extension is therefore post hoc, not a registration or independent replication. Report length AP/AUC within all six generators, including the one-positive GPT-4 stratum with an explicit instability warning. Preserve tied lengths with average ranks, divided by the number of answers in that generator; pool those normalized scores across all 900 rows. This uses target generator identities and their unlabeled length distribution, not target labels, but is transductive and is not an inference-time source-calibrated policy. Save every normalized score. Apply the identical rank normalization to coverage NLI as a descriptive symmetry check, keeping raw coverage metrics alongside it. Do not interpret point differences as statistical equivalence, superiority or a causal decomposition of generator and length effects. No new threshold or significance claim is selected from these diagnostics.
