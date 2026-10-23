#!/bin/bash
set -euo pipefail

DROPIN_DIR=/etc/systemd/system/ordivon-gateway.service.d
DROPIN="$DROPIN_DIR/40-otel-traces.conf"
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
TEMPLATE="$SCRIPT_DIR/../systemd/ordivon-gateway.service.d/40-otel-traces.example.conf"

test -f "$TEMPLATE"
systemctl is-active --quiet vector.service
curl -fsS --max-time 2 http://127.0.0.1:3200/ready >/dev/null

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
