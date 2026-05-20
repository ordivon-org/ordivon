#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
OUT="${ROOT}/artifacts/security"
mkdir -p "${OUT}"
cd "${ROOT}"

run_json() {
  local name="$1"
  shift
  if command -v "$1" >/dev/null 2>&1; then
    "$@" > "${OUT}/${name}.json"
  else
    printf '{"tool":"%s","status":"missing"}\n' "$1" > "${OUT}/${name}.json"
  fi
}

if cargo audit --version >/dev/null 2>&1; then
  cargo audit --json > "${OUT}/cargo-audit.json"
else
  printf '{"tool":"cargo-audit","status":"missing"}\n' > "${OUT}/cargo-audit.json"
fi

if cargo deny --version >/dev/null 2>&1; then
  cargo deny check --format json > "${OUT}/cargo-deny.json"
else
  printf '{"tool":"cargo-deny","status":"missing"}\n' > "${OUT}/cargo-deny.json"
fi

if command -v gitleaks >/dev/null 2>&1; then
  gitleaks detect --source . --redact --report-format json --report-path "${OUT}/gitleaks.json"
else
  printf '{"tool":"gitleaks","status":"missing"}\n' > "${OUT}/gitleaks.json"
fi

if command -v syft >/dev/null 2>&1; then
  syft dir:. -o cyclonedx-json="${OUT}/sbom.cdx.json"
else
  printf '{"tool":"syft","status":"missing"}\n' > "${OUT}/sbom.cdx.json"
fi

sha256sum "${OUT}"/*.json > "${OUT}/verification-summary.sha256"
