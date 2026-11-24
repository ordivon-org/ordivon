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
  local url="$1" dst="$2" expected="$3" official_alternate="${4:-}"
  if [[ -n "${ORDIVON_SQL_DIST_DIR:-}" ]]; then
    cp -- "${ORDIVON_SQL_DIST_DIR}/$(basename "$dst")" "$dst"
  else
    # Both URLs are from the exact product publisher. Stalled CDN links
    # must not cost 3 x 95 seconds before the first verified byte.
    local endpoint fetched=false
    for endpoint in "$url" "$official_alternate"; do
      [[ -n "$endpoint" ]] || continue
      rm -f -- "$dst"
      if curl --fail --location --silent --show-error --retry 1 \
          --retry-delay 1 --connect-timeout 7 --max-time 55 \
          --speed-time 12 --speed-limit 4096 "$endpoint" -o "$dst"; then
        fetched=true
        break
      fi
    done
    if [[ "$fetched" != true ]]; then
      echo "SQL verifier official distribution unavailable: $(basename "$dst")" >&2
      return 1
    fi
  fi
  local actual
  actual="$(sha256sum "$dst" | cut -d' ' -f1)"
  [[ "$actual" == "$expected" ]] ||
    { echo "SQL verifier release SHA-256 mismatch: $(basename "$dst")" >&2; exit 7; }
}

download \
 'https://apt.postgresql.org/pub/repos/apt/pool/main/p/postgresql-18/postgresql-client-18_18.6-1.pgdg24.04+2_amd64.deb' \
 "$scratch/pg-client18.6.deb" \
 'b9d10d99a73bf7aa375be2fe36626c40499cfdf553d0ad174674a88a1b256b43' \
 'https://apt-archive.postgresql.org/pub/repos/apt/pool/main/p/postgresql-18/postgresql-client-18_18.6-1.pgdg24.04+2_amd64.deb'
download \
 'https://github.com/osquery/osquery/releases/download/5.23.1/osquery_5.23.1-1.linux_amd64.deb' \
 "$scratch/osquery_5.23.1-1.linux_amd64.deb" \
 '1431a9a6394657eba3cdd3476a462a6fe9721fc3664a70f23efcf7e37816787a' \
 'https://pkg.osquery.io/deb/osquery_5.23.1-1.linux_amd64.deb'

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
