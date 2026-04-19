#!/usr/bin/env python3

import json
import subprocess
import sys


def main() -> int:
    data = json.load(sys.stdin)
    classifications = data.get("classifications", [])

    actions = {item["action"] for item in classifications}
    blocking = [
        item for item in classifications
        if item.get("classification") == "known_blocking"
    ]
    unknowns = [
        item for item in classifications
        if item.get("classification") == "unknown"
    ]

    print(json.dumps({
        "status": "received",
        "actions": sorted(actions),
        "blocking_count": len(blocking),
        "unknown_count": len(unknowns),
    }, indent=2), file=sys.stderr)

    if blocking:
        print(json.dumps({
            "status": "blocked",
            "reason": "Known blocking failures present",
            "blocking_failures": blocking,
        }, indent=2))
        return 1

    if unknowns:
        print(json.dumps({
            "status": "escalate",
            "reason": "Unknown failures present",
            "unknown_failures": unknowns,
        }, indent=2))
        return 1

    if "regenerate_wrappers" in actions:
        result = subprocess.run(
            [
                "python3",
                "evidenceKit/evidence-kit/bin/gen-index.py",
                "--art-dir",
                "evidenceKit/evidence-kit/artifacts",
            ],
            capture_output=True,
            text=True,
        )

        print(json.dumps({
            "status": "ran_action",
            "action": "regenerate_wrappers",
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }, indent=2))

        return result.returncode

    print(json.dumps({
        "status": "no_action_taken"
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())