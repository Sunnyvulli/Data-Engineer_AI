# Ranking Is Not Recovery: A Budgeted Audit of Early Kilonova Classification in Simulated Light Curves

Hanumantha Rao Vulli

Research draft for author review. 19 October 2026. Simulation study; observed-event validation incomplete. Not submitted, peer reviewed or accepted. No institutional affiliation asserted.

## Abstract

Early astronomical classifiers must recover rare targets within finite follow-up resources. We compare a frozen random-forest baseline with a credited RAPID-inspired recurrent adaptation on PLAsTiCC simulated light curves. Both receive only observations from first detection through three days later and select the highest-ranked 5% of objects. On 1,570 source test objects containing 21 kilonova targets, recurrent AP is 0.0893 versus forest AP 0.1459, while budgeted recovery is eight versus seven targets. On a separate 27,925-object simulated remainder containing two targets, recurrent AP is higher, yet both models recover zero targets within budget. These metric disagreements caution against treating ranking improvement as operational recovery. One seed, reused exposed outcomes, two independent targets and incompatible observed-data representation prevent a general sensitivity claim. We provide frozen protocols, derived scores and an explicit observed-data failure record rather than inferring real-event performance.

## 1. Research question and prior work

PLAsTiCC provides simulated astronomical time series for classification research [1,2]. RAPID studies early transient classification using recurrent neural networks [3]. We ask a resource-specific question: under the same allowed early observations and ranking budget, does a recurrent adaptation improve rare-target recovery over an existing forest baseline?

This is an empirical comparison of established methods. The recurrent implementation changes RAPID's representation, time grid, binary target and training schedule. It does not reproduce the original paper, current astrorapid package, released survey-specific weights or a new architecture. The current package's TCN and released ZTF/Pan-STARRS passbands are not silently treated as the original two-GRU design or LSST weights. The protocol at b2a590a36d5f3a2e265309b15273e81500e54697 was fixed before new recurrent outcomes. The forest benchmark and independent two-target test outcomes were already exposed, so this is not blind confirmation.

## 2. Data and allowed information

Source data are the pinned PLAsTiCC unblinded release [2]. The seed-42 object-disjoint allocation has 4,708 training objects with 60 positives, 1,570 validation objects with 21 positives and 1,570 test objects with 21 positives. Metadata class 64 defines the kilonova target. Redshift, extinction, simulation truth and metadata predictors are excluded.

First alert is the first detected_bool=1 observation in any of six LSST bands. Allowed information starts there and ends three days later, inclusive. No pre-alert or future photometry enters either model. The independent simulated remainder uses shard-01 objects with IDs above 53125, excluding the previously identified potentially incomplete last ID 342868. It contains 27,925 objects and only two positives. Source/external ID disjointness and score alignment are independently checked; this does not establish a representative real sky population.

The recurrent input uses 13 causal grid times at 0.25-day spacing. Each band contributes latest available flux, uncertainty and an observed-band indicator. Same-time, same-band points combine by inverse-variance weighting. Before a band's first observation, its channels remain zero. Only source-training allowed observations determine scale factors. Flux is transformed with asinh and uncertainty with log1p after scaling. No interpolation sees a later measurement. This compression differs from the forest summary features and can discard within-bin history. Equal allowed observations therefore do not mean equal representations or resources.

## 3. Fixed models and evaluation

The adaptation has two unidirectional 100-unit GRUs with batch normalization and 0.2 dropout, followed by a two-class softmax. It has 97,602 parameters and is trained for exactly 25 epochs using balanced class weights, Adam at 0.001, batch size 64 and seed 42. The first best source-validation AP checkpoint is retained; epoch 23 is selected with validation AP 0.107131. The forest has no corresponding checkpoint search. This selection asymmetry is retained as a limitation, not hidden as matched compute.

The operational policy selects ceil(0.05*n) objects ranked by positive score, using stable sorted-ID tie handling. AP and ROC AUC describe ranking; default 0.5 threshold results are supplementary diagnostics. Class-weighted scores are not established calibrated probabilities. All methods use identical held-out objects within a split.

Uncertainty uses 300 complete-object bootstrap resamples conditional on fitted policies. These intervals exclude fitting and source-selection uncertainty. For only two independent positives, bootstrap recall can be degenerate; illustrative exact-binomial recall intervals additionally assume exchangeable independent positive events and do not remove sampling bias. No claim of population certainty follows from a zero-width empirical interval.

## 4. Measured outcomes

| Evaluation | Model | Objects | Positives | AP | Selected | Found |
| --- | --- | --- | --- | --- | --- | --- |
| Source test | GRU adaptation | 1570 | 21 | 0.089313 | 79 | 8 |
| Source test | Frozen forest | 1570 | 21 | 0.145852 | 79 | 7 |
| Simulated remainder | GRU adaptation | 27925 | 2 | 0.000767 | 1397 | 0 |
| Simulated remainder | Frozen forest | 27925 | 2 | 0.000072 | 1397 | 0 |

