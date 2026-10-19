"""Dated negative-control sampling and strict observed-data admission, no scoring."""

from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import urllib.parse
import urllib.request
import numpy as np
import pandas as pd
from .common import sha256, write_json

FRAME = "https://sites.astro.caltech.edu/ztf/bts/explorer.php?format=csv"


def coordinate(value, ra=False):
    text = str(value).strip()
    if ":" in text:
        parts = text.lstrip("+-").split(":")
        if len(parts) != 3:
            raise ValueError("Expected sexagesimal coordinate")
        a, b, c = map(float, parts)
        if not 0 <= b < 60 or not 0 <= c < 60 or a < 0:
            raise ValueError("Invalid sexagesimal coordinate")
        result = (
            (a + b / 60 + c / 3600)
            * (-1 if text.startswith("-") else 1)
            * (15 if ra else 1)
        )
    else:
        result = float(text)
    if not np.isfinite(result) or not (
        (0 <= result < 360) if ra else (-90 <= result <= 90)
    ):
        raise ValueError("Coordinate outside sky bounds")
    return result


def select(frame):
    required = {"ZTFID", "RA", "Dec", "type"}
    if not required <= set(frame):
        raise ValueError("Unknown BTS schema")
    selected = []
    invalid = duplicates = 0
    seen = set()
    sn_rows = 0
    for _, row in frame.iterrows():
        if not str(row["type"]).strip().startswith("SN"):
            continue
        sn_rows += 1
        name = str(row.ZTFID).strip()
        try:
            if not name.startswith("ZTF"):
                raise ValueError("Invalid ZTF identifier")
            ra = coordinate(row.RA, ra=True)
            dec = coordinate(row.Dec)
        except (ValueError, TypeError):
            invalid += 1
            continue
        if name in seen:
            duplicates += 1
            continue
        seen.add(name)
        selected.append(
            {
                "ztf_id": name,
                "provider_class": str(row["type"]).strip(),
                "ra_deg": ra,
                "dec_deg": dec,
                "selection_sha256": hashlib.sha256(name.encode()).hexdigest(),
            }
        )
    selected.sort(key=lambda row: row["selection_sha256"])
    return selected[:20], {
        "frame_rows": len(frame),
        "provider_sn_rows": sn_rows,
        "invalid_excluded": invalid,
        "duplicate_ids_excluded": duplicates,
        "eligible_unique_ids": len(selected),
        "selected": min(20, len(selected)),
    }


def admission(columns, filter_system, row_count=None):
    reasons = []
    if row_count == 0:
        reasons.append("no photometry rows returned for the fixed first-selected cone")
    if filter_system != "LSST":
        reasons.append(
            "filter system differs: ZTF versus LSST; no verified response mapping"
        )
    missing = sorted(
        {"object_id", "mjd", "passband", "flux", "flux_err", "detected_bool"}
        - set(columns)
    )
    if missing:
        reasons.append("required model fields absent: " + ", ".join(missing))
    reasons.extend(
        [
            "difference-image flux/uncertainty convention not established by this catalog query",
            "broker first-alert/detection history not established",
            "cone candidates require explicit source-identity crossmatch",
        ]
    )
    return {
        "admitted_for_scoring": False,
        "reasons": reasons,
        "model_scores_computed": False,
        "performance_metrics": None,
    }


def run(data="data/raw", output="results/followup"):
    data, output = Path(data), Path(output)
    data.mkdir(parents=True, exist_ok=True)
    source = data / "bts-readiness.csv"
    if not source.exists():
        with urllib.request.urlopen(FRAME, timeout=60) as response:
            source.write_bytes(response.read())
    frame = pd.read_csv(source)
    sample, counts = select(frame)
    if not sample:
        raise ValueError("No eligible negative-control objects")
    first = sample[0]
    query = (
        "https://irsa.ipac.caltech.edu/cgi-bin/ZTF/nph_light_curves?"
        + urllib.parse.urlencode(
            {
                "POS": f"CIRCLE {first['ra_deg']:.10f} {first['dec_deg']:.10f} {1.5/3600:.10f}",
                "BANDNAME": "g,r",
                "BAD_CATFLAGS_MASK": "32768",
                "COLLECTION": "ztf_dr24",
                "FORMAT": "CSV",
            }
        )
    )
    cache = data / "bts-first-selected-dr24.csv"
    provenance = data / "bts-first-selected-dr24-provenance.json"
    retrieved = datetime.now(timezone.utc).isoformat()
    response_summary = {
        "query_url": query,
        "object_id": first["ztf_id"],
        "query_started_utc": retrieved,
    }
    try:
        if not cache.exists():
            with urllib.request.urlopen(query, timeout=60) as response:
                cache.write_bytes(response.read())
                response_summary["http_status"] = response.status
            response_summary["sha256"] = sha256(cache)
            write_json(provenance, response_summary)
        else:
            response_summary = json.loads(provenance.read_text())
            if response_summary["query_url"] != query or response_summary[
                "sha256"
            ] != sha256(cache):
                raise ValueError(
                    "Cached archive query or bytes do not match provenance"
                )
        curves = pd.read_csv(cache, dtype={"oid": str})
        response_summary.update(
            {
                "status": "public response parsed",
                "bytes": cache.stat().st_size,
                "sha256": sha256(cache),
                "snapshot_saved_utc": datetime.fromtimestamp(
                    cache.stat().st_mtime, timezone.utc
                ).isoformat(),
                "rows": len(curves),
                "columns": list(curves),
                "candidate_archive_ids": (
                    int(curves.oid.nunique()) if "oid" in curves else None
                ),
            }
        )
        gate = admission(curves.columns, "ZTF", len(curves))
    except Exception as exc:
        response_summary.update(
            {
                "status": "access or schema failure",
                "error": type(exc).__name__ + ": " + str(exc),
            }
        )
        gate = {
            "admitted_for_scoring": False,
            "model_scores_computed": False,
            "performance_metrics": None,
            "reasons": ["access/schema failure; no valid model input established"],
        }
    result = {
        "status": "completed observed-data readiness audit; no classifier performance experiment",
        "frame": {
            "url": FRAME,
            "sha256": sha256(source),
            "bytes": source.stat().st_size,
            "snapshot_saved_utc": datetime.fromtimestamp(
                source.stat().st_mtime, timezone.utc
            ).isoformat(),
            "selection_limit": "default BTS query quality/purity selection, then provider-SN negative controls",
        },
        "selection": counts,
        "selected_objects": sample,
        "first_object_archive_query": response_summary,
        "admission": gate,
        "permissions": {
            "catalog": "official public BTS explorer asks research users to cite its paper; no blanket redistribution license asserted",
            "archive_terms": "https://irsa.ipac.caltech.edu/data_use_terms.html",
            "acknowledgments": "https://irsa.ipac.caltech.edu/ack.html",
        },
        "limits": [
            "provider classifications not independently adjudicated",
            "20 deterministic negative controls, only first archive cone queried",
            "no kilonova positives or representative alert population",
            "no full source-table redistribution",
            "this mapping failure does not prove all observed-data comparisons impossible",
        ],
    }
    write_json(output / "observed-readiness.json", result)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", default="data/raw")
    parser.add_argument("--output", default="results/followup")
    args = parser.parse_args()
    run(args.data, args.output)
