#!/usr/bin/env python3

import json
import subprocess
import sys

def main() -> int:
    data = json.load(sys.stdin)
    print(json.dumps(data, indent=2), file=sys.stderr)
    actions = {item["action"] for item in data.get("classifications", [])}

    print(json.dumps({
        "status": "received",
        "actions": sorted(actions)
    }, indent=2), file=sys.stderr)

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