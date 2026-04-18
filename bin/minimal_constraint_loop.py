#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

sys.path.append(str(Path(__file__).resolve().parent.parent))

from failure_codes import FailureCode


class CheckFn(Protocol):
    def __call__(self, root: Path) -> list["Violation"]:
        ...


class RepairFn(Protocol):
    def __call__(self, root: Path, violation: "Violation") -> bool:
        ...


@dataclass(frozen=True)
class Violation:
    constraint_id: str
    code: str
    entity: str
    entity_id: str
    details: dict[str, str]


@dataclass(frozen=True)
class Constraint:
    id: str
    description: str
    severity: str
    check: CheckFn
    repair: RepairFn | None = None


def cast_missing_wrapper_check(root: Path) -> list[Violation]:
    violations: list[Violation] = []

    for cast in root.glob("*.cast"):
        expected_wrapper = cast.with_suffix(".cast.html")
        if not expected_wrapper.exists():
            violations.append(
                Violation(
                    constraint_id="cast_missing_wrapper",
                    code=FailureCode.CAST_MISSING_WRAPPER.value,
                    entity="Cast",
                    entity_id=cast.name,
                    details={
                        "cast_path": str(cast),
                        "expected_wrapper": str(expected_wrapper),
                    },
                )
            )

    return violations


def no_cast_files_check(root: Path) -> list[Violation]:
    cast_files = list(root.glob("*.cast"))

    if not cast_files:
        return [
            Violation(
                constraint_id="no_cast_files",
                code=FailureCode.NO_CAST_FILES_FOUND.value,
                entity="ArtifactDir",
                entity_id=str(root),
                details={"path": str(root)},
            )
        ]

    return []


def wrapper_integrity_check(root: Path) -> list[Violation]:
    violations: list[Violation] = []

    for wrapper in root.glob("*.cast.html"):
        try:
            content = wrapper.read_text(encoding="utf-8")
        except OSError as exc:
            violations.append(
                Violation(
                    constraint_id="wrapper_integrity",
                    code=FailureCode.WRAPPER_UNREADABLE.value,
                    entity="Wrapper",
                    entity_id=wrapper.name,
                    details={"error": str(exc)},
                )
            )
            continue

        cast_name = wrapper.name.removesuffix(".html")

        has_player = "<asciinema-player" in content
        has_js = "asciinema-player.min.js" in content
        has_css = "asciinema-player.min.css" in content
        has_cast_ref = (
            f"src='./{cast_name}'" in content
            or f'src="./{cast_name}"' in content
        )
        player_count = content.count("<asciinema-player")

        if player_count > 1:
            violations.append(
                Violation(
                    constraint_id="wrapper_integrity",
                    code=FailureCode.WRAPPER_DUPLICATE_PLAYER_BLOCK.value,
                    entity="Wrapper",
                    entity_id=wrapper.name,
                    details={
                        "path": str(wrapper),
                        "player_count": str(player_count),
                    },
                )
            )

        if not has_player:
            violations.append(
                Violation(
                    constraint_id="wrapper_integrity",
                    code=FailureCode.WRAPPER_MISSING_PLAYER.value,
                    entity="Wrapper",
                    entity_id=wrapper.name,
                    details={"path": str(wrapper)},
                )
            )

        if not has_js:
            violations.append(
                Violation(
                    constraint_id="wrapper_integrity",
                    code=FailureCode.WRAPPER_MISSING_JS.value,
                    entity="Wrapper",
                    entity_id=wrapper.name,
                    details={"path": str(wrapper)},
                )
            )

        if not has_css:
            violations.append(
                Violation(
                    constraint_id="wrapper_integrity",
                    code=FailureCode.WRAPPER_MISSING_CSS.value,
                    entity="Wrapper",
                    entity_id=wrapper.name,
                    details={"path": str(wrapper)},
                )
            )

        if not has_cast_ref:
            violations.append(
                Violation(
                    constraint_id="wrapper_integrity",
                    code=FailureCode.WRAPPER_MISSING_CAST_REF.value,
                    entity="Wrapper",
                    entity_id=wrapper.name,
                    details={"path": str(wrapper)},
                )
            )

    return violations


