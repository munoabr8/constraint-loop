#!/usr/bin/env bash
set -euo pipefail

tmpdir="$(mktemp -d)"
trap "rm -rf '$tmpdir'" EXIT

# no cast files → blocking
set +e
output="$(python3 bin/run_constraint_loop.py "$tmpdir")"
rc=$?
set -e

echo "$output"

if [[ "$rc" -ne 1 ]]; then
  echo "[fail] expected exit code 1"
  exit 1
fi

# ---- Summary assertions ----
echo "$output" | grep -q '"final_decision": "halt"' || {
  echo "[fail] expected halt"
  exit 1
}

echo "$output" | grep -q '"violation_count": 1' || {
  echo "[fail] expected violation_count 1"
  exit 1
}

echo "$output" | grep -q '"blocking_count": 1' || {
  echo "[fail] expected blocking_count 1"
  exit 1
}

echo "$output" | grep -q '"nonblocking_count": 0' || {
  echo "[fail] expected nonblocking_count 0"
  exit 1
}

artifact_path="$(
  OUTPUT_JSON="$output" python3 - <<'PY'
import json, os
print(json.loads(os.environ["OUTPUT_JSON"])["run_artifact"])
PY
)"

python3 - "$artifact_path" <<'PY'
import json, sys
from pathlib import Path

data = json.loads(Path(sys.argv[1]).read_text())

if data["final_decision"] != "halt":
    raise SystemExit("[fail] blocking artifact mismatch")

if data.get("repaired_any"):
    raise SystemExit("[fail] should not repair in blocking case")

handler = data["handler_output"]["parsed"]

if handler.get("blocking_count") != 1:
    raise SystemExit("[fail] handler blocking_count mismatch")

print("[pass] blocking path behaves correctly")
PY