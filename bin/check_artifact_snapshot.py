#!/usr/bin/env python3

import argparse
import json
import sys
from pathlib import Path


def violation(code: str, entity: str, entity_id: str, details: dict | None = None) -> dict:
    return {
        "violation_type": code,
        "entity": entity,
        "entity_id": entity_id,
        "details": details or {},
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshot", required=True)
    args = parser.parse_args()

    snapshot_path = Path(args.snapshot).resolve()

    if not snapshot_path.exists():
        print(json.dumps({
            "status": "fail",
            "violations": [
                violation(
                    "SNAPSHOT_FILE_MISSING",
                    "Snapshot",
                    str(snapshot_path),
                    {"path": str(snapshot_path)},
                )
            ]
        }, indent=2))
        return 1

    data = json.loads(snapshot_path.read_text(encoding="utf-8"))

    casts = set(data.get("casts", []))
    wrappers = set(data.get("wrappers", []))
    assets = set(data.get("assets", []))
    relations = data.get("relations", [])

    violations = []

    # Invariant 1: every cast should have a wrapper relation
    related_casts = {r.get("cast") for r in relations}
    for cast in sorted(casts):
        if cast not in related_casts:
            violations.append(
                violation(
                    "SNAPSHOT_CAST_MISSING_RELATION",
                    "Cast",
                    cast,
                    {"cast": cast},
                )
            )

    # Invariant 2: relation wrapper must exist in wrappers
    for rel in relations:
        cast = rel.get("cast")
        wrapper = rel.get("wrapper")

        if wrapper not in wrappers:
            violations.append(
                violation(
                    "SNAPSHOT_RELATION_WRAPPER_MISSING",
                    "Relation",
                    f"{cast}->{wrapper}",
                    {"cast": cast, "wrapper": wrapper},
                )
            )

    # Invariant 3: relation cast must exist in casts
    for rel in relations:
        cast = rel.get("cast")
        wrapper = rel.get("wrapper")

        if cast not in casts:
            violations.append(
                violation(
                    "SNAPSHOT_RELATION_CAST_MISSING",
                    "Relation",
                    f"{cast}->{wrapper}",
                    {"cast": cast, "wrapper": wrapper},
                )
            )

    # Invariant 4: no duplicate cast-wrapper relations
    seen = set()
    for rel in relations:
        pair = (rel.get("cast"), rel.get("wrapper"))
        if pair in seen:
            violations.append(
                violation(
                    "SNAPSHOT_DUPLICATE_RELATION",
                    "Relation",
                    f"{pair[0]}->{pair[1]}",
                    {"cast": pair[0], "wrapper": pair[1]},
                )
            )
        seen.add(pair)

        
    # Invariant 6: every wrapper must appear in exactly one relation
    wrapper_counts = {w: 0 for w in wrappers}

    for rel in relations:
        wrapper = rel.get("wrapper")
        if wrapper in wrapper_counts:
            wrapper_counts[wrapper] += 1

    for wrapper, count in sorted(wrapper_counts.items()):
        if count == 0:
            violations.append(
                violation(
                    "SNAPSHOT_WRAPPER_MISSING_RELATION",
                    "Wrapper",
                    wrapper,
                    {"wrapper": wrapper},
                )
            )
        elif count > 1:
            violations.append(
                violation(
                    "SNAPSHOT_WRAPPER_MULTIPLE_RELATIONS",
                    "Wrapper",
                    wrapper,
                    {"wrapper": wrapper, "count": count},
                )
            )



    # Invariant 5: required shared assets exist
    required_assets = {
        "asciinema-player.min.js",
        "asciinema-player.min.css",
    }
    for asset in sorted(required_assets):
        if asset not in assets:
            violations.append(
                violation(
                    "SNAPSHOT_REQUIRED_ASSET_MISSING",
                    "Asset",
                    asset,
                    {"asset": asset},
                )
            )

    if violations:
        print(json.dumps({
            "status": "fail",
            "violations": violations,
        }, indent=2))
        return 1

    print(json.dumps({
        "status": "pass",
        "violations": [],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())