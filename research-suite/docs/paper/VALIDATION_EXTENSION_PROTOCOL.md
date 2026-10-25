# Citation validation extension — 25 October 2026

Frozen before new model inference. Existing ALCE/RAGTruth-test outcomes are exposed.
This extension is not an independent expert review or a registered clinical study.

## AttrScore comparator

Use official OSU-NLP-Group/AttrScore FLAN-T5-Large (770M), Hugging Face
`osunlp/attrscore-flan-t5-large` revision
`282eb2ab5d537f5badf5fa33008d96abff34607b`, Apache-2.0 model metadata.
Weight SHA-256: `163ba0ad32e03ce021207b4f9ac63654cdaa99beb644467dafc0016b9bb92125`.
Official reference: https://github.com/OSU-NLP-Group/AttrScore .
The checkpoint is trained on repurposed combined_train data. No claim of absence
of pretraining or semantic overlap is possible. Raw restricted text/weights stay local.

Use the official attribution-validator instruction, response-only Claim and supplied
Reference, matching the existing allowed-input policy (no question, generator,
quality or annotation as predictors). Keep the first120 claim tokens and fill the
remaining512-token encoder budget with reference tokens after accounting for the
instruction/separators. Retain truncation counts. This bounded policy is an adaptation,
not exact reproduction of the original paper's reported scores.

Greedy generation, max_new_tokens8, no sampling. Exact case-insensitive output mapping:
Attributable -> risk0; Contradictory or Extrapolatory -> risk1. Unrecognized output
is an explicit failure; do not invent a class. Report failure counts and exclude only
failed rows from paired comparisons with the identical mask on every comparator.
This yields tied-score AP and discrete operating points, not calibrated probabilities.
Test the parser with all labels/invalid output and run three documented semantic
fixtures without using their outcomes to tune prompts or choose checkpoints.

Evaluate all900 existing RAGTruth QA-test responses, with exact ID/group/label
reconciliation against retained scores. This is exposed-target exploratory comparison.
Report AP/AUC, recall/FPR/review burden at the fixed discrete rule, and paired AP
differences versus length, coverage NLI and both lexical source models. Resample
complete question groups5000times, seed20261025. Intervals are descriptive95%
percentile intervals; no simultaneous significance or superiority claim. Do not
rerun/select a policy until significance appears.

Local resource cap: CPU only, four threads, batch1, at most8GiB process RSS,
60minutes inference wall time and4GiB model downloads. Cache input hash, model
revision, policy version, exact row IDs and output strings after every10rows.
Record measured wall time/RSS, partial completion and failures; never fabricate
unexecuted output. No paid API/cloud use.

## Calibration and window diagnostics

On existing cached source-validation predictions, resample complete source groups
5000times and recompute the empirical90%-recall threshold. Describe threshold
instability conditional on the fitted model; no retraining/generalisation guarantee.
On existing paired risks, compute5000complete-question intervals for length minus
coverage and within-generator length minus identically normalized coverage. These
are exploratory on the exposed target.

A causal coverage/aggregation explanation requires separately controlled rerunning
of the same NLI weights. Existing bounded versus coverage policies jointly change
coverage and aggregation, so they cannot isolate that effect. Do not label a cached
comparison a controlled ablation. Implement/run only if model/data access and
remaining resources permit, otherwise retain it as an explicit unfinished item.

## Fresh confirmation gate

Do not relabel any of the900 exposed answers, change their groups, or call a new
seed independent confirmation. RAGTruth train is not independent-corpus confirmation,
and prior unobserved access to it cannot be disproved. Before a defensible fresh test,
establish an unexposed dataset/annotation frame, check overlap with all evaluated
questions and comparator training sources, freeze selection and endpoints before
opening outcomes, and verify compatible annotation units. If this cannot be
established, record the blocked gate rather than manufacture confirmatory evidence.

## Human review and submission

Prepare a concrete review packet and final-claim checklist. External human review
and substantive author review cannot be performed by automated self-audits. No
reviewer endorsement, authorship approval, journal submission, preprint deposit or
acceptance is implied or performed by this protocol.
