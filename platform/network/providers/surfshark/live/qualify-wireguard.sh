#!/usr/bin/env bash
set -euo pipefail

SCRIPT=$(readlink -f "$0")
SURFPATH=${SURFPATH:-/root/tools/bin/surfpath}
LEASE_OWNER=${LEASE_OWNER:-network-v2-surfshark-live-qualification}
LEASE_TIMEOUT=${LEASE_TIMEOUT:-30}
NAME=${NAME:-chatgpt-browserless-r1}
TEMPORAL=${TEMPORAL:-/opt/ordivon/external/temporal-cli/1.8.3/temporal}
EXTERIOR_ANCHOR=${EXTERIOR_ANCHOR:-/root/tools/bin/exterior-anchor}
RUNTIME_STATE=${RUNTIME_STATE:-/root/.local/state/ordivon-workstation/exterior-anchors/chatgpt-browserless-r1/runtime-state.json}
RECOVER_PATH=${RECOVER_PATH:-ordivon-browserless-anchor-recover.path}
RECOVER_SERVICE=${RECOVER_SERVICE:-ordivon-browserless-anchor-recover.service}
RECON_PATH=${RECON_PATH:-ordivon-browserless-netns-reconcile.path}
RECON_SERVICE=${RECON_SERVICE:-ordivon-browserless-netns-reconcile.service}
ANCHOR_UNIT=${ANCHOR_UNIT:-ordivon-exterior-anchor-chatgpt-browserless-r1.service}
SNAPSHOT=${SNAPSHOT:-/var/lib/network-v2/providers/surfshark/live/latest.json}
NODE=${NODE:-kr-seo}
PROFILE=${PROFILE:-/etc/network-v2/providers/$NODE.conf}
OUTPUT=${OUTPUT:-/var/lib/network-v2/providers/surfshark/live/qualified-$NODE.json}
MAX_SNAPSHOT_AGE=${MAX_SNAPSHOT_AGE:-300}
WGGO=${WGGO:-/usr/local/libexec/network-v2/wireguard-go}
DNSPROXY=${DNSPROXY:-/usr/bin/dnsproxy}

