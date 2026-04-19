#!/usr/bin/env bash
set -euo pipefail

tmpdir="$(mktemp -d)"
trap "rm -rf '$tmpdir'" EXIT

cat <<'EOF' > "$tmpdir/run.cast.html"
<html>
  <head>
    <link rel='stylesheet' href='./asciinema-player.min.css'>
    <script src='./asciinema-player.min.js'></script>
  </head>
  <body>
    <broken-player src='./run.cast'></broken-player>
  </body>
</html>
EOF

touch "$tmpdir/run.cast"
touch "$tmpdir/asciinema-player.min.css"
touch "$tmpdir/asciinema-player.min.js"

output="$(python3 bin/run_constraint_loop.py "$tmpdir")"

echo "$output"

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

missing = [key for key in required_top_level if key not in data]
if missing:
    raise SystemExit(f"missing top-level keys: {missing}")

if data["final_decision"] != "recovered":
    raise SystemExit(f"expected final_decision=recovered, got {data['final_decision']}")

if data["repaired_any"] is not True:
    raise SystemExit(f"expected repaired_any=true, got {data['repaired_any']}")

if "repair_output" not in data or data["repair_output"] is None:
    raise SystemExit("missing repair_output")

if "recheck_output" not in data or data["recheck_output"] is None:
    raise SystemExit("missing recheck_output")

recheck_parsed = data["recheck_output"].get("parsed")
if not isinstance(recheck_parsed, dict):
    raise SystemExit("recheck_output.parsed missing or not an object")

if recheck_parsed.get("status") != "pass":
    raise SystemExit(f"expected recheck_output.parsed.status=pass, got {recheck_parsed.get('status')}")

check_parsed = data["check_output"].get("parsed")
if not isinstance(check_parsed, dict):
    raise SystemExit("check_output.parsed missing or not an object")

classification_parsed = data["classification_output"].get("parsed")
if not isinstance(classification_parsed, dict):
    raise SystemExit("classification_output.parsed missing or not an object")

handler_parsed = data["handler_output"].get("parsed")
if not isinstance(handler_parsed, dict):
    raise SystemExit("handler_output.parsed missing or not an object")

print("[pass] run artifact schema valid for recovered case")
PY