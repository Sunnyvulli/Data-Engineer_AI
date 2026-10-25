# Length Baselines and Evidence-Support Triage: An ALCE-to-RAGTruth Audit

Hanumantha Rao Vulli

Research manuscript draft for author review. Revised October 25, 2026 UTC. Not peer reviewed or accepted. No institutional affiliation is asserted.

## Abstract

No advantage for the tested evidence-reading scores over answer length was established on this set; neither approach was shown superior. We revisit source-calibrated lexical and small natural-language-inference (NLI) policies on 900 RAGTruth QA answers from 150 question groups, with 160 positives. In a post-hoc diagnostic, longer-answer ranking yields average precision (AP) 0.386 and ROC AUC 0.727, compared with coverage NLI AP 0.281 and AUC 0.699. Length ranked within each generator and pooled yields AP 0.296 and AUC 0.632; identically normalized coverage NLI yields AP 0.236 and AUC 0.625. These point estimates lack paired length-versus-NLI uncertainty intervals, and within-generator AUC comparisons are mixed. They do not establish equivalence or superiority. Generator positive counts range from 1 to 52 per 150 answers. Length has above-chance AUC in five generator strata; the remaining GPT-4 stratum has only one positive and length AUC 0.074. Generator mixture, answer length and annotation exposure cannot be causally separated. Historical ALCE sentence comparisons and frozen RAGTruth thresholds provide context: ASQA lexical flags 98.9% of answers; ELI5-calibrated coverage NLI misses 14 of 160 positives while flagging 70.9%. The original coverage-versus-lexical AP intervals, ELI5 [0.017, 0.117] and ASQA [-0.053, 0.054], are exploratory, uncorrected contrasts from 300 question-cluster resamples. The later length diagnostics and this reframing were prompted by exposed outcomes and critique, not preregistered confirmation. We release code, derived scores and failure audits, with restricted source text kept local.

## 1. Research question and bounded contribution

The primary question in this revised manuscript is whether the tested evidence-reading rankings establish an advantage beyond a trivial answer-length control on this particular benchmark. No advantage for evidence-reading scores over length has been established on this set, and neither approach has been shown superior. Raw length has a higher pooled AP point estimate than the tested detectors, but paired uncertainty for that contrast is not yet available and coverage NLI has higher AUC in four of six generator strata. The comparison remains exploratory; it does not establish reliable detection or statistical equivalence.

The original study asked whether source-calibrated policies retain recall and manageable workload across ALCE sentences and RAGTruth whole answers, with a diagnostic comparison of bounded and coverage NLI representations. That protocol preceded target scoring. Length and generator controls were introduced after the outcomes and critiques were exposed, and motivated the revised framing. They are post-hoc observational diagnostics; the original source-transfer question remains secondary context. Stronger matched detectors and a fresh frozen confirmation set remain untested.

ALCE evaluates answers with citations and provides human sentence-support annotations (Gao et al., 2023). RAGTruth provides manually annotated hallucination spans in generated responses grounded in supplied material (Niu et al., 2024). Their annotations serve related purposes but are not identical constructs. This manuscript reports an empirical audit; it does not introduce a new learning algorithm, claim a first use of window aggregation, establish state-of-the-art performance, or establish a comprehensive novelty result. Previously exposed ALCE comparisons are historical context. The new RAGTruth protocol was committed before its model outcomes were computed.

## 2. Data, labels and independence

The ALCE annotation file contains 2,604 sentences from 200 supplied question groups across ASQA and ELI5. All available model responses to the same supplied question stay together. Source train and validation sets follow the existing seed42 split: ASQA has 639 training sentences from 81 questions and 172 validation sentences from 19 questions; ELI5 has 1,430 training sentences from 81 questions and 363 validation sentences from 19 questions. Unsupported is the positive class, defined as one minus the binary human sentence-support label. The other domain is an exposed historical target, never used to calibrate the new external experiment.

