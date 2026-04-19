#!/usr/bin/env python3
import json
import sys

KNOWN_FAILURES = {
    "MISSING_RELATION": {
        "classification": "known_deterministic",
        "action": "regenerate_wrappers",
        "known": True,
        "code": "MISSING_RELATION",
    },
    "WRAPPER_MISSING_PLAYER": {
        "classification": "known_deterministic",
        "action": "regenerate_wrappers",
        "known": True,
        "code": "WRAPPER_MISSING_PLAYER",
    },
    "WRAPPER_MISSING_JS": {
        "classification": "known_deterministic",
        "action": "regenerate_wrappers",
        "known": True,
        "code": "WRAPPER_MISSING_JS",
    },
    "WRAPPER_MISSING_CSS": {
        "classification": "known_deterministic",
        "action": "regenerate_wrappers",
        "known": True,
        "code": "WRAPPER_MISSING_CSS",
    },
    "WRAPPER_MISSING_CAST_REF": {
        "classification": "known_deterministic",
        "action": "regenerate_wrappers",
        "known": True,
        "code": "WRAPPER_MISSING_CAST_REF",
    },
    "NO_CAST_FILES_FOUND": {
        "classification": "known_blocking",
        "action": "halt_missing_inputs",
        "known": True,
        "code": "NO_CAST_FILES_FOUND",
    },
    "CAST_MISSING_WRAPPER": {
        "classification": "known_blocking",
        "action": "halt_missing_wrapper",
        "known": True,
        "code": "CAST_MISSING_WRAPPER",
    },
    "WRAPPER_UNREADABLE": {
        "classification": "known_blocking",
        "action": "halt_unreadable_wrapper",
        "known": True,
        "code": "WRAPPER_UNREADABLE",
    },
    "WRAPPER_DUPLICATE_PLAYER_BLOCK": {
        "classification": "known_blocking",
        "action": "manual_review",
        "known": True,
        "code": "WRAPPER_DUPLICATE_PLAYER_BLOCK",
    },
}

def main() -> int:
    data = json.load(sys.stdin)
    classified = []

    for v in data.get("violations", []):
        vt = v.get("violation_type")

        if vt in KNOWN_FAILURES:
            meta = KNOWN_FAILURES[vt]
            classified.append({
                "status": data.get("status"),
                "known": meta["known"],
                "code": meta["code"],
                "entity": v.get("entity"),
                "entity_id": v.get("entity_id"),
                "details": v.get("details", {}),
                "classification": meta["classification"],
                "action": meta["action"],
            })
        else:
            classified.append({
                "status": data.get("status"),
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
            })

    print(json.dumps({
        "status": data.get("status"),
        "classifications": classified
    }, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())