#!/usr/bin/env bash
set -euo pipefail
MODEL=${1:-threat-models/security-v2-r1.json}
# OWASP Threat Model Library v1.0.2, exact upstream blob verified on capture.
# CI must not rely on raw.githubusercontent.com responding on every commit.
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
SCHEMA_FILE="$SCRIPT_DIR/../schemas/owasp-threat-model-v1.0.2.schema.json"
SCHEMA_SHA256='428772fecfed799921e90bb7e7acf7ce7bb8e379128e43c4e7f4346a528539be'
[[ -f "$SCHEMA_FILE" ]] || { echo 'OWASP threat-model schema missing' >&2; exit 2; }
printf '%s  %s\n' "$SCHEMA_SHA256" "$SCHEMA_FILE" | sha256sum --check --status ||
  { echo 'OWASP threat-model schema digest mismatch' >&2; exit 3; }
uvx --from 'check-jsonschema==0.34.0' check-jsonschema --schemafile "$SCHEMA_FILE" "$MODEL"
