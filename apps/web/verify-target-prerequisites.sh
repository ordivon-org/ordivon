#!/usr/bin/env bash
# Fail before building if native candidate qualification cannot execute.
# No dependency installation or production database discovery.
set -euo pipefail
for tool in initdb pg_ctl postgres psql pg_dump pg_restore; do
  if ! command -v "$tool" >/dev/null; then
    echo "WEB_TARGET_PREREQUISITE_MISSING: $tool (native PostgreSQL 18)" >&2
    exit 1
  fi
  version=$("$tool" --version)
  if [[ ! "$version" =~ [[:space:]]18\. ]]; then
    echo "WEB_TARGET_PREREQUISITE_INVALID: $version (require native PostgreSQL 18)" >&2
    exit 1
  fi
done
cargo nextest --version
rustc --version
opa version
node --version
pnpm --version
if [[ $(id -u) == 0 ]]; then
  command -v runuser >/dev/null
  id postgres >/dev/null
fi
echo "Web target native prerequisites present; real Chromium launch still mandatory in verify:operator"
