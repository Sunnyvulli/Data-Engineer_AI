# Frozen RAPID-inspired recurrent comparison

October 19, 2026 UTC, before new training or scores. Existing forest benchmark and two-event independent-shard outcomes are already exposed; this is a bounded reused-benchmark comparison, not blind confirmation.

## Attribution and scope

Muthukrishna et al. (2019), RAPID, PASP 131 118002, DOI 10.1088/1538-3873/ab1609, https://arxiv.org/html/1904.00014v2, describes two unidirectional 100-unit GRUs with batch normalization/dropout. The inspected current astrorapid repository instead trains a TCN; neither released ZTF weights nor its filter assumptions will be silently applied to LSST. This independently implemented **RAPID-inspired GRU adaptation** uses public TensorFlow/Keras APIs. It changes the photometric representation, time grid, target and training schedule; it is not an exact paper/package reproduction or a new architecture. All new code is original, with conceptual credit retained.

TensorFlow CPU 2.21.0 installed in an isolated directory, and a synthetic forward pass succeeded. No paid service or GPU is required. Preserve exact package versions, source/input/model hashes, wall time, RSS, validation history, failures and scores. No raw light curves or third-party weights are republished.

## Matched allowed information and deterministic representation

Use the original PLAsTiCC training metadata/light curves and seed42 object-disjoint split (same sorted eligible object IDs as the forest). Positive target is metadata class64. No metadata predictors, redshift, extinction, peak time, pre-alert data or post-cutoff measurements are allowed. Alert = first detected_bool=1 in any of six bands. Include all observations from that alert through alert+3 days inclusive. Both methods receive the same allowed observations and share the 5% ranking budget; their input representations and training resources differ.

GRU representation: 13 grid times 0,0.25,...,3 days, six bands, three channels per band: latest available flux, its uncertainty and observed-band indicator. At each grid time take only the most recent observation time at or before that grid. Same-time/same-band measurements combine by inverse-variance mean/error. Before the first available band measurement, all three channels are zero. No interpolation from a later grid or observation. This compression can discard within-bin history that forest statistics retain; report it as a representation limitation.

For each band, scale = max(median absolute flux among that band's allowed **source-training observations**,1). Transform observed flux by asinh(flux/scale), uncertainty by log1p(error/scale); mask remains 0/1. Scales never use validation/test/independent data. Preprocessing must pass post-cutoff, pre-alert, causal-grid, absent-band and train-only-scaling integrity tests before training.

## Fixed model/training budget and evaluation

Input 13x18 → unidirectional GRU100(return_sequences=True) → BatchNormalization → Dropout0.2 → GRU100(last state) → BatchNormalization → Dropout0.2 → Dense2 softmax. These endpoint-only binary outputs differ from RAPID's multiclass sequence outputs. Adam learning_rate0.001, sparse categorical cross entropy, inverse-frequency class weights n_train/(2*n_class), batch64, exactly25 epochs, one seed42, four CPU intra-op threads and one inter-op thread. Enable TensorFlow deterministic ops; record any unsupported-op error. Shuffle source-training rows with seeded NumPy permutations. Use explicit train_on_batch loops to avoid background dataset thread-pool constraints.

After each epoch score source validation only; retain the first epoch achieving the best validation AP. No early stopping, architecture search, external-score feedback or target-selected threshold. Source validation is used for this neural checkpoint selection; the original forest did not use it for model search, so report this asymmetry. Default0.5 probabilities are a diagnostic, not a calibrated operational policy. Rank by positive score with stable ties in sorted object-ID order; select ceil(0.05*n).

Only after weights are selected: evaluate original held-out seed42 source objects and the already exposed independent shard01 remainder IDs >53125, excluding the last potentially incomplete ID342868 as before. Do not tune on either. Compare against the trusted, locally trained original three-day forest artifact, whose hash is retained; verify its original held-out metrics match the committed release. No repeated forest training is required. Retain missing-object/ID mismatches as errors, not silent sample changes.

Report AP, ROC AUC, default-threshold diagnostics, budget precision/recall and complete-object bootstrap intervals (300 resamples), with paired GRU-minus-forest AP intervals. For the independent sample's two positives, retain exact-binomial recall diagnostic and warn that a degenerate bootstrap is not certainty. Save both methods' aligned scores/IDs/labels, training history, scale values and local artifact hashes without publishing executable model binaries. One seed and reused simulations cannot establish superiority across architectures, real-event performance, discovery, novelty or publication readiness.

## Four-perspective acceptance rules

Researcher: report worse/unstable results as measured. Supervisor: protocol and integrity controls precede model outcomes. Industry user: preserve follow-up cost and sparse-event uncertainty. Critical reviewer: distinguish an adapted architecture from a reproduction, matched allowed observations from identical representations/resources, and simulations from observed events. These are self-review perspectives, not independent endorsements.
