#!/usr/bin/env bash
set -euo pipefail

tmpdir="$(mktemp -d)"
trap "rm -rf '$tmpdir'" EXIT

cat <<'EOF' > "$tmpdir/run.cast.html"
<!doctype html>
<meta charset='utf-8'>
<title>run.cast</title>
<body>
<link rel='stylesheet' href='./asciinema-player.min.css'>
<script src='./asciinema-player.min.js'></script>
<asciinema-player src='./run.cast'></asciinema-player>
</body>
EOF

touch "$tmpdir/run.cast"
touch "$tmpdir/asciinema-player.min.css"
touch "$tmpdir/asciinema-player.min.js"

output="$(python3 bin/run_constraint_loop.py "$tmpdir")"

echo "$output" | grep -q '"violation_count": 1' || {
  echo "[fail] expected violation_count 1"
  exit 1
}

echo "$output" | grep -q '"nonblocking_count": 1' || {
  echo "[fail] expected nonblocking_count 1"
  exit 1
}

echo "$output" | grep -q '"blocking_count": 0' || {
  echo "[fail] expected blocking_count 0"
  exit 1
}

echo "$output"

artifact_path="$(
  OUTPUT_JSON="$output" python3 - <<'PY'
import json, os
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

# ---- Assertions ----

if data["final_decision"] != "no_repair_path":
    raise SystemExit(f"[fail] expected final_decision=no_repair_path, got {data['final_decision']}")

handler = data["handler_output"]["parsed"]

if handler.get("nonblocking_count", 0) <= 0:
    raise SystemExit("[fail] expected nonblocking_count > 0")

if handler.get("blocking_count") != 0:
    raise SystemExit("[fail] expected blocking_count == 0")

if handler.get("unknown_count") != 0:
    raise SystemExit("[fail] expected unknown_count == 0")

nonblocking = handler.get("nonblocking_failures", [])

if not any(f.get("code") == "WRAPPER_MISSING_HEAD_STRUCTURE" for f in nonblocking):
    raise SystemExit("[fail] expected WRAPPER_MISSING_HEAD_STRUCTURE in nonblocking_failures")

print("[pass] nonblocking path behaves correctly")
PY