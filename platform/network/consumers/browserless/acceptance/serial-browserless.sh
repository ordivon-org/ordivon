#!/usr/bin/env bash
set -euo pipefail

SCRIPT=$(readlink -f "$0")
SURFPATH=${SURFPATH:-/root/tools/bin/surfpath}
LEASE_OWNER=${LEASE_OWNER:-network-v2-browserless-serial}
LEASE_TIMEOUT=${LEASE_TIMEOUT:-30}

restore_after_lease() {
  set +e
  systemctl reset-failed ordivon-browserless-anchor-recover.service ordivon-browserless-netns-reconcile.service \
    ordivon-exterior-anchor-chatgpt-browserless-r1.service \
    ordivon-browserless@11.service ordivon-browserless@12.service ordivon-browserless@13.service >/dev/null 2>&1 || true

  # First try the current fresh Surfpath observation.  If the serial proof aged it
  # out, refresh through the existing Surfpath owner rather than synthesizing one.
  systemctl start ordivon-browserless-anchor-recover.service >/dev/null 2>&1 || true
  for _ in $(seq 1 40); do
    [ "$(systemctl is-active ordivon-exterior-anchor-chatgpt-browserless-r1.service 2>/dev/null)" = active ] && break
    sleep .25
  done
  if [ "$(systemctl is-active ordivon-exterior-anchor-chatgpt-browserless-r1.service 2>/dev/null)" != active ]; then
    systemctl start ordivon-surfshark-hot.service >/dev/null 2>&1 || true
    for _ in $(seq 1 240); do
      state=$(systemctl is-active ordivon-surfshark-hot.service 2>/dev/null || true)
      [ "$state" != activating ] && [ "$state" != active ] && break
      sleep .25
    done
    systemctl start ordivon-browserless-anchor-recover.service >/dev/null 2>&1 || true
    for _ in $(seq 1 180); do
      [ "$(systemctl is-active ordivon-exterior-anchor-chatgpt-browserless-r1.service 2>/dev/null)" = active ] && break
      sleep .25
    done
  fi

  systemctl start ordivon-browserless-netns-reconcile.service >/dev/null 2>&1 || true
  systemctl start ordivon-browserless-anchor-recover.path ordivon-browserless-netns-reconcile.path >/dev/null 2>&1 || true
  for _ in $(seq 1 180); do
    ok=1
    for u in ordivon-browserless@11.service ordivon-browserless@12.service ordivon-browserless@13.service; do
      [ "$(systemctl is-active "$u" 2>/dev/null)" = active ] || ok=0
    done
    [ "$ok" = 1 ] && break
    sleep .25
  done
  set -e
}

accept_restored_production() {
  for u in ordivon-runtime.service temporal.service ordivon-exterior-anchor-chatgpt-browserless-r1.service \
    ordivon-browserless-anchor-recover.path ordivon-browserless-netns-reconcile.path \
    ordivon-browserless@11.service ordivon-browserless@12.service ordivon-browserless@13.service; do
    [ "$(systemctl is-active "$u" 2>/dev/null)" = active ]
  done
  local token ready code
  token=$(cat /etc/ordivon/browserless.token)
  ready=0
  for _ in $(seq 1 100); do
    code=$(curl -sS --connect-timeout 2 --max-time 5 -o /tmp/nv2-browserless-restored-version.json -w '%{http_code}' \
      "http://127.0.0.1:13111/json/version?token=$token" 2>/dev/null || true)
    [ "$code" = 200 ] && { ready=1; break; }
    sleep .5
  done
  [ "$ready" = 1 ]
  code=$(curl -sS --connect-timeout 5 --max-time 30 -o /tmp/nv2-browserless-restored-chatgpt.html -w '%{http_code}' \
    -H 'content-type: application/json' -d '{"url":"https://chatgpt.com/"}' \
    "http://127.0.0.1:13111/content?token=$token")
  [ "$code" = 200 ]
  grep -Eqi 'chatgpt|openai|challenge' /tmp/nv2-browserless-restored-chatgpt.html
  python3 - <<'PY'
import json
r=json.load(open('/root/.local/state/ordivon-workstation/exterior-anchors/chatgpt-browserless-r1/runtime-state.json'))
c=json.load(open('/etc/ordivon/agent-automation-browserless.json'))
assert r['namespace']==c['browserSubstrate']['endpoints'][0]['networkNamespace']
print('restored_namespace='+r['namespace'])
print('restored_endpoint='+r['endpointIp'])
print('restored_health='+r['recoveryState'])
PY
  echo production_restore=PASS
}

