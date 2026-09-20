#!/usr/bin/env bash
set -euo pipefail

SCRIPT=$(readlink -f "$0")
ROOT=$(cd "$(dirname "$SCRIPT")/../.." && pwd)
SURFPATH=${SURFPATH:-/root/tools/bin/surfpath}
EXTERIOR_ANCHOR=${EXTERIOR_ANCHOR:-/root/tools/bin/exterior-anchor}
TEMPORAL=${TEMPORAL:-/opt/ordivon/external/temporal-cli/1.8.3/temporal}
STATE=/run/ordivon/network-v2-browserless-cutover-state.json
RECEIPT_DIR=/var/lib/network-v2/browserless-cutover
NS=nv2-browserless-prod
WG_IF=nv2blwg
PROFILE=/etc/network-v2/browserless/$WG_IF.conf
ENV_FILE=/etc/network-v2/browserless/provider.env
CATALOG_MANIFEST=/etc/network-v2/providers/catalog-profiles/MANIFEST.tsv
ANCHOR_NAME=chatgpt-browserless-r1
ANCHOR_UNIT=ordivon-exterior-anchor-chatgpt-browserless-r1.service
RUNTIME_STATE=/root/.local/state/ordivon-workstation/exterior-anchors/$ANCHOR_NAME/runtime-state.json
CONFIG=/etc/ordivon/agent-automation-browserless.json
QUADLET=/etc/containers/systemd/ordivon-browserless@.container
OPERATOR=/etc/systemd/system/ordivon-browserless-operator-proxy@.service
RECOVER_PATH=ordivon-browserless-anchor-recover.path
RECON_PATH=ordivon-browserless-netns-reconcile.path
RECOVER_SERVICE=ordivon-browserless-anchor-recover.service
RECON_SERVICE=ordivon-browserless-netns-reconcile.service

verify_browserless() {
  local token code
  token=$(cat /etc/ordivon/browserless.token)
  for i in 11 12 13; do
    code=''
    for _ in $(seq 1 100); do
      code=$(curl -sS --connect-timeout 2 --max-time 5 -o "/tmp/nv2-browserless-$i-version.json" -w '%{http_code}' \
        "http://127.0.0.1:131$i/json/version?token=$token" 2>/dev/null || true)
      [ "$code" = 200 ] && break
      sleep .5
    done
    [ "$code" = 200 ]
  done
  code=$(curl -sS --connect-timeout 5 --max-time 45 -o /tmp/nv2-browserless-production-chatgpt.html -w '%{http_code}' \
    -H 'content-type: application/json' -d '{"url":"https://chatgpt.com/"}' \
    "http://127.0.0.1:13111/content?token=$token")
  [ "$code" = 200 ]
  grep -Eqi 'chatgpt|openai|challenge' /tmp/nv2-browserless-production-chatgpt.html
  echo browserless-production-real-browser=PASS
}

rollback_after_lease() {
  [ -f "$STATE" ] || return 0
  local backup
  backup=$(jq -r '.backupDir' "$STATE")
  echo "browserless cutover failed; restoring legacy production from $backup" >&2
  set +e
  systemctl stop ordivon-browserless-operator-proxy@11.service ordivon-browserless-operator-proxy@12.service ordivon-browserless-operator-proxy@13.service >/dev/null 2>&1
  systemctl stop ordivon-browserless@11.service ordivon-browserless@12.service ordivon-browserless@13.service >/dev/null 2>&1
  systemctl disable --now network-v2-browserless.target >/dev/null 2>&1
  [ -f "$backup/browserless.container" ] && install -m 0644 "$backup/browserless.container" "$QUADLET"
  [ -f "$backup/operator.service" ] && install -m 0644 "$backup/operator.service" "$OPERATOR"
  [ -f "$backup/agent-config.json" ] && install -m 0600 "$backup/agent-config.json" "$CONFIG"
  systemctl daemon-reload >/dev/null 2>&1
  systemctl enable "$RECOVER_SERVICE" "$RECON_SERVICE" >/dev/null 2>&1 || true
  systemctl enable --now "$RECOVER_PATH" "$RECON_PATH" >/dev/null 2>&1 || true
  systemctl reset-failed "$RECOVER_SERVICE" "$RECON_SERVICE" "$ANCHOR_UNIT" >/dev/null 2>&1 || true
  systemctl start "$RECOVER_SERVICE" >/dev/null 2>&1 || true
  for _ in $(seq 1 120); do
    [ "$(systemctl is-active "$ANCHOR_UNIT" 2>/dev/null)" = active ] && break
    sleep .25
  done
  if [ "$(systemctl is-active "$ANCHOR_UNIT" 2>/dev/null)" != active ]; then
    # Legacy recovery requires a fresh Surfpath observation. Refresh it only on rollback;
    # the Network v2 production path itself never depends on Surfpath discovery.
    systemctl start ordivon-surfshark-hot.service >/dev/null 2>&1 || true
    for _ in $(seq 1 240); do
      state=$(systemctl is-active ordivon-surfshark-hot.service 2>/dev/null || true)
      [ "$state" != activating ] && [ "$state" != active ] && break
      sleep .25
    done
    systemctl start "$RECOVER_SERVICE" >/dev/null 2>&1 || true
    for _ in $(seq 1 180); do
      [ "$(systemctl is-active "$ANCHOR_UNIT" 2>/dev/null)" = active ] && break
      sleep .25
    done
  fi
  systemctl start "$RECON_SERVICE" >/dev/null 2>&1 || true
  for _ in $(seq 1 120); do
    [ "$(systemctl is-active ordivon-browserless@11.service 2>/dev/null)" = active ] && \
    [ "$(systemctl is-active ordivon-browserless@12.service 2>/dev/null)" = active ] && \
    [ "$(systemctl is-active ordivon-browserless@13.service 2>/dev/null)" = active ] && break
    sleep .25
  done
  systemctl start ordivon-browserless-operator-proxy@11.service ordivon-browserless-operator-proxy@12.service ordivon-browserless-operator-proxy@13.service >/dev/null 2>&1 || true
  verify_browserless >/dev/null 2>&1 || true
  rm -f "$STATE"
  set -e
}

