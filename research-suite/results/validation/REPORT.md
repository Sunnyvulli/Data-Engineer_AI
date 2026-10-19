# Additional scientific validation

October19,2026 UTC. All three projects have working, measured baseline implementations. These new bounded experiments do not establish broad deployment validity. See docs/paper/REVIEW_AND_CLAIM_AUDIT.md for the skeptical four-perspective review.

## Citation support

Frozen independent RAGTruth test:900 QA answers,150 question groups,160 positives,740 negatives; zero exact ALCE question exclusions. No target training or tuning. Sentence-level ALCE and answer-level RAGTruth are different units.

| Source calibration | Policy | AP | Unsupported recall | Supported FPR | Review fraction | Missed positives |
| --- | --- | --- | --- | --- | --- | --- |
| ASQA | Lexical | .28081 | 1.00000 | .98649 | .98889 | 0 |
| ASQA | Bounded NLI | .21016 | .33125 | .27027 | .28111 | 107 |
| ASQA | Coverage NLI | .28124 | .60000 | .31081 | .36222 | 64 |
| ELI5 | Lexical | .21803 | .81875 | .64054 | .67222 | 29 |
| ELI5 | Bounded NLI | .21016 | .79375 | .64054 | .66778 | 33 |
| ELI5 | Coverage NLI | .28124 | .91250 | .66486 | .70889 | 14 |

Coverage uses the same frozen NLI weights and precommitted windows. Its AP difference from ELI5 lexical has conditional question-bootstrap95% interval[.01657,.11699]; from ASQA lexical[-.05315,.05365]. Neither is a universal superiority claim.151 evidence contexts and458 claims were truncated by bounded NLI. Coverage used1836 pairs, zero re-encoding truncations. Source thresholds offer no target recall guarantee; even the strongest measured recall/workload tradeoffs leave material misses or review burden. Full metrics, generator/quality strata and uncertainties are in external-support.json. Full permitted derived scores are in external-support-scores.json. No raw restricted text is published.

## Paired visual phishing

Verified archiveMD5 85937228498c1efffb2ee497389482a2. The actual download contains7062 PNGs;7050 exact unique agreeing URL matches retained,8 ambiguous and4 unmatched excluded. Paired corpus1765 phishing/5285 legitimate records. There are4598 components, a largest2035-record component and102 components spanning provider splits. New folds keep these groups intact, not the provider's assignments.

| Seed | URL AP / Recall / FPR | Image AP / Recall / FPR | Equal fusion AP / Recall / FPR |
| --- | --- | --- | --- |
| 17 | .90351 / .50417 / .00662 | .76211 / .00000 / .00757 | .84756 / .24503 / .01703 |
| 42 | .89631 / .53945 / .00851 | .59550 / .00385 / .02271 | .75044 / .19949 / .03595 |
| 91 | .95012 / .74663 / .01325 | .62295 / .00000 / .01514 | .82565 / .40731 / .05582 |

Thresholds selected for empirical validationFPR<=1% do not transfer that budget to the test set. URL ranking exceeds this original compact image and equal-fusion baseline in all three seeds. Do not describe this as a successful multimodal improvement. Components distort actual fold sizes:3325train/1109validation/2616test, with1559test positives. This tests source-labelled paired data under the frozen grouping rule, not live campaigns, manually adjudicated ground truth or deployment rates. Model runtime including decode/grouping/training676.54seconds. Persisted test predictions are compressed as visual-phishing-scores.json.gz; decompress with Python gzip to reproduce audit metrics. No downloaded URLs/screenshots are redistributed.

Post-outcome component-support audit: all 1,559 held-out phishing positives are in one 2,035-row component in each seed. Only 179/300 seed-42 component bootstrap samples retain both classes. Conditional intervals cannot establish generalization across positive components, and the three seeds are not independent positive-component replications. The copied uncertainty-unit label is corrected to screenshot/hostname component; numerical predictions and intervals are unchanged. See three-study-audit.json and docs/paper/PHISHING_MANUSCRIPT.md.

## Astronomy

Earlier matched simulation comparisons and failures remain in results/followup/RECURRENT_REPORT.md. The new all20-object ZTF protocol is committed, but observed data access has failed; no real-event model metric is claimed. Inspect observed-alerts.json for exact current access status. A provider-selected supernova-only sample could establish ingestion/causality at most. Positive kilonova cases, compatible photometric representation and a representative alert population remain missing. Do not silently replace a selected missing object or map ZTF bands onto LSST.

## Reproduce and inspect

Install requirements-lock.txt and the research package. Citation inference additionally requires requirements-nli.txt and the pinned model files; source data download pointers/hashes are in the protocol. Visual input uses official Zenodo21379702 archive and openpyxl/Pillow dependencies. Run the corresponding modules from the suite root:

```
python -m research_suite.external_support --data data/raw --output results/validation --models data/models/nli-deberta-v3-small
python -m research_suite.visual_phishing --archive data/raw/multimodal-phishing.zip --output results/validation
python docs/paper/audit_outputs.py
python -m unittest discover -s tests
```

These are noncommercial research uses subject to underlying data terms. Evaluation scripts, descriptors and reporting code are original; methods and source datasets are attributed. A PDF manuscript and editable Markdown are in docs/paper/. No paper has been submitted externally or accepted.
