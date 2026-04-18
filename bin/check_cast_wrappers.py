#!/usr/bin/env python3

from pathlib import Path
import json
import argparse


def fail(violation: dict) -> int:
    print(json.dumps({"status": "fail", "violations": [violation]}, indent=2))
    return 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifacts", required=True)
    args = parser.parse_args()

    art_dir = Path(args.artifacts)
    violations = []

    if not art_dir.exists():
        return fail({
            "violation_type": "MISSING_DIRECTORY",
            "entity": "ArtifactDirectory",
            "entity_id": str(art_dir)
        })

    if not art_dir.is_dir():
        return fail({
            "violation_type": "NOT_A_DIRECTORY",
            "entity": "ArtifactDirectory",
            "entity_id": str(art_dir)
        })

    cast_files = sorted(art_dir.glob("*.cast"))

    if not cast_files:
        return fail({
            "violation_type": "NO_CAST_FILES",
            "entity": "ArtifactDirectory",
            "entity_id": str(art_dir)
        })

    for cast in cast_files:
        wrapper = cast.with_suffix(cast.suffix + ".html")
        if not wrapper.exists():
            violations.append({
                "violation_type": "MISSING_RELATION",
                "entity": "Cast",
                "entity_id": cast.name,
                "expected_relation": "has_wrapper",
                "expected_target": wrapper.name
            })

    if violations:
        print(json.dumps({"status": "fail", "violations": violations}, indent=2))
        return 1

    print(json.dumps({"status": "pass", "violations": []}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())