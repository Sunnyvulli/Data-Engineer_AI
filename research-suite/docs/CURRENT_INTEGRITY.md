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

## Reviewed scanner findings
The first full-history scan reported six generic-api-key matches: three public tokenizer artifact SHA-256 checksums in `src/research_suite/entailment.py` and the same three checksums in `results/followup/nli-comparison.json`, all in snapshot 3f3797b. Each matched line has a tokenizer filename and a 64-character hexadecimal SHA-256 used for model-file integrity, not authentication. `.gitleaksignore` records only these six exact commit/path/rule/line fingerprints. No rule, directory, file or future commit is broadly excluded. A separate temporary synthetic-key probe confirms default detection remains active; that probe is not committed or a real credential.

## 20 October citation-review follow-up

See [review response](paper/REVIEW_RESPONSE.md) and [diagnostic protocol](paper/REVIEW_RESPONSE_PROTOCOL.md). The added post-hoc length ranking has AP 0.385779, exceeding the tested detectors, and the manuscript now states that limitation. All 58 existing tests, diagnostic self-checks, 19 saved-output reconciliations and multi-study audit pass locally. New results retain hashes and all grouped fold assignments; CI requires deterministic regeneration. The original model outputs are unchanged. This is not a new independent test or peer review. Career qualification facts and publication status remain unchanged.

## Within-generator control and revised framing — 2026-10-20

The diagnostic script reports per-generator length AP/AUC and pooled average tied ranks divided by stratum n. Within-generator length ranks yield AP 0.295864 / AUC 0.632204; identically normalized coverage NLI yields AP 0.236435 / AUC 0.625422. All six strata remain visible, including GPT-4's opposite-direction length AUC 0.074 with only one positive. Checks cover ties, rank invariance to within-generator monotone scale changes, permutation alignment, invalid inputs and an independent pair-count AUC oracle. Reframing is explicitly post hoc; no causal effect, equivalence or superiority is established.


## 25 October exploratory-analysis history scan

PR #7 passed the research integrity job but its first history scan flagged two generic-api-key matches. Inspection showed both are the same public pinned tokenizer SHA-256: token_rate_analysis.py line 15 at 400f5481 and token-rate-analysis.json line 5 at c7fe2e2e. The value independently matches the existing pinned tokenizer file and the already-audited NLI provenance. Added only the exact commit/path/rule/line fingerprints to .gitleaksignore; no default rule or scan scope was disabled. Analysis code, results, plan and derived intervals remain unchanged.