restore_after_lease(){
  set +e
  systemctl reset-failed "$RECOVER_SERVICE" "$RECON_SERVICE" "$ANCHOR_UNIT" \
    ordivon-browserless@11.service ordivon-browserless@12.service ordivon-browserless@13.service >/dev/null 2>&1 || true
  systemctl start "$RECOVER_SERVICE" >/dev/null 2>&1 || true
  for _ in $(seq 1 40); do [ "$(systemctl is-active "$ANCHOR_UNIT" 2>/dev/null)" = active ] && break; sleep .25; done
  if [ "$(systemctl is-active "$ANCHOR_UNIT" 2>/dev/null)" != active ]; then
    systemctl start ordivon-surfshark-hot.service >/dev/null 2>&1 || true
    for _ in $(seq 1 240); do
      st=$(systemctl is-active ordivon-surfshark-hot.service 2>/dev/null || true)
      [ "$st" != activating ] && [ "$st" != active ] && break
      sleep .25
    done
    systemctl start "$RECOVER_SERVICE" >/dev/null 2>&1 || true
    for _ in $(seq 1 180); do [ "$(systemctl is-active "$ANCHOR_UNIT" 2>/dev/null)" = active ] && break; sleep .25; done
  fi
  systemctl start "$RECON_SERVICE" >/dev/null 2>&1 || true
  systemctl start "$RECOVER_PATH" "$RECON_PATH" >/dev/null 2>&1 || true
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
accept_restored(){
  for u in ordivon-runtime.service temporal.service ordivon-agent-temporal-worker.service \
    ordivon-agent-automation-mcp.service "$ANCHOR_UNIT" ordivon-browserless@11.service \
    ordivon-browserless@12.service ordivon-browserless@13.service; do
    [ "$(systemctl is-active "$u" 2>/dev/null)" = active ]
  done
  token=$(cat /etc/ordivon/browserless.token)
  ready=0
  for _ in $(seq 1 100); do
    code=$(curl -sS --connect-timeout 2 --max-time 5 -o /tmp/nv2-liveq-version.json -w '%{http_code}' \
      "http://127.0.0.1:13111/json/version?token=$token" 2>/dev/null || true)
    [ "$code" = 200 ] && { ready=1; break; }
    sleep .5
  done
  [ "$ready" = 1 ]
  echo production_restore=PASS
}

if [ "${NETWORK_V2_LIVE_QUALIFY_INNER:-0}" != 1 ]; then
  [ -x "$SURFPATH" ]
  set +e
  "$SURFPATH" graduation-lease --owner "$LEASE_OWNER" --timeout-seconds "$LEASE_TIMEOUT" -- \
    /usr/bin/env NETWORK_V2_LIVE_QUALIFY_INNER=1 "$SCRIPT"
  rc=$?
  set -e
  restore_after_lease
  accept_restored
  exit "$rc"
fi

NS=${NS:-nv2-surf-liveq}
HOST_IF=${HOST_IF:-nv2slqh}
NS_IF=${NS_IF:-nv2slqn}
HOST_IP=${HOST_IP:-10.252.242.1}
NS_IP=${NS_IP:-10.252.242.2}
RULE_PREF=${RULE_PREF:-11988}
WG_IF=${WG_IF:-nv2livewg}
TMP=$(mktemp -d /tmp/network-v2-surf-liveq.XXXXXX)
ACTIVE_PROFILE=''; DNS_PID=''; OLD_NS=''; OLD_GEN=''
cleanup(){
  set +e
  [ -n "$DNS_PID" ] && kill "$DNS_PID" >/dev/null 2>&1 || true
  [ -n "$DNS_PID" ] && wait "$DNS_PID" >/dev/null 2>&1 || true
  ip rule del priority "$RULE_PREF" >/dev/null 2>&1 || true
  if [ -n "$ACTIVE_PROFILE" ] && ip netns list | awk '{print $1}' | grep -qx "$NS"; then
    ip netns exec "$NS" env WG_QUICK_USERSPACE_IMPLEMENTATION="$WGGO" wg-quick down "$ACTIVE_PROFILE" >/dev/null 2>&1 || true
  fi
  ip netns del "$NS" >/dev/null 2>&1 || true
  ip link del "$HOST_IF" >/dev/null 2>&1 || true
  rm -rf "/etc/netns/$NS" "$TMP"
  rm -f "/var/run/wireguard/$WG_IF.sock"
}
trap cleanup EXIT

for x in "$TEMPORAL" "$EXTERIOR_ANCHOR" "$WGGO" "$DNSPROXY"; do [ -x "$x" ]; done
[ -f "$SNAPSHOT" ]; [ -f "$PROFILE" ]
"$TEMPORAL" workflow list --address 127.0.0.1:17233 --namespace default \
  --query 'ExecutionStatus="Running" AND TaskQueue="ordivon-agent-automation"' --limit 100 --output json >"$TMP/running.json"
python3 - "$TMP/running.json" <<'PY'
import json,sys
rows=json.load(open(sys.argv[1])); print(f'runningWorkflows={len(rows)}')
if rows: raise SystemExit(20)
PY

python3 - "$SNAPSHOT" "$NODE" "$MAX_SNAPSHOT_AGE" "$TMP/candidate.json" <<'PY'
import hashlib,json,sys,time
p,node,maxage,out=sys.argv[1:]; maxage=int(maxage)
d=json.load(open(p)); claimed=d.get('snapshotDigest','')
payload={k:v for k,v in d.items() if k!='snapshotDigest'}
actual='sha256:'+hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(',',':')).encode()).hexdigest()
if claimed!=actual: raise SystemExit('snapshot digest mismatch')
if d.get('standingAtObservation')!='FRESH_PARTIAL_CANDIDATE_SNAPSHOT': raise SystemExit('snapshot standing invalid')
age=max(0,int(time.time())-int(d.get('observedUnix') or 0))
if age>maxage: raise SystemExit(f'snapshot stale age={age}s max={maxage}s')
host=node+'.prod.surfshark.com'
rows=[x for x in d.get('candidates',[]) if x.get('hostname')==host]
if len(rows)!=1 or not rows[0].get('wireguard'): raise SystemExit('wireguard candidate missing')
w=rows[0]['wireguard']; ips=w.get('ips') or []
if not ips or not w.get('wgpubkey'): raise SystemExit('wireguard endpoint set empty')
json.dump({'snapshotDigest':claimed,'snapshotObservedUnix':d['observedUnix'],'hostname':host,'wgpubkey':w['wgpubkey'],'ips':ips},open(out,'w'))
print('snapshotDigest='+claimed); print('liveEndpoints='+','.join(ips))
PY
EXPECTED_PUB=$(jq -r '.wgpubkey' "$TMP/candidate.json")
PROFILE_PUB=$(yq -p=ini -o=json -r '.Peer.PublicKey' "$PROFILE")
[ "$PROFILE_PUB" = "$EXPECTED_PUB" ]

