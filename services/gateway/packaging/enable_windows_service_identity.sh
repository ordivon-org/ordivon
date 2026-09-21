#!/bin/bash
set -euo pipefail

CREDENTIAL_DIR=/etc/ordivon/gateway
CLIENT_ID="$CREDENTIAL_DIR/windows-access-client-id"
CLIENT_SECRET="$CREDENTIAL_DIR/windows-access-client-secret"
DROPIN_DIR=/etc/systemd/system/ordivon-gateway.service.d
DROPIN="$DROPIN_DIR/30-windows-service-identity.conf"
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
TEMPLATE="$SCRIPT_DIR/../systemd/ordivon-gateway.service.d/30-windows-service-identity.example.conf"

for path in "$CLIENT_ID" "$CLIENT_SECRET"; do
  if [ -L "$path" ] || [ ! -f "$path" ]; then
    echo "Gateway Windows service identity credential is missing or not a regular file: $path" >&2
    exit 2
  fi
  mode=$(stat -Lc '%a' "$path")
  if [ "$mode" != "600" ]; then
    echo "Gateway Windows service identity credential must be mode 600: $path" >&2
    exit 2
  fi
  if [ "$(stat -Lc '%U:%G' "$path")" != "root:root" ]; then
    echo "Gateway Windows service identity credential must be root-owned: $path" >&2
    exit 2
  fi
done

test -f "$TEMPLATE"
install -d -m 0755 "$DROPIN_DIR"
install -m 0644 "$TEMPLATE" "$DROPIN"
systemctl daemon-reload
systemctl restart ordivon-gateway.service

for _ in $(seq 1 50); do
  if systemctl is-active --quiet ordivon-gateway.service \
    && curl -fsS --max-time 2 http://127.0.0.1:8899/health >/dev/null; then
    systemctl show ordivon-gateway.service \
      -p ActiveState -p SubState -p Result -p MainPID -p NRestarts --no-pager
    exit 0
  fi
  sleep 0.2
done

systemctl status ordivon-gateway.service --no-pager >&2 || true
exit 1
