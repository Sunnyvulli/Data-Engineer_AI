# Citation audit: independent review packet

Prepared 25 October 2026. This packet is a request for substantive assessment, not evidence that review occurred. Manuscript and all results are unpublished. No journal submission or preprint deposit has been made.

## Read in this order

1. `MANUSCRIPT.md` / `MANUSCRIPT.pdf`: canonical paper and its explicitly negative baseline finding.
2. `VALIDATION_EXTENSION_PROTOCOL.md` and `WINDOW_DIAGNOSTIC_PROTOCOL.md`: frozen extension designs. Both are post hoc with respect to the existing RAGTruth outcomes.
3. `results/validation/validation-extension.json`: row-aligned comparison, failures, paired group intervals and source calibration uncertainty.
4. `results/validation/window-diagnostic.json`: controlled window rankings, exact row IDs and token-window audit. Its aggregate audit must reconcile the full/full/max policy with the original cache.
5. `REVIEW_RESPONSE.md`, `READINESS.md`, and the data/model hashes in the protocols.

All paths are relative to this directory except results paths, which are relative to research-suite. Restricted raw text and downloaded weights are deliberately omitted. Reproduction requires independently obtaining the named upstream files and obeying their terms.

## Questions requiring an external researcher's judgment

- Does the narrowly stated benchmark audit add useful evidence beyond existing AttrScore/AttributionBench work? Identify the closest missing prior work and any claim that duplicates it.
- Is it fair to compare discrete AttrScore labels with continuous rankings under AP? Are the context adaptation, truncation and annotation-unit differences sufficiently prominent?
- Does the sentence-to-whole-answer shift invalidate a particular inference? What would a compatible annotation unit require?
- Are complete-question resampling, fixed-model conditioning and source-threshold instability interpreted correctly? Which uncertainty sources remain unrepresented?
- Does the window factorial design distinguish its two coverage axes and aggregation without making an unjustified general causal claim?
- Do any remaining phrases imply superiority, statistical equivalence, operational reliability or fresh confirmation unsupported by the evidence?
- Is a bounded technical report justified now? What additional evidence is essential before a journal submission?

Please supply specific sections, objections and proposed corrections. A favorable informal response is not journal peer review. Record reviewer identity, consent to attribution, date, exact comments and the author's reasoned response only after they actually exist. Do not list an uncontacted researcher as a reviewer.

## Author's substantive review

Hanumantha must read the complete manuscript, inspect representative allowed local examples, explain the primary endpoint and leakage/independence controls in his own words, verify the code/results and references, and take responsibility for corrections. An approval click is not substantive authorship. Resolve any contribution or disclosure issues before naming an author on a submission.

AI assistance was used substantially for code, experimental execution, analysis and manuscript drafting. This is not a claim that all ideas, claims or analysis were independently originated by the human author. Disclose the actual assistance accurately; do not misstate it as grammar-only editing. The author must determine with a venue whether the resulting contributions satisfy its authorship and AI-use policy.

## Confirmation gate: currently unresolved

The existing 900 RAGTruth answers are exposed. Another seed, resampling them, changing their groups or using their annotations again is not a fresh test. The RAGTruth training partition is the same corpus and cannot establish independent-corpus confirmation. AttributionBench combines prior datasets, including AttrScore sources; its existence alone establishes neither non-overlap nor compatible whole-answer units.

Before running any confirmation: identify an unexposed question/source sampling frame with permitted use; document semantic and exact overlap checks against ALCE, RAGTruth and known model training sources; freeze the complete-question sampling rule, all policies, endpoints and resource limits; obtain blinded human whole-answer support annotations with a documented rubric, adjudication and uncertainty; keep outcomes inaccessible until predictions are locked. Unknown pretraining overlap must remain a limitation. No new annotated frame or independent annotator has been established in this release. No confirmation outcomes are fabricated.

## Decision record to complete after review

- Human author's substantive amendments: pending.
- External research review and response: pending.
- Unexposed independent confirmation sampling/annotation: pending.
- Venue contribution/AI-policy eligibility: unresolved.
- Final anonymization, venue template and account metadata: not yet submission-ready.
