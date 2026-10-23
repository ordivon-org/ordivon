#!/usr/bin/env bash
# Read-only native SQL verifier toolchain for Ubuntu 24.04 CI.
# Extraction is isolated: neither the PostgreSQL service nor osqueryd is installed.
set -euo pipefail
target="${1:?usage: install_sql_verifiers.sh ABSOLUTE_OUTPUT_DIRECTORY}"
[[ "$target" = /* ]] || { echo "SQL verifier target must be absolute" >&2; exit 2; }
scratch="$(mktemp -d "${RUNNER_TEMP:-/tmp}/ordivon-sql-verifier.XXXXXXXX")"
trap 'rm -rf -- "$scratch"' EXIT
mkdir -p "$scratch/pg" "$scratch/osquery" "$target/bin"

download() {
  local url="$1" dst="$2" expected="$3"
  if [[ -n "${ORDIVON_SQL_DIST_DIR:-}" ]]; then
    cp -- "${ORDIVON_SQL_DIST_DIR}/$(basename "$dst")" "$dst"
  else
    curl --fail --location --silent --show-error --retry 2 --connect-timeout 10 \
      --max-time 95 "$url" -o "$dst"
  fi
  local actual
  actual="$(sha256sum "$dst" | cut -d' ' -f1)"
  [[ "$actual" == "$expected" ]] ||
    { echo "SQL verifier release SHA-256 mismatch: $(basename "$dst")" >&2; exit 7; }
}

download \
 'https://apt.postgresql.org/pub/repos/apt/pool/main/p/postgresql-18/postgresql-client-18_18.6-3.pgdg24.04+1_amd64.deb' \
 "$scratch/pg-client18.6.deb" \
 '635c8cbad024be8d1208433ec902cf721ae77028e7d6b7e0231a2768ba4dacfa'
download \
 'https://github.com/osquery/osquery/releases/download/5.23.1/osquery_5.23.1-1.linux_amd64.deb' \
 "$scratch/osquery_5.23.1-1.linux_amd64.deb" \
 '1431a9a6394657eba3cdd3476a462a6fe9721fc3664a70f23efcf7e37816787a'

# Only extract package bytes; never invoke privileged .deb maintainer scripts.
ar p "$scratch/pg-client18.6.deb" data.tar.xz | tar -xJf - -C "$scratch/pg"
ar p "$scratch/osquery_5.23.1-1.linux_amd64.deb" data.tar.gz | tar -xzf - -C "$scratch/osquery"
pg="$scratch/pg/usr/lib/postgresql/18/bin/psql"
osquery="$scratch/osquery/opt/osquery/bin/osqueryd"
[[ -x "$pg" && -x "$osquery" ]] || { echo "Missing verified SQL executables" >&2; exit 8; }

# Install both Linux ELF executables in isolated toolchain target.
install -m 755 "$pg" "$target/bin/psql"
install -m 755 "$osquery" "$target/bin/osqueryi"
[[ "$("$target/bin/psql" --version)" == *' 18.6 '* ]] ||
  { echo "psql version is not PostgreSQL 18.6" >&2; exit 9; }
[[ "$("$target/bin/osqueryi" --version)" == *'5.23.1'* ]] ||
  { echo "osqueryi version is not 5.23.1" >&2; exit 9; }
echo "Verified isolated SQL executables:"
"$target/bin/psql" --version
"$target/bin/osqueryi" --version
