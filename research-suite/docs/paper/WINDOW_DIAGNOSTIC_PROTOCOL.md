# Controlled NLI window diagnostic — 25 October 2026

Frozen before this rerun; the target outcomes are already exposed. This is exploratory, not confirmation.

Use the existing hash-checked cross-encoder/nli-deberta-v3-small ONNX revision fa2804872c3b4bd748f38c0185cc85775361e735 and all 900 existing QA test rows, with no refitting or source-threshold selection. Use exactly the established end-aligned evidence384/stride320 and claim120/stride100 windows. Retain all pairwise entailment scores once.

The 2x2 evidence/claim coverage design uses either the first window or every window on each axis. Always take maximum entailment over the selected evidence windows for each claim window. For all-claim policies report both maximum and mean unsupported risk over claim windows; these coincide for first-claim policies. Six unique rankings result. This separates evidence coverage, claim coverage and claim aggregation conditional on these weights and window boundaries; it is not a general causal claim about token length or the original bounded policy.

Reconcile full-evidence/full-claim/max risk to the existing 900-row coverage cache (absolute tolerance1e-5); stop aggregate interpretation if this fails. Record IDs, pair counts, truncation, runtime, model identity, AP/AUC. No outcome-selected policy, tuning or superiority claims. Complete-question bootstrap5000, seed20261025, descriptive95% intervals, contrast each other ranking minus established full/full/max. CPU2threads batch4, local only, no paid service, at most30minutes. Raw texts and model weights are not committed.
