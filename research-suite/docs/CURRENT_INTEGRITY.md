# Current snapshot integrity, 2026-10-19

Reviewed source snapshot: `3f3797b64176e24a15e9b2b813cce87768917ef1` (the deliberate history reset is preserved).

Executed locally from `research-suite`:

```sh
PYTHONPATH=src python -m unittest discover -s tests -v
python docs/paper/audit_outputs.py
python docs/paper/audit_three_studies.py
```

All 58 integrity tests pass; the output audit reports 19 checks passed and the multi-study saved-score audit reports passed. The latter retains the negative result that all phishing test positives belong to one component per seed, so conditional bootstrap intervals do not establish independent-component generalization. No new model training, dataset download, raw-data reproduction, external validation, publication acceptance or peer review occurred in this check.

The workflow now runs on every push and PR, including root-only documentation changes, and retains saved-output audit artifacts. A separate default-rule Gitleaks job scans all reachable history with redacted output. Scanner success is not proof against unknown formats or unreachable objects, and does not rewrite prior history. Branch and main CI results determine current verification status.
