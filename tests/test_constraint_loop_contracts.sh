#!/usr/bin/env bash
set -euo pipefail

pass() {
  printf '[pass] %s\n' "$1"
}

fail() {
  printf '[fail] %s\n' "$1" >&2
  exit 1
}

cleanup() {
  local dir="${1:-}"
  [[ -n "$dir" ]] && rm -rf "$dir"
}

assert_exit_code() {
  local expected="$1"
  local actual="$2"
  local label="$3"

  if [[ "$actual" -ne "$expected" ]]; then
    fail "$label: expected exit code $expected, got $actual"
  fi
}

assert_file_contains() {
  local needle="$1"
  local file="$2"
  local label="$3"

  if ! grep -q "$needle" "$file"; then
    fail "$label: expected '$needle' in $file"
  fi
}

assert_file_not_contains() {
  local needle="$1"
  local file="$2"
  local label="$3"

  if grep -q "$needle" "$file"; then
    fail "$label: did not expect '$needle' in $file"
  fi
}

assert_json_contains() {
  local needle="$1"
  local file="$2"
  local label="$3"

  if ! grep -q "$needle" "$file"; then
    fail "$label: expected JSON output to contain '$needle'"
  fi
}

run_pipeline_capture() {
  local input_file="$1"
  local output_file="$2"

  set +e
  cat "$input_file" \
    | python3 bin/classify_failure.py \
    | python3 bin/handle_failure.py > "$output_file"
  local rc=$?
  set -e

  return "$rc"
}

run_repair_capture() {
  local input_file="$1"
  local output_file="$2"

  set +e
  cat "$input_file" | python3 bin/repair_failure.py > "$output_file"
  local rc=$?
  set -e

  return "$rc"
}

main() {
  local tmpdir
  tmpdir="$(mktemp -d)"
  trap "cleanup '$tmpdir'" EXIT

  local blocking_out="$tmpdir/blocking.json"
  local unknown_out="$tmpdir/unknown.json"
  local repair_unknown_out="$tmpdir/repair_unknown.json"
  local repair_known_out="$tmpdir/repair_known.json"
  local rc

  printf '== blocking path exits 1 ==\n'
  if run_pipeline_capture "tests/fixtures/check_known_blocking.json" "$blocking_out"; then
    fail "blocking path: expected nonzero exit"
  else
    rc=$?
    assert_exit_code 1 "$rc" "blocking path"
  fi
  assert_json_contains '"status": "blocked"' "$blocking_out" "blocking path"
  assert_json_contains '"code": "NO_CAST_FILES_FOUND"' "$blocking_out" "blocking path"
  pass "blocking path exits 1 and reports blocked"

  printf '== unknown path exits 1 ==\n'
  if run_pipeline_capture "tests/fixtures/check_unknown.json" "$unknown_out"; then
    fail "unknown path: expected nonzero exit"
  else
    rc=$?
    assert_exit_code 1 "$rc" "unknown path"
  fi
  assert_json_contains '"status": "escalate"' "$unknown_out" "unknown path"
  assert_json_contains '"code": "UNKNOWN_FAILURE"' "$unknown_out" "unknown path"
  pass "unknown path exits 1 and reports escalate"

  printf '== repair unknown exits 1 ==\n'
  if run_repair_capture "tests/fixtures/classified_unknown.json" "$repair_unknown_out"; then
    fail "repair unknown: expected nonzero exit"
  else
    rc=$?
    assert_exit_code 1 "$rc" "repair unknown"
  fi
  assert_json_contains '"repaired_any": false' "$repair_unknown_out" "repair unknown"
  assert_json_contains '"reason": "Refusing to repair unknown failure"' "$repair_unknown_out" "repair unknown"
  pass "repair unknown exits 1 and refuses repair"

  printf '== deterministic repair exits 0 and changes file ==\n'
  local repair_dir="$tmpdir/repairable"
  mkdir -p "$repair_dir"
  local wrapper="$repair_dir/run.cast.html"

  cat <<'EOF' > "$wrapper"
<html>
  <body>
    <broken-player src="run.cast"></broken-player>
  </body>
</html>
EOF

  cat > "$tmpdir/classified_repairable.json" <<EOF
{
  "status": "fail",
  "classifications": [
    {
      "status": "fail",
      "known": true,
      "code": "WRAPPER_MISSING_PLAYER",
      "entity": "Wrapper",
      "entity_id": "run.cast.html",
      "details": {
        "path": "$wrapper"
      },
      "classification": "known_deterministic",
      "action": "regenerate_wrappers"
    }
  ]
}
EOF

  if run_repair_capture "$tmpdir/classified_repairable.json" "$repair_known_out"; then
    rc=0
  else
    rc=$?
    fail "deterministic repair: expected exit code 0, got $rc"
  fi

  assert_json_contains '"repaired_any": true' "$repair_known_out" "deterministic repair"
  assert_file_contains '<asciinema-player' "$wrapper" "deterministic repair"
  assert_file_not_contains 'broken-player' "$wrapper" "deterministic repair"
  pass "deterministic repair exits 0 and changes file"

  printf '\nAll contract tests passed.\n'
}

main "$@"