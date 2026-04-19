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

echo "$output" | grep -q '"final_decision": "recovered"' || {
  echo "[fail] expected recovered"
  exit 1
}

echo "$output" | grep -q '"repaired_any": true' || {
  echo "[fail] expected repaired_any true"
  exit 1
}

echo "[pass] run_constraint_loop recovered case"
