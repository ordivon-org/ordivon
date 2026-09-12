#!/usr/bin/env bash
set -euo pipefail

CONFIG_ROOT=${CONFIG_ROOT:-/etc/network-v2/providers}
PROFILE_ROOT=${PROFILE_ROOT:-$CONFIG_ROOT/catalog-profiles}
PROFILE_MANIFEST=${PROFILE_MANIFEST:-$PROFILE_ROOT/MANIFEST.tsv}
SERVER_CATALOG=${SERVER_CATALOG:-/usr/local/share/network-v2/gluetun-servers/surfshark.json}
SERVER_CATALOG_LOCK=${SERVER_CATALOG_LOCK:-external/gluetun-servers.lock}
NODE_A=${NODE_A:-kr-seo}
NODE_B=${NODE_B:-th-bkk}
WGGO=${WGGO:-/usr/local/libexec/network-v2/wireguard-go}
TARGET_URL=${TARGET_URL:-https://openapi.okx.com/api/v5/public/time}
TARGET_JQ=${TARGET_JQ:-'.code == "0" and (.data | type == "array") and (.data | length >= 1)'}
ROOT_PORT=${ROOT_PORT:-28220}
ROOT_API_PORT=${ROOT_API_PORT:-28229}
ROOT_UNIT=network-v2-r6-urltest.service
ROOT_CFG=config/finance-okx-singbox.json
CARRIER_CFG=config/provider-carrier.json

declare -A NODE SOURCE NS HOST_IF NS_IF WG_IF HOST_IP NS_IP CARRIER_PORT SB_UNIT SOURCE_PEER SELECTED HANDSHAKE ACTIVE_PROFILE LAST_PROFILE
NODE[A]=$NODE_A; NODE[B]=$NODE_B
SOURCE[A]=$CONFIG_ROOT/$NODE_A.conf; SOURCE[B]=$CONFIG_ROOT/$NODE_B.conf
NS[A]=nv2-r6-provider-a; NS[B]=nv2-r6-provider-b
HOST_IF[A]=nv2r6ha; HOST_IF[B]=nv2r6hb
NS_IF[A]=nv2r6na; NS_IF[B]=nv2r6nb
WG_IF[A]=nv2r6a; WG_IF[B]=nv2r6b
HOST_IP[A]=10.252.240.1; HOST_IP[B]=10.252.241.1
NS_IP[A]=10.252.240.2; NS_IP[B]=10.252.241.2
CARRIER_PORT[A]=28221; CARRIER_PORT[B]=28221
SB_UNIT[A]=network-v2-r6-provider-a-carrier.service
SB_UNIT[B]=network-v2-r6-provider-b-carrier.service

candidate_rows() {
  local k=$1
  awk -F '\t' -v node="${NODE[$k]}" '$1==node {print $2 "\t" $4}' "$PROFILE_MANIFEST"
}

fallback_profile() {
  local k=$1
  candidate_rows "$k" | awk -F '\t' 'NR==1{print $2}'
}

cleanup() {
  systemctl stop "$ROOT_UNIT" >/dev/null 2>&1 || true
  systemctl reset-failed "$ROOT_UNIT" >/dev/null 2>&1 || true
  for k in A B; do
    systemctl stop "${SB_UNIT[$k]}" >/dev/null 2>&1 || true
    systemctl reset-failed "${SB_UNIT[$k]}" >/dev/null 2>&1 || true
    profile=${ACTIVE_PROFILE[$k]-}
    [ -n "$profile" ] || profile=$(fallback_profile "$k" 2>/dev/null || true)
    if [ -n "$profile" ]; then
      ip netns exec "${NS[$k]}" env WG_QUICK_USERSPACE_IMPLEMENTATION="$WGGO" wg-quick down "$profile" >/dev/null 2>&1 || true
    fi
    ip netns del "${NS[$k]}" >/dev/null 2>&1 || true
    ip link del "${HOST_IF[$k]}" >/dev/null 2>&1 || true
    rm -rf "/etc/netns/${NS[$k]}"
    rm -f "/var/run/wireguard/${WG_IF[$k]}.sock"
  done
}
trap cleanup EXIT
cleanup

test -x "$WGGO"
test -f "$SERVER_CATALOG"; test -f "$SERVER_CATALOG_LOCK"; test -f "$PROFILE_MANIFEST"
expected_catalog_digest=$(awk -F= '$1=="sha256"{print $2}' "$SERVER_CATALOG_LOCK")
test -n "$expected_catalog_digest"
test "$(sha256sum "$SERVER_CATALOG" | awk '{print $1}')" = "$expected_catalog_digest"
test "$(awk 'NF{c++}END{print c+0}' "$PROFILE_MANIFEST")" -eq 6

for k in A B; do
  test -f "${SOURCE[$k]}"; test ! -L "${SOURCE[$k]}"
  case "$(stat -c %a "${SOURCE[$k]}")" in 600|400) ;; *) echo "unsafe source provider config mode: ${SOURCE[$k]}" >&2; exit 2;; esac
  SOURCE_PEER[$k]=$(awk '/^[[:space:]]*PublicKey[[:space:]]*=/{sub(/^[^=]*=/,""); gsub(/^[[:space:]]+|[[:space:]]+$/,""); print; exit}' "${SOURCE[$k]}")
  test -n "${SOURCE_PEER[$k]}"
  host=$(awk -F'[ =:]+' '/^[[:space:]]*Endpoint[[:space:]]*=/{print $2; exit}' "${SOURCE[$k]}")
  catalog_key=$(jq -r --arg h "$host" '.servers[] | select(.vpn=="wireguard" and .hostname==$h) | .wgpubkey' "$SERVER_CATALOG" | head -n1)
  test -n "$catalog_key"; test "${SOURCE_PEER[$k]}" = "$catalog_key"
  while IFS=$'\t' read -r ip profile; do
    test -n "$ip"; test -f "$profile"; test ! -L "$profile"
    case "$(stat -c %a "$profile")" in 600|400) ;; *) echo "unsafe catalog profile mode: $profile" >&2; exit 3;; esac
    WG_QUICK_USERSPACE_IMPLEMENTATION="$WGGO" wg-quick strip "$profile" >/dev/null
    test "$(yq -p=ini -o=json -r '.Interface.Table' "$profile")" = off
    test "$(yq -p=ini -o=json -r '.Interface.MTU' "$profile")" = 1280
    test "$(yq -p=ini -o=json -r '.Interface.DNS // ""' "$profile")" = ''
    test "$(yq -p=ini -o=json -r '.Peer.Endpoint' "$profile")" = "$ip:51820"
    test "$(yq -p=ini -o=json -r '.Peer.PublicKey' "$profile")" = "${SOURCE_PEER[$k]}"
  done < <(candidate_rows "$k")