The independent external selection uses the published RAGTruth test split and task_type QA only. Every eligible response is retained, without filtering by generator, quality, label or score. A complete question group would be excluded if its lowercased whitespace-normalized question exactly matched any ALCE question. There were zero such exclusions, leaving 900 answers and 150 source_id groups. A positive answer has at least one supplied hallucination span; zero spans is negative under this released annotation rule, not a certificate of truth. All supplied quality flags, including imperfect outputs, remain available only as descriptive strata. Neither question text, model identity, quality flags, prompts nor human annotation spans enter model inputs. Only the response and its supplied evidence do.

The ALCE file SHA-256 is cfed9293752413d7c7631f36524dd4ee9ef58b209cdf9c63f6fc1e280b43cca6. RAGTruth is pinned to commit c103204b9ce28d6bbad859304bf30de72b8ed8fe; the complete input hashes are stored in the protocol and measured result. The annotation repository has an MIT license, while its underlying MS MARCO web material has separate noncommercial research terms. Raw questions, passages, answers and hallucination spans are not redistributed. Exact question matching cannot establish semantic independence. Unknown model-pretraining overlap, corpus selection and annotation errors remain unresolved.

## 3. Frozen policies and evaluation

The lexical policy uses evidence-token overlap, number of citations, unique claim-token count, unique evidence-token count, unmatched-number fraction and a missing-citation indicator. A train-only standard scaler and balanced logistic regression fit each ALCE source separately. The highest validation threshold retaining at least 90% source unsupported recall is fixed before external scoring. The external complete answer is represented with one supplied evidence citation. This changes feature distributions; it is not a sentence-to-answer invariant. The implementation requires the previously measured lexical ALCE target AP and source threshold to reproduce before external inference.

The NLI comparator is cross-encoder/nli-deberta-v3-small at immutable revision fa2804872c3b4bd748f38c0185cc85775361e735, with hash-checked ONNX/tokenizer files and an Apache-2.0 model card. The model card identifies SNLI/MultiNLI training and label order contradiction, entailment, neutral. Unsupported risk is one minus the entailment softmax score. It is a model score, not a calibrated real-world probability. The bounded representation allows 512 total pair tokens and caps the answer at 120 tokens, truncating evidence first. Earlier ALCE-calibrated thresholds are reused without external adaptation.

The coverage diagnostic uses these identical weights. Evidence windows have 384 tokens and stride 320; answer windows have 120 tokens and stride 100. An end-aligned final window ensures that every original token appears in a window. Each answer window receives its maximum entailment score across all evidence windows. The whole-answer risk is the maximum unsupported score across answer windows. The policy uses 1,836 inference pairs for 900 external answers, with zero re-encoding truncations. Source validation separately calibrates this new representation, using the same 90% recall rule. Window dimensions and aggregation were frozen before target scoring. This method can split joint semantics and is intrinsically length-dependent; it is a diagnostic adaptation, not a claimed novel detector.

We report average precision (AP), ROC AUC, recall, supported-answer false-positive rate (FPR), review fraction and missed positives. AP is scikit-learn average precision, not trapezoidal PR area. Thresholds use source validation only. Review-all and review-none controls expose the workload extremes. Uncertainty uses 300 complete-source_id bootstrap resamples, seed 20261019, with paired AP differences on identical rows. These percentile intervals condition on fitted policies and the sampled corpus. They do not include model-fitting, annotation, source-selection or pretraining uncertainty. Multiple descriptive contrasts are not a family-wise corrected significance study.

## 4. Measured results

Table 1 gives the historical ALCE sentence-transfer results. These rows are not pooled with whole-answer RAGTruth metrics.

| Direction | Policy | AP | Recall | Review | Missed |
| --- | --- | --- | --- | --- | --- |
| ASQA to ELI5 | Lexical | 0.919 | 92.84% | 70.33% | 64 |
| ASQA to ELI5 | Bounded NLI | 0.838 | 81.54% | 63.97% | 165 |
| ELI5 to ASQA | Lexical | 0.857 | 86.33% | 52.53% | 38 |
| ELI5 to ASQA | Bounded NLI | 0.775 | 95.32% | 84.96% | 13 |

