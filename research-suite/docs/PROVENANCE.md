# Provenance, originality, and attribution

The implementation and explanatory prose were written for this project. Existing repository implementations were not copied into this package. Scientific concepts, library algorithms, datasets, and evaluation practices have prior authors and are credited below. The code is an original implementation of established methods; originality of code does not establish scientific novelty. No automated plagiarism-screening certification or exhaustive similarity search is claimed.

Hanumantha Rao Vulli is the project owner. This repository does not claim that the owner performed unrecorded experiments, has a UTAS appointment, or received external peer review. Before any paper submission, the human author must verify the implementation, own the claims, follow required disclosure policies, and satisfy the venue's authorship rules.

## Primary sources

1. Mohammad, R., McCluskey, L., and Thabtah, F. **Phishing Websites**. UCI Machine Learning Repository (2015). https://archive.ics.uci.edu/dataset/327/phishing+websites . UCI advertises CC BY 4.0. Original raw data are not committed; fetch hashes are retained.
2. Gao, T., Yen, H., Yu, J., and Chen, D. **Enabling Large Language Models to Generate Text with Citations**. EMNLP (2023). https://aclanthology.org/2023.emnlp-main.398/ . Official code/data entry: https://github.com/princeton-nlp/ALCE . Used asset: human_eval/human_eval_citations_completed.json. The repository advertises MIT licensing; underlying retrieved passages can retain separate source rights. Download is pinned to commit 246c476a4edfc564266b7346b6e29ef4861ae937. Raw claims/passages are not redistributed here.
3. **Unblinded Data for PLAsTiCC Classification Challenge**. Zenodo record 2539456. https://zenodo.org/records/2539456 . Used assets: plasticc_train_metadata.csv.gz and plasticc_train_lightcurves.csv.gz. Consult record metadata and associated PLAsTiCC papers for dataset authorship, terms, and citation requirements. Raw observations are not committed.
4. The PLAsTiCC team. **The Photometric LSST Astronomical Time-series Classification Challenge (PLAsTiCC): Data set** (2018). https://arxiv.org/abs/1810.00001 . Context and dataset design.
5. **PhishIntention**, official research project: https://github.com/lindsey98/PhishIntention . Related work informing the larger multimodal direction; no implementation or pretrained weights incorporated.
6. **PhishLLM**, official research project: https://github.com/imethanlee/PhishLLM . Related work demonstrating existing vision-language phishing research; no code incorporated.

## Data and software separation

`results/data-manifest.json` records exact downloaded bytes and SHA-256 hashes. Public result tables contain measured aggregates and derived astronomy rankings, not raw copied articles or model-generated answers. Dependencies include NumPy, pandas, SciPy, scikit-learn, and joblib (installed with scikit-learn); their own licenses apply. This repository does not relicense third-party datasets, code, model weights, or excerpts. No claim of complete legal clearance for every upstream passage is made.

Git history establishes delivery history, not sole human authorship or priority of a research idea. Citations are acknowledgements, not evidence of endorsement.

## Follow-up data and prior analyses
PhiUSIIL raw URLs were separately downloaded from primary UCI dataset 967, credited to Arvind Prasad and Shalini Chandra (2024), DOI 10.1016/j.cose.2023.103545, CC BY 4.0. Only URL/label columns are used for the new predictors. Related public corpus-artifact analyses and specialised research systems are credited in `docs/followup/RELATED_WORK.md`. The follow-up does not claim those previously discussed concerns as new discoveries. Additional PLAsTiCC observations and metadata come from the same primary Zenodo record, with fixed source hashes recorded. Raw URLs are never visited or redistributed in this repository.
