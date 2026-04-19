

#!/usr/bin/env bash


set -euo pipefail

tmpdir="$(mktemp -d)"
trap "rm -rf '$tmpdir'" EXIT

cat <<'EOF' > "$tmpdir/run.cast.html"
<html>
  <body>
    <asciinema-player></asciinema-player>
  </body>
</html>
EOF

touch "$tmpdir/run.cast"

set +e
output="$(python3 bin/run_constraint_loop.py "$tmpdir")"
rc=$?
set -e

echo "$output"

if [[ "$rc" -ne 1 ]]; then
  echo "[fail] expected exit code 1"
  exit 1
fi

echo "$output" | grep -q '"final_decision": "escalate"' || {
  echo "[fail] expected escalate"
  exit 1
}

echo "[pass] unknown escalation path works"