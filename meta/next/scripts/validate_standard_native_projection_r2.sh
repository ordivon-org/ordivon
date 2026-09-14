#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCHEMA="$ROOT/schemas/standard-native-profile-projection-v1.schema.json"
RECEIPT="${1:-$ROOT/evidence/acceptance/standard-native-enterprise-r2-dogfood-20260914.json}"
VALIDATOR="${CHECK_JSONSCHEMA:-check-jsonschema}"

command -v "$VALIDATOR" >/dev/null
TMP="$(mktemp -d /tmp/standard-native-projection.XXXXXX)"
trap 'rm -rf "$TMP"' EXIT

python - "$RECEIPT" "$TMP" <<'PY'
import json, pathlib, sys
receipt = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
out = pathlib.Path(sys.argv[2])
for case in receipt["cases"]:
    (out / f"{case['caseId']}.json").write_text(json.dumps(case, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
PY

"$VALIDATOR" --schemafile "$SCHEMA" "$TMP"/*.json >/tmp/standard-native-r2-schema-validation.log
VERSION="$($VALIDATOR --version | head -1)"
cat <<JSON
{
  "schemaVersion": 1,
  "kind": "ordivon.standard-native.enterprise-r2-schema-validation",
  "standing": "PASS",
  "validator": "${VERSION}",
  "schema": "schemas/standard-native-profile-projection-v1.schema.json",
  "instances": ["research", "runtime", "game"],
  "boundary": "This validates the thin projection shape only. It does not validate domain semantics, authority applicability, compliance or domain verdict correctness."
}
JSON
