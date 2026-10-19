# RAPID-inspired recurrent comparison and observed-data readiness

Original implementation/analysis by Hanumantha Rao Vulli. Measured October 19, 2026 UTC. This is a bounded adaptation experiment, not scientific novelty, an accepted publication, a RAPID paper/package reproduction or real-event validation.

## Fixed comparison and attribution

The [protocol](../../docs/followup/RECURRENT_PROTOCOL.md) was committed before training (`b2a590a36d5f3a2e265309b15273e81500e54697`). The model adapts the two unidirectional 100-unit GRUs described by [Muthukrishna et al. (2019)](https://arxiv.org/html/1904.00014v2). It changes the input grid, six-band representation, binary endpoint target and training budget. The current astrorapid repository uses a TCN and released ZTF/Pan-STARRS filters; those weights were not relabelled as LSST weights.

Both methods receive only observations between first detected_bool=1 and three days later, inclusive. GRU uses a causal 13-point grid with latest observed flux/error/mask per band and source-training-only scales. Forest uses its original summary features. Thus allowed observations, object split, target and ranking budget match, while representation and computational/selection resources differ. The GRU retains only its best source-validation AP checkpoint; forest had no analogous checkpoint search. Exposed simulated test outcomes are reused and are not a fresh blind holdout.

| Split | Objects | Kilonova targets |
|---|---:|---:|
| train | 4708 | 60 |
| validation | 1570 | 21 |
| test | 1570 | 21 |

One seed 42, exactly 25 epochs. Selected epoch 23 by source-validation AP 0.1071. Network parameters: 97,602. Model revision decisions were not based on test results. Class-weighted scores are not calibrated probabilities.

## Measured results

| Evaluation | Model | Objects | Positives | AP | ROC AUC | Top-5% selected | Targets found | Budget recall |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Source held-out | rapid_inspired_gru | 1570 | 21 | 0.089313 | 0.8235 | 79 | 8 | 38.1% |
| Source held-out | frozen_forest | 1570 | 21 | 0.145852 | 0.8743 | 79 | 7 | 33.3% |
| Independent simulated remainder | rapid_inspired_gru | 27925 | 2 | 0.000767 | 0.9310 | 1397 | 0 | 0.0% |
| Independent simulated remainder | frozen_forest | 27925 | 2 | 0.000072 | 0.4210 | 1397 | 0 | 0.0% |

On the source held-out split, GRU has lower AP but selects one additional target at the same budget (8 versus 7). On the independent remainder its AP is higher, but both models miss both targets within the budget. These differing metric directions and sparse targets do not establish overall superiority or useful deployment sensitivity.


Paired AP differences (GRU minus forest), with 300 complete-object bootstrap resamples conditional on the fitted models:

- Source held-out: -0.056539; 95% interval [-0.16006661095516342, 0.028352718455091422].
- Independent remainder: 0.000696; 95% interval [0.0004509565611142046, 0.002074452513664329].

The independent remainder contains only two positive events. This is insufficient for a reliable population sensitivity claim. Budget recall intervals from sparse-event bootstraps can be degenerate; the exact-binomial diagnostics below require independent exchangeable positive events and do not remove selection/domain bias:

- rapid_inspired_gru: 0/2 targets selected; illustrative Clopper–Pearson 95% recall interval [0.0, 0.841886116991581].
- frozen_forest: 0/2 targets selected; illustrative Clopper–Pearson 95% recall interval [0.0, 0.841886116991581].

Detailed default 0.5 diagnostics and uncertainty are retained in `recurrent-comparison.json`. Default0.5 is not the operational budget policy. `recurrent-source-scores.csv` and `recurrent-independent-scores.csv` preserve aligned IDs, simulated labels and both scores. Original forest AP and independent population size were checked against the earlier release; source/external ID overlap is rejected.

## Failure, recovery and compute

The initial evaluation stopped after training on a JSON-schema lookup error: the old independent AP was nested under metrics, not at top level. All 25 validation records and the already selected model were retained. Evaluation resumed from the recorded model SHA-256 using safe-mode Keras loading; no retraining, new checkpoint selection or parameter change occurred. `recurrent-recovery.json` records the error, selected-artifact hash and source hashes. The artifact hash must match the final result.

Recovery evaluation wall time: 199.4 seconds; peak recovery-process RSS 2602.5 MiB. Original training duration/RSS were not separately persisted before the error and are not fabricated. TensorFlow 2.21.0, Keras 3.15.1, four CPU intra-op threads and deterministic operations. Exact installed versions are in `requirements-recurrent-runtime-lock.txt`. The retained dependency scan reported no advisories at that scan, not a security guarantee.

## Observed-data readiness: no classifier scores

The [readiness protocol](../../docs/followup/OBSERVED_READINESS_PROTOCOL.md) was committed before CSV sampling/query (`a90e35460fc03513d9ca3bb77433db7a7751526f`). Source: [official BTS Sample Explorer](https://sites.astro.caltech.edu/ztf/bts/explorer.php?format=csv), which requests citation of its research paper. Public visibility is not asserted to provide a blanket redistribution license; the full source table is not redistributed. IRSA public-data terms and acknowledgments are linked in the output manifest.

The default-query snapshot had 10,551 records, including 6,989 unique eligible provider-classified SN records. The 20 lowest SHA-256 ZTF identifiers were selected as a negative-control frame. Provider classifications were not independently adjudicated; this is not a kilonova-positive or representative alert sample.

The fixed first selected object, ZTF21acfaugw, returned HTTP 200 and 0 photometry rows for the frozen 1.5 arcsec public DR24 g/r cone. That outcome is retained; no replacement object was chosen after seeing it. The earlier 724-row documentation-example query is not substituted for this sampling result.

Direct model admission was rejected. Verified gaps include no returned rows for the preselected cone, ZTF-versus-LSST filter response, catalog magnitudes rather than verified difference-flux inputs, absent broker detection history and unestablished source crossmatch. No flux, uncertainty, alert flags or model results were invented. Sampling/query/hash/schema details and selected factual identifiers are in `observed-readiness.json`; raw source tables remain local. A cached query must match its recorded URL and SHA-256 before reuse.

A follow-on observed study would need a new frozen access/coverage protocol, compatible difference-alert photometry and physical passband/unit mapping, verified source identities and an independently labelled evaluation frame. These are not closed by this access audit. The failure of this direct mapping does not prove all observed astronomy comparisons impossible.

## Four-perspective self-review

- Researcher: report every measured ranking and missed event; one seed and reused simulations cannot establish broad model superiority.
- Supervisor: source validation selected the checkpoint; the schema failure was recovered without retraining. Require fresh evaluation for any outcome-driven revision.
- Industry user: a shared 5% follow-up budget exposes resource cost, while sparse positives and absent observed-data admission prevent deployment claims.
- Critical reviewer: this is a credited GRU adaptation with differing representations/resources, not a reproduction. Zero-row archive access and provider-label sampling are explicit limitations, not fabricated validation.

These are structured self-review perspectives, not independent expert endorsements.

## Reproduction

```bash
python -m pip install -r requirements-lock.txt
python -m pip install -r requirements-recurrent-runtime-lock.txt
PYTHONPATH=src python -m research_suite.recurrent --trust-local-model
PYTHONPATH=src python -m research_suite.observed_readiness
PYTHONPATH=src python -m research_suite.recurrent_report
python -m unittest discover -s tests -v
```

Fetch the original/follow-up data and reproduce the original trusted seed 42 forest artifact first. Never load someone else’s joblib model. Optional `--resume-selected-model` requires the locally generated selected artifact, full training progress and matching recovery manifest; ordinary runs train from scratch under the fixed protocol. The changing BTS snapshot is cached locally with hashes; a new snapshot is a new dated readiness audit.
