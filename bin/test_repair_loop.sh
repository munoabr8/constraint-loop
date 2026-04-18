#!/usr/bin/env bash
set -euo pipefail

ART_DIR="${1:-evidenceKit/evidence-kit/artifacts}"
WRAPPER_NAME="${2:-run.cast.html}"
VALIDATOR="constraint-loop/bin/check_wrapper_contents.py"
CLASSIFIER="constraint-loop/bin/classify_failure.py"
HANDLER="constraint-loop/bin/handle_failure.py"

ART_DIR="$(realpath "$ART_DIR")"
TARGET="$ART_DIR/$WRAPPER_NAME"
BACKUP="$TARGET.bak"

cleanup() {
  if [[ -f "$BACKUP" ]]; then
    mv -f "$BACKUP" "$TARGET"
  fi
}
trap cleanup EXIT

if [[ ! -f "$TARGET" ]]; then
  echo "[test] missing target wrapper: $TARGET" >&2
  exit 1
fi

cp "$TARGET" "$BACKUP"

python3 - "$TARGET" <<'PY'
from pathlib import Path
import sys

target = Path(sys.argv[1])
content = target.read_text()
if "<asciinema-player" not in content:
    raise SystemExit(f"Target wrapper already broken: {target}")
target.write_text(content.replace("<asciinema-player", "<broken-player", 1))
print(f"[test] broke wrapper: {target}")
PY

echo "[test] validator should fail before repair"
if python3 "$VALIDATOR" --artifacts "$ART_DIR"; then
  echo "[test] validator unexpectedly passed before repair" >&2
  exit 1
else
  echo "[test] pre-repair failure confirmed"
fi

echo "[test] running control loop"
if python3 "$VALIDATOR" --artifacts "$ART_DIR" | \
   python3 "$CLASSIFIER" | \
   python3 "$HANDLER"; then
  echo "[test] control loop completed"
else
  echo "[test] control loop pipeline returned nonzero (expected if validator detected failure before repair)"
fi

echo "[test] reached post-repair section"

echo "[test] validator should pass after repair"
FINAL_FILE="$(mktemp)"
python3 "$VALIDATOR" --artifacts "$ART_DIR" | tee "$FINAL_FILE"

python3 - "$FINAL_FILE" <<'PY'
import json
import sys
from pathlib import Path

data = json.loads(Path(sys.argv[1]).read_text())
if data.get("status") != "pass":
    raise SystemExit("Final validator status was not pass")
print("[test] repair loop succeeded")
PY

rm -f "$FINAL_FILE" "$BACKUP"
trap - EXIT