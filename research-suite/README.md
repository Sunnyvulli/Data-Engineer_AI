# Applied ML Research Suite

Three runnable, independently implemented research baselines by Hanumantha Rao Vulli. The suite studies phishing feature robustness, citation-support triage, and early astronomical transient prioritisation.

**Status:** executed public-data baselines, not completed novel research papers or production-certified systems. No UTAS affiliation or collaboration is claimed. Raw source data are downloaded separately and retain their own terms.

**Paper packages:** [readiness decisions and corrected publication shortlist](docs/paper/READINESS.md), [citation manuscript](docs/paper/MANUSCRIPT.pdf), [phishing manuscript](docs/paper/PHISHING_MANUSCRIPT.pdf), and [simulation astronomy manuscript](docs/paper/ASTRONOMY_MANUSCRIPT.pdf). All are drafts for author review, not accepted publications. The new saved-score audit identifies only one positive phishing component in each test split; see [audit evidence](results/validation/three-study-audit.json).

| Project | Working implementation | Evidence and limits |
|---|---|---|
| [Phishing robustness](docs/PHISHING.md) | Two classifiers, grouped evaluation, feature-block outage tests, batch scoring | 11,055 historical UCI records; engineered features, not screenshot/text multimodal detection |
| [Evidence checkpoints](docs/CHECKPOINTS.md) | Deterministic and learned citation-support triage; batch review flags | 2,604 ALCE human-labelled sentences from 200 questions; not a fact checker or learning-outcome trial |
| [Early transient prioritisation](docs/TRANSIENTS.md) | Early light-curve features, rare-event classifiers, ranked follow-up candidates | PLAsTiCC simulated observations; not live Rubin/GW alerts or telescope control |

## Run from this directory