if [ "${NETWORK_V2_BROWSERLESS_LEASE_INNER:-0}" != 1 ]; then
  [ -x "$SURFPATH" ]
  set +e
  "$SURFPATH" graduation-lease --owner "$LEASE_OWNER" --timeout-seconds "$LEASE_TIMEOUT" -- \
    /usr/bin/env NETWORK_V2_BROWSERLESS_LEASE_INNER=1 "$SCRIPT"
  inner_rc=$?
  set -e
  restore_after_lease
  accept_restored_production
  exit "$inner_rc"
fi

# Transitional differential gate.  The current legacy Browserless carrier and
# Network v2 share one Surfshark WireGuard identity, so concurrent shadowing is
# not a valid experiment.  This gate serializes ownership: stop one exact legacy
# ExteriorAnchor generation, prove the v2 namespace, then unconditionally restore
# and rebind the legacy production carrier.

NAME=${NAME:-chatgpt-browserless-r1}
TEMPORAL=${TEMPORAL:-/opt/ordivon/external/temporal-cli/1.8.3/temporal}
EXTERIOR_ANCHOR=${EXTERIOR_ANCHOR:-/root/tools/bin/exterior-anchor}
RUNTIME_STATE=${RUNTIME_STATE:-/root/.local/state/ordivon-workstation/exterior-anchors/chatgpt-browserless-r1/runtime-state.json}
BROWSER_CONFIG=${BROWSER_CONFIG:-/etc/ordivon/agent-automation-browserless.json}
ANCHOR_UNIT=${ANCHOR_UNIT:-ordivon-exterior-anchor-chatgpt-browserless-r1.service}
RECOVER_PATH=${RECOVER_PATH:-ordivon-browserless-anchor-recover.path}
RECOVER_SERVICE=${RECOVER_SERVICE:-ordivon-browserless-anchor-recover.service}
RECON_PATH=${RECON_PATH:-ordivon-browserless-netns-reconcile.path}
RECON_SERVICE=${RECON_SERVICE:-ordivon-browserless-netns-reconcile.service}

NS=${NS:-nv2-browserless-serial}
HOST_IF=${HOST_IF:-nv2blsh}
NS_IF=${NS_IF:-nv2blsn}
HOST_IP=${HOST_IP:-10.252.246.1}
NS_IP=${NS_IP:-10.252.246.2}
RULE_PREF=${RULE_PREF:-11994}
WG_IF=${WG_IF:-nv2r6a}
WGGO=${WGGO:-/usr/local/libexec/network-v2/wireguard-go}
PROFILE=${PROFILE:-/etc/network-v2/providers/kr-seo.conf}
DNSPROXY=${DNSPROXY:-/usr/bin/dnsproxy}
IMAGE=${IMAGE:-ghcr.io/browserless/chromium@sha256:5e3f3e59e5d8d545f0766534e3d76dc4fb6ac17b9e05f52d125dd51e3908f631}
CONTAINER=${CONTAINER:-network-v2-browserless-serial}
PORT=${PORT:-3021}
TOKEN=${TOKEN:-network-v2-browserless-serial-token}
DNS_PID=''
OLD_NS=''
OLD_GEN=''

cleanup_candidate() {
  set +e
  podman rm -f "$CONTAINER" >/dev/null 2>&1 || true
  if [ -n "$DNS_PID" ]; then kill "$DNS_PID" >/dev/null 2>&1 || true; wait "$DNS_PID" >/dev/null 2>&1 || true; fi
  ip rule del priority "$RULE_PREF" >/dev/null 2>&1 || true
  if [ -f "$TMP_PROFILE" ] && ip netns list | awk '{print $1}' | grep -qx "$NS"; then
    ip netns exec "$NS" env WG_QUICK_USERSPACE_IMPLEMENTATION="$WGGO" wg-quick down "$TMP_PROFILE" >/dev/null 2>&1 || true
  fi
  ip netns del "$NS" >/dev/null 2>&1 || true
  ip link del "$HOST_IF" >/dev/null 2>&1 || true
  rm -rf "/etc/netns/$NS" "$TMP_DIR"
  rm -f "/var/run/wireguard/$WG_IF.sock"
}


trap cleanup_candidate EXIT

TMP_DIR=$(mktemp -d /tmp/network-v2-browserless-serial.XXXXXX)
TMP_PROFILE="$TMP_DIR/$WG_IF.conf"

for x in "$TEMPORAL" "$EXTERIOR_ANCHOR" "$WGGO" "$DNSPROXY"; do [ -x "$x" ]; done
[ -f "$PROFILE" ]
[ -f "$RUNTIME_STATE" ]
podman image exists "$IMAGE"

