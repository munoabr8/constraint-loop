#!/usr/bin/env bash
set -euo pipefail

tmpdir="$(mktemp -d)"
trap "rm -rf '$tmpdir'" EXIT

set +e
output="$(python3 bin/run_constraint_loop.py "$tmpdir")"
rc=$?
set -e

echo "$output"

if [[ "$rc" -ne 1 ]]; then
  echo "[fail] expected exit code 1, got $rc"
  exit 1
fi

echo "$output" | grep -q '"final_decision": "halt"' || {
  echo "[fail] expected halt"
  exit 1
}

echo "[pass] run_constraint_loop blocking case"