readarray -t META < <(python3 - "$RUNTIME_STATE" <<'PY'
import json,sys
x=json.load(open(sys.argv[1]))
for k in ('generationDigest','namespace','parentIngress'): print(x.get(k) or '')
PY
)
OLD_GEN=${META[0]}; OLD_NS=${META[1]}; INGRESS=${META[2]}
case "$INGRESS" in native-a) ROUTE_TABLE=201;; native-b) ROUTE_TABLE=202;; *) echo "unsupported ingress $INGRESS" >&2; exit 21;; esac
systemctl stop "$RECOVER_PATH" "$RECON_PATH"
set +e
"$EXTERIOR_ANCHOR" stop --name "$NAME" --expect-generation "$OLD_GEN" >"$TMP/stop.json"
set -e
REQ=$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["requestDigest"])' "$TMP/stop.json")
set +e
"$EXTERIOR_ANCHOR" reconcile-stop --name "$NAME" --request "$REQ" --budget-seconds 60 >"$TMP/reconcile.json"
set -e
EFFECT=$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1])).get("effectState"))' "$TMP/reconcile.json")
if [ "$EFFECT" != completed ]; then
  set +e
  "$EXTERIOR_ANCHOR" stop --name "$NAME" --expect-generation "$OLD_GEN" >"$TMP/stop2.json"
  set -e
  EFFECT=$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1])).get("effectState"))' "$TMP/stop2.json")
fi
[ "$EFFECT" = completed ]; [ ! -e "/run/netns/$OLD_NS" ]
echo legacy_identity_quiesced=PASS

ip netns add "$NS"
ip link add "$HOST_IF" type veth peer name "$NS_IF"
ip link set "$NS_IF" netns "$NS"
ip addr add "$HOST_IP/30" dev "$HOST_IF"; ip link set "$HOST_IF" up
ip -n "$NS" addr add "$NS_IP/30" dev "$NS_IF"; ip -n "$NS" link set lo up; ip -n "$NS" link set "$NS_IF" up
mkdir -p "/etc/netns/$NS"
printf 'nameserver 127.0.0.1\noptions timeout:2 attempts:2\n' >"/etc/netns/$NS/resolv.conf"
awk 'BEGIN{done=0} /^hosts:/{print "hosts: files dns";done=1;next} {print} END{if(!done)print "hosts: files dns"}' /etc/nsswitch.conf >"/etc/netns/$NS/nsswitch.conf"
ip rule add from "$NS_IP"/32 priority "$RULE_PREF" table "$ROUTE_TABLE"

