# Three-paper readiness decision

Audit date: 19 October 2026. These are research drafts, not submitted or accepted publications. This decision supersedes earlier conversational suggestions based only on project labels.

| Study / manuscript | Completed evidence and artifacts | Scientific readiness decision | Concrete remaining work |
| --- | --- | --- | --- |
| Citation: Length Baselines and Evidence-Support Triage | Focused manuscript PDF/Markdown; 900 RAGTruth QA responses, 150 question groups; source-frozen lexical/NLI comparisons; permitted scores and uncertainty; independent metric reconciliation | Most developed draft for author review. Journal submission readiness not established. | Expand matched recent task-specific comparators and related-work positioning; distinguish annotation-unit shift from domain shift; obtain substantive human review. Any outcome-driven improvement needs unexposed confirmation. |
| Phishing: When Compact Screenshot Fusion Hurts | New focused PDF/Markdown; 7,050 paired records; all three seeds and negative fusion outcomes; saved-score and component-support audits | Bounded negative-result technical report. Not defensible as general phishing-detector validation. | Every test positive lies in one component per seed. Obtain multiple independently sampled positive components and a prospectively frozen confirmation design; inspect grouping bridges and collection shortcuts before scoring new data. Do not relax grouping after outcomes or present three seeds as independent positive replications. |
| Astronomy: Ranking Is Not Recovery | New simulation-only PDF/Markdown; fixed early observation window; forest/GRU comparison; four saved-score reconciliations; explicit budget failure and access logs | Simulation technical report. Observed-event validation and broad recovery claims remain unsupported. | More independently selected positive events, additional seeds/resource-matched comparator selection, physical photometry harmonization and permissioned observed detections. Existing access record has 18 fixed objects unattempted, not 20 completed queries. |

## What was audited in this release

All 58 existing integrity tests passed before changes. Saved citation/phishing metrics reconciled for 19 policies; astronomy AP, ROC AUC and top-5% counts reconcile for four model/split combinations. Table values in the two new manuscripts are checked against measured JSON by build_focused_papers.py. The source/external astronomy IDs are disjoint. This is saved-artifact verification, not fresh training, raw-data reproduction or independent scientific peer review.

The phishing bootstrap metadata incorrectly named RAGTruth source_id because it reused a citation helper. The helper now accepts an explicit resampling-unit description; visual inference passes the screenshot/hostname component. Existing aggregate metadata are corrected without changing numeric scores, cutoffs or intervals. The audit exposes one positive component per seed and only 179/300 valid seed-42 bootstrap resamples. Narrow or degenerate intervals do not establish independent positive-component sensitivity.

The existing citation manuscript remains the canonical citation paper. The training-budget selector pilot is exploratory supporting work, not a fourth publication or a separate paper that duplicates its parent results. Do not create multiple thin archival papers from the same claims.

## Publication routes and current policy checks

| Destination | Decision | Cost and qualification |
| --- | --- | --- |
| TMLR: https://jmlr.org/tmlr/ | Conditional first journal to assess for the citation study after scientific strengthening and author review. An applications/behavior study can be in scope, but routine reimplementation is insufficient. | Official policy imposes no author fees. Anonymized submission, current template, eligible authors and sufficient annual quota required. Current single-author quota parameters allow two ordinary single-author submissions per year; do not assume all three can be submitted together. No acceptance or readiness claim. |
| Astronomy and Computing: https://shop.elsevier.com/journals/astronomy-and-computing/2213-1337 | Conditional astronomy target: official scope includes simulations and reports on positive/negative practical outcomes. An observed-data paper would require additional evidence; a strictly simulation report must retain its limits. | Scope verified; current author-fee route could not be verified from the accessible policy pages. Not certified as a free publication option. |
| Computers & Security: https://shop.elsevier.com/journals/computers-and-security/0167-4048 | Remove earlier recommendation for this ML phishing paper. Official publisher page states a moratorium on submissions featuring significant AI/ML components. | An apparent broad cybersecurity topic match does not override this exclusion. |
| arXiv: https://info.arxiv.org/about/index.html | Possible preprint route after human review, appropriate category and moderation; phishing cs.CR, citation cs.CL and astronomy astro-ph.IM are provisional category suggestions, not guaranteed classifications. | Official page confirms no submission fees and no peer review. Endorsement/account and source-format requirements may apply. No deposit performed. |
| Zenodo: https://about.zenodo.org/terms/ | Possible versioned technical-report/artifact DOI route after human review and rights checks. | Official terms allow free uploads; deposit does not establish journal acceptance or peer review. No DOI reserved or invented. |

Primary policy pages checked 19 October 2026: TMLR https://www.jmlr.org/tmlr/editorial-policies.html ; author guide https://jmlr.org/tmlr/author-guide.html ; arXiv https://info.arxiv.org/about/index.html ; Zenodo https://about.zenodo.org/terms/ ; publisher journal pages above. No conference registration or journal APC is incurred. No simultaneous archival submissions.

## Release and author handoff

GitHub publication of code and drafts is within the authorized project scope. External manuscript submission has not been performed. Before external submission the human author needs to inspect the full paper, make substantive revisions as appropriate, confirm authorship and exact final claims, and provide accurate identity/account metadata. This is a concrete review of the supplied manuscripts, not a request to approve an unseen proposal. Scientific deficits listed above cannot be resolved by author approval alone.

Reconcile outputs without raw data:

```
python docs/paper/audit_outputs.py
python docs/paper/audit_three_studies.py
python docs/paper/build_focused_papers.py
PYTHONPATH=src python -m unittest discover -s tests -v
```

The PDF builder requires reportlab in addition to the scientific dependency lock. Model/data downloads are needed for full experiment regeneration. Scores and reports retain upstream terms; raw research text, dangerous URLs and screenshots remain excluded.

## Within-generator follow-up — 20 October 2026

CI now regenerates length AP/AUC within all six generators and pooled average tied ranks divided by generator sample size. Within-generator length ranks yield AP 0.295864 / AUC 0.632204; symmetrically normalized coverage NLI yields AP 0.236435 / AUC 0.625422. Every row retains both ranks. No equivalence, superiority or causal decomposition is established. The GPT-4 one-positive stratum remains visible and explicitly unstable. Original model outputs, source thresholds, test counts and unpublished status are unchanged.
