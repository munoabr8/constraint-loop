#!/usr/bin/env bash
set -euo pipefail

ART_DIR="/Users/abrahammunoz/evidenceKit/evidence-kit/artifacts"
SNAPSHOT="/Users/abrahammunoz/evidenceKit/evidence-kit/artifacts/artifacts.snapshot.json"

echo "== run constraint loop =="
python3 bin/run_constraint_loop.py "$ART_DIR"

echo
echo "== log latest run =="
python3 bin/log_run_summary.py "$(ls -t runs/*.outcome.json | head -n 1)"

echo
echo "== export snapshot =="
python3 /Users/abrahammunoz/evidenceKit/evidence-kit/bin/export_artifact_snapshot.py \
  --artifacts "$ART_DIR" \
  --out "$SNAPSHOT"

echo
echo "== check snapshot =="
python3 bin/check_artifact_snapshot.py --snapshot "$SNAPSHOT"