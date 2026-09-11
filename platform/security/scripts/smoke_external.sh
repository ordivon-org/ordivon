#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="$ROOT/artifacts"
TARGET="$ROOT/fixtures/smoke"
mkdir -p "$OUT"

/usr/bin/gitleaks detect --no-git --source "$TARGET" --exit-code 0 --report-format sarif --report-path "$OUT/gitleaks.sarif" --no-banner
uvx --from semgrep==1.177.0 semgrep scan --config p/python --sarif --output "$OUT/semgrep.sarif" "$TARGET"
/usr/bin/trivy fs --quiet --scanners vuln,secret --exit-code 0 --format sarif --output "$OUT/trivy.sarif" "$TARGET"
/usr/bin/syft scan "dir:$TARGET" -q -o "cyclonedx-json=$OUT/sbom.cdx.json"
/usr/bin/osv-scanner scan source -r "$TARGET" --format json > "$OUT/osv.json"
