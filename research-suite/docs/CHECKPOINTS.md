# Citation-support review checkpoints

## Question and implementation

Can inexpensive signals prioritise unsupported sentences for review while retaining most unsupported cases? `src/research_suite/checkpoints.py` compares review-all, review-none, a deterministic lexical policy, and a logistic regression trained on lexical/structural signals.

The primary data are ALCE's released human citation annotations. The positive class is `sentence_recall_score=0`: the sentence is not fully supported by its cited documents. This is a support judgment, **not** a judgment of objective truth. The loader skips only aggregate `overall_results` entries and rejects unexpected per-sentence labels.

Features are claim/evidence lexical coverage, citation count, claim/evidence token-set sizes, unmatched numeric fraction, and missing citations. Reference markers such as `[1]` are removed before counting numbers. No human scores, automatic scores, model names, question IDs, or dataset labels enter the model features. All sentences and all model answers for the same dataset/question ID are grouped into the same split. ASQA and ELI5 are also reported separately, but this is not a held-out-domain experiment.

A validation threshold targets >=90% unsupported recall. It is applied unchanged on test sentences. Triage precision, recall, review fraction, missed unsupported counts, and unsupported rate among unflagged sentences are reported. High lexical overlap can conceal contradictions or negation; a low score is not a reason to accept a claim as true. Cite existence/URL availability are not checked by this implementation.

## Working use

`research-suite triage examples/claim.json` returns an explainable deterministic review flag. After training, `predict` can use the learned model to create a CSV review queue from your own claim/evidence objects. It works offline and does not send the submitted text to an external service.

## Next research gate

Compare with current entailment-based and retrieval-grounded systems; evaluate adversarial numeric/negation cases and new domains; assess independent annotator agreement. A user study and appropriate institutional ethics review are needed before claims about learning, trust, reviewer time, or reduced decision harm. The current work is a reproducible baseline, not an evaluation of student outcomes.
