#!/usr/bin/env bash
set -euo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)
MODE_MARKER=/etc/network-v2/gluetun/m4-owned-mode.selected
STATE_ROOT=/var/lib/network-v2/m4-cold-replacement
IMAGE='docker.io/qmcgaw/gluetun@sha256:1baa76576dea1dfbafbd62bb635daf40fd87171f63273c2fdfe630418783011e'
SUBSTRATE=network-v2-browserless.target
LEGACY_WG=network-v2-browserless-wireguard.service
LEGACY_DNS=network-v2-browserless-dns.service
LEGACY_CARRIER=network-v2-browserless-provider-carrier.service
LEGACY_TARGET=network-v2-browserless-legacy-provider.target
OWNED_TARGET=network-v2-gluetun-owned.target
OWNED=network-v2-gluetun-owned.service
OWNED_ADAPTER=network-v2-gluetun-owned-adapter.service
CTR=network-v2-gluetun-owned-r1
CONSEQUENCE="$ROOT/capabilities/gluetun/acceptance/candidate-consequence.sh"
BROWSERLESS_PREPARE="$ROOT/../../services/harness/scripts/browserless_podman_deploy.py"

CONSUMER_UNITS=(
  network-v2-chat-ingress-proxy.service
  network-v2-claude-proxy.service
  network-v2-windows-real-chrome-proxy.service
  network-v2-finance-egress.service
  network-v2-model-provider-egress.service
  network-v2-supply-chain-egress.service
  network-v2-x-reality-egress.service
)

MANAGED_PATHS=(
  etc/systemd/system/network-v2-browserless.target
  etc/systemd/system/network-v2-browserless-wireguard.service
  etc/systemd/system/network-v2-browserless-legacy-provider.target
  etc/systemd/system/network-v2-gluetun-owned.target
  etc/systemd/system/network-v2-gluetun-owned-adapter.service
  etc/systemd/system/network-v2-gluetun-legacy-restore.service
  etc/containers/systemd/network-v2-gluetun-owned.container
  etc/containers/systemd/network-v2-gluetun-owned.network
  usr/local/libexec/network-v2/provider-identity-exclusive
  usr/local/libexec/network-v2/m4-owned-restore-legacy
  usr/local/libexec/network-v2/browserless-provider-carrier-ready
  etc/network-v2/browserless/provider-carrier-gluetun-candidate.json
  etc/network-v2/gluetun/serialized-candidate.env
  etc/network-v2/chat-ingress/sing-box.json
  etc/systemd/system/network-v2-chat-ingress-proxy.service
  etc/network-v2/claude/sing-box.json
  etc/systemd/system/network-v2-claude-proxy.service
  etc/network-v2/windows-real-chrome/sing-box.json
  etc/systemd/system/network-v2-windows-real-chrome-proxy.service
  etc/systemd/system/network-v2-finance-egress.service
  etc/systemd/system/network-v2-model-provider-egress.service
  etc/systemd/system/network-v2-supply-chain-egress.service
  etc/systemd/system/network-v2-x-reality-egress.service
  etc/ordivon/agent-automation-browserless.json
  etc/ordivon/browser-use-browserless.json
)

usage() {
  echo "usage: $0 --preflight | --execute | --rollback STATE_DIR" >&2
  exit 64
}

wg_totals() {
  ip netns exec nv2-browserless-prod wg show nv2blwg transfer 2>/dev/null \
    | awk '{rx+=$2; tx+=$3} END{printf "%d %d\n",rx,tx}' || printf '0 0\n'
}

targeted_established() {
  {
    ss -Htn state established 2>/dev/null || true
    ip netns exec nv2-browserless-prod ss -Htn state established 2>/dev/null || true
  } | awk '$4 ~ /:(19680|19682|19581|19881|19480|19780|19080)$/ || $5 ~ /:(19680|19682|19581|19881|19480|19780|19080)$/ {n++} END{print n+0}'
}

