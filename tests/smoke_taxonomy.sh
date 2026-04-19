#!/usr/bin/env bash
set -euo pipefail

# run_test() {
#   local name="$1"
#   local input="$2"

#   echo "== $name =="
#   cat "$input" | python3 bin/classify_failure.py
#   echo
# }

# run_test "known deterministic" "tests/fixtures/check_known_deterministic.json"
# run_test "known blocking" "tests/fixtures/check_known_blocking.json"
# run_test "unknown" "tests/fixtures/check_unknown.json"

 
fail() {
  printf '[fail] %s\n' "$1" >&2
  exit 1
}

pass() {
  printf '[pass] %s\n' "$1"
}

assert_contains() {
  local needle="$1"
  local haystack="$2"
  local label="$3"

  echo "$haystack" | grep -q "$needle" || fail "$label: missing $needle"
}

### known deterministic
echo "== known deterministic =="

out="$(
  cat tests/fixtures/check_known_deterministic.json \
  | python3 bin/classify_failure.py
)"

echo "$out"
assert_contains '"action": "repair_wrapper"' "$out" "known deterministic"
assert_contains '"code": "WRAPPER_MISSING_PLAYER"' "$out" "known deterministic"
assert_contains '"classification": "known_deterministic"' "$out" "known deterministic"

pass "known deterministic classification correct"


### known blocking
echo "== known blocking =="

out="$(
  cat tests/fixtures/check_known_blocking.json \
  | python3 bin/classify_failure.py
)"

echo "$out"

assert_contains '"code": "NO_CAST_FILES_FOUND"' "$out" "known blocking"
assert_contains '"classification": "known_blocking"' "$out" "known blocking"

pass "known blocking classification correct"


### unknown
echo "== unknown =="

out="$(
  cat tests/fixtures/check_unknown.json \
  | python3 bin/classify_failure.py
)"

echo "$out"

assert_contains '"code": "UNKNOWN_FAILURE"' "$out" "unknown"
assert_contains '"classification": "unknown"' "$out" "unknown"

pass "unknown classification correct"

echo
echo "smoke taxonomy assertions passed"