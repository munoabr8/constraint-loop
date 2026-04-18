#!/usr/bin/env bash
set -euo pipefail

ART_DIR="/Users/abrahammunoz/evidenceKit/evidence-kit/artifacts"
LOOP_SCRIPT="/Users/abrahammunoz/constraint-loop/bin/minimal_constraint_loop.py"
TARGET="$ART_DIR/run.cast.html"
CLEAN_BAK="$ART_DIR/run.cast.html.clean.bak"

fail() {
  echo "[FAIL] $1" >&2
  exit 1
}

restore_clean() {
  cp "$CLEAN_BAK" "$TARGET"
}

run_loop() {
  python3 "$LOOP_SCRIPT" --artifacts "$ART_DIR"
}

run_loop_no_repair() {
  python3 "$LOOP_SCRIPT" --artifacts "$ART_DIR" --no-repair
}

assert_contains() {
  local haystack="$1"
  local needle="$2"
  if [[ "$haystack" != *"$needle"* ]]; then
    fail "expected output to contain: $needle"
  fi
}

assert_not_contains() {
  local haystack="$1"
  local needle="$2"
  if [[ "$haystack" == *"$needle"* ]]; then
    fail "expected output NOT to contain: $needle"
  fi
}

break_duplicate_player() {
  python3 - <<'PY'
from pathlib import Path
import sys

p = Path("/Users/abrahammunoz/evidenceKit/evidence-kit/artifacts/run.cast.html")
text = p.read_text(encoding="utf-8", errors="ignore")

if text.count("<asciinema-player") > 1:
    print("already duplicated")
    sys.exit(0)

duplicate_block = (
    "<asciinema-player src='./run.cast' "
    "cols='auto' rows='auto' terminal-font-size='16px' "
    "speed='1' preload='true' loop='false' "
    "style='width:100%; height:100vh'></asciinema-player>\n"
)

if "</body>" not in text:
    print("expected </body> not found")
    sys.exit(1)

updated = text.replace("</body>", duplicate_block + "</body>", 1)
p.write_text(updated, encoding="utf-8")
print("changed: True")
PY
}

break_player() {
  python3 - <<'PY'
from pathlib import Path
import sys

p = Path("/Users/abrahammunoz/evidenceKit/evidence-kit/artifacts/run.cast.html")
text = p.read_text(encoding="utf-8", errors="ignore")

if "<broken-player" in text:
    print("already broken")
    sys.exit(0)

updated = text.replace("<asciinema-player", "<broken-player", 1)
if updated == text:
    print("expected player tag not found")
    sys.exit(1)

p.write_text(updated, encoding="utf-8")
print("changed: True")
PY
}

break_js() {
  python3 - <<'PY'
from pathlib import Path
import sys

p = Path("/Users/abrahammunoz/evidenceKit/evidence-kit/artifacts/run.cast.html")
text = p.read_text(encoding="utf-8", errors="ignore")

if "broken-player.min.js" in text:
    print("already broken")
    sys.exit(0)

updated = text.replace("asciinema-player.min.js", "broken-player.min.js", 1)
if updated == text:
    print("expected JS reference not found")
    sys.exit(1)

p.write_text(updated, encoding="utf-8")
print("changed: True")
PY
}

break_css() {
  python3 - <<'PY'
from pathlib import Path
import sys

p = Path("/Users/abrahammunoz/evidenceKit/evidence-kit/artifacts/run.cast.html")
text = p.read_text(encoding="utf-8", errors="ignore")

if "broken-player.min.css" in text:
    print("already broken")
    sys.exit(0)

updated = text.replace("asciinema-player.min.css", "broken-player.min.css", 1)
if updated == text:
    print("expected CSS reference not found")
    sys.exit(1)

p.write_text(updated, encoding="utf-8")
print("changed: True")
PY
}

