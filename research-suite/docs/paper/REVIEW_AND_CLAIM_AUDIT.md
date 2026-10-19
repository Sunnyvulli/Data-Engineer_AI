# Four-perspective self-review and claim audit

October 19, 2026. This is an internal critical review performed within the project, not independent expert peer review. The 19 scored policies were independently reconciled from saved predictions with aggregate AP, ROC, recall, FPR and confusion counts to absolute tolerance1e-12. Evidence: results/validation/output-audit.json. All55 integrity tests passed locally after the new implementations.

| Perspective | Challenge | Evidence and response | Residual gap |
| --- | --- | --- | --- |
| Student/reproducer | Can someone reproduce results without copied text or hidden labels? | Original scripts, immutable hashes, frozen protocols, tests and derived predictions are provided. Labels, prompts, quality and generator metadata are excluded from citation predictors. | Data/model downloads and optional packages are required; pretraining overlap remains unknown. |
| Professor/researcher | Is this a novel algorithm or causal domain-shift study? | No. It is a bounded transfer audit. Corpus, annotation unit and evidence presentation shift together. Window coverage and aggregation also change together. | Stronger matched detectors, unit-matched human annotations, formal novelty review and external critique remain needed. |
| Industry user | Does higher recall reduce review work or improve live detection? | ASQA lexical recall100% requires98.9% review. ELI5 coverage catches91.3% but flags70.9% and misses14/160. Visual fusion reduces AP on all three splits. | No representative prospective alert/website population, real user trial, deployment cost or security guarantee. |
| Critical reviewer/judge | Are uncertainty, negative results and implementation failures hidden? | Question/component bootstrap intervals are conditional, no target tuning occurred, all seeds and failures are retained. A preprocessing initializer error was corrected before any visual fitting. | Three seeds are not a population sample. A large visual component strongly distorts held-out prevalence; observed astronomical evidence remains unavailable. |

## Claims allowed by evidence

- Citation:900 independent-corpus whole answers,150 question clusters,160 released positives. Coverage AP.281 versus bounded.210 on these fixed inputs/weights; no universal detector ranking. Source recall does not transfer uniformly. Sentence/answer figures are separate, not pooled.
- Phishing:7050 paired provider-labelled examples, original compact descriptors, duplicate-aware components, three seeds. URL AP.896-.950; fusion AP.750-.848; image AP.595-.762. The visual method did not improve ranking. Validation FPR<=1% does not imply test FPR<=1%; some test values exceed it.
- Astronomy:completed earlier matched simulations; no observed kilonova classifier performance. API access failures are data-access evidence only, not negative astronomical observations.
- Manuscript:a draft technical report for human author review, with verified primary references. Not an accepted paper or a demonstrated novel contribution.

## Claims explicitly rejected

No100% accuracy, live robustness, calibrated factual truth, broad real-world validity, state of the art, plagiarism-free guarantee, accepted publication, independent expert review, invented credentials, affiliation, grants, student-learning benefit or deployment readiness.

## Visual leakage and sampling challenge

4598 input-only components include a2035-record connected component and10 mixed-label components.102 components cross the provider's original train/validation/test assignments, which is why those assignments were not reused. Exact host/pixel and Hamming<=2 difference-hash links are transitively closed across all classes. That prevents these specific duplicates crossing new folds, but can merge unrelated visually simple pages and does not prove campaign independence. Test partitions contain2616 rows including1559 phishing records (59.6%), unlike the25.0% phishing paired corpus. Seeds change assignments but their aggregate sizes happen to match. Report actual sizes, not nominal60/20/20 proportions or deployment prevalence. Do not weaken grouping after viewing performance.

## Manuscript release checks

Five PDF pages rendered and visually inspected: no clipping, overlapping tables or missing pages observed. References checked against ACL Anthology (Gao et al.2023; Niu et al.2024), the pinned official model card, RAGTruth and MS MARCO sources. Tables are generated from saved JSON. The author must verify content and substantive authorship before any external submission. Preparing a draft and posting code are not peer-reviewed acceptance.
