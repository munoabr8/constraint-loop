#!/usr/bin/env bash
set -euo pipefail

run_test() {
  local name="$1"
  local input="$2"

  echo "== $name =="
  cat "$input" | python3 bin/classify_failure.py
  echo
}

run_test "known deterministic" "tests/fixtures/check_known_deterministic.json"
run_test "known blocking" "tests/fixtures/check_known_blocking.json"
run_test "unknown" "tests/fixtures/check_unknown.json"
