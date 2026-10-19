# Source Recall Does Not Guarantee Transfer: A Reproducible Audit of Evidence-Support Triage

Hanumantha Rao Vulli

Research manuscript draft for author review. October 19, 2026 UTC. Not peer reviewed or accepted. No institutional affiliation is asserted.

## Abstract

Evidence-support triage can reduce manual review only if its recall and workload transfer beyond its calibration corpus. We audit six lexical features and an openly licensed small natural-language-inference (NLI) model under frozen source-only thresholds. Earlier ALCE sentence experiments are contrasted with a separately selected RAGTruth QA test set containing 900 whole answers in 150 question groups, with 160 positive annotations. At the original ASQA threshold, lexical triage catches every positive but flags 98.9% of answers. At the original ELI5 threshold, it catches 81.9% and flags 67.2%. The fixed bounded NLI representation has average precision 0.210. A precommitted coverage-window diagnostic raises this to 0.281, but at the ELI5-calibrated cutoff still misses 14 of 160 positives while flagging 70.9% of answers. Its paired AP difference from the ELI5 lexical model has a question-cluster percentile interval [0.017, 0.117]; its difference from the ASQA lexical model includes zero. These are conditional benchmark findings, not a general ranking or deployment guarantee. We release original code, frozen protocols, derived predictions and failure audits, keeping restricted source text local.

## 1. Research question and bounded contribution

A high unsupported-claim recall on source validation does not specify the fraction of answers a user must inspect elsewhere. This audit asks: how do source-calibrated triage policies behave when the evidence task changes corpus and annotation unit? A second, diagnostic question asks whether covering all input tokens changes the behavior of the same NLI weights relative to a fixed truncation policy.

ALCE evaluates answers with citations and provides human sentence-support annotations (Gao et al., 2023). RAGTruth provides manually annotated hallucination spans in generated responses grounded in supplied material (Niu et al., 2024). Their annotations serve related purposes but are not identical constructs. This manuscript reports an empirical audit; it does not introduce a new learning algorithm, claim a first use of window aggregation, establish state-of-the-art performance, or establish a comprehensive novelty result. Previously exposed ALCE comparisons are historical context. The new RAGTruth protocol was committed before its model outcomes were computed.

## 2. Data, labels and independence

The ALCE annotation file contains 2,604 sentences from 200 supplied question groups across ASQA and ELI5. All available model responses to the same supplied question stay together. Source train and validation sets follow the existing seed42 split: ASQA has 639 training sentences from 81 questions and 172 validation sentences from 19 questions; ELI5 has 1,430 training sentences from 81 questions and 363 validation sentences from 19 questions. Unsupported is the positive class, defined as one minus the binary human sentence-support label. The other domain is an exposed historical target, never used to calibrate the new external experiment.

The independent external selection uses the published RAGTruth test split and task_type QA only. Every eligible response is retained, without filtering by generator, quality, label or score. A complete question group would be excluded if its lowercased whitespace-normalized question exactly matched any ALCE question. There were zero such exclusions, leaving 900 answers and 150 source_id groups. A positive answer has at least one supplied hallucination span; zero spans is negative under this released annotation rule, not a certificate of truth. All supplied quality flags, including imperfect outputs, remain available only as descriptive strata. Neither question text, model identity, quality flags, prompts nor human annotation spans enter model inputs. Only the response and its supplied evidence do.

The ALCE file SHA-256 is cfed9293752413d7c7631f36524dd4ee9ef58b209cdf9c63f6fc1e280b43cca6. RAGTruth is pinned to commit c103204b9ce28d6bbad859304bf30de72b8ed8fe; the complete input hashes are stored in the protocol and measured result. The annotation repository has an MIT license, while its underlying MS MARCO web material has separate noncommercial research terms. Raw questions, passages, answers and hallucination spans are not redistributed. Exact question matching cannot establish semantic independence. Unknown model-pretraining overlap, corpus selection and annotation errors remain unresolved.

## 3. Frozen policies and evaluation

The lexical policy uses evidence-token overlap, number of citations, unique claim-token count, unique evidence-token count, unmatched-number fraction and a missing-citation indicator. A train-only standard scaler and balanced logistic regression fit each ALCE source separately. The highest validation threshold retaining at least 90% source unsupported recall is fixed before external scoring. The external complete answer is represented with one supplied evidence citation. This changes feature distributions; it is not a sentence-to-answer invariant. The implementation requires the previously measured lexical ALCE target AP and source threshold to reproduce before external inference.

