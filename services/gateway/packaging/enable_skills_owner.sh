#!/bin/bash
set -euo pipefail

CREDENTIAL=/etc/ordivon/skills-mcp.token
DROPIN_DIR=/etc/systemd/system/ordivon-gateway.service.d
DROPIN="$DROPIN_DIR/50-skills-owner.conf"
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
TEMPLATE="$SCRIPT_DIR/../systemd/ordivon-gateway.service.d/50-skills-owner.example.conf"

if [ -L "$CREDENTIAL" ] || [ ! -f "$CREDENTIAL" ]; then
  echo "Gateway Skills owner credential is missing or not a regular file: $CREDENTIAL" >&2
  exit 2
fi
mode=$(stat -Lc '%a' "$CREDENTIAL")
if [ "$mode" != "600" ] && [ "$mode" != "400" ]; then
  echo "Gateway Skills owner credential must be mode 600 or 400: $CREDENTIAL" >&2
  exit 2
fi
if [ "$(stat -Lc '%U:%G' "$CREDENTIAL")" != "root:root" ]; then
  echo "Gateway Skills owner credential must be root-owned: $CREDENTIAL" >&2
  exit 2
fi

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
