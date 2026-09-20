#!/usr/bin/env bash
# Emit a GitHub Actions matrix JSON from scripts/ci/matrix.json
# Usage: matrix-from-json.sh deb|rpm
set -euo pipefail
KIND=${1:?kind}
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
FILE="$ROOT/scripts/ci/matrix.json"
python3 - "$FILE" "$KIND" <<'PY'
import json, sys
path, kind = sys.argv[1], sys.argv[2]
data = json.load(open(path, encoding="utf-8"))
cells = data[kind]
print(json.dumps({"include": cells}))
PY