Python 3.11+ is required; Python 3.12 was used for the committed results. No paid services, API keys, or GPU are needed. Downloads total approximately 28 MB. Allow several minutes for the complete CPU benchmark.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e .
python -m unittest discover -s tests -v
research-suite fetch all
research-suite run all
research-suite report
```

For Windows PowerShell, activate with `.venv\Scripts\Activate.ps1` instead. `requirements-lock.txt` records exact numerical-library versions used for the committed run; install those before `pip install -e .` when matching that environment. Timing varies by hardware.

For one project:

```bash
research-suite fetch phishing
research-suite run phishing --seeds 17 42 91
research-suite triage examples/claim.json
```

The CLI can also be run without installing the package: `PYTHONPATH=src python -m research_suite.cli ...` on Unix-like systems.

## Batch scoring

Running the experiments with seed 42 creates local artifacts in `results/models/`. They are deliberately excluded from source control. Training artifacts use joblib: load only files you created and trust.

```bash
research-suite predict --model results/models/checkpoints.joblib --input examples/claims.json --output results/my-review-queue.csv --trust-local-model
```

The phishing model accepts a CSV containing exactly the 30 UCI feature columns, no label column. Missing entries are permitted. This is **not** a URL-only detector. The astronomy model accepts observations with `object_id,mjd,passband,flux,flux_err,detected_bool`; score with `results/models/transients-3d.joblib`. Its observation units and detection conventions must match PLAsTiCC. The checkpoint model accepts a JSON list of objects with `text` and `citations`, where each citation contains `text`.

All scores are baseline model outputs, not verified probabilities of harm or discovery. In particular, class-balanced models can be poorly calibrated. The astronomy `flag_at_training_threshold` field uses 0.5; the benchmark's operational policy is instead top 5% of a candidate batch.

## Inspect the evidence

- [Measured results and interpretation](results/SUMMARY.md)
- `results/*.json`: split sizes, policies, input hashes, environment, and per-run metrics
- `results/*.csv`: analysis-friendly metrics and held-out astronomy rankings
- [Four-perspective review](docs/REVIEW.md)
- [Sources, attribution, and originality](docs/PROVENANCE.md)
- [Research and publication roadmap](docs/RESEARCH_PLAN.md)

The three seed repetitions reuse the same datasets and overlapping objects. Their spread measures split sensitivity, **not** independent replication or a statistical confidence interval. Parameters and policies are fixed rather than selected using the test results. Test results are now exposed; future research changes require a new held-out evaluation to avoid adapting to these tests.

## Follow-up validation

The [fixed follow-up protocols](docs/followup/PROTOCOL.md) add raw-URL representation tests on PhiUSIIL, ALCE corpus transfer with question-cluster intervals, and frozen-model testing on independent simulated objects. The initial astronomy sample had no target events and is retained as a feasibility failure; a separately documented adaptive second stage evaluates the untouched remainder. See [the measured technical report](results/followup/REPORT.md) and [related-work matrix](docs/followup/RELATED_WORK.md). These do not establish a novel method, publication acceptance, or real-world validation.

Additional data are fetched explicitly with `research-suite fetch followup` (approximately 321 MB). The ordinary `fetch all` command retains the smaller original baseline bundle. Follow-up command examples are in the report.


## Open-model comparison and independent feed probe

The [frozen NLI protocol](docs/followup/NLI_PROTOCOL.md) adds an established open entailment comparator to the same ALCE support task. Optional CPU dependencies and the 568 MB model are separate from the original install. From this directory:

```bash
python -m pip install -r requirements-nli.txt
PYTHONPATH=src python -m research_suite.entailment fetch
PYTHONPATH=src python -m research_suite.entailment run
```

The model revision and all downloaded artifacts are hash-checked. The bounded context can truncate evidence; this is not a reproduction of the original ALCE large-model evaluator. No model weights or cited passages are redistributed.

The [independent one-snapshot phishing protocol](docs/followup/REAL_FEED_PROTOCOL.md) permits only a conditional provider-feed agreement probe. Run `PYTHONPATH=src python -m research_suite.feed_probe` after fetching follow-up source data. The first snapshot and its provenance are cached under ignored `data/raw/`; reruns reuse them and never visit listed sites. The original snapshot cannot be downloaded again by hash from a changing feed. Raw URLs/individual predictions are not published. A new snapshot is a new experiment and needs its own provenance; do not silently replace the cache.

See [specialised astronomy and observed-data feasibility](docs/followup/ASTRONOMY_FEASIBILITY.md) for the remaining matched comparison and real-data requirements. Accessible archive data or pretrained weights alone do not establish a completed comparison.

Measured outputs for the new phase: [open comparison and independent-source probe report](results/followup/OPEN_COMPARISON_REPORT.md).


## Matched recurrent adaptation and observed-data admission

The [RAPID-inspired GRU comparison and observed-readiness report](results/followup/RECURRENT_REPORT.md) records a source-validation-selected, six-band, three-day neural adaptation versus the frozen forest. It is an adaptation, not a reproduction of RAPID's published results. Both methods missed the two independent simulated targets at the shared 5% budget. The dated observed-data sampling audit retained a zero-row result and rejected incompatible catalog photometry without inventing model scores.

Optional CPU runtime: `requirements-recurrent-runtime-lock.txt`. After recreating the original trusted forest artifact, run `PYTHONPATH=src python -m research_suite.recurrent --trust-local-model`. New protocols and complete commands, hashes, recovery history, uncertainty and limitations are in the report. Observed readiness: `PYTHONPATH=src python -m research_suite.observed_readiness`; this performs no classifier scoring.


## Independent research and manuscript

Read the [900-answer and paired visual validation report](results/validation/REPORT.md), [manuscript draft](docs/paper/MANUSCRIPT.md), [PDF](docs/paper/MANUSCRIPT.pdf), [source attribution](docs/validation/DATA_ATTRIBUTION.md) and [free dissemination guidance](docs/paper/FREE_DISSEMINATION.md). The independent [research programme](docs/validation/INDEPENDENT_RESEARCH_PROGRAMME.md) and [26-fit data-selection pilot](docs/validation/DATA_SELECTION_REPORT.md) preserve exploratory status, exposed targets and negative findings. These are not university-affiliated projects or accepted publications. Observed astronomy validation remains incomplete. Current work: [checkpoint](docs/validation/PAPER_CHECKPOINT.md).
