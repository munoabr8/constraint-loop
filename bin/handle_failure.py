#!/usr/bin/env python3

import json
import sys


def build_outcome(
    *,
    input_status: str,
    actions: list[str],
    blocking_failures: list[dict],
    unknown_failures: list[dict],
    repaired_any: bool,
    final_decision: str,
    reason: str,
    action_result: dict | None = None,
) -> dict:
    outcome = {
        "status": "complete",
        "input_status": input_status,
        "actions": actions,
        "blocking_count": len(blocking_failures),
        "unknown_count": len(unknown_failures),
        "repaired_any": repaired_any,
        "final_decision": final_decision,
        "reason": reason,
    }

    if blocking_failures:
        outcome["blocking_failures"] = blocking_failures

    if unknown_failures:
        outcome["unknown_failures"] = unknown_failures

    if action_result is not None:
        outcome["action_result"] = action_result

    return outcome


def main() -> int:
    data = json.load(sys.stdin)
    classifications = data.get("classifications", [])
    input_status = data.get("status", "unknown")

    actions = sorted({item["action"] for item in classifications})

    blocking = [
        item for item in classifications
        if item.get("classification") == "known_blocking"
    ]
    unknowns = [
        item for item in classifications
        if item.get("classification") == "unknown"
    ]
    deterministic = [
        item for item in classifications
        if item.get("classification") == "known_deterministic"
    ]

    print(json.dumps({
        "status": "received",
        "actions": actions,
        "blocking_count": len(blocking),
        "unknown_count": len(unknowns),
        "deterministic_count": len(deterministic),
    }, indent=2), file=sys.stderr)

    if blocking:
        outcome = build_outcome(
            input_status=input_status,
            actions=actions,
            blocking_failures=blocking,
            unknown_failures=unknowns,
            repaired_any=False,
            final_decision="halt",
            reason="Known blocking failures present",
        )
        print(json.dumps(outcome, indent=2))
        return 1

    if unknowns:
        outcome = build_outcome(
            input_status=input_status,
            actions=actions,
            blocking_failures=blocking,
            unknown_failures=unknowns,
            repaired_any=False,
            final_decision="escalate",
            reason="Unknown failures present",
        )
        print(json.dumps(outcome, indent=2))
        return 1

    if deterministic:
        outcome = build_outcome(
            input_status=input_status,
            actions=actions,
            blocking_failures=blocking,
            unknown_failures=unknowns,
            repaired_any=False,
            final_decision="repair_required",
            reason="Deterministic repair required",
        )
        print(json.dumps(outcome, indent=2))
        return 0

    outcome = build_outcome(
        input_status=input_status,
        actions=actions,
        blocking_failures=blocking,
        unknown_failures=unknowns,
        repaired_any=False,
        final_decision="no_action_taken",
        reason="No actionable deterministic route selected",
    )
    print(json.dumps(outcome, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())