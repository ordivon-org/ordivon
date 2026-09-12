#!/usr/bin/env bash
set -euo pipefail

PROVIDER_UNIT=network-v2-r4-provider-carrier-smoke.service
NATIVE_UNIT=network-v2-r4-native-carrier-smoke.service
HAPROXY_UNIT=network-v2-r4-priority-failover-smoke.service
PROVIDER_PORT=28183
NATIVE_PORT=28184
FAILOVER_PORT=28182
PROVIDER_CFG=$(mktemp /tmp/network-v2-r4-provider.XXXXXX.json)
NATIVE_CFG=$(mktemp /tmp/network-v2-r4-native.XXXXXX.json)
HAPROXY_CFG=$(mktemp /tmp/network-v2-r4-haproxy.XXXXXX.cfg)

cleanup() {
  systemctl stop "$HAPROXY_UNIT" >/dev/null 2>&1 || true
  systemctl stop "$NATIVE_UNIT" >/dev/null 2>&1 || true
  systemctl stop "$PROVIDER_UNIT" >/dev/null 2>&1 || true
  systemctl reset-failed "$HAPROXY_UNIT" "$NATIVE_UNIT" "$PROVIDER_UNIT" >/dev/null 2>&1 || true
  rm -f "$PROVIDER_CFG" "$NATIVE_CFG" "$HAPROXY_CFG"
}
trap cleanup EXIT
cleanup

command -v haproxy >/dev/null
haproxy -v | grep -q '^HAProxy version 3\.4\.'

namespace=''
default_dev=''
ingress_ip=''
probe_url=''
direct_expected=''
provider_expected=''

# A namespace is admitted only if the root can reach its carrier side directly
# and a bounded external observation proves an egress identity distinct from
# native direct. Generic HTTPS success alone is not provider-path evidence.
for candidate in $(ip netns list | awk '{print $1}'); do
  dev=$(ip netns exec "$candidate" sh -c \
    "ip -4 route show default | awk 'NR==1{for(i=1;i<=NF;i++) if(\$i==\"dev\"){print \$(i+1); exit}}'" \
    2>/dev/null || true)
  [ -n "$dev" ] || continue
  side_ip=$(ip netns exec "$candidate" sh -c \
    "ip -4 -o addr show scope global | awk -v d='$dev' '\$2!=d {split(\$4,a,\"/\"); print a[1]; exit}'" \
    2>/dev/null || true)
  [ -n "$side_ip" ] || continue
  root_route=$(ip -4 route get "$side_ip" 2>/dev/null | head -n 1 || true)
  [ -n "$root_route" ] || continue
  printf '%s\n' "$root_route" | grep -q ' dev ' || continue
  if printf '%s\n' "$root_route" | grep -q ' via '; then
    continue
  fi

  for candidate_url in \
    https://ifconfig.me/ip \
    https://api.ipify.org \
    https://icanhazip.com \
    https://checkip.amazonaws.com; do
    direct=$(curl -4 -fsS --connect-timeout 3 --max-time 8 "$candidate_url" 2>/dev/null | tr -d '[:space:]' || true)
    provider=$(ip netns exec "$candidate" curl -4 -fsS --connect-timeout 3 --max-time 8 "$candidate_url" 2>/dev/null | tr -d '[:space:]' || true)
    if [ -n "$direct" ] && [ -n "$provider" ] && [ "$direct" != "$provider" ]; then
      namespace=$candidate
      default_dev=$dev
      ingress_ip=$side_ip
      probe_url=$candidate_url
      direct_expected=$direct
      provider_expected=$provider
      break 2
    fi
  done
done

[ -n "$namespace" ] || { echo 'no root-reachable provider namespace with distinct current egress is observable' >&2; exit 2; }

cat >"$PROVIDER_CFG" <<EOF
{
  "log": {"level": "warn", "timestamp": true},
  "inbounds": [{"type": "http", "tag": "provider-carrier-in", "listen": "0.0.0.0", "listen_port": $PROVIDER_PORT}],
  "outbounds": [{"type": "direct", "tag": "provider-direct"}],
  "route": {
    "rules": [{"ip_is_private": true, "action": "reject"}, {"ip_version": 6, "action": "reject"}],
    "final": "provider-direct"
  }
}
EOF

