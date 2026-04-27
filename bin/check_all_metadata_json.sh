#!/usr/bin/env bash
set -euo pipefail

MODE="${1:-execution}"

tmp="$(mktemp)"

{
  echo '{"violations":['

  first=1

  for f in artifacts/*.meta.txt; do
    [[ -e "$f" ]] || continue

    while IFS= read -r line; do
      [[ "$line" == *'"METADATA_OK"'* ]] && continue

      if [[ "$first" -eq 0 ]]; then
        echo ','
      fi

      printf '%s' "$line"
      first=0
    done < <(bin/check_metadata.sh --mode "$MODE" "$f" || true)
  done

  echo ']}'
} > "$tmp"

python3 - "$tmp" <<'PY'
import json
import sys
from collections import Counter, defaultdict

path = sys.argv[1]

with open(path, "r", encoding="utf-8") as f:
    data = json.load(f)

violations = data.get("violations", [])

by_type = Counter(v.get("type", "UNKNOWN") for v in violations)
by_file = defaultdict(list)

for v in violations:
    file = v.get("file", "UNKNOWN")
    by_file[file].append(v)

data["summary"] = {
    "total_violations": len(violations),
    "files_with_violations": len(by_file),
    "by_type": dict(by_type),
    "by_file": {
        file: {
            "count": len(items),
            "types": sorted(set(i.get("type", "UNKNOWN") for i in items)),
            "fields": sorted(set(i.get("field") for i in items if i.get("field"))),
        }
        for file, items in sorted(by_file.items())
    },
}

print(json.dumps(data, indent=2))
PY

rm -f "$tmp"