# Fail closed instead of interrupting an Agent Automation workload.
"$TEMPORAL" workflow list --address 127.0.0.1:17233 --namespace default \
  --query 'ExecutionStatus="Running" AND TaskQueue="ordivon-agent-automation"' --limit 100 --output json >"$TMP_DIR/running.json"
python3 - "$TMP_DIR/running.json" <<'PY'
import json,sys
rows=json.load(open(sys.argv[1]))
print(f'runningWorkflows={len(rows)}')
if rows: raise SystemExit(20)
PY

readarray -t META < <(python3 - "$RUNTIME_STATE" <<'PY'
import json,sys
x=json.load(open(sys.argv[1]))
for k in ('generationDigest','namespace','endpointIp','parentIngress'):
 print(x.get(k) or '')
PY
)
OLD_GEN=${META[0]}; OLD_NS=${META[1]}; ENDPOINT=${META[2]}; INGRESS=${META[3]}
case "$INGRESS" in native-a) ROUTE_TABLE=201;; native-b) ROUTE_TABLE=202;; *) echo "unsupported ingress: $INGRESS" >&2; exit 21;; esac
printf 'legacy_generation=%s\nlegacy_namespace=%s\nendpoint=%s\ningress=%s\n' "$OLD_GEN" "$OLD_NS" "$ENDPOINT" "$INGRESS"

# Quiesce the one exact legacy generation.  A pending first stop is not failure:
# once the service is terminal, a second owner stop admits exact-generation
# residual namespace/resolver cleanup.
systemctl stop "$RECOVER_PATH" "$RECON_PATH"
set +e
"$EXTERIOR_ANCHOR" stop --name "$NAME" --expect-generation "$OLD_GEN" >"$TMP_DIR/stop.json"
set -e
REQUEST=$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["requestDigest"])' "$TMP_DIR/stop.json")
set +e
"$EXTERIOR_ANCHOR" reconcile-stop --name "$NAME" --request "$REQUEST" --budget-seconds 60 >"$TMP_DIR/reconcile.json"
set -e
EFFECT=$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1])).get("effectState"))' "$TMP_DIR/reconcile.json")
if [ "$EFFECT" != completed ]; then
  set +e
  "$EXTERIOR_ANCHOR" stop --name "$NAME" --expect-generation "$OLD_GEN" >"$TMP_DIR/stop2.json"
  set -e
  EFFECT=$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1])).get("effectState"))' "$TMP_DIR/stop2.json")
fi
[ "$EFFECT" = completed ]
[ ! -e "/run/netns/$OLD_NS" ]
echo legacy_identity_quiesced=PASS

# Build one candidate from the endpoint that was proven healthy immediately
# before quiescence. Endpoint discovery authority is a separate provider gate.
EP="$ENDPOINT:51820" yq -p=ini -o=ini \
  'del(.Interface.DNS) | .Interface.Table="off" | .Interface.MTU="1380" | .Peer.Endpoint=strenv(EP) | .Peer.PersistentKeepalive="5"' \
  "$PROFILE" >"$TMP_PROFILE"
chmod 0600 "$TMP_PROFILE"

ip netns add "$NS"
ip link add "$HOST_IF" type veth peer name "$NS_IF"
ip link set "$NS_IF" netns "$NS"
ip addr add "$HOST_IP/30" dev "$HOST_IF"
ip link set "$HOST_IF" up
ip -n "$NS" addr add "$NS_IP/30" dev "$NS_IF"
ip -n "$NS" link set lo up
ip -n "$NS" link set "$NS_IF" up
mkdir -p "/etc/netns/$NS"
printf 'nameserver 127.0.0.1\noptions timeout:2 attempts:2\n' >"/etc/netns/$NS/resolv.conf"
awk 'BEGIN{done=0} /^hosts:/{print "hosts: files dns";done=1;next} {print} END{if(!done)print "hosts: files dns"}' \
  /etc/nsswitch.conf >"/etc/netns/$NS/nsswitch.conf"
ip -n "$NS" route add "$ENDPOINT/32" via "$HOST_IP" dev "$NS_IF"
ip rule add from "$NS_IP"/32 priority "$RULE_PREF" table "$ROUTE_TABLE"

ip netns exec "$NS" env WG_QUICK_USERSPACE_IMPLEMENTATION="$WGGO" wg-quick up "$TMP_PROFILE" >/dev/null
ip -n "$NS" route replace default dev "$WG_IF"
HANDSHAKE=0
for _ in $(seq 1 24); do
  ip netns exec "$NS" ping -4 -c1 -W1 1.1.1.1 >/dev/null 2>&1 || true
  HANDSHAKE=$(ip netns exec "$NS" wg show "$WG_IF" latest-handshakes | awk 'NR==1{print $2+0}')
  [ "$HANDSHAKE" -gt 0 ] && break
  sleep .25
