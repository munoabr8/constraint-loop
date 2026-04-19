#!/usr/bin/env bash
set -euo pipefail

python3 - <<'PY'
from failure_codes import FailureCode
from failure_metadata import FAILURE_METADATA

enum_codes = {code.value for code in FailureCode if code.value != "UNKNOWN_FAILURE"}
metadata_codes = set(FAILURE_METADATA.keys())

missing_in_metadata = sorted(enum_codes - metadata_codes)
extra_in_metadata = sorted(metadata_codes - enum_codes)

if missing_in_metadata:
    raise SystemExit(f"Missing in metadata: {missing_in_metadata}")

if extra_in_metadata:
    raise SystemExit(f"Extra in metadata: {extra_in_metadata}")

required = {"classification", "action", "known"}

for code, meta in FAILURE_METADATA.items():
    missing_keys = sorted(required - set(meta.keys()))
    if missing_keys:
        raise SystemExit(f"{code} missing keys: {missing_keys}")

print("failure metadata matches failure codes")
PY
