# Frozen one-snapshot independent phishing-feed probe

October 19, 2026 UTC. Fixed before fetching/scoring the feed. This is a one-class external-source probe of a URL model, not a balanced deployment test or a multimodal experiment.

## Permission and provenance

OpenPhish's official Community Feed page links to `https://raw.githubusercontent.com/openphish/public_feed/refs/heads/main/feed.txt`. Its current Terms of Use permit academic, independent and personal research outside organizational business operations, and restrict redistribution. Sources inspected: https://openphish.com/phishing_feeds.html and https://openphish.com/terms.html. Use only for this personal research; do not redistribute the feed, URLs, individual risk scores or pages. Report aggregate counts/metrics and provenance (fetch UTC, source URL, full-file SHA-256). No visits to listed sites, no screenshots, no purchases, no application to its academic programme.

## Fixed source model and selection

Reconstruct the existing PhiUSIIL full-URL character TF-IDF/logistic model exactly: 30,000 smallest SHA-256 unique trimmed URLs, conflicting URLs excluded; exact normalized hostname group split seed42; char3..5, max_features30,000, min_df2; class-balanced liblinear logistic max_iter2,000 seed42. Fit source training only and choose threshold using source validation <=1% FPR. Refit is required because the earlier benchmark did not persist this raw-URL artifact; it is not new model selection. Preserve fitted model/threshold locally and publish their artifact hash, not an untrusted binary.

Fetch one feed snapshot once. Whitespace-trim, deduplicate exact URLs, require explicit HTTP/HTTPS and a parseable hostname. Score all valid unique URLs after excluding exact hostnames present anywhere in the selected 30,000-row source corpus. Do not choose by predicted outcome. Retain overlap/exclusion counts. No registered-domain, campaign or time separation is established.

## Reporting

All feed entries have a provider-reported phishing label, not independent manual adjudication. Report the fraction flagged at the frozen threshold, its complete-host bootstrap percentile interval (300 resamples, seed20261019), source validation FPR, total and retained entries, threshold and corpus/model hashes. Do not compute AP, ROC AUC, precision or real-world false-positive rate from this one-class sample. This is conditional provider-feed agreement, not verified sensitivity to all phishing. A single limited snapshot has selection bias, no population sampling frame and no campaign weighting. No benign control set means operational performance remains unknown. No hyperparameter or threshold change after outcomes.
