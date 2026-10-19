"""Frozen paired visual/URL baseline; never executes downloaded pages."""

from __future__ import annotations
import argparse
import collections
import hashlib
import io
import json
from pathlib import Path
import re
import time
from urllib.parse import urlsplit
import zipfile
import numpy as np
from PIL import Image
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from .common import (
    binary_metrics,
    environment,
    split_groups,
    threshold_at_fpr,
    write_json,
)
from .external_support import uncertainty


def filename_key(url):
    return re.sub(r'[/\\:*?"<>|]', "_", re.sub(r"^https?://", "", str(url)))


def image_features(image):
    image = image.convert("RGB")
    pixels = np.asarray(image)
    hist = np.concatenate(
        [
            np.histogram(pixels[:, :, c], bins=16, range=(0, 256))[0]
            / (image.width * image.height)
            for c in range(3)
        ]
    )
    gray = np.asarray(image.convert("L").resize((64, 64)), dtype=float) / 255
    blocks = gray.reshape(8, 8, 8, 8).transpose(0, 2, 1, 3).reshape(64, 64)
    f = np.r_[
        hist,
        blocks.mean(1),
        blocks.std(1),
        np.log1p(image.width),
        np.log1p(image.height),
        image.width / image.height,
    ]
    small = np.asarray(image.convert("L").resize((9, 8)))
    dhash = int.from_bytes(np.packbits(small[:, 1:] > small[:, :-1]).tobytes(), "big")
    digest = hashlib.sha256(str(image.size).encode() + pixels.tobytes()).hexdigest()
    return f, dhash, digest


