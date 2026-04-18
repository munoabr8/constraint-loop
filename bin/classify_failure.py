#!/usr/bin/env python3

import json
import sys

KNOWN_DETERMINISTIC = {
    "MISSING_RELATION": "regenerate_wrappers",
    "WRAPPER_MISSING_PLAYER": "regenerate_wrappers",
    "WRAPPER_MISSING_JS": "regenerate_wrappers",
    "WRAPPER_MISSING_CSS": "regenerate_wrappers",
    "WRAPPER_MISSING_CAST_REF": "regenerate_wrappers",
}

def main() -> int:
    data = json.load(sys.stdin)
    classified = []

    for v in data.get("violations", []):
        vt = v.get("violation_type")
        if vt in KNOWN_DETERMINISTIC:
            classified.append({
                "violation_type": vt,
                "classification": "known_deterministic",
                "action": KNOWN_DETERMINISTIC[vt]
            })
        else:
            classified.append({
                "violation_type": vt,
                "classification": "unknown",
                "action": "invoke_llm"
            })

    print(json.dumps({
        "status": data.get("status"),
        "classifications": classified
    }, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())