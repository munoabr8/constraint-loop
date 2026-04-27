#!/usr/bin/env bash
set -euo pipefail

ART_DIR="${1:-../evidenceKit/evidence-kit/artifacts}"
TARGET="$ART_DIR/run.cast.html"
BACKUP="$TARGET.bak"

CHECKER="bin/check_wrapper_contents.py"
LOOP="bin/run_repair_loop.sh"

cleanup() {
  if [[ -f "$BACKUP" ]]; then
    echo "[test] restoring original file"
    mv "$BACKUP" "$TARGET"
  fi
}
trap cleanup EXIT

echo "[test] backing up $TARGET"
cp "$TARGET" "$BACKUP"

echo "[test] breaking wrapper head"
sed -i '' '/<head>/,/<\/head>/d' "$TARGET"

echo "[test] running checker (expect fail)"
set +e
python3 "$CHECKER" --artifacts "$ART_DIR"
CHECK_STATUS=$?
set -e

if [[ "$CHECK_STATUS" -eq 0 ]]; then
  echo "[test] ERROR: checker passed after intentional break"
  exit 1
fi

echo "[test] running repair loop"
"$LOOP" "$ART_DIR"

echo "[test] re-validating (expect pass)"
python3 "$CHECKER" --artifacts "$ART_DIR"

echo "[test] SUCCESS: wrapper head repair regression passed"