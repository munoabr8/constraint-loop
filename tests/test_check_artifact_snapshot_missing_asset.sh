#!/usr/bin/env bash
set -euo pipefail

tmpdir="$(mktemp -d)"
trap "rm -rf '$tmpdir'" EXIT

cat <<'EOF' > "$tmpdir/artifacts.snapshot.json"
{
  "generated_at": "2026-04-19T00:00:00+00:00",
  "artifacts_dir": "/tmp/fake-artifacts",
  "casts": [
    "run.cast"
  ],
  "wrappers": [
    "run.cast.html"
  ],
  "assets": [
    "asciinema-player.min.css"
  ],
  "relations": [
    {
      "cast": "run.cast",
      "wrapper": "run.cast.html"
    }
  ]
}
EOF

set +e
output="$(python3 bin/check_artifact_snapshot.py --snapshot "$tmpdir/artifacts.snapshot.json")"
rc=$?
set -e

echo "$output"

if [[ "$rc" -ne 1 ]]; then
  echo "[fail] expected exit code 1"
  exit 1
fi

echo "$output" | grep -q '"violation_type": "SNAPSHOT_REQUIRED_ASSET_MISSING"' || {
  echo "[fail] expected SNAPSHOT_REQUIRED_ASSET_MISSING"
  exit 1
}

echo "[pass] snapshot checker fails on missing required asset"