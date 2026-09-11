#!/usr/bin/env bash
set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET="${1:-$ROOT/fixtures/smoke}"
OUT="${2:-$ROOT/artifacts}"
mkdir -p "$OUT"
rm -f "$OUT"/{gitleaks.sarif,semgrep.sarif,trivy.sarif,sbom.cdx.json,osv.json,provider-status.json}

/usr/bin/gitleaks detect --no-git --source "$TARGET" --report-format sarif --report-path "$OUT/gitleaks.sarif" --no-banner
gitleaks_rc=$?

uvx --from semgrep==1.177.0 semgrep scan --config p/python --error --sarif --output "$OUT/semgrep.sarif" "$TARGET"
semgrep_rc=$?

/usr/bin/trivy fs --quiet --scanners vuln,secret --exit-code 1 --format sarif --output "$OUT/trivy.sarif" "$TARGET"
trivy_rc=$?

/usr/bin/syft scan "dir:$TARGET" -q -o "cyclonedx-json=$OUT/sbom.cdx.json"
syft_rc=$?

/usr/bin/osv-scanner scan source -r "$TARGET" --format json > "$OUT/osv.json"
osv_rc=$?

classify_detection() {
  local rc="$1"
  if [ "$rc" -eq 0 ]; then printf 'true false';
  elif [ "$rc" -eq 1 ]; then printf 'true true';
  else printf 'false false'; fi
}
read -r gitleaks_mech gitleaks_block <<<"$(classify_detection "$gitleaks_rc")"
read -r semgrep_mech semgrep_block <<<"$(classify_detection "$semgrep_rc")"
read -r trivy_mech trivy_block <<<"$(classify_detection "$trivy_rc")"
read -r osv_mech osv_block <<<"$(classify_detection "$osv_rc")"
if [ "$syft_rc" -eq 0 ]; then syft_mech=true; else syft_mech=false; fi

cat > "$OUT/provider-status.json" <<EOF
{
  "providers": [
    {"provider":"gitleaks","exitCode":$gitleaks_rc,"mechanicalSuccess":$gitleaks_mech,"blocking":$gitleaks_block},
    {"provider":"semgrep","exitCode":$semgrep_rc,"mechanicalSuccess":$semgrep_mech,"blocking":$semgrep_block},
    {"provider":"trivy","exitCode":$trivy_rc,"mechanicalSuccess":$trivy_mech,"blocking":$trivy_block},
    {"provider":"syft","exitCode":$syft_rc,"mechanicalSuccess":$syft_mech,"blocking":false},
    {"provider":"osv-scanner","exitCode":$osv_rc,"mechanicalSuccess":$osv_mech,"blocking":$osv_block}
  ]
}
EOF

if [ "$gitleaks_mech" != true ] || [ "$semgrep_mech" != true ] || [ "$trivy_mech" != true ] || [ "$syft_mech" != true ] || [ "$osv_mech" != true ]; then
  exit 2
fi
exit 0