break_cast_ref() {
  python3 - <<'PY'
from pathlib import Path
import re
import sys

p = Path("/Users/abrahammunoz/evidenceKit/evidence-kit/artifacts/run.cast.html")
text = p.read_text(encoding="utf-8", errors="ignore")

if "src='./wrong.cast'" in text or 'src="./wrong.cast"' in text:
    print("already broken")
    sys.exit(0)

patterns = [
    r"src='./run\.cast'",
    r'src="./run\.cast"',
]

updated = text
changed = False

for pat in patterns:
    new = re.sub(pat, "src='./wrong.cast'", updated, count=1)
    if new != updated:
        updated = new
        changed = True
        break

if not changed:
    print("expected cast src not found")
    sys.exit(1)

p.write_text(updated, encoding="utf-8")
print("changed: True")
PY
}

verify_clean_baseline() {
  local output
  output="$(run_loop_no_repair)"
  echo "$output"
  assert_contains "$output" '"status": "pass"'
  assert_contains "$output" '"violations": []'
}

test_case() {
  local name="$1"
  local breaker="$2"
  local expected_code="$3"

  echo
  echo "=== TEST: $name ==="

  restore_clean

  local precheck
  precheck="$(run_loop_no_repair)"
  echo "$precheck"
  assert_contains "$precheck" '"status": "pass"'

  "$breaker"

  local detect_output
  local detect_status

  set +e
  detect_output="$(run_loop_no_repair 2>&1)"
  detect_status=$?
  set -e

  echo "$detect_output"

if [[ $detect_status -eq 0 ]]; then
  fail "expected detection step to fail for $name, but it passed"
fi

 
local repair_output
local repair_status

set +e
repair_output="$(run_loop 2>&1)"
repair_status=$?
set -e

echo "$repair_output"

if [[ $repair_status -ne 0 ]]; then
  fail "expected repair step to succeed for $name"
fi

assert_contains "$repair_output" "\"code\": \"$expected_code\""
assert_contains "$repair_output" '"repaired_any": true'
assert_contains "$repair_output" '"final_status": "pass"'




  local noop_output
  noop_output="$(run_loop)"
  echo "$noop_output"
  assert_contains "$noop_output" '"status": "pass"'
  assert_contains "$noop_output" '"repaired_any": false'
  assert_contains "$noop_output" '"violations": []'
}


test_no_cast_files() {
  echo
  echo "=== TEST: no cast files ==="

  # backup and remove all .cast files
  mapfile -t CAST_FILES < <(find "$ART_DIR" -maxdepth 1 -name "*.cast")

  if [[ ${#CAST_FILES[@]} -eq 0 ]]; then
    fail "no cast files to test with"
  fi

  for f in "${CAST_FILES[@]}"; do
    mv "$f" "$f.bak"
  done

  local detect_output
  local detect_status

  set +e
  detect_output="$(run_loop_no_repair 2>&1)"
  detect_status=$?
  set -e

  echo "$detect_output"

  if [[ $detect_status -eq 0 ]]; then
    fail "expected failure when no cast files exist"
  fi

  assert_contains "$detect_output" '"code": "NO_CAST_FILES_FOUND"'

  # restore files
  for f in "${CAST_FILES[@]}"; do
    mv "$f.bak" "$f"
  done
}

main() {
  [[ -f "$LOOP_SCRIPT" ]] || fail "loop script not found: $LOOP_SCRIPT"
  [[ -f "$TARGET" ]] || fail "target wrapper not found: $TARGET"
  [[ -f "$CLEAN_BAK" ]] || fail "clean backup not found: $CLEAN_BAK"

  echo "=== VERIFY CLEAN BASELINE ==="
  restore_clean
  verify_clean_baseline

  test_case "missing player" break_player "WRAPPER_MISSING_PLAYER"
  test_case "missing js" break_js "WRAPPER_MISSING_JS"
  test_case "missing css" break_css "WRAPPER_MISSING_CSS"
  test_case "missing cast ref" break_cast_ref "WRAPPER_MISSING_CAST_REF"
test_no_cast_files
test_case "duplicate player block" break_duplicate_player "WRAPPER_DUPLICATE_PLAYER_BLOCK"
  echo
  echo "[PASS] all regression tests passed"
}

main "$@"