#!/usr/bin/env bash
set -euo pipefail
SITE=${1:-th-bkk}
NS=nv2-browserless-prod
WG=network-v2-browserless-wireguard.service
DNS=network-v2-browserless-dns.service
CARRIER=network-v2-browserless-provider-carrier.service
PROFILE=/etc/network-v2/browserless/nv2blwg.conf
ENV_FILE=/etc/network-v2/browserless/provider.env
MANIFEST=/etc/network-v2/providers/catalog-profiles/MANIFEST.tsv
STATE_DIR=/var/lib/network-v2/browserless-provider-switch
STATE=$STATE_DIR/current-state.json
READY=${NETWORK_V2_PROVIDER_READY:-/usr/local/libexec/network-v2/browserless-provider-carrier-ready}
PRODUCTION_PATH=${NETWORK_V2_BROWSERLESS_PRODUCTION_PATH:-/usr/local/libexec/network-v2/browserless-production-path}
TEMPORAL=${TEMPORAL:-/opt/ordivon/external/temporal-cli/1.8.3/temporal}
mkdir -p "$STATE_DIR"

[ -e "/run/netns/$NS" ]
for u in network-v2-browserless-netns.service network-v2-browserless-forward.service; do systemctl is-active --quiet "$u"; done
[ -f "$MANIFEST" ]
row=$(awk -F '\t' -v site="$SITE" '$1==site{print; exit}' "$MANIFEST")
[ -n "$row" ]
tab=$(printf '\t')
IFS="$tab" read -r node endpoint iface source_profile source_digest <<<"$row"
[ "$node" = "$SITE" ]
[[ "$endpoint" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]
[ -f "$source_profile" ]
[ "sha256:$(sha256sum "$source_profile" | awk '{print $1}')" = "$source_digest" ]

# Do not change the sole shared identity while Agent Automation is actively using Browserless.
if [ -x "$TEMPORAL" ]; then
  "$TEMPORAL" workflow list --address 127.0.0.1:17233 --namespace default \
    --query 'ExecutionStatus="Running" AND TaskQueue="ordivon-agent-automation"' --limit 100 --output json >/tmp/nv2-provider-switch-running.json
  [ "$(jq 'length' /tmp/nv2-provider-switch-running.json)" -eq 0 ]
fi

old_site=$(awk -F= '$1=="PROVIDER_SITE"{print $2}' "$ENV_FILE" 2>/dev/null || true)
old_endpoint=$(awk -F= '$1=="ENDPOINT"{print $2}' "$ENV_FILE")
if [ "$old_site" = "$SITE" ] && [ "$old_endpoint" = "$endpoint" ]; then
  systemctl start "$WG" "$DNS" "$CARRIER"
  "$PRODUCTION_PATH"
  "$READY"
  printf '{"schemaVersion":1,"kind":"ordivon.network-v2.provider-switch","standing":"ALREADY_SELECTED","providerSite":"%s","endpoint":"%s"}\n' "$SITE" "$endpoint"
  exit 0
fi

stamp=$(date -u +%Y%m%dT%H%M%SZ)
backup=$STATE_DIR/backup-$stamp
mkdir -p "$backup"
install -m 0600 "$PROFILE" "$backup/profile"
install -m 0600 "$ENV_FILE" "$backup/env"
jq -n --arg startedAt "$stamp" --arg oldSite "$old_site" --arg oldEndpoint "$old_endpoint" --arg newSite "$SITE" --arg newEndpoint "$endpoint" --arg backup "$backup" \
  '{schemaVersion:1,standing:"SWITCHING",startedAt:$startedAt,oldSite:$oldSite,oldEndpoint:$oldEndpoint,newSite:$newSite,newEndpoint:$newEndpoint,backupDir:$backup}' >"$STATE"

rollback() {
  set +e
  systemctl stop "$CARRIER" "$DNS" "$WG" >/dev/null 2>&1 || true
  install -m 0600 "$backup/profile" "$PROFILE"
  install -m 0600 "$backup/env" "$ENV_FILE"
  systemctl start "$WG" >/dev/null 2>&1 || true
  systemctl start "$DNS" >/dev/null 2>&1 || true
  systemctl start "$CARRIER" >/dev/null 2>&1 || true
  "$PRODUCTION_PATH" >/dev/null 2>&1 || true
  rm -f "$STATE"
  set -e
}
trap rollback ERR INT TERM

# Stop the old session while its old profile/environment are still intact so its route and interface cleanly release.
systemctl stop "$CARRIER" "$DNS" "$WG"

tmp_profile=$(mktemp "$STATE_DIR/profile.XXXXXX")
tmp_env=$(mktemp "$STATE_DIR/env.XXXXXX")
trap 'rm -f "$tmp_profile" "$tmp_env"' EXIT
EP="$endpoint:51820" yq -p=ini -o=ini \
  'del(.Interface.DNS) | .Interface.Table="off" | .Interface.MTU="1280" | .Peer.Endpoint=strenv(EP) | .Peer.PersistentKeepalive="5"' \
  "$source_profile" >"$tmp_profile"
chmod 0600 "$tmp_profile"
WG_QUICK_USERSPACE_IMPLEMENTATION=/usr/local/libexec/network-v2/wireguard-go wg-quick strip "$tmp_profile" >/dev/null
python3 - "$ENV_FILE" "$tmp_env" "$SITE" "$endpoint" <<'PY'
import sys
src,dst,site,endpoint=sys.argv[1:]
lines=open(src,encoding='utf-8').read().splitlines()
out=[]; seen_site=False; seen_ep=False
for line in lines:
    if line.startswith('ENDPOINT='):
        line='ENDPOINT='+endpoint; seen_ep=True
    elif line.startswith('PROVIDER_SITE='):
        line='PROVIDER_SITE='+site; seen_site=True
    out.append(line)
if not seen_ep: out.append('ENDPOINT='+endpoint)
if not seen_site: out.append('PROVIDER_SITE='+site)
open(dst,'w',encoding='utf-8').write('\n'.join(out)+'\n')
PY
chmod 0600 "$tmp_env"
install -m 0600 "$tmp_profile" "$PROFILE"
install -m 0600 "$tmp_env" "$ENV_FILE"

systemctl start "$WG"
systemctl start "$DNS"
systemctl start "$CARRIER"
"$PRODUCTION_PATH"
"$READY"
actual=$(ip netns exec "$NS" wg show nv2blwg endpoints | awk 'NR==1{print $2}')
case "$actual" in "$endpoint":*) ;; *) echo "provider endpoint mismatch: $actual" >&2; false;; esac
completed=$(date -u +%Y-%m-%dT%H:%M:%SZ)
jq -n --arg completedAt "$completed" --arg oldSite "$old_site" --arg oldEndpoint "$old_endpoint" --arg providerSite "$SITE" --arg endpoint "$endpoint" --arg actualEndpoint "$actual" \
  '{schemaVersion:1,kind:"ordivon.network-v2.provider-switch",standing:"PASS",completedAt:$completedAt,oldSite:$oldSite,oldEndpoint:$oldEndpoint,providerSite:$providerSite,endpoint:$endpoint,actualEndpoint:$actualEndpoint,namespacePreserved:true}' \
  >"$STATE_DIR/provider-switch.json"
rm -f "$STATE"
trap - ERR INT TERM
printf '{"schemaVersion":1,"kind":"ordivon.network-v2.provider-switch","standing":"PASS","providerSite":"%s","endpoint":"%s","namespacePreserved":true}\n' "$SITE" "$endpoint"
