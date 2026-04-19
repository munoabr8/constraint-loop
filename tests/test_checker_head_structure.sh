#!/usr/bin/env bash
set -euo pipefail

tmpdir="$(mktemp -d)"
trap "rm -rf '$tmpdir'" EXIT

cat <<'EOF' > "$tmpdir/run.cast.html"
<html>
  <body>
    <link rel='stylesheet' href='./asciinema-player.min.css'>
    <script src='./asciinema-player.min.js'></script>
    <asciinema-player src='./run.cast'></asciinema-player>
  </body>
</html>
EOF

touch "$tmpdir/run.cast"

set +e
output="$(python3 bin/check_wrapper_contents.py --artifacts "$tmpdir")"
rc=$?
set -e

echo "$output"

if [[ "$rc" -ne 1 ]]; then
  echo "[fail] expected checker exit code 1, got $rc"
  exit 1
fi

echo "$output" | grep -q '"violation_type": "WRAPPER_MISSING_HEAD_STRUCTURE"' || {
  echo "[fail] expected WRAPPER_MISSING_HEAD_STRUCTURE"
  exit 1
}

echo "[pass] checker detects missing head structure"