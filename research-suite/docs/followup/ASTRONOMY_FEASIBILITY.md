# Specialised transient baseline and real-data feasibility

Inspected October 19, 2026 UTC. This assessment contains no new classifier score. The existing independent PLAsTiCC result (two targets, both missed within the budget) remains unchanged.

## RAPID source and released weights

Primary repository: https://github.com/daniel-muthukrishna/astrorapid at commit `7f28499ff71f8520ed6fcf530929587336a0c5de`. The repository's MIT license credits Daniel Muthukrishna (2019). File hashes and weight inventory are recorded in `results/followup/astrorapid-source-audit.json`. Source files were inspected locally; they are not republished as original work.

`astrorapid/classify.py` provides two ZTF models (known/unknown redshift, g/r) and two released Pan-STARRS known-redshift models (g/r/i/z). The ZTF models include a Kilonova class. Their HDF5 files are about 1.5–1.8 MB and are listed in the repository tree; missing weights or licensing are therefore **not** established blockers. Runtime dependencies include TensorFlow/Keras, astropy and extinction; compatibility with this Python 3.12 environment has not yet been tested.

The existing benchmark instead uses simulated LSST six-band photometry, no redshift/extinction predictor, first `detected_bool` alert, no pre-alert observations, inclusive three-day cutoff and a 5% ranking budget. Directly renaming LSST g/r as ZTF g/r would introduce a response/photometric-domain shift. The released preprocessing also expects a 6144 first-detection flag and exposes redshift/extinction processing and a regular time grid. Neither future observations nor interpolation informed by future points may enter the early comparator.

Primary custom-training documentation: https://astrorapid.readthedocs.io/en/latest/usage.html. It supports a custom data reader and passbands. A matched six-band retraining study is therefore a feasible research direction, **not completed here and not proven impossible**. Before running, freeze a new protocol defining identical allowed observations and object splits, causal prefix preprocessing, absent-band handling, training/validation-only model selection, fixed compute budget, seeds, and the shared ranking budget. A locally reimplemented recurrent model must be called an adaptation and credited, not a reproduction of released-weight results. Do not select an architecture using the exposed two-event independent test.

## Permissioned observed data

IRSA's public-data terms state that most public data have no usage restrictions: https://irsa.ipac.caltech.edu/data_use_terms.html (policy last updated February 8, 2023; inspected October 19, 2026). Public ZTF releases are identified at https://irsa.ipac.caltech.edu/data/ZTF/docs/releases/; DR24 is present in the listing. Proprietary data require separate rights; no login or proprietary collection is used. IRSA and mission acknowledgments/citations are required in any resulting research: https://irsa.ipac.caltech.edu/ack.html.

API documentation: https://irsa.ipac.caltech.edu/docs/program_interface/ztf_lightcurve_api.html. A request to the documented example object ID is retained as an **access-only smoke test**, with URL, UTC timestamp, hash, response status and schema in `results/followup/irsa-access-smoke.json`. It is not a scientific sample, labelled transient, kilonova detection or performance measurement. Catalog photometry is not automatically interchangeable with difference-flux alerts and non-detection history.

A defensible future observed negative-control frame is the spectroscopically classified ZTF Bright Transient Survey sample: https://sites.astro.caltech.edu/ztf/bts/bts.php. Its brightness, visibility and classification-selection cuts exclude much of the alert population. Freeze a dated catalog, deterministic object selection, time interval, sky-coordinate matching radius, treatment of multiple light curves, quality flags, photometric conversion and early alert convention before scores. Do not label unclassified objects as negatives or choose objects by model success. An SN-heavy negative set cannot estimate kilonova sensitivity or deployment precision.

AT2017gfo photometry releases from the original observers are another possible single-event diagnostic: https://www.engrave-eso.org/AT2017gfo-Data-Release/ and https://www.pessto.org/index.py?pageId=60. No data-use license for an assembled multi-source table was verified in this assessment; source-level attribution/terms and photometric-system mapping must be checked before redistribution/use. A famous single event cannot supply a representative independent positive population.

## Four-perspective self-review

- Researcher: preserve the sparse-target failure and separate simulated validation, archive access and real-event inference.
- Supervisor: require a matched protocol and causal preprocessing tests before training; exposed test labels cannot guide tuning.
- Industry user: public download access does not establish alert availability, reliable latency, telescope scheduling or deployment validity.
- Critical reviewer: accessible specialised weights are not missing; the remaining work is scientific harmonisation and implementation, not an invented access excuse. No broad non-transient blocker has been established.

These perspectives are an structured self-review, not independent expert endorsements.


## Subsequent executed bounded study

The [recurrent adaptation report](../../results/followup/RECURRENT_REPORT.md) now records completed TensorFlow CPU execution of a credited RAPID-inspired two-GRU adaptation under matched allowed observations/object split/budget. It does not run the current package's TCN or released survey-specific weights. The observed-data readiness study uses a frozen BTS negative-control sample; its first preselected public cone returned zero rows and direct admission to LSST-simulation models was rejected. The compatibility and real-event validation gaps above are retained, not declared solved by this adaptation.