if [ "${NETWORK_V2_BROWSERLESS_CUTOVER_INNER:-0}" != 1 ]; then
  rm -f "$STATE"
  set +e
  if [ "${NETWORK_V2_BROWSERLESS_DIRECT_QUIESCED:-0}" = 1 ]; then
    # Migration-only path: old Surfpath graduation status can report FREE while
    # ordinary workers still hold shared flock state. The caller must quiesce all
    # old mutators first; refuse direct promotion if any Surfpath lock remains.
    if lslocks -o PATH 2>/dev/null | grep -Eq '/run/ordivon/surfpath-(graduation|mutation-drain)\.lock|/run/ordivon/surfpath\.lock'; then
      echo 'direct quiesced promotion refused: Surfpath lock still held' >&2
      rc=70
    else
      /usr/bin/env NETWORK_V2_BROWSERLESS_CUTOVER_INNER=1 "$SCRIPT"
      rc=$?
    fi
  else
    "$SURFPATH" graduation-lease --owner network-v2-browserless-production-cutover --timeout-seconds 30 -- \
      /usr/bin/env NETWORK_V2_BROWSERLESS_CUTOVER_INNER=1 "$SCRIPT"
    rc=$?
  fi
  set -e
  if [ "$rc" -ne 0 ]; then
    rollback_after_lease
    exit "$rc"
  fi
  rm -f "$STATE"
  exit 0
fi

# No cutover while an Agent Automation occurrence is active.
"$TEMPORAL" workflow list --address 127.0.0.1:17233 --namespace default \
  --query 'ExecutionStatus="Running" AND TaskQueue="ordivon-agent-automation"' --limit 100 --output json >/tmp/nv2-browserless-running.json
[ "$(jq 'length' /tmp/nv2-browserless-running.json)" -eq 0 ]

for x in "$EXTERIOR_ANCHOR" /usr/local/libexec/network-v2/wireguard-go /usr/bin/dnsproxy /usr/bin/yq /usr/bin/jq; do [ -x "$x" ]; done
for f in "$RUNTIME_STATE" "$CATALOG_MANIFEST" "$CONFIG" "$QUADLET" "$OPERATOR"; do [ -f "$f" ]; done