def wrapper_integrity_repair(root: Path, violation: Violation) -> bool:
    repairable_codes = {
        FailureCode.WRAPPER_MISSING_PLAYER.value,
        FailureCode.WRAPPER_MISSING_JS.value,
        FailureCode.WRAPPER_MISSING_CSS.value,
        FailureCode.WRAPPER_MISSING_CAST_REF.value,
        FailureCode.WRAPPER_DUPLICATE_PLAYER_BLOCK.value,
    }

    if violation.code not in repairable_codes:
        return False

    wrapper_path = Path(violation.details["path"])
    if not wrapper_path.exists():
        return False

    try:
        content = wrapper_path.read_text(encoding="utf-8")
    except OSError:
        return False

    cast_name = wrapper_path.name.removesuffix(".html")

    updated = content.replace("<broken-player", "<asciinema-player")

    matches = list(
        re.finditer(
            r"<asciinema-player\b.*?</asciinema-player>",
            updated,
            re.DOTALL,
        )
    )
    if len(matches) > 1:
        first = matches[0]
        prefix = updated[:first.end()]
        suffix = updated[first.end():]
        suffix = re.sub(
            r"<asciinema-player\b.*?</asciinema-player>",
            "",
            suffix,
            flags=re.DOTALL,
        )
        updated = prefix + suffix

    if "./asciinema-player.min.css" not in updated and "asciinema-player.min.css" not in updated:
        css_tag = "<link rel='stylesheet' href='./asciinema-player.min.css'>\n"
        if "</body>" in updated:
            updated = updated.replace("</body>", css_tag + "</body>", 1)
        else:
            updated += "\n" + css_tag

    if "./asciinema-player.min.js" not in updated and "asciinema-player.min.js" not in updated:
        js_tag = "<script src='./asciinema-player.min.js'></script>\n"
        if "</body>" in updated:
            updated = updated.replace("</body>", js_tag + "</body>", 1)
        else:
            updated += "\n" + js_tag

    updated = re.sub(
        r"(<asciinema-player\b[^>]*\bsrc=)['\"][^'\"]+['\"]",
        rf"\1'./{cast_name}'",
        updated,
        count=1,
    )

    if "<asciinema-player" not in updated:
        injected = (
            f"<asciinema-player src='./{cast_name}' "
            "cols='auto' rows='auto' terminal-font-size='16px' "
            "speed='1' preload='true' loop='false' "
            "style='width:100%; height:100vh'></asciinema-player>\n"
        )
        if "</body>" in updated:
            updated = updated.replace("</body>", injected + "</body>", 1)
        else:
            updated += "\n" + injected

    if updated == content:
        return False

    try:
        wrapper_path.write_text(updated, encoding="utf-8")
    except OSError:
        return False

    return True


def run_constraints(root: Path, constraints: list[Constraint]) -> dict:
    results: list[dict] = []
    repaired_any = False

    for constraint in constraints:
        violations = constraint.check(root)
        for violation in violations:
            repaired = False
            if constraint.repair is not None:
                repaired = constraint.repair(root, violation)
                repaired_any = repaired_any or repaired

            results.append(
                {
                    "constraint_id": violation.constraint_id,
                    "code": violation.code,
                    "entity": violation.entity,
                    "entity_id": violation.entity_id,
                    "details": violation.details,
                    "severity": constraint.severity,
                    "repaired": repaired,
                }
            )

    status = "pass" if not results else "fail"

    return {
        "status": status,
        "repaired_any": repaired_any,
        "violations": results,
    }


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Minimal constraint loop")
    parser.add_argument("--artifacts", required=True, help="Path to artifacts directory")
    parser.add_argument(
        "--no-repair",
        action="store_true",
        help="Only detect violations; do not attempt repair",
    )
    args = parser.parse_args()

    root = Path(args.artifacts).resolve()
    if not root.exists() or not root.is_dir():
        print(
            json.dumps(
                {"status": "error", "message": f"invalid artifacts path: {root}"},
                indent=2,
            )
        )
        return 2

    repair_fn = None if args.no_repair else wrapper_integrity_repair

    constraints = [
        Constraint(
            id="wrapper_integrity",
            description="Wrapper must be structurally valid",
            severity="high",
            check=wrapper_integrity_check,
            repair=repair_fn,
        ),
        Constraint(
            id="cast_missing_wrapper",
            description="Every cast must have a wrapper",
            severity="high",
            check=cast_missing_wrapper_check,
            repair=None,
        ),
        Constraint(
            id="no_cast_files",
            description="At least one .cast file must exist",
            severity="high",
            check=no_cast_files_check,
            repair=None,
        ),
    ]

    first_pass = run_constraints(root, constraints)

    if first_pass["repaired_any"]:
        repairless_constraints = [
            Constraint(
                id=c.id,
                description=c.description,
                severity=c.severity,
                check=c.check,
                repair=None,
            )
            for c in constraints
        ]
        second_pass = run_constraints(root, repairless_constraints)
        output = {
            "initial": first_pass,
            "revalidation": second_pass,
            "final_status": second_pass["status"],
        }
        print(json.dumps(output, indent=2))
        return 0 if second_pass["status"] == "pass" else 1

    print(json.dumps(first_pass, indent=2))
    return 0 if first_pass["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())