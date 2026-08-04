#!/bin/bash
set -e

if [ ! -f "pyproject.toml" ]; then
    exit 0
fi

repo="https://github.com/karned-rekipe/arclith.git"
ref="${ARCLITH_FRAMEWORK_REF:-${GITHUB_HEAD_REF:-main}}"

if [ "$ref" != "main" ] && ! git ls-remote --exit-code --heads "$repo" "$ref" >/dev/null 2>&1; then
    ref="main"
fi

python - "$repo" "$ref" <<'PY'
from pathlib import Path
import re
import sys

repo = sys.argv[1]
ref = sys.argv[2]
pyproject = Path("pyproject.toml")
text = pyproject.read_text(encoding="utf-8")
text = re.sub(
    r'arclith = \{ path = "\.\./(?:arclith|framework)", editable = true \}',
    f'arclith = {{ git = "{repo}", branch = "{ref}" }}',
    text,
)
pyproject.write_text(text, encoding="utf-8")
PY

echo "✓ pyproject.toml patched for CI"
grep "arclith" pyproject.toml
