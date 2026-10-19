# When Compact Screenshot Fusion Hurts: A Component-Aware Phishing Baseline Audit

Hanumantha Rao Vulli

Research draft for author review. 19 October 2026. Not submitted, peer reviewed or accepted. No institutional affiliation asserted.

## Abstract

Adding a second input modality does not by itself establish better phishing detection. We evaluate URL character features, compact screenshot descriptors and equal-score fusion on 7,050 uniquely paired provider-labelled records. An input-only connected-component rule links exact hostnames, identical decoded images and perceptual near duplicates before splitting. Across three fixed seeds, URL average precision (AP) is 0.896-0.950, compared with 0.750-0.848 for fusion. Some thresholds calibrated to at most 1% empirical validation false-positive rate exceed that rate on held-out records. A subsequent saved-score audit identifies a decisive sampling limitation: every held-out phishing example belongs to one connected component in every seed. These results document a negative baseline outcome on this corpus; they do not establish a general ranking of modalities or campaign-level generalization. We release evaluation code, protocols and derived predictions without redistributing dangerous URLs or screenshots.

## 1. Question and contribution

This study asks whether a deliberately inexpensive screenshot representation improves a fixed URL baseline on identical held-out records. It also audits whether a validation false-positive-rate (FPR) budget transfers to those records. The contribution is a transparent benchmark and sampling diagnosis, not a new visual architecture. Existing visual phishing systems such as PhishIntention and PhishLLM investigate richer representations and mechanisms; they were not run here, so these experiments cannot rank against them or refute their findings [2,3].

The protocol was committed before model fitting at 09e17273d6ca68557f20e6017d7855dba2cb3bd4. The positive-component diagnosis in Section 4 was performed later on saved outputs, without fitting or changing the split. It is explicitly a post-outcome diagnostic.

## 2. Source, mapping and grouping

We use the Phishing and Legitimate Websites Dataset [1], Zenodo DOI 10.5281/zenodo.21379702. Its metadata declares CC BY 4.0. The pinned archive is 1,775,761,857 bytes with MD5 85937228498c1efffb2ee497389482a2. Although its URL workbook contains 60,000 rows, the actual archive contains 7,062 PNG files. We retain only exact unique URL-to-filename matches whose workbook class agrees with the image directory, yielding 7,050 pairs: 1,765 phishing and 5,285 legitimate. Eight ambiguous mappings and four unmatched images are excluded. These counts describe available paired records, not all workbook rows.

Mapping strips an HTTP/HTTPS prefix, normalizes Windows-forbidden filename characters to underscores and removes the screenshot's leading numeric index. No ambiguous match is guessed. This uses provider labels, not new independent human adjudication. No website is visited and no page script is executed.

Before splitting, transitive connected components merge records sharing an exact lowercase hostname, an exact decoded RGB pixel hash including dimensions, or a 64-bit difference hash within Hamming distance two. Group construction uses inputs, not outcomes. It produces 4,598 components, including a largest component of 2,035 rows and ten mixed-label components. A total of 102 components cross the provider's original partitions; those partitions are not reused. These links address specified duplicates but cannot certify campaign independence. A visually simple page can also bridge otherwise unrelated sites through transitive perceptual matches.

The fixed stratified group procedure uses seeds 17, 42 and 91 with nominal 60/20/20 allocation. Large indivisible groups distort the achieved row allocation: each seed has 3,325 training, 1,109 validation and 2,616 test records. Each test set has 1,559 positives, a prevalence of 59.6%, compared with 25.0% in the paired corpus. These are benchmark sampling properties, not estimates of deployment prevalence.

## 3. Predictors and evaluation

The URL model fits character TF-IDF 3-5 grams with at most 30,000 features and sublinear term frequency, followed by balanced logistic regression with C=1, liblinear and a maximum of 2,000 iterations. The image model standardizes 179 compact features: 48 normalized RGB histogram bins, 64 grayscale spatial means, 64 spatial standard deviations, and three image-size/aspect features. It uses the same logistic regression settings. Predictors receive neither directory labels, filenames, provider partitions nor numeric screenshot indices.

Equal fusion averages the URL and image phishing scores without selecting a fusion weight. All three policies use the same held-out rows. Training uses training records only; validation selects the lowest score threshold satisfying empirical FPR at most 1%. Test outcomes never select thresholds. Balanced-training scores are not established calibrated probabilities, and averaging them need not improve ranking.