QUALIFIED=''; HANDSHAKE=0; EXAMPLE_HTTP=''; PROVIDER_IP=''
while read -r endpoint; do
  [ -n "$endpoint" ] || continue
  cfg="$TMP/$WG_IF.conf"
  EP="$endpoint:51820" yq -p=ini -o=ini 'del(.Interface.DNS) | .Interface.Table="off" | .Interface.MTU="1380" | .Peer.Endpoint=strenv(EP) | .Peer.PersistentKeepalive="5"' "$PROFILE" >"$cfg"
  chmod 0600 "$cfg"; ACTIVE_PROFILE="$cfg"
  ip -n "$NS" route replace "$endpoint/32" via "$HOST_IP" dev "$NS_IF"
  if ! ip netns exec "$NS" env WG_QUICK_USERSPACE_IMPLEMENTATION="$WGGO" wg-quick up "$cfg" >/dev/null 2>&1; then ACTIVE_PROFILE=''; continue; fi
  ip -n "$NS" route replace default dev "$WG_IF"
  HANDSHAKE=0
  for _ in $(seq 1 24); do
    ip netns exec "$NS" ping -4 -c1 -W1 1.1.1.1 >/dev/null 2>&1 || true
    HANDSHAKE=$(ip netns exec "$NS" wg show "$WG_IF" latest-handshakes 2>/dev/null | awk 'NR==1{print $2+0}')
    [ "$HANDSHAKE" -gt 0 ] && break
    sleep .25
  done
  if [ "$HANDSHAKE" -gt 0 ]; then QUALIFIED="$endpoint"; break; fi
  ip netns exec "$NS" env WG_QUICK_USERSPACE_IMPLEMENTATION="$WGGO" wg-quick down "$cfg" >/dev/null 2>&1 || true
  ACTIVE_PROFILE=''
done < <(jq -r '.ips[]' "$TMP/candidate.json")
[ -n "$QUALIFIED" ]

ip netns exec "$NS" "$DNSPROXY" -l 127.0.0.1 -p 53 \
  -u https://1.1.1.1/dns-query -u https://8.8.8.8/dns-query \
  -f 162.252.172.57:53 -f 149.154.159.92:53 \
  --upstream-mode parallel --cache --pending-requests-enabled --refuse-any --timeout 5s >"$TMP/dnsproxy.log" 2>&1 &
DNS_PID=$!
ready=0
for _ in $(seq 1 50); do
  a=$(ip netns exec "$NS" getent ahostsv4 example.com 2>/dev/null | awk '{print $1}' | sort -u | tr '\n' ',' || true)
  [ -n "$a" ] && { ready=1; break; }
  sleep .2
done
[ "$ready" = 1 ]
EXAMPLE_HTTP=$(ip netns exec "$NS" curl -4 -sS --connect-timeout 6 --max-time 20 -o /dev/null -w '%{http_code}' https://example.com/)
[ "$EXAMPLE_HTTP" = 200 ]
PROVIDER_IP=$(ip netns exec "$NS" curl -4 -fsS --connect-timeout 4 --max-time 10 https://api.ipify.org | tr -d '[:space:]')

install -d -m 0755 "$(dirname "$OUTPUT")"
QUAL_TMP="$TMP/qualification.json"
python3 - "$TMP/candidate.json" "$QUAL_TMP" "$NODE" "$QUALIFIED" "$HANDSHAKE" "$EXAMPLE_HTTP" "$PROVIDER_IP" "$MAX_SNAPSHOT_AGE" <<'PY'
import datetime,hashlib,json,sys,time
c,out,node,endpoint,hs,example,egress,maxage=sys.argv[1:]
now=int(time.time())
p={
 'schemaVersion':1,'kind':'network-v2.surfshark-wireguard-qualification','truthRole':'physical-provider-endpoint-qualification',
 'provider':'surfshark','node':node,'endpointIp':endpoint,'endpointPort':51820,'transport':'wireguard',
 'sourceSnapshotDigest':json.load(open(c))['snapshotDigest'],
 'handshakeUnix':int(hs),'exampleHttp':int(example),'providerEgressIp':egress,
 'observedAt':datetime.datetime.fromtimestamp(now,datetime.timezone.utc).isoformat().replace('+00:00','Z'),
 'observedUnix':now,'freshnessMaxAgeSeconds':int(maxage),'standingAtObservation':'QUALIFIED_ENDPOINT'
}
canonical=json.dumps(p,sort_keys=True,separators=(',',':')).encode(); p['qualificationDigest']='sha256:'+hashlib.sha256(canonical).hexdigest()
with open(out,'w') as f: json.dump(p,f,indent=2,sort_keys=True); f.write('\n')
PY
PUBLISH="$OUTPUT.tmp.$$"
install -m 0644 "$QUAL_TMP" "$PUBLISH"
mv -f "$PUBLISH" "$OUTPUT"
cat "$OUTPUT"
echo surfshark-live-wireguard-qualification=PASS
