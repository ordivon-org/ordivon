#!/usr/bin/env bash
set -euo pipefail
CREDENTIAL_DIR=/etc/ordivon/gateway
CREDENTIAL="$CREDENTIAL_DIR/local-client-bearer"
DROPIN_DIR=/etc/systemd/system/ordivon-gateway.service.d
SOURCE=/opt/ordivon/gateway/current/systemd/ordivon-gateway.service.d/10-local-service-identity.example.conf
TARGET="$DROPIN_DIR/10-local-service-identity.conf"
install -d -m 0700 -o root -g root "$CREDENTIAL_DIR"
if [[ ! -e "$CREDENTIAL" ]]; then
  umask 077
  openssl rand -hex 32 > "$CREDENTIAL"
fi
[[ -f "$CREDENTIAL" && ! -L "$CREDENTIAL" ]]
[[ "$(stat -Lc '%U:%G' "$CREDENTIAL")" == 'root:root' ]]
mode=$(stat -Lc '%a' "$CREDENTIAL")
[[ "$mode" == '600' || "$mode" == '400' ]]
[[ "$(wc -c < "$CREDENTIAL")" -le 128 ]]
install -d -m 0755 "$DROPIN_DIR"
install -m 0644 "$SOURCE" "$TARGET"
systemctl daemon-reload
systemctl restart ordivon-gateway.service
ready=0
for _ in {1..40}; do
  if curl --fail --silent --show-error --max-time 1 http://127.0.0.1:8899/health >/dev/null 2>&1; then
    ready=1
    break
  fi
  sleep 0.25
done
[[ "$ready" == 1 ]]
