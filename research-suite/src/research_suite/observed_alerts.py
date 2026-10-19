"""Fixed-frame real ZTF alert access and causal-prefix checks, not ML validation."""

import argparse
import collections
import hashlib
import json
import math
from pathlib import Path
import urllib.request
from .common import write_json


def clean(records, oid):
    retained = []
    seen = {}
    rejected = collections.Counter()
    fallback = 0
    for row in records:
        if row.get("oid", oid) != oid:
            rejected["wrong_oid"] += 1
            continue
        try:
            mjd, mag, error = (
                float(row["mjd"]),
                float(row["magpsf"]),
                float(row["sigmapsf"]),
            )
            if (
                not all(math.isfinite(x) for x in [mjd, mag, error])
                or error <= 0
                or row["fid"] not in [1, 2]
            ):
                raise ValueError()
        except (ValueError, TypeError, KeyError):
            rejected["invalid_photometry"] += 1
            continue
        canonical = json.dumps(row, sort_keys=True, separators=(",", ":"))
        key = (
            str(row["candid"])
            if row.get("candid") is not None
            else hashlib.sha256(canonical.encode()).hexdigest()
        )
        fallback += int(row.get("candid") is None)
        if key in seen:
            if seen[key] != canonical:
                raise ValueError("Conflicting duplicate candid")
            rejected["exact_duplicate"] += 1
            continue
        seen[key] = canonical
        retained.append(dict(row, mjd=mjd, magpsf=mag, sigmapsf=error))
    return sorted(retained, key=lambda x: x["mjd"]), dict(rejected), fallback


def prefix(records, days):
    if not records:
        return None
    anchor = min(r["mjd"] for r in records)
    selected = [r for r in records if 0 <= r["mjd"] - anchor <= days]
    return {
        "detections": len(selected),
        "g": sum(r["fid"] == 1 for r in selected),
        "r": sum(r["fid"] == 2 for r in selected),
        "min_mag": min(r["magpsf"] for r in selected),
        "max_mag": max(r["magpsf"] for r in selected),
    }


def run(frame, raw, output):
    raw = Path(raw)
    raw.mkdir(parents=True, exist_ok=True)
    snapshot = json.loads(Path(frame).read_text())
    rows = []
    for obj in snapshot["selected_objects"]:
        oid = obj["ztf_id"]
        url = f"https://api.alerce.online/ztf/v1/objects/{oid}/detections"
        result = {"oid": oid, "provider_class": obj["provider_class"], "url": url}
        try:
            path = raw / (oid + ".json")
            if path.exists():
                payload = path.read_bytes()
                result["cached"] = True
            else:
                with urllib.request.urlopen(
                    urllib.request.Request(
                        url,
                        headers={
                            "User-Agent": "VulliResearchSuite/0.1 public-research"
                        },
                    ),
                    timeout=30,
                ) as response:
                    payload = response.read()
                    result["http_status"] = response.status
                path.write_bytes(payload)
            result["sha256"] = hashlib.sha256(payload).hexdigest()
            data = json.loads(payload)
            if not isinstance(data, list):
                raise ValueError("Expected list of detections")
            valid, rejected, fallback = clean(data, oid)
            result.update(
                raw_rows=len(data),
                valid_rows=len(valid),
                rejected=rejected,
                fallback_ids=fallback,
                difference_sign_counts=dict(
                    collections.Counter(str(r.get("isdiffpos")) for r in valid)
                ),
            )
            result["prefixes"] = {str(d): prefix(valid, d) for d in [1, 3, 7]}
            if valid:
                future = dict(
                    valid[0],
                    mjd=valid[0]["mjd"] + 1000,
                    magpsf=-100,
                    candid="synthetic_future",
                )
                result["future_invariance"] = all(
                    prefix(valid, d) == prefix(valid + [future], d) for d in [1, 3, 7]
                )
                if not result["future_invariance"]:
                    raise AssertionError("Future contamination")
            else:
                result["future_invariance"] = None
        except Exception as e:
            result["error"] = type(e).__name__ + ": " + str(e)
        rows.append(result)
        write_json(output, {"status": "in_progress", "objects": rows})
        print(oid, result.get("valid_rows"), result.get("error"), flush=True)
    result = {
        "status": "completed fixed-frame observed alert processing audit, not classifier validation",
        "frame_sha256": hashlib.sha256(Path(frame).read_bytes()).hexdigest(),
        "selected": len(rows),
        "objects_with_valid_detections": sum(r.get("valid_rows", 0) > 0 for r in rows),
        "objects_with_errors": sum("error" in r for r in rows),
        "future_invariance_passes": sum(
            r.get("future_invariance") is True for r in rows
        ),
        "kilonova_positives": 0,
        "classifier_metrics": None,
        "objects": rows,
        "limits": [
            "BTS provider-selected SN negative controls only",
            "earliest API detection is not guaranteed true first alert",
            "ZTF g/r magnitudes are not LSST six-band fluxes",
            "no observed kilonova recall or representative false-positive estimate",
            "no raw packet redistribution license asserted",
        ],
    }
    write_json(output, result)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--frame", default="results/followup/observed-readiness.json")
    p.add_argument("--raw", default="data/raw/observed-alerts")
    p.add_argument("--output", default="results/validation/observed-alerts.json")
    a = p.parse_args()
    run(a.frame, a.raw, a.output)
