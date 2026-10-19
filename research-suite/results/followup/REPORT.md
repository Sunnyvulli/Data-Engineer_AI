# Validation limits in three inexpensive ML workflows

Engineering research report, October 2026. Project owner: Hanumantha Rao Vulli. This is an unreviewed technical report, not an accepted paper, a claim of scientific novelty, or production validation.

## Purpose and protocol

The first release established reproducible baselines. This follow-up asks how results change under different input representations, corpus transfer, and independent simulation objects. Protocols were committed before the new outcomes were inspected: `304fbdb56b33bef05c90ec4cd6db0a74c19802aa`, with pre-execution clarification `b74e5ae0fd8542e76b0c21ccc41dec63990427a9`. The astronomy pilot's lack of target events led to a separately committed adaptive stage-two protocol `f5b950ffb2bbdf9a106cbc2678e3171a727de85f`; it must not be described as the original fixed test.

Intervals below are 95% percentile cluster bootstrap intervals from 300 resamples (seed 20261018), conditional on the fitted model. They do not correct sample selection, collection bias, benchmark exposure, or training uncertainty. Related work and unexecuted specialised baselines are listed in `docs/followup/RELATED_WORK.md`.

## 1. Phishing: the score depends on representation and corpus construction

The primary PhiUSIIL archive contains 235,795 rows. The audit found 425 exact duplicate URL rows and excluded 0 conflicting URL groups. A fixed SHA-256-ranked subset of 30,000 unique URLs was split by exact normalized hostname. This is not campaign, registered-domain, or temporal separation. Only raw text was used; precomputed similarity/probability fields were excluded.

| Representation | AP | AP interval | Recall at validation-selected threshold | Test FPR |
| --- | ---: | --- | ---: | ---: |
| full_url | 0.9986 | [0.9976, 0.9994] | 0.9946 | 0.0117 |
| hostname | 0.8948 | [0.8807, 0.9076] | 0.5733 | 0.0117 |

Paired host-cluster interval for AP(full URL) minus AP(hostname): [0.0912, 0.1176].

Class legitimate: HTTPS 100.00%; leading www. 100.00%; nonempty path 0.00%; query 0.00%.

Class phishing: HTTPS 48.63%; leading www. 41.50%; nonempty path 27.14%; query 6.04%.

Interpretation: the representation gap and class-dependent URL formatting create a serious collection-artifact risk. Removing paths/schemes also removes potentially useful real signals, so this ablation cannot causally attribute the entire score gap to artifacts. It does show why the near-perfect full-URL result should not be promoted as current-world effectiveness. Prior public engineering work reports related PhiUSIIL concerns and is credited; these observations are not claimed as a first discovery. This experiment is a second-corpus model, not external validation of the incompatible UCI-327 engineered-feature detector.

## 2. Citation support: a source recall target does not ensure target recall

Source-domain validation selects thresholds targeting at least 90% unsupported-sentence recall. All answers and sentences for a question stay together. The other corpus supplies the test set; target labels do not enter fitting or threshold choice.

| Source → target | Policy | AP (continuous policies only) | Unsupported recall | Recall interval | Review fraction |
| --- | --- | ---: | ---: | --- | ---: |
| asqa → eli5 | learned_lexical | 0.9194 | 0.9284 | [0.9067, 0.9484] | 0.7033 |
| asqa → eli5 | lexical | 0.9082 | 0.9351 | [0.9155, 0.9538] | 0.7139 |
| asqa → eli5 | released_automatic | binary/constant scores | 0.8378 | [0.8052, 0.8689] | 0.4880 |
| asqa → eli5 | review_all | binary/constant scores | 1.0000 | [1.0000, 1.0000] | 1.0000 |
| asqa → eli5 | review_none | binary/constant scores | 0.0000 | [0.0000, 0.0000] | 0.0000 |
| eli5 → asqa | learned_lexical | 0.8570 | 0.8633 | [0.8130, 0.9096] | 0.5253 |
| eli5 → asqa | lexical | 0.8211 | 0.8561 | [0.8061, 0.9066] | 0.5055 |
| eli5 → asqa | released_automatic | binary/constant scores | 0.7770 | [0.7177, 0.8309] | 0.3342 |
| eli5 → asqa | review_all | binary/constant scores | 1.0000 | [1.0000, 1.0000] | 1.0000 |
| eli5 → asqa | review_none | binary/constant scores | 0.0000 | [0.0000, 0.0000] | 0.0000 |