done
[ "$HANDSHAKE" -gt 0 ]

# dnsproxy is the mature resolver authority already selected by Network v2.
# Secure DoH is primary; provider-native DNS is fallback only.
ip netns exec "$NS" "$DNSPROXY" -l 127.0.0.1 -p 53 \
  -u https://1.1.1.1/dns-query -u https://8.8.8.8/dns-query \
  -f 162.252.172.57:53 -f 149.154.159.92:53 \
  --upstream-mode parallel --cache --pending-requests-enabled --refuse-any --timeout 5s \
  >"$TMP_DIR/dnsproxy.log" 2>&1 &
DNS_PID=$!

ready=0
for _ in $(seq 1 50); do
  answers=$(ip netns exec "$NS" getent ahostsv4 api.openai.com 2>/dev/null | awk '{print $1}' | sort -u | tr '\n' ',' || true)
  if echo "$answers" | grep -Eq '162\.159\.|172\.66\.'; then ready=1; break; fi
  sleep .2
done
[ "$ready" = 1 ]
OPENAI_DNS=$(ip netns exec "$NS" getent ahostsv4 api.openai.com | awk '{print $1}' | sort -u | tr '\n' ',')
CHATGPT_DNS=$(ip netns exec "$NS" getent ahostsv4 chatgpt.com | awk '{print $1}' | sort -u | tr '\n' ',')
echo "$OPENAI_DNS" | grep -Eq '162\.159\.|172\.66\.'
echo "$CHATGPT_DNS" | grep -Eq '104\.18\.|172\.64\.'

OPENAI_HTTP=$(ip netns exec "$NS" curl -4 -sS --connect-timeout 6 --max-time 20 -o /dev/null -w '%{http_code}' https://api.openai.com/v1/models)
CHATGPT_HTTP=$(ip netns exec "$NS" curl -4 -sS --connect-timeout 6 --max-time 20 -o /dev/null -w '%{http_code}' https://chatgpt.com/)
case "$OPENAI_HTTP" in 200|401|403|404) ;; *) exit 31;; esac
case "$CHATGPT_HTTP" in 200|301|302|403) ;; *) exit 32;; esac

podman run -d --rm --name "$CONTAINER" --pull=never --network "ns:/run/netns/$NS" --shm-size 1g \
  --dns 127.0.0.1 -e "TOKEN=$TOKEN" -e "PORT=$PORT" -e CONCURRENT=1 -e QUEUED=2 -e TIMEOUT=90000 -e 'DEBUG=-*' \
  "$IMAGE" >/dev/null
BROWSER_READY=0
for i in $(seq 1 120); do
  if ip netns exec "$NS" curl -fsS --connect-timeout 1 --max-time 3 "http://127.0.0.1:$PORT/json/version?token=$TOKEN" >"$TMP_DIR/version.json" 2>/dev/null; then
    BROWSER_READY=1; echo browser_ready_attempt="$i"; break
  fi
  sleep .25
done
[ "$BROWSER_READY" = 1 ]
CHAT_CONTENT=$(ip netns exec "$NS" curl -sS --connect-timeout 5 --max-time 40 -o "$TMP_DIR/chatgpt.html" -w '%{http_code}' \
  -H 'content-type: application/json' -d '{"url":"https://chatgpt.com/"}' "http://127.0.0.1:$PORT/content?token=$TOKEN")
[ "$CHAT_CONTENT" = 200 ]
grep -Eqi 'chatgpt|openai|challenge' "$TMP_DIR/chatgpt.html"
PROVIDER_IP=$(ip netns exec "$NS" curl -4 -fsS --connect-timeout 4 --max-time 10 https://api.ipify.org | tr -d '[:space:]')

printf 'handshake=%s\nopenai_dns=%s\nchatgpt_dns=%s\nopenai_http=%s\nchatgpt_http=%s\nprovider_egress=%s\nchatgpt_content_http=%s\n' \
  "$HANDSHAKE" "$OPENAI_DNS" "$CHATGPT_DNS" "$OPENAI_HTTP" "$CHATGPT_HTTP" "$PROVIDER_IP" "$CHAT_CONTENT"
echo browserless-serial-wireguard=PASS
echo browserless-serial-dnsproxy=PASS
echo browserless-serial-real-browser=PASS