The NLI comparator is cross-encoder/nli-deberta-v3-small at immutable revision fa2804872c3b4bd748f38c0185cc85775361e735, with hash-checked ONNX/tokenizer files and an Apache-2.0 model card. The model card identifies SNLI/MultiNLI training and label order contradiction, entailment, neutral. Unsupported risk is one minus the entailment softmax score. It is a model score, not a calibrated real-world probability. The bounded representation allows 512 total pair tokens and caps the answer at 120 tokens, truncating evidence first. Earlier ALCE-calibrated thresholds are reused without external adaptation.

The coverage diagnostic uses these identical weights. Evidence windows have 384 tokens and stride320; answer windows have120 tokens and stride100. An end-aligned final window ensures that every original token appears in a window. Each answer window receives its maximum entailment score across all evidence windows. The whole-answer risk is the maximum unsupported score across answer windows. The policy uses 1,836 inference pairs for 900 external answers, with zero re-encoding truncations. Source validation separately calibrates this new representation, using the same 90% recall rule. Window dimensions and aggregation were frozen before target scoring. This method can split joint semantics and is intrinsically length-dependent; it is a diagnostic adaptation, not a claimed novel detector.

We report average precision (AP), ROC AUC, recall, supported-answer false-positive rate (FPR), review fraction and missed positives. AP is scikit-learn average precision, not trapezoidal PR area. Thresholds use source validation only. Review-all and review-none controls expose the workload extremes. Uncertainty uses 300 complete-source_id bootstrap resamples, seed20261019, with paired AP differences on identical rows. These percentile intervals condition on fitted policies and the sampled corpus. They do not include model-fitting, annotation, source-selection or pretraining uncertainty. Multiple descriptive contrasts are not a family-wise corrected significance study.

## 4. Measured results

Table 1 gives the historical ALCE sentence-transfer results. These rows are not pooled with whole-answer RAGTruth metrics.

| Direction | Policy | AP | Recall | Review | Missed |
| --- | --- | --- | --- | --- | --- |
| ASQA to ELI5 | Lexical | 0.919 | 92.8% | 70.3% | 64 |
| ASQA to ELI5 | Bounded NLI | 0.838 | 81.5% | 64.0% | 165 |
| ELI5 to ASQA | Lexical | 0.857 | 86.3% | 52.5% | 38 |
| ELI5 to ASQA | Bounded NLI | 0.775 | 95.3% | 85.0% | 13 |

Table 2 gives the new whole-answer RAGTruth results. Source denotes the calibration policy, not a target subgroup. Bounded and coverage NLI risk rankings are the same across source rows; only their source-calibrated thresholds change. The target positive prevalence is 17.8%.

| Source | Policy | AP | Recall | FPR | Review | Missed |
| --- | --- | --- | --- | --- | --- | --- |
| ASQA | learned_lexical | 0.281 | 100.0% | 98.6% | 98.9% | 0 |
| ASQA | bounded_nli | 0.210 | 33.1% | 27.0% | 28.1% | 107 |
| ASQA | coverage_nli | 0.281 | 60.0% | 31.1% | 36.2% | 64 |
| ELI5 | learned_lexical | 0.218 | 81.9% | 64.1% | 67.2% | 29 |
| ELI5 | bounded_nli | 0.210 | 79.4% | 64.1% | 66.8% | 33 |
| ELI5 | coverage_nli | 0.281 | 91.2% | 66.5% | 70.9% | 14 |

The bounded representation truncated evidence for 151 of 900 answers and truncated claims for 458. Consequently, a positive answer annotation can refer to text not observed by this policy. Covering all tokens improves AP from0.210 to0.281 for these fixed weights, but does not isolate token coverage as a causal explanation: aggregation and representation change together. With ELI5 calibration, coverage misses14 positives rather than bounded NLI's33, while increasing the review fraction from66.8% to70.9% and supported-answer FPR from64.1% to66.5%. With ASQA calibration, coverage misses64 positives; its recall is60.0%. There is no transferred 90% recall guarantee.

Table 3 gives the conditional 95% percentile intervals for AP and its paired difference from the corresponding lexical source policy. These are descriptive intervals from 150 question clusters, not900 independent answer draws.

| Source / Policy | AP interval | AP difference from lexical |
| --- | --- | --- |
| ASQA / learned_lexical | [0.231, 0.344] | reference |
| ASQA / bounded_nli | [0.174, 0.255] | [-0.121, -0.025] |
| ASQA / coverage_nli | [0.227, 0.337] | [-0.053, 0.054] |
| ELI5 / learned_lexical | [0.181, 0.264] | reference |
| ELI5 / bounded_nli | [0.174, 0.255] | [-0.046, 0.032] |
| ELI5 / coverage_nli | [0.227, 0.337] | [0.017, 0.117] |

