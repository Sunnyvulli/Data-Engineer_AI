"""Single-snapshot, provider-labelled phishing probe; no target-page visits.

OpenPhish data are not redistributed. See docs/followup/REAL_FEED_PROTOCOL.md.
"""

from __future__ import annotations
import argparse
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit
import urllib.request
import numpy as np
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from .common import sha256, split_groups, threshold_at_fpr, write_json, environment
from .followup import raw_url_data, host

FEED = (
    "https://raw.githubusercontent.com/openphish/public_feed/refs/heads/main/feed.txt"
)


def select_urls(lines, source_hosts):
    """Outcome-independent unique URL selection; exact-host overlap exclusion."""
    unique = list(dict.fromkeys(s.strip() for s in lines if s.strip()))
    selected = []
    invalid = overlap = 0
    for url in unique:
        try:
            if urlsplit(url).scheme not in ("http", "https"):
                raise ValueError("Expected explicit web scheme")
            hostname = host(url)
        except ValueError:
            invalid += 1
            continue
        if hostname in source_hosts:
            overlap += 1
        else:
            selected.append((url, hostname))
    return selected, {
        "nonempty_lines": sum(bool(s.strip()) for s in lines),
        "unique_urls": len(unique),
        "invalid_excluded": invalid,
        "source_host_overlap_excluded": overlap,
        "retained": len(selected),
    }


def agreement_interval(flagged, hosts, repetitions=300):
    """Whole-host percentile interval; not population sensitivity uncertainty."""
    flagged, hosts = np.asarray(flagged, dtype=float), np.asarray(hosts)
    unique = np.unique(hosts)
    if not len(unique):
        return None
    members = [np.flatnonzero(hosts == h) for h in unique]
    rng = np.random.default_rng(20261019)
    values = [
        float(
            flagged[
                np.concatenate(
                    [members[i] for i in rng.integers(0, len(unique), len(unique))]
                )
            ].mean()
        )
        for _ in range(repetitions)
    ]
    return {
        "resampling_unit": "exact normalized hostname",
        "clusters": len(unique),
        "resamples": repetitions,
        "percentile_95": np.quantile(values, [0.025, 0.975]).tolist(),
        "limitation": "conditional snapshot agreement; not adjudicated recall or deployment uncertainty",
    }


def run(data, output):
    data, output = Path(data), Path(output)
    frame, _ = raw_url_data(data / "phiusiil.zip")
    y = frame.positive.to_numpy()
    train, validation, test = split_groups(y, frame.hostname.to_numpy(), 42)
    model = make_pipeline(
        TfidfVectorizer(
            analyzer="char", ngram_range=(3, 5), max_features=30000, min_df=2
        ),
        LogisticRegression(
            solver="liblinear", max_iter=2000, class_weight="balanced", random_state=42
        ),
    )
    model.fit(frame.URL.iloc[train], y[train])
    v = model.predict_proba(frame.URL.iloc[validation])[:, 1]
    threshold = threshold_at_fpr(y[validation], v)
    artifact = output.parent / "models" / "phiusiil-raw-url.joblib"
    artifact.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(
        {
            "model": model,
            "threshold": threshold,
            "source_sha256": sha256(data / "phiusiil.zip"),
        },
        artifact,
    )
    snapshot = data / "openphish-community.txt"
    metadata = data / "openphish-community-provenance.json"
    if snapshot.exists() != metadata.exists():
        raise ValueError("Snapshot and provenance must both exist or both be absent")
    if not snapshot.exists():
        with urllib.request.urlopen(FEED, timeout=60) as response:
            content = response.read()
            provenance = {
                "source": FEED,
                "fetched_utc": datetime.now(timezone.utc).isoformat(),
                "last_modified": response.headers.get("Last-Modified"),
                "bytes": len(content),
            }
        snapshot.write_bytes(content)
        provenance["sha256"] = sha256(snapshot)
        write_json(metadata, provenance)
    provenance = __import__("json").loads(metadata.read_text())
    if sha256(snapshot) != provenance["sha256"]:
        raise ValueError("Cached snapshot hash mismatch")
    urls, audit = select_urls(snapshot.read_text().splitlines(), set(frame.hostname))
    if not urls:
        raise ValueError("No independent valid URLs remain; no rate can be estimated")
    p = model.predict_proba([u for u, _ in urls])[:, 1]
    flagged = p >= threshold
    result = {
        "status": "completed one-snapshot provider-labelled external probe; no balanced deployment validation",
        "source_model": "PhiUSIIL full-URL seed42 frozen reconstruction",
        "source_sha256": sha256(data / "phiusiil.zip"),
        "local_artifact_sha256": sha256(artifact),
        "environment": environment(),
        "provenance": provenance,
        "permission_sources": [
            "https://openphish.com/terms.html",
            "https://openphish.com/phishing_feeds.html",
        ],
        "terms_scope": "personal independent noncommercial research; no feed/URL/individual score redistribution",
        "selection": audit,
        "threshold": threshold,
        "source_validation_fpr": float(np.mean(v[y[validation] == 0] >= threshold)),
        "provider_reported_phishing_flagged": int(flagged.sum()),
        "provider_feed_agreement": float(flagged.mean()),
        "uncertainty": agreement_interval(flagged, [h for _, h in urls]),
        "not_estimable": [
            "independently adjudicated phishing recall",
            "false-positive rate",
            "precision",
            "AP",
            "ROC AUC",
        ],
        "limits": [
            "one limited feed snapshot; provider labels not independently adjudicated",
            "no benign controls; no deployment prevalence or representative sampling frame",
            "exact-host exclusion does not exclude related registered domains or campaigns",
            "PhiUSIIL collection shortcuts remain; no screenshot/HTML capability",
        ],
    }
    write_json(output / "real-feed-probe.json", result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", default="data/raw")
    parser.add_argument("--output", default="results/followup")
    args = parser.parse_args()
    run(args.data, args.output)


if __name__ == "__main__":
    main()
