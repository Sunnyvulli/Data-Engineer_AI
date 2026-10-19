# Frozen bounded open entailment comparison

Prepared October 19, 2026 UTC, before computing new ALCE entailment outputs. Earlier lexical outcomes on this corpus are already known; this is a disclosed benchmark reuse, not a fresh blind test or a claim of novelty.

## Model and feasibility

Use `cross-encoder/nli-deberta-v3-small`, immutable revision `fa2804872c3b4bd748f38c0185cc85775361e735`. Its model card declares Apache-2.0 and SNLI/MultiNLI training. It is an accessible established NLI baseline, not claimed to be the newest or strongest support verifier. The repository supplies a 568,032,787-byte full-precision ONNX export. Label order from config: contradiction, entailment, neutral. No model remote code is executed. Model and tokenizer bytes will be hashed; no weights or source passages are republished.

Primary sources: https://huggingface.co/cross-encoder/nli-deberta-v3-small/tree/fa2804872c3b4bd748f38c0185cc85775361e735 and its README/config. Runtime: ONNX Runtime 1.24.4, tokenizers 0.22.2, CPU provider, four inference threads, batch size 4. Runtime installation/download/inference are feasibility gates; failure is retained, not replaced by invented scores.

## Inputs, aggregation and leakage controls

Reuse all 2,604 ALCE annotated sentences in original file order and the existing question-grouped ASQA-to-ELI5 and ELI5-to-ASQA splits with seed 42. Inputs contain only sentence text and its cited documents' titles/text, in annotation order. Remove bracketed numeric citation markers from the sentence. Concatenate cited documents separated by two newlines; no retrieval, labels, precision scores or automatic evaluator outputs enter model inputs. Missing evidence yields unsupported risk 1 without inference.

One premise/hypothesis pair per sentence: cited evidence as premise, sentence as hypothesis. Truncate the claim alone to at most 120 tokenizer tokens, then truncate evidence only to fit a total sequence length of 512. No sliding-window or outcome-selected evidence. Record original evidence/claim token lengths and truncation counts. This bounded first-context comparator can discard relevant evidence; labels describe original complete evidence. It is not equivalent to the original ALCE large-model evaluator. Combined evidence allows some joint support, but this truncation is a material limit.

Risk = 1 minus softmax probability of entailment. No model fine-tuning or calibration. Select the review threshold using only the source validation questions, with the same >=90% unsupported-recall rule as the existing lexical model. Evaluate both models on identical target rows. Include a default NLI risk threshold of 0.5 as a diagnostic, review-all and review-none. Report unsupported-class AP, review fraction, unsupported recall, missed unsupported count and question-cluster percentile intervals (300 resamples), plus paired AP difference NLI minus learned lexical. AP on released binary automatic labels is not a matched ranking comparator.

## Validity, compute and failure reporting

Time and peak resident memory are measured. A synthetic entailment/contradiction smoke pair may check input ordering and output shape before ALCE inference; it is not a scientific accuracy result. Preserve sentence risks in annotation order without redistributing passages. Abort rather than score nonfinite output or unrecognized label order. Do not change model, context, threshold or split after seeing results. A runtime failure can be fixed without tuning on test outcomes, and must be documented. Conditional bootstrap intervals omit corpus/model-selection uncertainty and possible pretraining contamination. This experiment does not measure factual truth, real deployment performance or publication readiness.
