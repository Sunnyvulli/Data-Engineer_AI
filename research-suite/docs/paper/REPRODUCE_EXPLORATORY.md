# Reproduce the exposed-target extension

Install `requirements-exploratory.txt` in an isolated Python 3.12 environment. The manuscript builder additionally needs ReportLab and the documented DejaVu fonts. Run from `research-suite`:

```bash
python docs/paper/exploratory_analysis.py
python docs/paper/token_rate_analysis.py --responses /path/to/dataset_response.jsonl --tokenizer /path/to/pinned/tokenizer.json
python docs/paper/audit_exploratory.py
python docs/paper/render_exploratory_results.py
python docs/paper/build_manuscript.py
```

Use the original pinned RAGTruth file and coverage tokenizer; their hashes are required by the scripts. Obtain restricted source materials only under their upstream terms, keep them local, and do not add them to Git. The base paired analysis needs only the committed permitted scores/audit caches. No model inference, new labels, alternative fold/seed, network call or paid service is required for that analysis. The token extension needs the existing pinned tokenizer and annotations, not a new detector. Limit numerical-library threads to one for predictable CPU use.

The scripts preserve the original 300-draw result files. New primary output includes every planned contrast, all bootstrap draw indices and both populations' grouped folds/out-of-fold predictions. Run metadata includes the active code commit, script hashes, plan hash and package versions; a later reproduction therefore legitimately records a different active commit. Compare substantive values and script hashes rather than demanding identical provenance metadata. Invalid primary draws are JSON null, never silently replaced. Token output retains derived counts and model summaries; source answers and character spans are excluded.

The post-run `EXPLORATORY_EXECUTION_NOTES_20261025.md` records the boundary identification limitation and four numerical warnings. Reproducing a converged fit does not resolve this limitation. Do not retroactively change the original plan or remove boundary fits after examining results. A future changed analysis requires a separate dated protocol/amendment and explicit distinction from this run.