Table 2 gives the new whole-answer RAGTruth results. Source denotes the calibration policy, not a target subgroup. Bounded and coverage NLI risk rankings are the same across source rows; only their source-calibrated thresholds change. The target positive prevalence is 17.8%.

| Source | Policy | AP | ROC AUC | Recall | FPR | Review | Missed |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ASQA | learned_lexical | 0.281 | 0.709 | 100.00% | 98.65% | 98.89% | 0 |
| ASQA | bounded_nli | 0.210 | 0.602 | 33.12% | 27.03% | 28.11% | 107 |
| ASQA | coverage_nli | 0.281 | 0.699 | 60.00% | 31.08% | 36.22% | 64 |
| ELI5 | learned_lexical | 0.218 | 0.620 | 81.88% | 64.05% | 67.22% | 29 |
| ELI5 | bounded_nli | 0.210 | 0.602 | 79.38% | 64.05% | 66.78% | 33 |
| ELI5 | coverage_nli | 0.281 | 0.699 | 91.25% | 66.49% | 70.89% | 14 |

The bounded representation truncated evidence for 151 of 900 answers and truncated claims for 458. Consequently, a positive answer annotation can refer to text not observed by this policy. Covering all tokens improves AP from 0.210 to 0.281 for these fixed weights, but does not isolate token coverage as a causal explanation: aggregation and representation change together. With ELI5 calibration, coverage misses 14 positives rather than bounded NLI's 33, while increasing the review fraction from 66.8% to 70.9% and supported-answer FPR from 64.1% to 66.5%. With ASQA calibration, coverage misses 64 positives; its recall is 60.0%. There is no transferred 90% recall guarantee. The ELI5 coverage recall is exactly 146/160 = 91.25%; table percentages use two decimals to avoid inconsistent one-decimal rounding.

Table 3 gives the conditional 95% percentile intervals for AP and its paired difference from the corresponding lexical source policy. These are descriptive intervals from 150 question clusters, not 900 independent answer draws.

| Source / Policy | AP interval | AP difference from lexical |
| --- | --- | --- |
| ASQA / learned_lexical | [0.231, 0.344] | reference |
| ASQA / bounded_nli | [0.174, 0.255] | [-0.121, -0.025] |
| ASQA / coverage_nli | [0.227, 0.337] | [-0.053, 0.054] |
| ELI5 / learned_lexical | [0.181, 0.264] | reference |
| ELI5 / bounded_nli | [0.174, 0.255] | [-0.046, 0.032] |
| ELI5 / coverage_nli | [0.227, 0.337] | [0.017, 0.117] |

The coverage-versus-ELI5 lexical AP interval excludes zero under this conditional procedure. The coverage-versus-ASQA lexical difference includes zero. Review-all obtains recall 100%, FPR 100% and review 100%; review-none obtains recall 0%, FPR 0% and review 0%. Both constant-score controls have AP equal to prevalence, 0.178. Neither is a practical efficiency success. The ASQA lexical policy's perfect recall with 98.9% review approaches the review-all extreme, so recall alone obscures its operational weakness.

### 4.1. Post-hoc generator and length controls

These controls were added after the target outcomes and the owner's critique were visible. Every generator is retained, including GPT-4 with only one positive. Table 4 reports within-generator length and coverage NLI ROC AUC; AP and both length directions are retained in review-diagnostics.json. Sparse positive strata are descriptive only.

| Generator | Answers | Positives | Length AUC | Coverage NLI AUC |
| --- | --- | --- | --- | --- |
| gpt-3.5-turbo-0613 | 150 | 5 | 0.664 | 0.818 |
| gpt-4-0613 | 150 | 1 | 0.074 | 0.638 |
| llama-2-13b-chat | 150 | 36 | 0.684 | 0.601 |
| llama-2-70b-chat | 150 | 35 | 0.570 | 0.633 |
| llama-2-7b-chat | 150 | 52 | 0.600 | 0.638 |
| mistral-7B-instruct | 150 | 31 | 0.773 | 0.655 |

