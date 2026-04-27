#!/usr/bin/env python3

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("artifact_path", help="Path to a run artifact JSON file")
    parser.add_argument(
        "--out",
        default="runs/RUN_HISTORY.md",
        help="Markdown history file to append to",
    )
    args = parser.parse_args()

    artifact_path = Path(args.artifact_path).resolve()
    out_path = Path(args.out).resolve()

    data = json.loads(artifact_path.read_text(encoding="utf-8"))

    started_at = data.get("started_at", "unknown")
    final_decision = data.get("final_decision", "unknown")
    violation_count = data.get("violation_count", 0)
    blocking_count = data.get("blocking_count", 0)
    nonblocking_count = data.get("nonblocking_count", 0)
    unknown_count = data.get("unknown_count", 0)
    repair_action_count = data.get("repair_action_count", 0)
    repaired_any = data.get("repaired_any", False)

    out_path.parent.mkdir(parents=True, exist_ok=True)

    entry = (
        f"## {started_at}\n\n"
        f"- decision: `{final_decision}`\n"
        f"- violations: `{violation_count}`\n"
        f"- blocking: `{blocking_count}`\n"
        f"- nonblocking: `{nonblocking_count}`\n"
        f"- unknown: `{unknown_count}`\n"
        f"- repair_actions: `{repair_action_count}`\n"
        f"- repaired_any: `{str(repaired_any).lower()}`\n"
        f"- artifact: `{artifact_path}`\n\n"
    )

    with out_path.open("a", encoding="utf-8") as f:
        f.write(entry)

    print(entry, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())