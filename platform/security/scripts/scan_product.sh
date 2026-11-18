#!/usr/bin/env bash
set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET="${1:?target repository path is required}"
OUT="${2:-$ROOT/artifacts/product}"
GITLEAKS_CONFIG="${3:-$ROOT/profiles/product/gitleaks.toml}"
mkdir -p "$OUT"
rm -f "$OUT"/{gitleaks.sarif,semgrep.sarif,trivy.sarif,sbom.cdx.json,osv.json,provider-status.json}

observed_subject_revision="$(git -C "$TARGET" rev-parse HEAD 2>/dev/null || printf 'UNKNOWN')"
# A Git commit identifies only committed bytes. Dirty/untracked source must never
# inherit HEAD's trusted revision just because rev-parse returned a SHA.
if [[ "$observed_subject_revision" != "UNKNOWN" ]] && \
   [[ -n "$(git -C "$TARGET" status --porcelain --untracked-files=all 2>/dev/null)" ]]; then
  observed_subject_revision="UNKNOWN"
fi
gitleaks_config_sha256="$(sha256sum "$GITLEAKS_CONFIG" | awk '{print $1}')"

/usr/bin/gitleaks detect --no-git --source "$TARGET" --config "$GITLEAKS_CONFIG" --exit-code 10 --report-format sarif --report-path "$OUT/gitleaks.sarif" --no-banner
gitleaks_rc=$?

uvx --from semgrep==1.177.0 semgrep scan --config p/python --error --sarif --output "$OUT/semgrep.sarif" \
  --exclude research --exclude evidence --exclude docs --exclude fixtures --exclude scenarios \
  "$TARGET"
semgrep_rc=$?

/usr/bin/trivy fs --quiet --scanners vuln,secret --exit-code 1 --format sarif --output "$OUT/trivy.sarif" \
  --skip-dirs "$TARGET/research" --skip-dirs "$TARGET/evidence" --skip-dirs "$TARGET/docs" \
  --skip-dirs "$TARGET/fixtures" --skip-dirs "$TARGET/scenarios" "$TARGET"
trivy_rc=$?

/usr/bin/syft scan "dir:$TARGET" -q \
  --exclude './research/**' --exclude './evidence/**' --exclude './docs/**' --exclude './fixtures/**' --exclude './scenarios/**' \
  -o "cyclonedx-json=$OUT/sbom.cdx.json"
syft_rc=$?

/usr/bin/osv-scanner scan source -r "$TARGET" --format json \
  --experimental-exclude research --experimental-exclude evidence --experimental-exclude docs \
  --experimental-exclude fixtures --experimental-exclude scenarios > "$OUT/osv.json"
osv_rc=$?

classify_detection() {
  local rc="$1"
  if [ "$rc" -eq 0 ]; then printf 'true false';
  elif [ "$rc" -eq 1 ]; then printf 'true true';
  else printf 'false false'; fi
}
if [ "$gitleaks_rc" -eq 0 ]; then
  gitleaks_mech=true; gitleaks_block=false
elif [ "$gitleaks_rc" -eq 10 ]; then
  gitleaks_mech=true; gitleaks_block=true
else
  gitleaks_mech=false; gitleaks_block=false
fi
read -r semgrep_mech semgrep_block <<<"$(classify_detection "$semgrep_rc")"
read -r trivy_mech trivy_block <<<"$(classify_detection "$trivy_rc")"
read -r osv_mech osv_block <<<"$(classify_detection "$osv_rc")"
if [ "$syft_rc" -eq 0 ]; then syft_mech=true; else syft_mech=false; fi

# A source checkout can also change while native providers are running.
if [[ "$observed_subject_revision" != "UNKNOWN" ]] && { \
   [[ "$(git -C "$TARGET" rev-parse HEAD 2>/dev/null || printf 'UNKNOWN')" != "$observed_subject_revision" ]] || \
   [[ -n "$(git -C "$TARGET" status --porcelain --untracked-files=all 2>/dev/null)" ]]; \
}; then
  observed_subject_revision="UNKNOWN"
fi

cat > "$OUT/provider-status.json" <<EOF
{
  "profile":"product",
  "observedSubjectRevision":"$observed_subject_revision",
  "gitleaksConfigSha256":"sha256:$gitleaks_config_sha256",
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
