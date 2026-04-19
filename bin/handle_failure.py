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
    repair_actions: list[dict] | None = None,
    nonblocking_failures: list[dict] | None = None,
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

    if nonblocking_failures:
        outcome["nonblocking_failures"] = nonblocking_failures
        outcome["nonblocking_count"] = len(nonblocking_failures)
    else:
        outcome["nonblocking_count"] = 0

    if repair_actions:
        outcome["repair_actions"] = repair_actions
        outcome["repair_action_count"] = len(repair_actions)
    else:
        outcome["repair_action_count"] = 0

    if action_result is not None:
        outcome["action_result"] = action_result

    return outcome


def main() -> int:
    data = json.load(sys.stdin)
    classifications = data.get("classifications", [])
    input_status = data.get("status", "unknown")

    actions = sorted({item.get("action", "unknown_action") for item in classifications})

    blocking = [
        item for item in classifications
        if item.get("classification") == "known_blocking"
    ]

    unknowns = [
        item for item in classifications
        if item.get("classification") == "unknown"
    ]

    repair_actions = [
        item for item in classifications
        if item.get("action") == "repair_wrapper"
    ]

    nonblocking = [
        item for item in classifications
        if item.get("classification") not in {"known_blocking", "unknown"}
        and item.get("action") != "repair_wrapper"
    ]

    print(json.dumps({
        "status": "received",
        "actions": actions,
        "blocking_count": len(blocking),
        "unknown_count": len(unknowns),
        "repair_action_count": len(repair_actions),
        "nonblocking_count": len(nonblocking),
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
            repair_actions=repair_actions,
            nonblocking_failures=nonblocking,
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
            repair_actions=repair_actions,
            nonblocking_failures=nonblocking,
        )
        print(json.dumps(outcome, indent=2))
        return 1

    if repair_actions:
        outcome = build_outcome(
            input_status=input_status,
            actions=actions,
            blocking_failures=blocking,
            unknown_failures=unknowns,
            repaired_any=False,
            final_decision="repair_required",
            reason="Metadata indicates repairer execution is required",
            repair_actions=repair_actions,
            nonblocking_failures=nonblocking,
        )
        print(json.dumps(outcome, indent=2))
        return 0

    outcome = build_outcome(
        input_status=input_status,
        actions=actions,
        blocking_failures=blocking,
        unknown_failures=unknowns,
        repaired_any=False,
        final_decision="no_repair_path",
        reason="No blocking, unknown, or repairable actions selected",
        repair_actions=repair_actions,
        nonblocking_failures=nonblocking,
    )
    print(json.dumps(outcome, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())