def components(hosts, exact, perceptual):
    """Transitive input-only grouping including all <=2 bit near duplicates."""
    parent = list(range(len(hosts)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union(i, j):
        a, b = find(i), find(j)
        parent[max(a, b)] = min(a, b)

    for values in [hosts, exact]:
        seen = {}
        for i, v in enumerate(values):
            if v in seen:
                union(i, seen[v])
            else:
                seen[v] = i
    seen = {}
    masks = (
        [0]
        + [1 << a for a in range(64)]
        + [(1 << a) | (1 << b) for a in range(64) for b in range(a)]
    )
    for i, v in enumerate(perceptual):
        for mask in masks:
            j = seen.get(v ^ mask)
            if j is not None:
                union(i, j)
        seen[v] = i
    return np.array([str(find(i)) for i in range(len(hosts))])


def extract(archive, output):
    import openpyxl

    archive = Path(archive)
    if (
        hashlib.file_digest(archive.open("rb"), "md5").hexdigest()
        != "85937228498c1efffb2ee497389482a2"
    ):
        raise ValueError("Archive checksum mismatch")
    counts = collections.Counter()
    urls, hosts, features, dhashes, exact, labels, ids, provider = (
        [],
        [],
        [],
        [],
        [],
        [],
        [],
        [],
    )
    with zipfile.ZipFile(archive) as z:
        table = openpyxl.load_workbook(
            io.BytesIO(z.read("Phishing dataset/url/merged_features_final.xlsx")),
            read_only=True,
            data_only=True,
        )
        lookup = collections.defaultdict(list)
        for row in list(table.active.values)[1:]:
            lookup[filename_key(row[0])].append((str(row[0]), row[-1]))
        for name in sorted(z.namelist()):
            if not name.endswith(".png"):
                continue
            counts["images"] += 1
            matches = lookup[name.rsplit("/", 1)[1][:-4].split("_", 1)[1]]
            if len(matches) != 1:
                counts["ambiguous" if matches else "unmatched"] += 1
                continue
            url, label = matches[0]
            if label != name.split("/")[-2]:
                counts["label_conflict"] += 1
                continue
            try:
                with Image.open(io.BytesIO(z.read(name))) as im:
                    f, dh, eh = image_features(im)
            except (OSError, ValueError, Image.DecompressionBombError):
                counts["decode_failure"] += 1
                continue
            host = urlsplit(url).hostname
            if not host:
                counts["missing_host"] += 1
                continue
            urls.append(url)
            hosts.append(host.lower())
            features.append(f)
            dhashes.append(dh)
            exact.append(eh)
            labels.append(int(label == "phishing"))
            ids.append(hashlib.sha256(name.encode()).hexdigest())
            provider.append(name.split("/")[2])
            if len(ids) % 1000 == 0:
                print("Decoded", len(ids), flush=True)
    groups = components(hosts, exact, dhashes)
    y = np.array(labels)
    cluster_sizes = collections.Counter(groups)
    overlap = sum(len(set(np.array(provider)[groups == g])) > 1 for g in set(groups))
    audit = {
        "counts": dict(counts),
        "retained": len(y),
        "positives": int(y.sum()),
        "negatives": int((y == 0).sum()),
        "components": len(cluster_sizes),
        "largest_component": max(cluster_sizes.values()),
        "mixed_label_components": sum(
            len(set(y[groups == g])) > 1 for g in set(groups)
        ),
        "provider_cross_split_components": overlap,
        "descriptor_count": len(features[0]),
    }
    write_json(Path(output) / "visual-input-audit.json", audit)
    return np.array(urls), np.array(features), y, groups, ids, audit


def run(archive, output):
    start = time.monotonic()
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    urls, X, y, g, ids, audit = extract(archive, output)
    rows, scores, splits = [], [], []
    for seed in [17, 42, 91]:
        tr, va, te = split_groups(y, g, seed)
        url_model = make_pipeline(
            TfidfVectorizer(
                analyzer="char",
                ngram_range=(3, 5),
                max_features=30000,
                sublinear_tf=True,
            ),
            LogisticRegression(
                C=1,
                class_weight="balanced",
                solver="liblinear",
                max_iter=2000,
                random_state=seed,
            ),
        )
        image_model = make_pipeline(
            StandardScaler(),
            LogisticRegression(
                C=1,
                class_weight="balanced",
                solver="liblinear",
                max_iter=2000,
                random_state=seed,
            ),
        )
        url_model.fit(urls[tr], y[tr])
        image_model.fit(X[tr], y[tr])
        uv, ut = (
            url_model.predict_proba(urls[va])[:, 1],
            url_model.predict_proba(urls[te])[:, 1],
        )
        iv, it = (
            image_model.predict_proba(X[va])[:, 1],
            image_model.predict_proba(X[te])[:, 1],
        )
        splits.append(
            {
                "seed": seed,
                "train": len(tr),
                "validation": len(va),
                "test": len(te),
                "test_positives": int(y[te].sum()),
                "group_overlap": 0,
            }
        )
        for name, v, p in [
            ("url", uv, ut),
            ("image", iv, it),
            ("fusion", (uv + iv) / 2, (ut + it) / 2),
        ]:
            cut = threshold_at_fpr(y[va], v)
            row = {"seed": seed, "policy": name, **binary_metrics(y[te], p, cut)}
            if seed == 42:
                row["cluster_uncertainty"] = uncertainty(
                    y[te], p, g[te], cut, ut if name != "url" else None,
                    unit="complete input-derived screenshot/hostname component",
                )
            rows.append(row)
            scores.append(
                {
                    "seed": seed,
                    "policy": name,
                    "ids": [ids[i] for i in te],
                    "groups": g[te].tolist(),
                    "labels": y[te].tolist(),
                    "risk": p.tolist(),
                    "threshold": cut,
                }
            )
        print("Completed seed", seed, flush=True)
    write_json(output / "visual-phishing-scores.json", scores)
    result = {
        "status": "bounded provider-labelled paired screenshot/URL benchmark; not deployment validation",
        "source": "https://doi.org/10.5281/zenodo.21379702",
        "archive_md5": "85937228498c1efffb2ee497389482a2",
        "environment": environment(),
        "wall_seconds": time.monotonic() - start,
        "input_audit": audit,
        "splits": splits,
        "experiments": rows,
        "limits": [
            "provider labels not manually adjudicated here",
            "collection and source shortcuts possible",
            "near-duplicate hashes do not prove campaign independence",
            "single corpus, no prospective deployment validation",
            "cluster intervals conditional on fitted policies",
            "compact descriptors are not state of the art visual recognition",
        ],
    }
    write_json(output / "visual-phishing.json", result)
    return result


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--archive", default="data/raw/multimodal-phishing.zip")
    p.add_argument("--output", default="results/validation")
    a = p.parse_args()
    run(a.archive, a.output)
