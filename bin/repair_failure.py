#!/usr/bin/env python3

import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
from failure_codes import FailureCode

 
def repair_missing_player(wrapper: Path) -> bool:
    text = wrapper.read_text(encoding="utf-8", errors="ignore")
    updated = text
    changed = False

    if "<asciinema-player" not in updated and "<broken-player" in updated:
        updated = updated.replace("<broken-player", "<asciinema-player")
        changed = True

    if "</broken-player>" in updated:
        updated = updated.replace("</broken-player>", "</asciinema-player>")
        changed = True

    if changed:
        wrapper.write_text(updated, encoding="utf-8")

    return changed

def repair_classification(item: dict) -> dict:
    known = item.get("known", False)
    code_value = item.get("code")
    details = item.get("details", {})

    result = {
        "code": code_value,
        "known": known,
        "repaired": False,
        "reason": None,
    }

    if not known:
        result["reason"] = "Refusing to repair unknown failure"
        return result

    if not code_value:
        result["reason"] = "Missing failure code"
        return result

    try:
        code = FailureCode(code_value)
    except ValueError:
        result["reason"] = f"Invalid failure code: {code_value}"
        return result

    wrapper_path = details.get("path")
    if not wrapper_path:
        result["reason"] = "Missing wrapper path in details.path"
        return result

    wrapper = Path(wrapper_path)

    if not wrapper.exists():
        result["reason"] = f"Wrapper does not exist: {wrapper}"
        return result

    match code:
        case FailureCode.WRAPPER_MISSING_PLAYER:
            changed = repair_missing_player(wrapper)
            if not changed:
                result["reason"] = "No repair performed"
                return result

            result["repaired"] = True
            result["reason"] = f"Repaired {wrapper}"
            return result

        case _:
            result["reason"] = f"Unhandled deterministic failure code: {code.value}"
            return result


def main() -> int:
    data = json.load(sys.stdin)
    classifications = data.get("classifications", [])

    repair_results = []
    repaired_any = False

    for item in classifications:
        outcome = repair_classification(item)
        repair_results.append(outcome)
        if outcome["repaired"]:
            repaired_any = True

    print(json.dumps({
        "status": data.get("status"),
        "repaired_any": repaired_any,
        "results": repair_results
    }, indent=2))

    return 0 if repaired_any else 1


if __name__ == "__main__":
    raise SystemExit(main())