#!/usr/bin/env python3

import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
from failure_codes import FailureCode


JS_TAG = "<script src='./asciinema-player.min.js'></script>"
CSS_TAG = "<link rel='stylesheet' href='./asciinema-player.min.css'>"


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


def repair_missing_cast_ref(wrapper: Path, expected: str) -> bool:
    text = wrapper.read_text(encoding="utf-8", errors="ignore")
    updated = text

    if expected in updated:
        return False

    # Common malformed forms to normalize
    replacements = [
        ("src=\"run.cast\"", expected),
        ("src='run.cast'", expected),
        ("src=\"./run.cast\"", expected),
        ("src=\"./" + wrapper.with_suffix("").name + ".cast\"", expected),
        ("src='" + wrapper.with_suffix("").name + ".cast'", expected),
    ]

    changed = False
    for old, new in replacements:
        if old in updated:
            updated = updated.replace(old, new)
            changed = True

    if changed:
        wrapper.write_text(updated, encoding="utf-8")

    return changed


def repair_missing_js(wrapper: Path) -> bool:
    text = wrapper.read_text(encoding="utf-8", errors="ignore")

    if JS_TAG in text:
        return False

    updated = text

    if "</head>" in updated:
        updated = updated.replace("</head>", f"  {JS_TAG}\n</head>", 1)
    else:
        updated = f"{JS_TAG}\n{updated}"

    wrapper.write_text(updated, encoding="utf-8")
    return True


def repair_missing_head_structure(wrapper: Path) -> bool:
    text = wrapper.read_text(encoding="utf-8", errors="ignore")

    if "<head>" in text and "</head>" in text:
        return False

    body = text

    if "<body>" not in body:
        body = f"<body>\n{body}\n</body>"

    updated = f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  {CSS_TAG}
  {JS_TAG}
</head>
{body}
</html>
"""

    wrapper.write_text(updated, encoding="utf-8")
    return True


def repair_missing_css(wrapper: Path) -> bool:
    text = wrapper.read_text(encoding="utf-8", errors="ignore")

    if CSS_TAG in text:
        return False

    updated = text

    if "</head>" in updated:
        updated = updated.replace("</head>", f"  {CSS_TAG}\n</head>", 1)
    else:
        updated = f"{CSS_TAG}\n{updated}"

    wrapper.write_text(updated, encoding="utf-8")
    return True


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
            result["reason"] = f"Repaired missing player in {wrapper}"
            return result

        case FailureCode.WRAPPER_MISSING_HEAD_STRUCTURE:
            changed = repair_missing_head_structure(wrapper)
            if not changed:
                result["reason"] = "No repair performed"
                return result

            result["repaired"] = True
            result["reason"] = f"Inserted head structure in {wrapper}"
            return result    

        case FailureCode.WRAPPER_MISSING_CAST_REF:
            expected = details.get("expected")
            if not expected:
                result["reason"] = "Missing expected cast ref in details.expected"
                return result

            changed = repair_missing_cast_ref(wrapper, expected)
            if not changed:
                result["reason"] = "No repair performed"
                return result

            result["repaired"] = True
            result["reason"] = f"Repaired cast ref in {wrapper}"
            return result

        case FailureCode.WRAPPER_MISSING_JS:
            changed = repair_missing_js(wrapper)
            if not changed:
                result["reason"] = "No repair performed"
                return result

            result["repaired"] = True
            result["reason"] = f"Inserted JS tag in {wrapper}"
            return result

        case FailureCode.WRAPPER_MISSING_CSS:
            changed = repair_missing_css(wrapper)
            if not changed:
                result["reason"] = "No repair performed"
                return result

            result["repaired"] = True
            result["reason"] = f"Inserted CSS tag in {wrapper}"
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

    status = data.get("status")

    print(json.dumps({
        "status": status,
        "repaired_any": repaired_any,
        "results": repair_results
    }, indent=2))

    if status == "pass":
        return 0

    if repaired_any:
        return 0

    return 1



if __name__ == "__main__":
    raise SystemExit(main())