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
    <asciinema-player src='./run.cast'></asciinema-player>
    <asciinema-player src='./run.cast'></asciinema-player>
  </body>
</html>
EOF

touch "$tmpdir/run.cast"
touch "$tmpdir/asciinema-player.min.css"
touch "$tmpdir/asciinema-player.min.js"

set +e
output="$(python3 bin/run_constraint_loop.py "$tmpdir")"
rc=$?
set -e

echo "$output"

if [[ "$rc" -ne 1 ]]; then
  echo "[fail] expected exit code 1, got $rc"
  exit 1
fi

echo "$output" | grep -q '"final_decision": "escalate"' || {
  echo "[fail] expected escalate"
  exit 1
}

echo "[pass] run_constraint_loop unknown case"