done

setup_underlay() {
  local k=$1
  ip netns add "${NS[$k]}"
  ip link add "${HOST_IF[$k]}" type veth peer name "${NS_IF[$k]}"
  ip link set "${NS_IF[$k]}" netns "${NS[$k]}"
  ip addr add "${HOST_IP[$k]}/30" dev "${HOST_IF[$k]}"
  ip link set "${HOST_IF[$k]}" up
  ip -n "${NS[$k]}" addr add "${NS_IP[$k]}/30" dev "${NS_IF[$k]}"
  ip -n "${NS[$k]}" link set lo up
  ip -n "${NS[$k]}" link set "${NS_IF[$k]}" up
  mkdir -p "/etc/netns/${NS[$k]}"
  printf 'nameserver 127.0.0.1\n' >"/etc/netns/${NS[$k]}/resolv.conf"
  if ip -n "${NS[$k]}" route show default | grep -q .; then
    echo "provider namespace unexpectedly has ambient default route" >&2
    return 1
  fi
}

provider_up() {
  local k=$1 ip profile hs fallback
  fallback=$(fallback_profile "$k")
  ip netns exec "${NS[$k]}" env WG_QUICK_USERSPACE_IMPLEMENTATION="$WGGO" wg-quick down "${ACTIVE_PROFILE[$k]-$fallback}" >/dev/null 2>&1 || true
  unset 'ACTIVE_PROFILE[$k]' || true
  while IFS=$'\t' read -r ip profile; do
    ip -n "${NS[$k]}" route replace "$ip/32" via "${HOST_IP[$k]}" dev "${NS_IF[$k]}"
    if ! ip netns exec "${NS[$k]}" env WG_QUICK_USERSPACE_IMPLEMENTATION="$WGGO" wg-quick up "$profile" >/dev/null; then
      ip -n "${NS[$k]}" route del "$ip/32" >/dev/null 2>&1 || true
      continue
    fi
    ip -n "${NS[$k]}" route replace default dev "${WG_IF[$k]}"
    hs=0
    for _ in $(seq 1 18); do
      ip netns exec "${NS[$k]}" ping -4 -c1 -W1 1.1.1.1 >/dev/null 2>&1 || true
      hs=$(ip netns exec "${NS[$k]}" wg show "${WG_IF[$k]}" latest-handshakes | awk 'NR==1{print $2+0}')
      [ "${hs:-0}" -gt 0 ] && break
      sleep 0.3
    done
    if [ "${hs:-0}" -gt 0 ]; then
      ACTIVE_PROFILE[$k]=$profile
      LAST_PROFILE[$k]=$profile
      SELECTED[$k]=$ip
      HANDSHAKE[$k]=$hs
      return 0
    fi
    ip netns exec "${NS[$k]}" env WG_QUICK_USERSPACE_IMPLEMENTATION="$WGGO" wg-quick down "$profile" >/dev/null 2>&1 || true
    ip -n "${NS[$k]}" route del "$ip/32" >/dev/null 2>&1 || true
  done < <(candidate_rows "$k")
  return 1
}