Average ranks handle ties within each generator and are divided by that generator's answer count, then pooled over all 900 rows. This uses the unlabeled target score distribution and generator identities: a transductive diagnostic, not a source-frozen deployment policy. The identical transformation is applied to coverage NLI for symmetry. Table 5 includes both transformed and untransformed scores; a normalized length score versus raw NLI is not a matched normalization comparison.

| Ranking | AP | ROC AUC |
| --- | --- | --- |
| Raw length, longer risk | 0.386 | 0.727 |
| Raw length, shorter risk | 0.117 | 0.273 |
| Raw coverage NLI | 0.281 | 0.699 |
| Within-generator length ranks | 0.296 | 0.632 |
| Within-generator coverage ranks | 0.236 | 0.625 |

Length has ROC AUC above 0.5 in five generator samples. GPT-4 instead has length AUC 0.074 and only one positive; this unstable, opposite-direction result is retained rather than excluded. Normalizing within generators changes cross-generator comparisons and pooled AP/AUC; the reduction from raw length AUC 0.727 to rank-normalized AUC 0.632 is not an additive estimate of a generator effect. No uncertainty or equivalence margin has been established for these new differences. Longer answers may also have more opportunities for at least one annotated hallucination, without greater per-claim error. These data do not separate that exposure effect from semantic quality or generator behavior.

## 5. Interpretation and alternative explanations

The revised title focuses on baseline adequacy in this ALCE-to-RAGTruth audit. The present evidence establishes no advantage for the tested evidence-reading scores over length; it also does not establish length superiority. Failure of source recall and review workload to transfer is supporting context, not a universal transfer theorem.

The within-generator controls in Section 4.1 weaken a semantic-support interpretation without identifying a causal explanation. The five-fold complete-question cross-fitted generator prior from the earlier response has AP 0.274, ROC AUC 0.685. It uses target labels from other question groups; unlike the label-free rank transform, it is a target-supervised diagnostic and not a source-only comparator.

Coverage thresholds are 0.989811 for ASQA (172 sentences, 19 questions) and 0.451716 for ELI5 (363 sentences, 19 questions). They are empirical source recall cutoffs, not calibrated probabilities. Different source score distributions can produce different cutoffs, but the cached data do not establish why this gap occurs. Calibration sensitivity across independent question-group splits has not been measured; a 90% empirical source target is not a population recall guarantee. High historical sentence-level AP does not transfer unchanged to this answer-level benchmark. The target differs in generator mixture, response length, citation presentation, evidence and positive-label definition. These shifts occur together. Accordingly, the numerical AP drop cannot be attributed solely to domain shift, answer granularity or model architecture. A controlled unit-matched annotation study would be needed to separate those explanations.

AttrScore directly studies attribution errors and evaluates prompted and fine-tuned models (Yue et al., 2023). AttributionBench consolidates attribution evaluation and documents persistent failure modes (Li et al., 2024). These are close prior work, not systems reproduced here. Their task-specific F1 scores cannot be compared numerically with this audit's AP. REVIEW_RESPONSE_PROTOCOL.md records the required label mapping, checkpoint/license verification, context policy and source-only calibration for a matched AttrScore experiment, which remains unexecuted.

The small NLI model is an accessible open comparator, not a comprehensive current-model tournament. Target fine-tuning, prompt-based commercial judges, larger task-specific detectors and learned evidence retrieval are not tested. The source-only design answers a transfer question; it does not estimate the best achievable supervised RAGTruth performance. Comparison with the original RAGTruth paper's tuned systems would require their matched splits, units and procedures. No such numerical ranking is claimed.

