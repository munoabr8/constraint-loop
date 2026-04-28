#!/usr/bin/env bash
# tests/test_stress.sh
# Stress-tests the constraint loop with 50 cast files that each carry a
# repairable violation.  Every file is expected to be recovered after a
# single repair cycle.

set -euo pipefail

CAST_COUNT=50

tmpdir="$(mktemp -d)"
trap "rm -rf '$tmpdir'" EXIT

# ---------------------------------------------------------------------------
# Build fixture directory: 50 named casts, each with one repairable defect,
# cycling through four violation types so all code paths are exercised.
# ---------------------------------------------------------------------------
for i in $(seq 1 $CAST_COUNT); do
    name="recording_$(printf '%03d' "$i")"
    cast="$tmpdir/${name}.cast"
    wrapper="$tmpdir/${name}.cast.html"
    touch "$cast"

    variant=$(( (i - 1) % 4 ))

    case $variant in
      0)
        # broken-player tag → WRAPPER_MISSING_PLAYER (repairable)
        cat > "$wrapper" <<HTML
<html>
  <head>
    <link rel='stylesheet' href='./asciinema-player.min.css'>
    <script src='./asciinema-player.min.js'></script>
  </head>
  <body>
    <broken-player src='./${name}.cast'></broken-player>
  </body>
</html>
HTML
        ;;
      1)
        # missing JS tag → WRAPPER_MISSING_JS (repairable)
        cat > "$wrapper" <<HTML
<html>
  <head>
    <link rel='stylesheet' href='./asciinema-player.min.css'>
  </head>
  <body>
    <asciinema-player src='./${name}.cast'></asciinema-player>
  </body>
</html>
HTML
        ;;
      2)
        # missing CSS tag → WRAPPER_MISSING_CSS (repairable)
        cat > "$wrapper" <<HTML
<html>
  <head>
    <script src='./asciinema-player.min.js'></script>
  </head>
  <body>
    <asciinema-player src='./${name}.cast'></asciinema-player>
  </body>
</html>
HTML
        ;;
      3)
        # malformed cast ref → WRAPPER_MISSING_CAST_REF (repairable)
        cat > "$wrapper" <<HTML
<html>
  <head>
    <link rel='stylesheet' href='./asciinema-player.min.css'>
    <script src='./asciinema-player.min.js'></script>
  </head>
  <body>
    <asciinema-player src='run.cast'></asciinema-player>
  </body>
</html>
HTML
        ;;
    esac
done

touch "$tmpdir/asciinema-player.min.css"
touch "$tmpdir/asciinema-player.min.js"

# ---------------------------------------------------------------------------
# Run the constraint loop and time it
# ---------------------------------------------------------------------------
start_ts=$(date +%s)

output="$(python3 bin/run_constraint_loop.py "$tmpdir")"
rc=$?

end_ts=$(date +%s)
elapsed=$(( end_ts - start_ts ))

echo "$output"
echo "[stress] elapsed: ${elapsed}s for ${CAST_COUNT} cast files"

# ---------------------------------------------------------------------------
# Outcome assertions
# ---------------------------------------------------------------------------
if [[ "$rc" -ne 0 ]]; then
    echo "[fail] expected exit code 0, got $rc"
    exit 1
fi

echo "$output" | grep -q '"final_decision": "recovered"' || {
    echo "[fail] expected final_decision=recovered"
    exit 1
}

echo "$output" | grep -q '"repaired_any": true' || {
    echo "[fail] expected repaired_any=true"
    exit 1
}

echo "$output" | grep -q '"repair_attempt_count": 1' || {
    echo "[fail] expected repair_attempt_count=1"
    exit 1
}

echo "$output" | grep -q '"blocking_count": 0' || {
    echo "[fail] expected blocking_count=0"
    exit 1
}

echo "$output" | grep -q '"violation_count": 0' || {
    echo "[fail] expected violation_count=0 after repair"
    exit 1
}

# Violation count before repair must equal CAST_COUNT
artifact_path="$(
  OUTPUT_JSON="$output" python3 - <<'PY'
import json, os
print(json.loads(os.environ["OUTPUT_JSON"])["run_artifact"])
PY
)"

python3 - "$artifact_path" "$CAST_COUNT" <<'PY'
import json, sys
from pathlib import Path

data = json.loads(Path(sys.argv[1]).read_text())
expected_count = int(sys.argv[2])

initial_violations = len(data["check_output"]["parsed"].get("violations", []))
if initial_violations != expected_count:
    raise SystemExit(
        f"[fail] expected {expected_count} initial violations, got {initial_violations}"
    )

if data["final_decision"] != "recovered":
    raise SystemExit(
        f"[fail] artifact final_decision mismatch: {data['final_decision']}"
    )

recheck = data.get("recheck_output", {}).get("parsed", {})
if recheck.get("status") != "pass":
    raise SystemExit(
        f"[fail] expected recheck status=pass, got {recheck.get('status')}"
    )

print(f"[pass] stress test: all {expected_count} violations repaired and recovered")
PY

echo "[pass] stress test complete in ${elapsed}s"
