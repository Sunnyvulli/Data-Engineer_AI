# Frozen paired screenshot/URL baseline protocol

Prepared 2026-10-19 before any model fitting or performance calculation. Structural inspection only has occurred.

## Source and scope

Zenodo record https://zenodo.org/records/21379702, DOI 10.5281/zenodo.21379702, publication 2026-07-15; metadata declares CC BY 4.0. Attribute the six creators listed in the record. Downloaded archive 1775761857 bytes, verified MD5 85937228498c1efffb2ee497389482a2. Contrary to descriptive screenshot counts, this archive contains 7062 PNG screenshots: legitimate 5285, phishing 1777. The URL table has 60000 rows. Do not present all URL rows as paired visual examples or use separately described PhishIris images. No live website visits or scripts are executed.

Mapping rule fixed after inspecting names/schema: strip http/https prefix from URL and replace Windows-forbidden filename characters / : ? * quotation-mark < > vertical-bar backslash with underscore. Strip the leading numeric index and underscore from screenshot basename. Retain an image only if this exact normalized tail maps to one URL-table row and its class agrees with the screenshot directory. Structural audit: 7050 unique agreeing matches; 8 ambiguous and 4 unmatched excluded with counts, never guessed. Raw dangerous URLs and screenshots remain local; publish hash identifiers and derived scores/features only.

This is provider-labelled research data, not independent human adjudication. Collection dates and source-list construction can create shortcuts. No claim of contemporary deployment or security assurance.

## Leakage control and fixed models

Use all uniquely paired records. Decode with Pillow only, reject corrupt images with explicit counts. Derive exact decoded RGB pixel hash (includes dimensions) and 64-bit difference hash on 9x8 grayscale pixels. Merge connected components for (a) identical lowercase exact hostname, (b) identical decoded RGB pixels, or (c) Hamming distance <=2 between difference hashes. Transitive closure applies across all records and labels. Group construction sees inputs only, never model outcomes. It controls these duplicates but cannot certify semantic/domain-family/campaign independence. Report component count, largest component, conflicts and source split overlap. Ignore provider train/val/test membership for new models, and audit its cross-split duplicates.

Split connected components with the existing stratified group 60/20/20 split, seeds 17,42,91. Fail explicitly if both classes cannot be represented; do not substitute a favorable seed. Fit train only; validation selects lowest threshold meeting empirical <=1% false-positive rate. No test tuning.

URL baseline: lowercase character TF-IDF 3-5 grams, max_features=30000, sublinear_tf=True, logistic regression C=1 balanced liblinear max_iter=2000 random_state=seed. Screenshot baseline: 48 RGB hist bins (16 per channel normalized), grayscale 8x8 spatial means plus standard deviations (128), image log1p width/height and aspect ratio (3). Total 179 features; StandardScaler plus balanced logistic regression C=1 liblinear max_iter=2000. Original compact descriptors, not a novel visual model or OCR. Fusion: equal mean of the two frozen model probabilities, independently validation-thresholded; no learned or selected fusion weight. Evaluate URL, image and fusion on identical held-out rows. No filenames, directories, numeric index, labels, provider splits or handcrafted source DNS fields enter predictors.

Report AP, ROC AUC, recall, precision, FPR, confusion counts and validation thresholds for all seeds. Seed42 only: 300 component-cluster bootstrap resamples, seed20261019, AP/recall/FPR and paired AP improvement over URL. Intervals conditional on fitted policies, not annotation/collection-bias uncertainty. Preserve all failures and source artifacts; do not choose a winner by favorable metric. Record exact provenance, runtimes and software versions. No outcome-driven protocol changes; corrections must be documented before rerunning.
