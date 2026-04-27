#!/usr/bin/env bash
set -euo pipefail

ART_DIR="../evidenceKit/evidence-kit/artifacts"
TARGET="$ART_DIR/run.cast.html"
BACKUP="$TARGET.bak"

echo "[test] backing up $TARGET"
cp "$TARGET" "$BACKUP"

cleanup() {
  echo "[test] restoring original file"
  mv "$BACKUP" "$TARGET"
}
trap cleanup EXIT

echo "[test] breaking wrapper head"
# remove head section (simulate failure)
sed -i '' '/<head>/,/<\/head>/d' "$TARGET"

echo "[test] running checker (expect fail)"
python3 bin/check_wrapper_contents.py --artifacts "$ART_DIR"

echo "[test] running full loop"
python3 bin/check_wrapper_contents.py --artifacts "$ART_DIR" \
  | python3 bin/classify_failure.py \
  | python3 bin/repair_failure.py

echo "[test] re-validating (expect pass)"
python3 bin/check_wrapper_contents.py --artifacts "$ART_DIR"

echo "[test] SUCCESS if pass above"