cat >"$NATIVE_CFG" <<EOF
{
  "log": {"level": "warn", "timestamp": true},
  "inbounds": [{"type": "http", "tag": "native-carrier-in", "listen": "127.0.0.1", "listen_port": $NATIVE_PORT}],
  "outbounds": [{"type": "direct", "tag": "native-direct"}],
  "route": {
    "rules": [{"ip_is_private": true, "action": "reject"}, {"ip_version": 6, "action": "reject"}],
    "final": "native-direct"
  }
}
EOF

cat >"$HAPROXY_CFG" <<EOF
global
  maxconn 128

defaults
  mode tcp
  timeout connect 3s
  timeout client 15s
  timeout server 15s
  timeout check 3s

frontend workload
  bind 127.0.0.1:$FAILOVER_PORT
  default_backend egress

backend egress
  mode tcp
  option tcp-check
  tcp-check connect
  tcp-check send CONNECT\\ example.com:443\\ HTTP/1.1\\r\\n
  tcp-check send Host:\\ example.com:443\\r\\n
  tcp-check send \\r\\n
  tcp-check expect rstring HTTP/1\\.[01]\\ 200
  default-server inter 500ms fastinter 200ms downinter 500ms fall 1 rise 2
  server provider $ingress_ip:$PROVIDER_PORT check
  server native 127.0.0.1:$NATIVE_PORT check backup
EOF

sing-box check -c "$PROVIDER_CFG"
sing-box check -c "$NATIVE_CFG"
haproxy -c -f "$HAPROXY_CFG" >/dev/null

start_provider() {
  systemctl stop "$PROVIDER_UNIT" >/dev/null 2>&1 || true
  systemctl reset-failed "$PROVIDER_UNIT" >/dev/null 2>&1 || true
  systemd-run --quiet --unit="$PROVIDER_UNIT" --property=Type=simple --property=Restart=no \
    /usr/bin/ip netns exec "$namespace" /usr/bin/sing-box run -c "$PROVIDER_CFG"
  for _ in $(seq 1 60); do
    ip netns exec "$namespace" ss -ltn 2>/dev/null | grep -q ":$PROVIDER_PORT " && return 0
    sleep 0.1
  done
  return 1
}

start_provider
systemd-run --quiet --unit="$NATIVE_UNIT" --property=Type=simple --property=Restart=no \
  /usr/bin/sing-box run -c "$NATIVE_CFG"
for _ in $(seq 1 60); do
  ss -ltn 2>/dev/null | grep -q "127.0.0.1:$NATIVE_PORT" && break
  sleep 0.1
done
ss -ltn | grep -q "127.0.0.1:$NATIVE_PORT"

systemd-run --quiet --unit="$HAPROXY_UNIT" --property=Type=simple --property=Restart=no \
  /usr/bin/haproxy -db -f "$HAPROXY_CFG"
for _ in $(seq 1 60); do
  ss -ltn 2>/dev/null | grep -q "127.0.0.1:$FAILOVER_PORT" && break
  sleep 0.1
done
ss -ltn | grep -q "127.0.0.1:$FAILOVER_PORT"

selected_ip() {
  curl -4 -fsS --proxy "http://127.0.0.1:$FAILOVER_PORT" --connect-timeout 3 --max-time 8 "$probe_url" 2>/dev/null | tr -d '[:space:]'
}

wait_selected() {
  expected=$1
  label=$2
  last=''
  for _ in $(seq 1 40); do
    last=$(selected_ip || true)
    if [ "$last" = "$expected" ]; then
      printf '%s\n' "$last"
      return 0
    fi
    sleep 0.5
  done
  printf '%s expected=%s last=%s\n' "$label" "$expected" "$last" >&2
  return 1
}

selected_before_failure=$(wait_selected "$provider_expected" initial-provider)
systemctl stop "$PROVIDER_UNIT"
selected_after_provider_failure=$(wait_selected "$direct_expected" provider-failure)
start_provider
selected_after_provider_recovery=$(wait_selected "$provider_expected" provider-recovery)

printf 'provider_namespace=%s provider_dev=%s provider_side_ip=%s\n' "$namespace" "$default_dev" "$ingress_ip"
printf 'probe_url=%s\n' "$probe_url"
printf 'provider_expected=%s direct_expected=%s\n' "$provider_expected" "$direct_expected"
printf 'selected_before_failure=%s\n' "$selected_before_failure"
printf 'selected_after_provider_failure=%s\n' "$selected_after_provider_failure"
echo provider-failover=PASS
printf 'selected_after_provider_recovery=%s\n' "$selected_after_provider_recovery"
echo provider-failback=PASS