preflight() {
  podman image exists "$IMAGE"
  test -x "$CONSEQUENCE"
  systemctl is-active --quiet "$SUBSTRATE"
  systemctl is-active --quiet "$LEGACY_WG"
  systemctl is-active --quiet "$LEGACY_CARRIER"
  test ! -e "$MODE_MARKER"
  if podman container exists "$CTR" >/dev/null 2>&1; then
    echo "owned Gluetun container already exists" >&2
    return 43
  fi

  local established before_rx before_tx after_rx after_tx
  established=$(targeted_established)
  read -r before_rx before_tx < <(wg_totals)
  sleep 2
  read -r after_rx after_tx < <(wg_totals)
  printf '{"schemaVersion":1,"kind":"ordivon.network-v2.cold-replacement-preflight","standing":"%s","targetedEstablished":%s,"wgRxDelta":%s,"wgTxDelta":%s,"legacyActive":true,"ownedContainerAbsent":true}\n' \
    "$([ "$established" -eq 0 ] && echo READY || echo BUSY)" \
    "$established" "$((after_rx-before_rx))" "$((after_tx-before_tx))"
  test "$established" -eq 0
}

snapshot() {
  local state=$1
  install -d -m 0700 "$state"
  : >"$state/existing.txt"
  for p in "${MANAGED_PATHS[@]}"; do
    test -e "/$p" || test -L "/$p" || continue
    printf '%s\n' "$p" >>"$state/existing.txt"
  done
  if test -s "$state/existing.txt"; then
    tar --numeric-owner -C / -cpf "$state/backup.tar" -T "$state/existing.txt"
  else
    tar -C / -cpf "$state/backup.tar" --files-from /dev/null
  fi
  : >"$state/active-consumers.txt"
  for unit in "${CONSUMER_UNITS[@]}"; do
    systemctl is-active --quiet "$unit" && printf '%s\n' "$unit" >>"$state/active-consumers.txt" || true
  done
  sha256sum "$state/backup.tar" >"$state/backup.tar.sha256"
}

install_candidate_bytes() {
  install -d -m 0755 /etc/network-v2/browserless /etc/network-v2/gluetun /etc/containers/systemd /usr/local/libexec/network-v2

  install -m 0644 "$ROOT/capabilities/gluetun/m4-source/network-v2-browserless.target" /etc/systemd/system/network-v2-browserless.target
  install -m 0644 "$ROOT/capabilities/gluetun/m4-source/network-v2-browserless-wireguard.service" /etc/systemd/system/network-v2-browserless-wireguard.service
  install -m 0644 "$ROOT/capabilities/gluetun/m4-source/network-v2-browserless-legacy-provider.target" /etc/systemd/system/network-v2-browserless-legacy-provider.target
  install -m 0644 "$ROOT/capabilities/gluetun/m4-source/network-v2-gluetun-owned.target" /etc/systemd/system/network-v2-gluetun-owned.target
  install -m 0644 "$ROOT/capabilities/gluetun/m4-source/network-v2-gluetun-owned-adapter.service" /etc/systemd/system/network-v2-gluetun-owned-adapter.service
  install -m 0644 "$ROOT/capabilities/gluetun/m4-source/network-v2-gluetun-legacy-restore.service" /etc/systemd/system/network-v2-gluetun-legacy-restore.service
  install -m 0644 "$ROOT/capabilities/gluetun/m4-source/network-v2-gluetun-owned.container" /etc/containers/systemd/network-v2-gluetun-owned.container
  install -m 0644 "$ROOT/capabilities/gluetun/m4-source/network-v2-gluetun-owned.network" /etc/containers/systemd/network-v2-gluetun-owned.network
  install -m 0755 "$ROOT/capabilities/gluetun/m4-source/provider-identity-exclusive" /usr/local/libexec/network-v2/provider-identity-exclusive
  install -m 0755 "$ROOT/capabilities/gluetun/m4-source/m4-owned-restore-legacy" /usr/local/libexec/network-v2/m4-owned-restore-legacy
  install -m 0755 "$ROOT/consumers/browserless/provider-carrier-ready.sh" /usr/local/libexec/network-v2/browserless-provider-carrier-ready
  install -m 0644 "$ROOT/consumers/browserless/config/provider-carrier-gluetun-candidate.json" /etc/network-v2/browserless/provider-carrier-gluetun-candidate.json
  install -m 0644 "$ROOT/capabilities/gluetun/config/serialized-candidate.env" /etc/network-v2/gluetun/serialized-candidate.env

  install -m 0644 "$ROOT/consumers/chat-ingress/config/sing-box.json" /etc/network-v2/chat-ingress/sing-box.json
  install -m 0644 "$ROOT/consumers/chat-ingress/systemd/network-v2-chat-ingress-proxy.service" /etc/systemd/system/network-v2-chat-ingress-proxy.service
  install -m 0644 "$ROOT/consumers/claude/config/sing-box.json" /etc/network-v2/claude/sing-box.json
  install -m 0644 "$ROOT/consumers/claude/systemd/network-v2-claude-proxy.service" /etc/systemd/system/network-v2-claude-proxy.service
  install -m 0644 "$ROOT/consumers/windows-real-chrome/config/sing-box.json" /etc/network-v2/windows-real-chrome/sing-box.json
  install -m 0644 "$ROOT/consumers/windows-real-chrome/systemd/network-v2-windows-real-chrome-proxy.service" /etc/systemd/system/network-v2-windows-real-chrome-proxy.service
  install -m 0644 "$ROOT/consumers/finance/systemd/network-v2-finance-egress.service" /etc/systemd/system/network-v2-finance-egress.service
  install -m 0644 "$ROOT/consumers/model-provider/systemd/network-v2-model-provider-egress.service" /etc/systemd/system/network-v2-model-provider-egress.service
  install -m 0644 "$ROOT/consumers/supply-chain/systemd/network-v2-supply-chain-egress.service" /etc/systemd/system/network-v2-supply-chain-egress.service
  install -m 0644 "$ROOT/consumers/x-reality/systemd/network-v2-x-reality-egress.service" /etc/systemd/system/network-v2-x-reality-egress.service

  python3 "$BROWSERLESS_PREPARE" --prepare >/dev/null
  systemctl daemon-reload
}

