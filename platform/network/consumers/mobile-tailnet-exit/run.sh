#!/usr/bin/env bash
set -euo pipefail

CTR=network-v2-gluetun-owned-r1
RUNTIME="${MOBILE_TAILNET_RUNTIME_DIR:-/run/ordivon-mobile-tailnet-r1}"
STATE="${MOBILE_TAILNET_STATE_DIR:-/var/lib/ordivon-mobile-tailnet-r1}"
SOCKET="$RUNTIME/tailscaled.sock"
TAILSCALED=/usr/bin/tailscaled
TAILSCALE=/usr/bin/tailscale

provider_pid() {
  /usr/bin/podman inspect -f '{{.State.Pid}}' "$CTR" 2>/dev/null || true
}

valid_pid() {
  case "${1:-}" in
    ''|*[!0-9]*) return 1 ;;
  esac
  test "$1" -gt 1 && test -e "/proc/$1/ns/net"
}

provider_pid="$(provider_pid)"
if ! valid_pid "$provider_pid"; then
  echo "mobile-tailnet-exit: provider container unavailable" >&2
  exit 75
fi

mkdir -p "$RUNTIME" "$STATE"
chmod 0700 "$RUNTIME" "$STATE"
rm -f "$SOCKET" "$RUNTIME/tailscaled.pid" "$RUNTIME/provider.pid"

child=
# Invoked by EXIT/INT/TERM trap, not by a direct call.
# shellcheck disable=SC2329
cleanup() {
  rc=$?
  trap - EXIT INT TERM
  if test -n "${child:-}" && kill -0 "$child" 2>/dev/null; then
    kill "$child" 2>/dev/null || true
    for _ in $(seq 1 30); do
      kill -0 "$child" 2>/dev/null || break
      sleep 0.1
    done
    kill -KILL "$child" 2>/dev/null || true
  fi
  test -n "${child:-}" && wait "$child" 2>/dev/null || true
  rm -f "$RUNTIME/tailscaled.pid" "$RUNTIME/provider.pid"
  exit "$rc"
}
trap cleanup EXIT INT TERM

/usr/bin/nsenter -t "$provider_pid" -n "$TAILSCALED" \
  --tun=userspace-networking \
  --socket="$SOCKET" \
  --statedir="$STATE" \
  --state="$STATE/tailscaled.state" \
  --port=0 &
child=$!
printf '%s\n' "$child" >"$RUNTIME/tailscaled.pid"
printf '%s\n' "$provider_pid" >"$RUNTIME/provider.pid"

ready=0
for _ in $(seq 1 100); do
  if ! kill -0 "$child" 2>/dev/null; then
    wait "$child"
    exit $?
  fi
  if test -S "$SOCKET" && "$TAILSCALE" --socket="$SOCKET" status --json >/dev/null 2>&1; then
    "$TAILSCALE" --socket="$SOCKET" set --advertise-exit-node --accept-dns=true
    ready=1
    break
  fi
  sleep 0.1
done
if test "$ready" != 1; then
  echo "mobile-tailnet-exit: tailscale control socket did not become ready" >&2
  exit 70
fi

while kill -0 "$child" 2>/dev/null; do
  sleep 1
  current_provider_pid="$(provider_pid)"
  if ! valid_pid "$current_provider_pid" || test "$current_provider_pid" != "$provider_pid"; then
    echo "mobile-tailnet-exit: provider namespace changed; restarting" >&2
    exit 75
  fi
done

wait "$child"
exit $?
