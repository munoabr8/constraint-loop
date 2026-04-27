#!/usr/bin/env python3

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
CHECK_FS = ROOT / "bin" / "check_wrapper_contents.py"
CHECK_SNAPSHOT = ROOT / "bin" / "check_artifact_snapshot.py"


def run(cmd):
    result = subprocess.run(cmd, capture_output=True, text=True)
    try:
        parsed = json.loads(result.stdout)
    except:
        parsed = None
    return result.returncode, parsed, result.stdout


def main():
    if len(sys.argv) != 3:
        print("usage: compare_checks.py <artifacts_dir> <snapshot_file>")
        sys.exit(1)

    artifacts = sys.argv[1]
    snapshot = sys.argv[2]

    fs_rc, fs_parsed, fs_out = run([
        "python3", str(CHECK_FS), "--artifacts", artifacts
    ])

    snap_rc, snap_parsed, snap_out = run([
        "python3", str(CHECK_SNAPSHOT), "--snapshot", snapshot
    ])

    print("=== filesystem checker ===")
    print(fs_out)

    print("\n=== snapshot checker ===")
    print(snap_out)

    fs_violations = fs_parsed.get("violations", []) if fs_parsed else []
    snap_violations = snap_parsed.get("violations", []) if snap_parsed else []

    print("\n=== summary ===")
    print(f"filesystem violations: {len(fs_violations)}")
    print(f"snapshot violations: {len(snap_violations)}")

    fs_types = {v["violation_type"] for v in fs_violations}
    snap_types = {v["violation_type"] for v in snap_violations}

    print("\nmissing in snapshot checker:")
    print(sorted(fs_types - snap_types))

    print("\nextra in snapshot checker:")
    print(sorted(snap_types - fs_types))


if __name__ == "__main__":
    main()