We report scikit-learn AP, recall and FPR for every seed, retaining full ROC AUC and confusion counts in the result JSON. AP depends on class prevalence. The fixed seed-42 uncertainty procedure resamples complete components 300 times and skips resamples lacking both classes. Such conditional intervals do not include training uncertainty or collection bias. Their severe positive-component support limitation is reported below.

## 4. Results and component support

| Seed | Policy | AP | Recall | FPR |
| --- | --- | --- | --- | --- |
| 17 | URL | 0.903515 | 0.504169 | 0.006623 |
| 17 | Image | 0.762105 | 0.000000 | 0.007569 |
| 17 | Equal fusion | 0.847556 | 0.245029 | 0.017029 |
| 42 | URL | 0.896308 | 0.539448 | 0.008515 |
| 42 | Image | 0.595499 | 0.003849 | 0.022706 |
| 42 | Equal fusion | 0.750440 | 0.199487 | 0.035951 |
| 91 | URL | 0.950117 | 0.746632 | 0.013245 |
| 91 | Image | 0.622949 | 0.000000 | 0.015137 |
| 91 | Equal fusion | 0.825653 | 0.407312 | 0.055818 |

Fusion has lower AP and lower recall than URL in every recorded seed. Image-only recall is zero in two seeds and approximately 0.4% in the third. Test FPR exceeds 1% for every fusion policy and for the seed-91 URL policy. A validation constraint therefore supplies no observed test-set guarantee.

The saved-score audit finds 582 held-out components per seed, but only one contains phishing positives. That component has 2,035 rows, including all 1,559 test positives. Thus the three seeds do not constitute independent replication over positive components. Source collection effects, component identity and label can be entangled. Removing that component would leave no positive test examples and make two-class AP/recall evaluation inappropriate; we do not remove it after inspecting outcomes or weaken grouping to obtain a favorable test.

Only 179 of the 300 seed-42 bootstrap resamples retain both classes. Repeated inclusion of the same single positive component can produce an apparently fixed recall interval. That interval cannot estimate recall variation across unseen positive components. We retain the original conditional intervals in machine-readable results for transparency but do not use them as evidence of reliable phishing sensitivity. The original uncertainty unit label was copied from a citation helper; this release corrects it to the actual screenshot/hostname component without changing scores or numerical intervals.

## 5. Interpretation and limits

The supported conclusion is narrow: these particular compact descriptors and equal fusion do not improve the recorded URL baseline under this protocol. Possible explanations include insufficient visual semantics, incomparable score scales, collection shortcuts, and the large-component distribution shift. The experiment does not isolate these causes. It cannot support the broader claim that screenshots are unhelpful or that visual phishing systems generally fail.

A stronger follow-on study needs independently collected, permissioned and time-separated paired data with multiple positive components, provenance sufficient to examine collection artifacts, and a prespecified campaign/brand grouping design. Richer visual methods require a matched allowed-input and resource comparison. Any revised model selected after these results requires fresh confirmation; this test set is now exposed. No additional confirmation results are invented here.

## 6. Reproducibility, ethics and authorship

The canonical repository is Sunnyvulli/Data-Engineer_AI, directory research-suite. The protocol is docs/validation/VISUAL_PHISHING_PROTOCOL.md; implementation is src/research_suite/visual_phishing.py. Results are results/validation/visual-phishing.json and compressed derived risks visual-phishing-scores.json.gz. Run python docs/paper/audit_outputs.py and python docs/paper/audit_three_studies.py to reconcile recorded metrics and examine positive-component support without downloading raw inputs. Full fitting requires the checksum-verified original archive and the documented dependency lock.

The recorded decode/group/train runtime is 676.54 seconds; it excludes archive download. Raw URLs, screenshots and workbooks are not redistributed. Source licensing does not establish correct ground truth or operational safety. This work contains no live attack, prospective security trial or deployment claim.

The human author must verify the artifacts, revise and approve the final text, and satisfy venue authorship rules. No independent expert review, funding or affiliation is asserted.

## References

[1] Yadav, D. K.; Tejash, M.; Panda, S.; Mishra, P.; Nayak, S.; Sekh, A. A. (2026). Phishing and Legitimate Websites Dataset. Zenodo. https://doi.org/10.5281/zenodo.21379702 . Metadata license CC BY 4.0; pinned checksum above.

[2] PhishIntention research project. Official source and associated paper pointers. https://github.com/lindsey98/PhishIntention . Related work only; not an executed comparator.

[3] PhishLLM research project. Official source and associated paper pointers. https://github.com/imethanlee/PhishLLM . Related work only; not an executed comparator.