Window aggregation has opposing failure modes. A maximum across evidence may find a spurious supporting fragment, while a maximum risk across answer windows may penalize long otherwise supported answers. Splitting text can destroy conjunctions or reference resolution. No calibrated probability, reliable factual verdict or educational learning benefit follows from these scores. Generator and quality strata are released descriptively, without outcome-selected exclusions or selecting a preferred policy after inspecting a favorable stratum.

## 6. Reproducibility, ethics and limitations

Protocols, source hashes, original code, integrity tests, individual derived risks and aggregate outputs accompany the manuscript in Sunnyvulli/Data-Engineer_AI/research-suite. The external protocol is fixed at commit cf1c7b96b7aee262fd64816377dbcf04168ba5e7. Run python -m research_suite.external_support with the pinned local data and model directory after installing documented dependencies. Hash-validated caches permit interrupted inference to resume. The recorded elapsed time is a resumed invocation, not a reconstructed end-to-end compute bill; no total from discarded process time is fabricated. CPU inference uses four intra-operation threads and batch 4; no paid API or GPU was used.

Integrity checks cover hidden-label exclusion, complete token-window coverage, grouped paired resampling and existing causal/split controls. Passing tests cannot prove statistical validity or absence of all defects. The four-perspective review is a self-audit generated within this project, not independent expert peer review. No participant study, production deployment, manually adjudicated new labels or acceptance by a journal is represented.

The named human author must inspect the artifacts, verify the claims and confirm substantive authorship and the final text before external submission. AI is not listed as an author. No institutional affiliation, funding award or external reviewer is invented.

## 7. Conclusion

On this exposed RAGTruth whole-answer set, no advantage for the tested evidence-reading scores over answer length was established; neither approach was shown superior. Raw length has a higher pooled AP point estimate, but the paired length-versus-NLI uncertainty intervals remain uncomputed and within-generator AUC comparisons are mixed. These exploratory observations establish neither equivalence nor a causal explanation or general detector ranking. The original source-threshold workload failures remain relevant, but stronger matched comparators, calibration/window studies, fresh confirmation and independent human review are still required.

## References

Yue, X., Wang, B., Chen, Z., Zhang, K., Su, Y., & Sun, H. (2023). Automatic Evaluation of Attribution by Large Language Models. Findings of EMNLP, 4615-4635. https://doi.org/10.18653/v1/2023.findings-emnlp.307

Li, Y., Yue, X., Liao, Z., & Sun, H. (2024). AttributionBench: How Hard is Automatic Attribution Evaluation? Findings of ACL, 14919-14935. https://doi.org/10.18653/v1/2024.findings-acl.886

Gao, T., Yen, H., Yu, J., & Chen, D. (2023). Enabling Large Language Models to Generate Text with Citations. Proceedings of EMNLP,6465-6488. https://doi.org/10.18653/v1/2023.emnlp-main.398

Niu, C., Wu, Y., Zhu, J., Xu, S., Shum, K., Zhong, R., Song, J., & Zhang, T. (2024). RAGTruth: A Hallucination Corpus for Developing Trustworthy Retrieval-Augmented Language Models. Proceedings of ACL, Volume1: Long Papers,10862-10878. https://doi.org/10.18653/v1/2024.acl-long.585

Sentence Transformers. cross-encoder/nli-deberta-v3-small model card and immutable revision fa2804872c3b4bd748f38c0185cc85775361e735. https://huggingface.co/cross-encoder/nli-deberta-v3-small/tree/fa2804872c3b4bd748f38c0185cc85775361e735

Particle Media. RAGTruth source and annotation release, commit c103204b9ce28d6bbad859304bf30de72b8ed8fe. https://github.com/ParticleMedia/RAGTruth/tree/c103204b9ce28d6bbad859304bf30de72b8ed8fe

Microsoft. MS MARCO data and research-use terms. https://microsoft.github.io/msmarco/

Vulli research suite. Frozen external-support protocol and original evaluation implementation. https://github.com/Sunnyvulli/Data-Engineer_AI/tree/main/research-suite