OLD_GEN=$(jq -r '.generationDigest' "$RUNTIME_STATE")
OLD_NS=$(jq -r '.namespace' "$RUNTIME_STATE")
LEGACY_ENDPOINT=$(jq -r '.endpointIp' "$RUNTIME_STATE")
ENDPOINT=$(awk -F '\t' '$1=="kr-seo"{print $2; exit}' "$CATALOG_MANIFEST")
SOURCE_PROFILE=$(awk -F '\t' '$1=="kr-seo"{print $4; exit}' "$CATALOG_MANIFEST")
SOURCE_DIGEST=$(awk -F '\t' '$1=="kr-seo"{print $5; exit}' "$CATALOG_MANIFEST")
[ "$(jq -r '.recoveryState' "$RUNTIME_STATE")" = healthy ]
[[ "$OLD_GEN" == sha256:* ]]
[[ "$LEGACY_ENDPOINT" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]
[[ "$ENDPOINT" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]
[ -f "$SOURCE_PROFILE" ]
[ "sha256:$(sha256sum "$SOURCE_PROFILE" | awk '{print $1}')" = "$SOURCE_DIGEST" ]

mkdir -p "$RECEIPT_DIR" /etc/network-v2/browserless
BACKUP="$RECEIPT_DIR/backup-$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$BACKUP"
install -m 0644 "$QUADLET" "$BACKUP/browserless.container"
install -m 0644 "$OPERATOR" "$BACKUP/operator.service"
install -m 0600 "$CONFIG" "$BACKUP/agent-config.json"
jq -n --arg backup "$BACKUP" --arg oldGen "$OLD_GEN" --arg oldNs "$OLD_NS" --arg legacyEndpoint "$LEGACY_ENDPOINT" --arg endpoint "$ENDPOINT" \
  '{schemaVersion:1,backupDir:$backup,oldGeneration:$oldGen,oldNamespace:$oldNs,legacyEndpoint:$legacyEndpoint,endpoint:$endpoint}' >"$STATE"

# Production authority comes from the Network v2 catalog, never from the legacy Surfpath endpoint.
EP="$ENDPOINT:51820" yq -p=ini -o=ini \
  'del(.Interface.DNS) | .Interface.Table="off" | .Interface.MTU="1280" | .Peer.Endpoint=strenv(EP) | .Peer.PersistentKeepalive="5"' \
  "$SOURCE_PROFILE" >"$PROFILE"
chmod 0600 "$PROFILE"
cat >"$ENV_FILE" <<EOF
HOST_IF=nv2blph
NS_IF=nv2blpn
HOST_ADDR=10.252.246.1/30
NS_ADDR=10.252.246.2/30
NS_CIDR=10.252.246.0/30
HOST_IP=10.252.246.1
ENDPOINT=$ENDPOINT
PROFILE=$PROFILE
WG_IF=$WG_IF
EOF
chmod 0600 "$ENV_FILE"
mkdir -p "/etc/netns/$NS"
printf 'nameserver 127.0.0.1\noptions timeout:2 attempts:2\n' >"/etc/netns/$NS/resolv.conf"
awk 'BEGIN{done=0} /^hosts:/{print "hosts: files dns";done=1;next} {print} END{if(!done)print "hosts: files dns"}' \
  /etc/nsswitch.conf >"/etc/netns/$NS/nsswitch.conf"

for f in "$ROOT"/consumers/browserless/systemd/network-v2-browserless-netns.service \
         "$ROOT"/consumers/browserless/systemd/network-v2-browserless-forward.service \
         "$ROOT"/consumers/browserless/systemd/network-v2-browserless-wireguard.service \
         "$ROOT"/consumers/browserless/systemd/network-v2-browserless-dns.service \
         "$ROOT"/consumers/browserless/systemd/network-v2-browserless.target; do
  install -m 0644 "$f" "/etc/systemd/system/$(basename "$f")"
done
systemd-analyze verify "$ROOT"/consumers/browserless/systemd/network-v2-browserless-*.service "$ROOT"/consumers/browserless/systemd/network-v2-browserless.target
systemctl daemon-reload

# Fence the legacy auto-recovery before releasing its exact generation.
systemctl stop "$RECOVER_PATH" "$RECON_PATH"
systemctl stop ordivon-browserless-operator-proxy@11.service ordivon-browserless-operator-proxy@12.service ordivon-browserless-operator-proxy@13.service
systemctl stop ordivon-browserless@11.service ordivon-browserless@12.service ordivon-browserless@13.service

set +e
"$EXTERIOR_ANCHOR" stop --name "$ANCHOR_NAME" --expect-generation "$OLD_GEN" >/tmp/nv2-browserless-stop.json
stop_rc=$?
set -e
[ "$stop_rc" -eq 0 ] || [ -s /tmp/nv2-browserless-stop.json ]
REQUEST=$(jq -r '.requestDigest // empty' /tmp/nv2-browserless-stop.json)
if [ -n "$REQUEST" ]; then
  set +e
  "$EXTERIOR_ANCHOR" reconcile-stop --name "$ANCHOR_NAME" --request "$REQUEST" --budget-seconds 60 >/tmp/nv2-browserless-reconcile.json
  set -e
fi
if [ -e "/run/netns/$OLD_NS" ]; then
  "$EXTERIOR_ANCHOR" stop --name "$ANCHOR_NAME" --expect-generation "$OLD_GEN" >/tmp/nv2-browserless-stop2.json || true
fi
[ ! -e "/run/netns/$OLD_NS" ]
echo legacy_browserless_generation_released=PASS

# Start the mature Network v2 production data plane over the host's normal underlay.
systemctl start network-v2-browserless.target
"$ROOT/consumers/browserless/acceptance/production-path.sh"

GEN="sha256:$(cat "$PROFILE" "$ROOT"/consumers/browserless/systemd/network-v2-browserless-* | sha256sum | awk '{print $1}')"
python3 - "$QUADLET" "$OPERATOR" "$CONFIG" "$GEN" <<'PY'
import json,re,sys
quadlet,operator,config,generation=sys.argv[1:]
q=open(quadlet,encoding='utf-8').read()
q=re.sub(r'BindsTo=ordivon-exterior-anchor-chatgpt-browserless-r1\.service', 'BindsTo=network-v2-browserless.target', q)
q=re.sub(r'After=ordivon-exterior-anchor-chatgpt-browserless-r1\.service', 'After=network-v2-browserless.target', q)
q=re.sub(r'Network=ns:/run/netns/[^\n]+', 'Network=ns:/run/netns/nv2-browserless-prod', q)
open(quadlet,'w',encoding='utf-8').write(q)
o=open(operator,encoding='utf-8').read()
o=re.sub(r'BindsTo=ordivon-exterior-anchor-chatgpt-browserless-r1\.service', 'BindsTo=network-v2-browserless.target', o)
o=re.sub(r'After=ordivon-exterior-anchor-chatgpt-browserless-r1\.service', 'After=network-v2-browserless.target', o)
o=re.sub(r'ip netns exec [^ ]+ ', 'ip netns exec nv2-browserless-prod ', o)
open(operator,'w',encoding='utf-8').write(o)
c=json.load(open(config,encoding='utf-8'))
c['browserNetworkAuthority']={'kind':'network-v2','name':'browserless-prod','generationDigest':generation,'serviceUnit':'network-v2-browserless.target'}
for ep in c['browserSubstrate']['endpoints']:
    ep['networkNamespace']='nv2-browserless-prod'
with open(config,'w',encoding='utf-8') as f:
    json.dump(c,f,sort_keys=True,indent=2); f.write('\n')
PY
chmod 0644 "$QUADLET" "$OPERATOR"
chmod 0600 "$CONFIG"
systemctl daemon-reload
systemctl reset-failed network-v2-browserless.target network-v2-browserless-netns.service network-v2-browserless-wireguard.service network-v2-browserless-dns.service \
  ordivon-browserless@11.service ordivon-browserless@12.service ordivon-browserless@13.service >/dev/null 2>&1 || true
systemctl start ordivon-browserless-display@11.service ordivon-browserless-display@12.service ordivon-browserless-display@13.service
systemctl start ordivon-browserless@11.service ordivon-browserless@12.service ordivon-browserless@13.service
systemctl start ordivon-browserless-operator-proxy@11.service ordivon-browserless-operator-proxy@12.service ordivon-browserless-operator-proxy@13.service
verify_browserless

systemctl enable network-v2-browserless.target >/dev/null
systemctl disable "$RECOVER_PATH" "$RECON_PATH" "$RECOVER_SERVICE" "$RECON_SERVICE" >/dev/null 2>&1 || true

# Consumer services are deliberately not restarted or required here. Network owns the Browserless path; upper-layer consumers observe/reconcile the new generation through their own lifecycle.

# Egress-IP collection is supplemental evidence only. Core production acceptance above
# already proved the provider path and a real Browserless ChatGPT navigation.
PROVIDER_IP=$(ip netns exec "$NS" curl -4 -fsS --connect-timeout 2 --max-time 5 https://api.ipify.org 2>/dev/null | tr -d '[:space:]' || true)
[ -n "$PROVIDER_IP" ] || PROVIDER_IP=unavailable
jq -n --arg cutoverAt "$(date -u +%Y-%m-%dT%H:%M:%SZ)" --arg generation "$GEN" --arg endpoint "$ENDPOINT" \
  --arg providerIp "$PROVIDER_IP" --arg oldGeneration "$OLD_GEN" --arg oldNamespace "$OLD_NS" --arg backup "$BACKUP" \
  '{schemaVersion:1,standing:"PRODUCTION_CUTOVER_PASS",cutoverAt:$cutoverAt,generationDigest:$generation,endpoint:$endpoint,providerEgress:$providerIp,legacyGeneration:$oldGeneration,legacyNamespace:$oldNamespace,backupDir:$backup}' \
  >"$RECEIPT_DIR/production-cutover.json"
rm -f "$STATE"
echo network-v2-browserless-production-cutover=PASS
