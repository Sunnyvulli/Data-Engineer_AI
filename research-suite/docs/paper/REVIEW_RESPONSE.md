# Response to manuscript flags — 20 October 2026

This responds to the critique supplied by the portfolio owner. It is an author-side evidence audit, not independent peer review. The original target has been exposed; new diagnostics are explicitly post hoc.

| Flag | Evidence and action | Remaining work |
| --- | --- | --- |
| Generator / length confounding | Added reproducible cached-length rankings, within-generator AP/AUC, counts, and five-fold question-group cross-fitted generator priors. Length AP 0.385779 / AUC 0.726976 exceeds every tested detector; generator-prior AP 0.273537 / AUC 0.685220 uses other target groups' labels. Manuscript abstract, interpretation and conclusion now disclose the adverse length result. | Causal separation, stable small-generator estimates and fresh confirmation are unresolved. Target-supervised prior is not a source-only comparator. |
| Weak absolute performance | Retained prevalence 160/900, review-all extremes and missed positives; explicitly disclaimed semantic detection advantage in light of the length ranking. | A stronger task-specific detector has not been run. |
| Selective abstract interval | Abstract now gives both coverage-versus-lexical intervals and their exploratory, 300-resample, uncorrected status. | No family-wise inference or new larger bootstrap study is claimed. |
| Thin calibration / cutoff gap | Added exact ASQA 0.989811 / ELI5 0.451716 cutoffs, 172 / 363 rows and 19 groups each. State lack of sensitivity evidence and that scores are not calibrated probabilities. | Source-group calibration uncertainty and a cause for the cutoff gap are not established. |
| Methods / tables / formatting | Table 2 includes ROC AUC. Percentages use two decimals, including 146/160 = 91.25%; corrected audit rounding and text spacing. Embedded fonts replace renderer-dependent standard fonts; keep tables together. | None for these reporting fixes; model execution itself was not repeated. |
| Missing direct prior work | Verified and cited AttrScore (Yue et al., 2023) and AttributionBench (Li et al., 2024) using ACL primary records; updated related-work notes. | A focused reference update is not an exhaustive literature review. Protocol precedes new diagnostic computation, but not earlier target exposure. |
| Broad title | Added an explicit restriction to ALCE sentences → RAGTruth whole answers in interpretation. Initial response kept the old title; the follow-up now reframes title, abstract, section 1 and conclusion around length controls. Canonical file URLs remain stable. | New title: Length Baselines and Evidence-Support Triage: An ALCE-to-RAGTruth Audit. Academic CV citation and public research-card interpretation are synchronized in the portfolio follow-up. |

## Checks and reproducibility

Run from `research-suite`:

```sh
PYTHONPATH=src python -m unittest discover -s tests -q
python docs/paper/review_diagnostics.py
python docs/paper/audit_outputs.py
python docs/paper/audit_three_studies.py
```

58 existing integrity tests pass; the diagnostic script additionally checks synthetic exact metrics, complete-group folds and held-out-label invariance. All 19 saved-output policy checks reconcile. The multi-study audit passes while retaining its negative validity findings. CI regenerates the diagnostic JSON and requires a zero diff. Report includes input SHA-256s, seed 20261020, all 900 row IDs, lengths, folds and prior scores; restricted text is not redistributed. A per-row cache permutation that preserved the entire exact risk vector would remain an alignment limitation because the old token audit has no row IDs. Do not claim a fresh raw-data reproduction.

## Prospective reviewer contact (not contacted)

Verified on 20 October 2026: [Huan Sun's official Ohio State CSE profile](https://cse.osu.edu/people/sun.397) lists her as Associate Professor with tenure and gives `sun.397@osu.edu`. AttrScore's ACL record confirms authorship with Yu Su and four other authors. This is a possible contact, not an agreement to review or an endorsement. No email, review request, paper submission or public attribution of this critique to her has been sent.

A useful future request should ask about length/generator confounding, the exploratory multiple contrasts, and calibration on only 19 question groups. First finish the matched-comparator work and obtain the named author's review of the artifacts.

## Career-material consistency

No qualification, employment fact, publication status, enrollment, flagship engineering metric or integrity-test count changed. The research remains an unpublished audit with stronger comparators and independent human review pending. Existing career claims of reproducible experiments remain accurate; no new detector-performance boast should be added to the resume or cover letters. Portfolio/resume/CV/letter wording should retain those boundaries. No PDFs outside this manuscript were regenerated merely for activity.

## Within-generator follow-up — 20 October 2026

CI now regenerates length AP/AUC within all six generators and pooled average tied ranks divided by generator sample size. Within-generator length ranks yield AP 0.295864 / AUC 0.632204; symmetrically normalized coverage NLI yields AP 0.236435 / AUC 0.625422. Every row retains both ranks. No equivalence, superiority or causal decomposition is established. The GPT-4 one-positive stratum remains visible and explicitly unstable. Original model outputs, source thresholds, test counts and unpublished status are unchanged.


## Additional statistical review — 25 October 2026

Before implementing or running the additional analyses, committed `EXPLORATORY_ANALYSIS_PLAN.md` in 9002e048b42cec344165f8f8e4fe94f59a0e8bd6. It fixes all paired AP/AUC contrasts, question-cluster sampling, 5,000 draws and seed, GPT-4 inclusion/sensitivity, cross-fitting folds, length transform and model specifications. All remain exploratory because outcomes were already exposed. The annotation-exposure extension is a bounded generator-specific check, not a causal verdict.

Immediately softened the abstract, research question, interpretation and conclusion: no evidence-reading advantage has been established, and neither approach has been shown superior. Existing point estimates and historical intervals are unchanged. New intervals, incremental-value models, token-rate results and AttrScore have not been computed in this revision. Independent advisor review and double annotation remain pending.


## Fixed exploratory analyses executed — 25 October 2026

See EXPLORATORY_RESULTS.md and the updated manuscript Tables 6–9. The original plan is unchanged. Published primary code b040c4d preceded computation, and the dated token implementation amendment d57efc0 preceded token-rate analysis. All planned comparisons are reported, including zero-crossing intervals, generator-specific and macro estimates, and GPT-4 exclusion. Raw pooled AP favors length conditionally; NLI adds conditional out-of-fold AP/AUC signal beyond length and generator under the fixed model. This is a fresh-confirmation hypothesis, not a general method advantage.

All 235 character spans and 900 cached token lengths reconcile. Token-rate trends remain bounded annotation descriptions. Numerical convergence accepted boundary GPT-4 resamples with no annotated tokens; the post-run execution notes retain the original fits and explicitly flag nonidentification. No retrospective exclusion or result-driven plan edit occurred. Tests and saved-output audits check implementation and arithmetic, not statistical conclusions. AttrScore suitability/matched execution and genuinely independent confirmation/review remain separate gates.
