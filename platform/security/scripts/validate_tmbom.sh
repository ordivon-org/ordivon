#!/usr/bin/env bash
set -euo pipefail
MODEL=${1:-threat-models/security-v2-r1.json}
SCHEMA_SHA256='428772fecfed799921e90bb7e7acf7ce7bb8e379128e43c4e7f4346a528539be'
SCHEMA_URLS=(
  'https://raw.githubusercontent.com/OWASP/www-project-threat-model-library/v1.0.2/threat-model.schema.json'
  'https://cdn.jsdelivr.net/gh/OWASP/www-project-threat-model-library@v1.0.2/threat-model.schema.json'
)
TMP=$(mktemp)
trap 'rm -f "$TMP"' EXIT

schema_ready=false
for schema_url in "${SCHEMA_URLS[@]}"; do
  if curl --connect-timeout 10 --max-time 30 -fsSLo "$TMP" "$schema_url" \
    && printf '%s  %s\n' "$SCHEMA_SHA256" "$TMP" | sha256sum -c - >/dev/null; then
    schema_ready=true
    break
  fi
done

if [[ "$schema_ready" != true ]]; then
  echo "unable to fetch exact pinned TM-BOM schema from qualified carriers" >&2
  exit 1
fi

uvx --from 'check-jsonschema==0.34.0' check-jsonschema --schemafile "$TMP" "$MODEL"