The coverage-versus-ELI5 lexical AP interval excludes zero under this conditional procedure. The coverage-versus-ASQA lexical difference includes zero. Review-all obtains recall100%, FPR100% and review100%; review-none obtains recall0%, FPR0% and review0%. Both constant-score controls have AP equal to prevalence,0.178. Neither is a practical efficiency success. The ASQA lexical policy's perfect recall with98.9% review approaches the review-all extreme, so recall alone obscures its operational weakness.

## 5. Interpretation and alternative explanations

The useful finding is a failure of easy transfer, not a universally superior policy. High historical sentence-level AP does not transfer unchanged to this answer-level benchmark. The target differs in generator mixture, response length, citation presentation, evidence and positive-label definition. These shifts occur together. Accordingly, the numerical AP drop cannot be attributed solely to domain shift, answer granularity or model architecture. A controlled unit-matched annotation study would be needed to separate those explanations.

The small NLI model is an accessible open comparator, not a comprehensive current-model tournament. Target fine-tuning, prompt-based commercial judges, larger task-specific detectors and learned evidence retrieval are not tested. The source-only design answers a transfer question; it does not estimate the best achievable supervised RAGTruth performance. Comparison with the original RAGTruth paper's tuned systems would require their matched splits, units and procedures. No such numerical ranking is claimed.

Window aggregation has opposing failure modes. A maximum across evidence may find a spurious supporting fragment, while a maximum risk across answer windows may penalize long otherwise supported answers. Splitting text can destroy conjunctions or reference resolution. No calibrated probability, reliable factual verdict or educational learning benefit follows from these scores. Generator and quality strata are released descriptively, without outcome-selected exclusions or selecting a preferred policy after inspecting a favorable stratum.

## 6. Reproducibility, ethics and limitations

Protocols, source hashes, original code, integrity tests, individual derived risks and aggregate outputs accompany the manuscript in Sunnyvulli/Data-Engineer_AI/research-suite. The external protocol is fixed at commit cf1c7b96b7aee262fd64816377dbcf04168ba5e7. Run python -m research_suite.external_support with the pinned local data and model directory after installing documented dependencies. Hash-validated caches permit interrupted inference to resume. The recorded elapsed time is a resumed invocation, not a reconstructed end-to-end compute bill; no total from discarded process time is fabricated. CPU inference uses four intra-operation threads and batch4; no paid API or GPU was used.

Integrity checks cover hidden-label exclusion, complete token-window coverage, grouped paired resampling and existing causal/split controls. Passing tests cannot prove statistical validity or absence of all defects. The four-perspective review is a self-audit generated within this project, not independent expert peer review. No participant study, production deployment, manually adjudicated new labels or acceptance by a journal is represented.

The named human author must inspect the artifacts, verify the claims and confirm substantive authorship and the final text before external submission. AI is not listed as an author. No institutional affiliation, funding award or external reviewer is invented.

## 7. Conclusion

Under the frozen conditions tested here, source recall and historical sentence-level ranking do not establish efficient whole-answer triage. A coverage diagnostic improves one fixed NLI representation but still trades missed positives against substantial review workload. The evidence supports a bounded, reproducible transfer audit. Representative deployment validity, causal explanations for the shift, stronger matched comparators and independent human review remain open.

## References

Gao, T., Yen, H., Yu, J., & Chen, D. (2023). Enabling Large Language Models to Generate Text with Citations. Proceedings of EMNLP,6465-6488. https://doi.org/10.18653/v1/2023.emnlp-main.398

Niu, C., Wu, Y., Zhu, J., Xu, S., Shum, K., Zhong, R., Song, J., & Zhang, T. (2024). RAGTruth: A Hallucination Corpus for Developing Trustworthy Retrieval-Augmented Language Models. Proceedings of ACL, Volume1: Long Papers,10862-10878. https://doi.org/10.18653/v1/2024.acl-long.585

Sentence Transformers. cross-encoder/nli-deberta-v3-small model card and immutable revision fa2804872c3b4bd748f38c0185cc85775361e735. https://huggingface.co/cross-encoder/nli-deberta-v3-small/tree/fa2804872c3b4bd748f38c0185cc85775361e735

Particle Media. RAGTruth source and annotation release, commit c103204b9ce28d6bbad859304bf30de72b8ed8fe. https://github.com/ParticleMedia/RAGTruth/tree/c103204b9ce28d6bbad859304bf30de72b8ed8fe

Microsoft. MS MARCO data and research-use terms. https://microsoft.github.io/msmarco/

Vulli research suite. Frozen external-support protocol and original evaluation implementation. https://github.com/Sunnyvulli/Data-Engineer_AI/tree/main/research-suite
