#!/usr/bin/env bash
set -euo pipefail

API_BASE="${API_BASE:-http://127.0.0.1:8000}"
PROBE_BASE="${PROBE_BASE:-http://127.0.0.1:9000}"

require_command() {
	command -v "$1" >/dev/null || {
		echo "Missing command: $1" >&2
		exit 1
	}
}

require_command curl
require_command uv

request_id="$(
	uv run --frozen python - <<'PY'
import uuid

print(uuid.uuid4())
PY
)"

echo "Checking probes..."
curl -fsS "$PROBE_BASE/health" >/dev/null
curl -fsS "$PROBE_BASE/ready" >/dev/null
curl -fsS "$PROBE_BASE/info" >/dev/null

echo "Creating ingredient..."
create_response="$(
	curl -fsS -X POST "$API_BASE/v1/ingredients/" \
		-H "Content-Type: application/json" \
		-H "Idempotency-Key: demo-$request_id" \
		-H "Prefer: return=representation" \
		-d '{"name":"Farine demo Arclith"}'
)"

ingredient_id="$(
	CREATE_RESPONSE="$create_response" uv run --frozen python - <<'PY'
import json
import os

payload = json.loads(os.environ["CREATE_RESPONSE"])
print(payload["data"]["uuid"])
PY
)"

echo "Created ingredient: $ingredient_id"
curl -fsS "$API_BASE/v1/ingredients/$ingredient_id" >/dev/null
curl -fsS "$API_BASE/v1/ingredients/?name=Farine" >/dev/null
curl -fsS -X POST "$API_BASE/v1/ingredients/$ingredient_id/duplicate" \
	-H "Prefer: return=representation" >/dev/null
curl -fsS "$API_BASE/v1/ingredients/" >/dev/null

echo "Demo smoke OK"
