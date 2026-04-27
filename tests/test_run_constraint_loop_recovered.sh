 #!/usr/bin/env bash
 #test_run_constraint_loop_recovered.sh

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

echo "$output" | grep -q '"final_decision": "recovered"' || {
  echo "[fail] expected recovered"
  exit 1
}

echo "$output" | grep -q '"repaired_any": true' || {
  echo "[fail] expected repaired_any true"
  exit 1
}

echo "$output" | grep -q '"violation_count": 0' || {
  echo "[fail] expected violation_count 0 after repair"
  exit 1
}

echo "$output" | grep -q '"repair_attempt_count": 1' || {
  echo "[fail] expected repair_attempt_count 1"
  exit 1
}

echo "$output" | grep -q '"blocking_count": 0' || {
  echo "[fail] expected blocking_count 0"
  exit 1
}

artifact_path="$(
  OUTPUT_JSON="$output" python3 - <<'PY'
import json, os
print(json.loads(os.environ["OUTPUT_JSON"])["run_artifact"])
PY
)"

python3 - "$artifact_path" <<'PY'
import json
import sys
from pathlib import Path

data = json.loads(Path(sys.argv[1]).read_text())

if data["final_decision"] != "recovered":
    raise SystemExit("[fail] recovered artifact mismatch")

if not data.get("repaired_any"):
    raise SystemExit("[fail] expected repaired_any true")

recheck = data.get("recheck_output", {}).get("parsed", {})
if recheck.get("status") != "pass":
    raise SystemExit("[fail] expected recheck pass")

print("[pass] recovered path behaves correctly")
PY