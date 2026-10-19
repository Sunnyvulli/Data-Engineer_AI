# Early kilonova candidate prioritisation

## Question and implementation

Can low-cost light-curve features prioritise simulated kilonovae within a limited follow-up budget? `src/research_suite/transients.py` targets PLAsTiCC class 64 (kilonova) against all other labelled training classes.

Data come directly from the unblinded PLAsTiCC release on Zenodo. These are simulations, not observed Rubin alerts. The supplied training metadata contain simulation-truth fields; **none** is used as a predictor. Only `object_id` for alignment and `target` for the label are read from metadata. Photometric redshift, true peak time, true flux, class, sky position, and simulation parameters are not input features.

First alert is the first row with `detected_bool=1`. Objects without such a row are excluded, not assigned an artificial alert time. For each horizon (1, 3, or 7 days), observations are restricted to [first detection, first detection+horizon] **before aggregation**. Prior nondetections are deliberately omitted. Horizon does not imply that a source is still visible or observable at that time.

Features include counts, elapsed time, observed bands, and per-band flux moments, max signal-to-noise, and endpoint slopes. No future-data normalisation or whole-light-curve feature extraction occurs. Missing bands are imputed using training data only. The held-out objects are consistent across horizons because eligible IDs and labels are unchanged; tests protect the cutoff against future-observation changes.

## Evaluation

Logistic regression and random forests are evaluated across three fixed group splits. Validation is reserved without tuning. Models rank held-out candidates and the top ceil(5% of candidates) are selected. Reported metrics include average precision, precision/recall at budget, confusion counts at the illustrative 0.5 threshold, and Brier score. The random baseline is its theoretical expectation using held-out prevalence, not a selected lucky random draw.

Ranking CSVs are exported for seed 42; `heldout_label` is for retrospective evaluation and must not be supplied as a production input. The 5% rule is a count budget, not an observing-time or slew-cost scheduler. The small positive sample makes performance sensitive to split choice.

## Next research gate

Benchmark against specialised time-domain models, include independent observing cadences, quantify class-prior shift and calibration, model exposure/slew/weather constraints, and test on real survey data. No GW, neutrino, or high-energy stream is ingested. There is no telescope integration. Completing those parts of the UTAS programme would require substantially more work and likely collaboration.