The GRU has lower source AP but recovers one more target at the fixed budget: 38.1% versus 33.3% recall. The paired source AP difference is -0.056539, with conditional 95% percentile interval [-0.160067, 0.028353]. This does not establish a consistent source ranking advantage for either method.

On the simulated remainder, GRU AP exceeds forest AP by approximately 0.000696, with conditional interval [0.000451, 0.002074]. Nevertheless, both miss both targets among 1,397 selected objects. A ranking difference can coexist with identical failure at the operational budget. With zero recoveries among two positives, the illustrative two-sided Clopper-Pearson 95% recall interval is [0, 0.841886]. The sample is too sparse to estimate population recovery precisely. The interval must not be interpreted as an observed probability of successful deployment.

An independent saved-CSV audit recomputes both models' AP, ROC AUC, selected counts and recovered targets on both splits to absolute tolerance 1e-12, and checks object-ID uniqueness and source/external disjointness. This confirms arithmetic consistency of the released scores, not raw-data reproduction, label correctness or independent peer review.

## 5. Observed-data feasibility and failures

Observed-event validation is not completed. The frozen BTS negative-control sample contains twenty provider-classified supernova objects selected before queries. The first selected object's public IRSA cone returned zero rows under that specific query. That is an access/coverage outcome, not a classifier nondetection or a general absence of photometry.

The subsequent ALeRCE alert-access record reports two unique selected objects attempted, zero valid detection packets and eighteen unattempted objects. Connection failures and a proxy 403 are preserved. No classifier metrics are available. The sample is not replaced with convenient objects after observing failures, and no hypothetical fluxes are created.

Even successful access alone would not justify passing ZTF data into the LSST-simulation model. Filter responses, catalog magnitudes versus difference fluxes, uncertainty units, broker detection history and source matching need physical and procedural harmonization. A supernova negative-control frame cannot estimate kilonova sensitivity. A famous single observed positive would remain an individual diagnostic, not a representative positive population. No observed astronomical performance is reported here.

## 6. Reproducibility and limitations

Canonical source: Sunnyvulli/Data-Engineer_AI/research-suite. The frozen specification is docs/followup/RECURRENT_PROTOCOL.md. Implementation is src/research_suite/recurrent.py. Results and aligned derived CSV scores are in results/followup/recurrent-comparison.json, recurrent-source-scores.csv and recurrent-independent-scores.csv. The new audit is docs/paper/audit_three_studies.py. Data-byte hashes, source-only scales, training history, local artifact hashes and dependency versions are retained in the result JSON and runtime lock.

The first evaluation stopped after training because of a result-schema lookup error. Recovery loaded the already selected hash-checked model without retraining or choosing a new checkpoint. Recovery evaluation took 199.4 seconds with 2,602.5 MiB peak process RSS; full original training time was not preserved and is not invented. Regenerating full inference requires rebuilding the locally trained trusted artifacts and fetching pinned raw data; saved-score reconciliation alone does not regenerate those artifacts.

Major limitations are one training seed, exposed test outcomes, two independent targets, representation and selection-budget asymmetries, and no admitted observed-event benchmark. A stronger study needs a prespecified additional simulated confirmation set with materially more positives, resource-matched comparator selection, and physically compatible observed photometry with verified labels. Selection must precede outcome inspection. These remain requirements rather than completed results.

The human author must inspect and approve the final content and satisfy substantive authorship requirements. No institution, expert endorsement, accepted publication, successful discovery or deployment is claimed.

## 7. Conclusion

For these fixed simulated comparisons, AP and budgeted target recovery disagree. Both models miss both independent simulated targets at the 5% budget. The work supports a reproducible bounded failure analysis, while additional positive events and compatible observed-data validation remain essential for stronger scientific claims.

## References

[1] The PLAsTiCC team (2018). The Photometric LSST Astronomical Time-series Classification Challenge (PLAsTiCC): Data set. https://arxiv.org/abs/1810.00001 .

[2] PLASTICC Team and PLASTICC Modelers (2019). Unblinded Data for PLAsTiCC Classification Challenge. Zenodo record 2539456. Data curators: Gautham Narayan and Richard Kessler. https://zenodo.org/records/2539456 . Raw data are not redistributed here.

[3] Muthukrishna et al. (2019). RAPID: Early Classification of Explosive Transients using Deep Learning. PASP 131, 118002. https://doi.org/10.1088/1538-3873/ab1609 . https://arxiv.org/abs/1904.00014 .

[4] RAPID official implementation. https://github.com/daniel-muthukrishna/astrorapid . Inspected revision 7f28499ff71f8520ed6fcf530929587336a0c5de; conceptual attribution, not an exact reproduction.
