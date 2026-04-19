#!/usr/bin/env python3
import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
from failure_metadata import FAILURE_METADATA

 

def main() -> int:
    data = json.load(sys.stdin)
    classified = []

    for v in data.get("violations", []):
        vt = v.get("violation_type")

        if vt in FAILURE_METADATA:
            meta = FAILURE_METADATA[vt]
            classified.append({
                "status": data.get("status"),
                "known": meta["known"],
                "code": vt,
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