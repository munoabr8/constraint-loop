#!/usr/bin/env bash
set -euo pipefail

ART_DIR="${1:?usage: $0 <artifacts-dir>}"

CHECKER="bin/check_wrapper_contents.py"
REPAIRER="bin/repair_failure.py"

run_checker() {
  python3 "$CHECKER" --artifacts "$ART_DIR"
}

json_field() {
  local json_input="$1"
  local python_expr="$2"

  OUTPUT_JSON="$json_input" python3 -c "
import json
import os

data = json.loads(os.environ['OUTPUT_JSON'])
print($python_expr)
"
}

if output="$(run_checker 2>&1)"; then
  checker_rc=0
else
  checker_rc=$?
fi

echo "$output"

status="$(json_field "$output" "data['status']")"

if [[ "$status" == "pass" ]]; then
  echo "System valid. No action taken."
  exit 0
fi

code="$(json_field "$output" "data['violations'][0]['violation_type']")"
wrapper_name="$(json_field "$output" "data['violations'][0]['entity_id']")"
wrapper_path="$ART_DIR/$wrapper_name"

echo "status=[$status]"
echo "code=[$code]"
echo "wrapper_path=[$wrapper_path]"

if [[ -z "$code" ]]; then
  echo "No failure code extracted. Aborting."
  exit 1
fi

python3 "$REPAIRER" --code "$code" --wrapper "$wrapper_path"

echo "Re-validating..."

if output="$(run_checker 2>&1)"; then
  checker_rc=0
else
  checker_rc=$?
fi

echo "$output"

status="$(json_field "$output" "data['status']")"

if [[ "$status" == "pass" ]]; then
  echo "Recovery successful."
  exit 0
fi

echo "Recovery failed."
exit 1