provider_down() {
  local k=$1 profile
  profile=${ACTIVE_PROFILE[$k]-}
  [ -n "$profile" ] || profile=$(fallback_profile "$k")
  ip netns exec "${NS[$k]}" env WG_QUICK_USERSPACE_IMPLEMENTATION="$WGGO" wg-quick down "$profile" >/dev/null
  unset 'ACTIVE_PROFILE[$k]' || true
  if ip -n "${NS[$k]}" route show default | grep -q .; then
    echo "provider $k retained application default route after down" >&2
    return 1
  fi
}

start_carrier() {
  local k=$1
  sing-box check -c "$CARRIER_CFG"
  systemd-run --quiet --unit="${SB_UNIT[$k]}" --property=Type=simple --property=Restart=no \
    /usr/bin/ip netns exec "${NS[$k]}" /usr/bin/sing-box run -c "$PWD/$CARRIER_CFG"
  for _ in $(seq 1 60); do
    ip netns exec "${NS[$k]}" ss -ltn 2>/dev/null | grep -q ":${CARRIER_PORT[$k]} " && return 0
    sleep 0.1
  done
  return 1
}

probe_root() {
  local out meta
  out=$(mktemp)
  meta=$(curl -4 -sS --proxy "http://127.0.0.1:$ROOT_PORT" --connect-timeout 3 --max-time 12 -o "$out" -w '%{http_code} %{time_total}' "$TARGET_URL")
  jq -e "$TARGET_JQ" "$out" >/dev/null
  rm -f "$out"
  test "${meta%% *}" = 200
  printf '%s\n' "${meta#* }"
}

wait_root_success() {
  local t
  for _ in $(seq 1 12); do
    if t=$(probe_root 2>/dev/null); then printf '%s\n' "$t"; return 0; fi
    sleep 1
  done
  return 1
}

group_snapshot() {
  sing-box api --url "http://127.0.0.1:$ROOT_API_PORT" group show finance-okx-auto
}

refresh_group() {
  sing-box api --url "http://127.0.0.1:$ROOT_API_PORT" group urltest finance-okx-auto >/dev/null
  sleep 2
  group_snapshot
}

