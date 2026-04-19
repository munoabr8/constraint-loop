#!/usr/bin/env python3

import argparse
import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
from failure_codes import FailureCode


def make_violation(
    code: FailureCode,
    entity: str,
    entity_id: str,
    details: dict | None = None,
) -> dict:
    violation = {
        "violation_type": code.value,
        "entity": entity,
        "entity_id": entity_id,
        "details": details or {},
    }
    return violation


def wrapper_references_cast(content: str, cast_name: str) -> bool:
    expected_ref = f"src='./{cast_name}'"
    return expected_ref in content


def wrapper_has_player(content: str) -> bool:
    return "<asciinema-player" in content


def wrapper_player_count(content: str) -> int:
    return content.count("<asciinema-player")


def wrapper_has_local_or_cdn_js(content: str) -> bool:
    return (
        "<script src='./asciinema-player.min.js'></script>" in content
        or "https://cdn.jsdelivr.net/npm/asciinema-player" in content
    )


def wrapper_has_local_or_cdn_css(content: str) -> bool:
    return (
        "<link rel='stylesheet' href='./asciinema-player.min.css'>" in content
        or "https://cdn.jsdelivr.net/npm/asciinema-player" in content
    )


def inspect_wrapper(cast: Path, wrapper: Path) -> list[dict]:
    violations: list[dict] = []

    if not wrapper.exists():
        return violations  # existence handled elsewhere

    content = wrapper.read_text(encoding="utf-8", errors="ignore")

    base_details = {
        "path": str(wrapper),
    }

    if not wrapper_references_cast(content, cast.name):
        violations.append(
            make_violation(
                code=FailureCode.WRAPPER_MISSING_CAST_REF,
                entity="Wrapper",
                entity_id=wrapper.name,
                details={
                    **base_details,
                    "expected": f"src='./{cast.name}'",
                },
            )
        )

    player_count = wrapper_player_count(content)

    if player_count == 0:
        violations.append(
            make_violation(
                code=FailureCode.WRAPPER_MISSING_PLAYER,
                entity="Wrapper",
                entity_id=wrapper.name,
                details=base_details,
            )
        )
    elif player_count > 1:
        violations.append(
            make_violation(
                code=FailureCode.WRAPPER_DUPLICATE_PLAYER_BLOCK,
                entity="Wrapper",
                entity_id=wrapper.name,
                details={
                    **base_details,
                    "player_count": str(player_count),
                },
            )
        )

    if not wrapper_has_local_or_cdn_js(content):
        violations.append(
            make_violation(
                code=FailureCode.WRAPPER_MISSING_JS,
                entity="Wrapper",
                entity_id=wrapper.name,
                details=base_details,
            )
        )

    if not wrapper_has_local_or_cdn_css(content):
        violations.append(
            make_violation(
                code=FailureCode.WRAPPER_MISSING_CSS,
                entity="Wrapper",
                entity_id=wrapper.name,
                details=base_details,
            )
        )

    return violations


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifacts", required=True)
    args = parser.parse_args()

    art_dir = Path(args.artifacts)
    violations: list[dict] = []

    casts = sorted(art_dir.glob("*.cast"))

    if not casts:
        print(json.dumps({
            "status": "fail",
            "violations": [
                make_violation(
                    code=FailureCode.NO_CAST_FILES_FOUND,
                    entity="ArtifactsDirectory",
                    entity_id=str(art_dir),
                    details={
                        "path": str(art_dir),
                    },
                )
            ]
        }, indent=2))
        return 1

    for cast in casts:
        wrapper = cast.with_suffix(cast.suffix + ".html")
        violations.extend(inspect_wrapper(cast, wrapper))

    if violations:
        print(json.dumps({"status": "fail", "violations": violations}, indent=2))
        return 1

    print(json.dumps({"status": "pass", "violations": []}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())