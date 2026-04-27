#!/usr/bin/env bash
set -euo pipefail

ART_DIR="${1:-../evidenceKit/evidence-kit/artifacts}"

CHECKER="bin/check_wrapper_contents.py"
CLASSIFIER="bin/classify_failure.py"
REPAIRER="bin/repair_failure.py"

echo "[loop] checking artifacts: $ART_DIR"

set +e
CHECK_OUTPUT="$(python3 "$CHECKER" --artifacts "$ART_DIR")"
CHECK_STATUS=$?
set -e

echo "$CHECK_OUTPUT"

if [[ "$CHECK_STATUS" -eq 0 ]]; then
  echo "[loop] pass: no repair needed"
  exit 0
fi

echo "[loop] violations detected; attempting repair"

set +e
REPAIR_OUTPUT="$(
  echo "$CHECK_OUTPUT" \
    | python3 "$CLASSIFIER" \
    | python3 "$REPAIRER"
)"
REPAIR_STATUS=$?
set -e

echo "$REPAIR_OUTPUT"

echo "[loop] re-validating"

python3 "$CHECKER" --artifacts "$ART_DIR"

echo "[loop] repair loop completed successfully"