for k in A B; do setup_underlay "$k"; done
provider_up A
provider_up B
test "${SELECTED[A]}" != "${SELECTED[B]}"
start_carrier A
start_carrier B

sing-box check -c "$ROOT_CFG"
systemd-run --quiet --unit="$ROOT_UNIT" --property=Type=simple --property=Restart=no /usr/bin/sing-box run -c "$PWD/$ROOT_CFG"
for _ in $(seq 1 60); do
  if ss -ltn | grep -q "127.0.0.1:$ROOT_PORT" && ss -ltn | grep -q "127.0.0.1:$ROOT_API_PORT"; then break; fi
  sleep 0.1
done
ss -ltn | grep -q "127.0.0.1:$ROOT_PORT"
ss -ltn | grep -q "127.0.0.1:$ROOT_API_PORT"

set +e
curl -4 -sS --proxy "http://127.0.0.1:$ROOT_PORT" --connect-timeout 2 --max-time 5 https://example.com/ >/dev/null 2>&1
blocked_rc=$?
set -e
test "$blocked_rc" -ne 0
initial_t=$(wait_root_success)
initial_group=$(refresh_group)

provider_down B
a_only_t=$(wait_root_success)
b_down_group=$(refresh_group)

provider_up B
b_recovered_t=$(wait_root_success)
b_recovered_group=$(refresh_group)
provider_down A
b_only_t=$(wait_root_success)
a_down_group=$(refresh_group)

provider_down B
sleep 2
set +e
curl -4 -fsS --proxy "http://127.0.0.1:$ROOT_PORT" --connect-timeout 2 --max-time 6 "$TARGET_URL" >/dev/null 2>&1
both_down_rc=$?
set -e
test "$both_down_rc" -ne 0
both_down_group=$(refresh_group)

provider_up A
final_t=$(wait_root_success)
final_group=$(refresh_group)

printf 'provider_a_node=%s endpoint=%s handshake=%s profile_digest=sha256:%s\n' "${NODE[A]}" "${SELECTED[A]}" "${HANDSHAKE[A]}" "$(sha256sum "${LAST_PROFILE[A]}" | awk '{print $1}')"
printf 'provider_b_node=%s endpoint=%s handshake=%s profile_digest=sha256:%s\n' "${NODE[B]}" "${SELECTED[B]}" "${HANDSHAKE[B]}" "$(sha256sum "${LAST_PROFILE[B]}" | awk '{print $1}')"
printf 'gluetun_catalog_digest=sha256:%s\n' "$expected_catalog_digest"
printf 'initial_both_healthy_seconds=%s\n' "$initial_t"
printf '%s\n%s\n' '--- sing-box group: both healthy ---' "$initial_group"
printf 'b_down_a_survives_seconds=%s\n' "$a_only_t"
printf '%s\n%s\n' '--- sing-box group: provider-b down ---' "$b_down_group"
printf 'b_recovered_both_healthy_seconds=%s\n' "$b_recovered_t"
printf '%s\n%s\n' '--- sing-box group: provider-b recovered ---' "$b_recovered_group"
printf 'a_down_b_survives_seconds=%s\n' "$b_only_t"
printf '%s\n%s\n' '--- sing-box group: provider-a down ---' "$a_down_group"
printf 'both_provider_down_rc=%s\n' "$both_down_rc"
printf '%s\n%s\n' '--- sing-box group: both down ---' "$both_down_group"
echo both-provider-down-fail-closed=PASS
printf 'a_recovered_after_all_down_seconds=%s\n' "$final_t"
printf '%s\n%s\n' '--- sing-box group: provider-a recovered after all-down ---' "$final_group"
printf 'blocked_non_okx_connect_rc=%s\n' "$blocked_rc"
echo finance-okx-destination-allowlist=PASS
echo gluetun-catalog-provider-admission=PASS
echo static-yq-wgquick-profile=PASS
echo singbox-urltest-provider-health=PASS
echo network-v2-dual-provider-failclosed=PASS
