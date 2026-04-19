#tests/test_run_artifact_schema_blocking.sh

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

artifact_path="$(
  OUTPUT_JSON="$output" python3 - <<'PY'
import json
import os

data = json.loads(os.environ["OUTPUT_JSON"])
print(data["run_artifact"])
PY
)"

python3 - "$artifact_path" <<'PY'
import json
import sys
from pathlib import Path

artifact = Path(sys.argv[1])
data = json.loads(artifact.read_text())

required_top_level = [
    "started_at",
    "artifacts_dir",
    "check_output",
    "classification_output",
    "handler_output",
    "final_status",
    "final_decision",
    "repaired_any",
]

missing = [k for k in required_top_level if k not in data]
if missing:
    raise SystemExit(f"missing top-level keys: {missing}")

if data["final_decision"] != "halt":
    raise SystemExit(f"expected final_decision=halt, got {data['final_decision']}")

if data["repaired_any"] is not False:
    raise SystemExit(f"expected repaired_any=false, got {data['repaired_any']}")

if data.get("repair_output") not in (None,):
    raise SystemExit("expected repair_output to be absent or null for blocking case")

if data.get("recheck_output") not in (None,):
    raise SystemExit("expected recheck_output to be absent or null for blocking case")

handler_parsed = data["handler_output"].get("parsed")
if not isinstance(handler_parsed, dict):
    raise SystemExit("handler_output.parsed missing or not an object")

if handler_parsed.get("final_decision") != "halt":
    raise SystemExit(
        f"expected handler_output.parsed.final_decision=halt, got {handler_parsed.get('final_decision')}"
    )

print("[pass] run artifact schema valid for blocking case")
PY