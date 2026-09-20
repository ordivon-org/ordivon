#!/usr/bin/env bash
set -euo pipefail
MODEL=${1:-threat-models/security-v2-r1.json}
SCHEMA_URL='https://raw.githubusercontent.com/OWASP/www-project-threat-model-library/v1.0.2/threat-model.schema.json'
SCHEMA_SHA256='428772fecfed799921e90bb7e7acf7ce7bb8e379128e43c4e7f4346a528539be'
TMP=$(mktemp)
trap 'rm -f "$TMP"' EXIT
curl -fsSLo "$TMP" "$SCHEMA_URL"
printf '%s  %s\n' "$SCHEMA_SHA256" "$TMP" | sha256sum -c - >/dev/null
uvx --from 'check-jsonschema==0.34.0' check-jsonschema --schemafile "$TMP" "$MODEL"