wait_owned_ready() {
  for _ in $(seq 1 160); do
    if systemctl is-active --quiet "$OWNED" \
      && systemctl is-active --quiet "$OWNED_ADAPTER" \
      && nc -z -w1 10.252.246.1 19682 >/dev/null 2>&1; then
      return 0
    fi
    sleep 0.25
  done
  systemctl status "$OWNED" "$OWNED_ADAPTER" --no-pager >&2 || true
  podman logs --tail 120 "$CTR" >&2 || true
  return 71
}

restart_recorded_consumers() {
  local state=$1
  while IFS= read -r unit; do
    test -n "$unit" || continue
    systemctl restart "$unit"
    systemctl is-active --quiet "$unit"
  done <"$state/active-consumers.txt"
}

consumer_checks() {
  /usr/local/libexec/network-v2/browserless-provider-carrier-ready
  test -x /usr/local/libexec/network-v2/model-provider-ready && /usr/local/libexec/network-v2/model-provider-ready
  test -x /usr/local/libexec/network-v2/supply-chain-ready && /usr/local/libexec/network-v2/supply-chain-ready
  test -x /usr/local/libexec/network-v2/windows-real-chrome-ready && /usr/local/libexec/network-v2/windows-real-chrome-ready
  test -x /usr/local/libexec/network-v2/x-reality-ready && /usr/local/libexec/network-v2/x-reality-ready
  test -x /usr/local/libexec/network-v2/finance-ready && /usr/local/libexec/network-v2/finance-ready public 90
  test -x /usr/local/libexec/network-v2/claude-ready && /usr/local/libexec/network-v2/claude-ready
  test -x /usr/local/libexec/network-v2/chat-ingress-ready && /usr/local/libexec/network-v2/chat-ingress-ready
}

rollback() {
  local state=$1 failed=0
  set +e
  systemctl stop "$OWNED_TARGET" "$OWNED_ADAPTER" "$OWNED" >/dev/null 2>&1
  if podman container exists "$CTR" >/dev/null 2>&1; then podman rm -f "$CTR" >/dev/null 2>&1 || failed=1; fi
  if podman container exists "$CTR" >/dev/null 2>&1; then failed=1; fi
  rm -f "$MODE_MARKER"
  systemctl disable "$OWNED_TARGET" "$LEGACY_TARGET" >/dev/null 2>&1

  for p in "${MANAGED_PATHS[@]}"; do rm -f "/$p"; done
  tar -C / -xpf "$state/backup.tar" || failed=1
  systemctl daemon-reload || failed=1
  systemctl enable "$SUBSTRATE" >/dev/null 2>&1 || failed=1
  systemctl start network-v2-browserless-netns.service || failed=1
  systemctl start network-v2-browserless-forward.service || failed=1
  systemctl start "$LEGACY_WG" || failed=1
  systemctl start "$LEGACY_DNS" || failed=1
  systemctl start "$LEGACY_CARRIER" || failed=1
  systemctl start "$SUBSTRATE" || failed=1
  while IFS= read -r unit; do
    test -n "$unit" || continue
    systemctl restart "$unit" || failed=1
  done <"$state/active-consumers.txt"
  if test -x /usr/local/libexec/network-v2/browserless-provider-carrier-ready; then
    /usr/local/libexec/network-v2/browserless-provider-carrier-ready >/dev/null || failed=1
  fi
  if test -x /usr/local/libexec/network-v2/browserless-production-path; then
    /usr/local/libexec/network-v2/browserless-production-path >/dev/null || failed=1
  fi
  set -e
  test "$failed" -eq 0
}