The released automatic policy uses the historical ALCE binary support judgments, not a newly executed current entailment model. Binary-score AP is not compared with continuous ranking AP as a superiority claim. Review fractions and thresholds differ; this is a descriptive operating-point comparison, not matched-cost proof. Lexical overlap still cannot establish truth or detect all contradictions. Corpus transfer within ALCE does not establish performance across all disciplines, modern models, or actual student workflows.

## 3. Astronomy: retain the feasibility failure

The originally fixed first 5,000 independent objects yielded 0 kilonova targets among 5,000 detected objects. Status: **rare-event discrimination not estimable: selected sample lacks both classes**. AP: not estimable; rare-event recall: not estimable. No artificial zero or perfect rare-event score is substituted.

The adaptive second stage excluded the exposed first 5,000 objects and the shard's final object. It evaluated 27,925 detected objects containing 2 kilonova targets, with no original-training ID overlap. The three-day forest was frozen: no fitting or threshold selection used these target labels. Status: **two-class evaluation completed**.

AP: 0.0001; top-5% precision: 0.0000; top-5% recall: 0.0000.

AP interval: [0.0000, 0.0002]; budget-precision interval: [0.0000, 0.0000]; budget-recall interval: [0.0000, 0.0000].

Only 2 positive events were observed. The recall bootstrap can be degenerate when every observed event is missed; its zero-width interval must not be read as certainty. A post-outcome Clopper-Pearson diagnostic gives [0.0000, 0.8419] under independent, exchangeable positive-event assumptions. These assumptions may not hold across shared simulations. No stable rare-event generalisation claim follows.

This remains PLAsTiCC simulation-to-simulation testing. It does not validate performance on observed Rubin alerts, gravitational-wave triggers, a robotic telescope, or actual discoveries. The adaptive second stage and the shard's selection properties limit interpretation. Specialised time-series models such as RAPID have not been rerun under a matched protocol.

## Reproduction

From the research-suite directory, install the documented baseline dependencies, fetch the baseline data, and generate the frozen three-day model using the unchanged seed-42 baseline implementation. The additional public-data download is approximately 321 MB.

```bash
research-suite fetch followup
python -m research_suite.followup phishing
python -m research_suite.followup citations
python -m research_suite.followup transients --trust-local-model
python -m research_suite.followup transients --trust-local-model --remaining-shard
python -m research_suite.followup_report
```

Only load joblib artifacts that you trained and trust. URL strings are never visited. Raw datasets are not committed. Input hashes, model hash, environment versions, split sizes, class counts, and per-policy metrics are in adjacent JSON files. The fetch command checks fixed hashes.

## Four-perspective self-review

| Perspective | Decision from the evidence |
| --- | --- |
| Researcher/student | New runs are reproducible, and the zero-target pilot is retained. The owner must reproduce and explain the results before presenting the work. |
| Supervisor | Corpus-transfer and interval reporting improve the baseline package, but a contemporary specialised comparison and a demonstrated new contribution are still missing. |
| Industry user | Collection artifacts, domain-transfer loss, historical labels, and simulation limits prevent claims of deployment readiness. |
| Critical reviewer | No scores or missing events were invented. Adaptive changes, binary/continuous comparison limits, prior work, and limitations are explicitly disclosed. |

These perspectives are structured self-review, not external review or expert endorsement. No publication submission, external message, live payment, or paid model call was performed.


A later [open entailment comparison and independent-source probe report](OPEN_COMPARISON_REPORT.md) records the next bounded experiments. Its conclusions and remaining gaps supplement this earlier report.
