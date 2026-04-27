#!/usr/bin/env python3
import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
from failure_metadata import FAILURE_METADATA


METADATA_FAILURE_TYPES = {
    "METADATA_MISSING_FIELD",
    "METADATA_ARTIFACT_NOT_FOUND",
    "METADATA_BAD_EXIT_CODE",
    "METADATA_BAD_STATUS",
}


def classify_metadata_violation(v: dict, status=None) -> dict:
    violation_type = v.get("type")

    return {
        "status": status,
        "known": True,
        "code": violation_type,
        "entity": "MetadataSidecar",
        "entity_id": v.get("file"),
        "details": {
            "file": v.get("file"),
            "field": v.get("field"),
            "mode": v.get("mode"),
            "artifact": v.get("artifact"),
            "exit_code": v.get("exit_code"),
            "metadata_status": v.get("status"),
            "raw_violation": v,
        },
        "classification": "deterministic",
        "action": "metadata_repair_or_manual_review",
    }


def classify_known_violation(v: dict, status=None) -> dict:
    vt = v.get("violation_type")
    meta = FAILURE_METADATA[vt]

    return {
        "status": status,
        "known": meta["known"],
        "code": vt,
        "entity": v.get("entity"),
        "entity_id": v.get("entity_id"),
        "details": v.get("details", {}),
        "classification": meta["classification"],
        "action": meta["action"],
    }


def classify_unknown_violation(v: dict, status=None) -> dict:
    return {
        "status": status,
        "known": False,
        "code": "UNKNOWN_FAILURE",
        "entity": v.get("entity"),
        "entity_id": v.get("entity_id"),
        "details": {
            "reason": "No known classifier matched observed failure",
            "raw_violation": v,
        },
        "classification": "unknown",
        "action": "invoke_llm",
    }


def main() -> int:
    data = json.load(sys.stdin)
    status = data.get("status")
    classified = []

    for v in data.get("violations", []):
        violation_type = v.get("violation_type") or v.get("type")

        if violation_type in METADATA_FAILURE_TYPES:
            classified.append(classify_metadata_violation(v, status))
            continue

        if v.get("violation_type") in FAILURE_METADATA:
            classified.append(classify_known_violation(v, status))
            continue

        classified.append(classify_unknown_violation(v, status))

    print(json.dumps({
        "status": status,
        "classifications": classified
    }, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())