execute_body() {
  local state=$1
  install_candidate_bytes
  systemctl disable "$LEGACY_TARGET" >/dev/null 2>&1 || true

  systemctl stop "$LEGACY_CARRIER"
  systemctl stop "$LEGACY_DNS"
  systemctl stop "$LEGACY_WG"
  if systemctl is-active --quiet "$LEGACY_WG"; then
    echo "legacy WireGuard remained active" >&2
    return 72
  fi
  if ip -n nv2-browserless-prod link show nv2blwg >/dev/null 2>&1; then
    echo "legacy WireGuard interface survived stop" >&2
    return 72
  fi

  install -d -m 0755 "$(dirname "$MODE_MARKER")"
  install -m 0644 /dev/null "$MODE_MARKER"
  systemctl enable "$OWNED_TARGET" >/dev/null
  systemctl disable "$LEGACY_TARGET" >/dev/null 2>&1 || true
  systemctl start "$SUBSTRATE"
  systemctl start "$OWNED_TARGET"
  wait_owned_ready

  "$CONSEQUENCE"
  restart_recorded_consumers "$state"
  consumer_checks

  systemctl is-active --quiet "$OWNED"
  systemctl is-active --quiet "$OWNED_ADAPTER"
  if systemctl is-active --quiet "$LEGACY_WG"; then
    echo "legacy WireGuard unexpectedly active after cutover" >&2
    return 73
  fi
  if systemctl is-active --quiet "$LEGACY_CARRIER"; then
    echo "legacy carrier unexpectedly active after cutover" >&2
    return 74
  fi
  test -e "$MODE_MARKER"
  test "$(systemctl is-enabled "$OWNED_TARGET")" = enabled
  test "$(systemctl is-enabled "$LEGACY_TARGET" 2>/dev/null || true)" != enabled
}

execute() {
  preflight
  local state
  state="$STATE_ROOT/$(date -u +%Y%m%dT%H%M%SZ)-$$"
  snapshot "$state"
  printf '%s\n' "$state" >"$STATE_ROOT/latest"
  # Run the effect body as a standalone errexit scope, not as a conditional.
  # Bash can suppress errexit inside functions evaluated by an if-condition.
  set +e
  ( set -e; execute_body "$state" )
  local rc=$?
  set -e
  if test "$rc" -eq 0; then
    sha256sum "$ROOT/capabilities/gluetun/m4-source/network-v2-gluetun-owned.container"       "$ROOT/capabilities/gluetun/m4-source/network-v2-gluetun-owned.target"       "$ROOT/consumers/browserless/config/provider-carrier-gluetun-candidate.json"       >"$state/source.sha256"
    cat >"$state/receipt.json" <<EOF
{"schemaVersion":1,"kind":"ordivon.network-v2.cold-replacement-receipt","standing":"GLUETUN_DEFAULT_READY","stateDir":"$state","imageDigest":"sha256:1baa76576dea1dfbafbd62bb635daf40fd87171f63273c2fdfe630418783011e","modeSelector":"$MODE_MARKER","legacyRetainedForRollback":true}
EOF
    cat "$state/receipt.json"
    return 0
  fi
  echo "cold replacement failed rc=$rc; restoring Legacy" >&2
  if rollback "$state"; then
    echo "COLD_REPLACEMENT_FAILED_LEGACY_RESTORED" >&2
  else
    echo "COLD_REPLACEMENT_FAILED_ROLLBACK_INCOMPLETE state=$state" >&2
    return 90
  fi
  return "$rc"
}

case "${1:-}" in
  --preflight) preflight ;;
  --execute) execute ;;
  --rollback)
    test $# -eq 2 || usage
    rollback "$2"
    ;;
  *) usage ;;
esac
