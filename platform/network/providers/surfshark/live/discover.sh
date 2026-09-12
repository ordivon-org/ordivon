#!/usr/bin/env bash
set -euo pipefail

LOCK=${LOCK:-providers/surfshark/external/gluetun.lock}
OUTPUT=${OUTPUT:-/var/lib/network-v2/providers/surfshark/live/latest.json}
MAX_AGE_SECONDS=${MAX_AGE_SECONDS:-300}
NETNS=${NETNS:-}

value(){ awk -F= -v k="$1" '$1==k{print substr($0,index($0,"=")+1);exit}' "$LOCK"; }
BINARY=${GLUETUN_BINARY:-$(value install)}
EXPECTED_SHA=$(value sha256)
REVISION=$(value revision)
TAG=$(value tag)
MINRATIO=${MINRATIO:-$(value minratio)}

[ -x "$BINARY" ]
[ "$(sha256sum "$BINARY" | awk '{print $1}')" = "$EXPECTED_SHA" ]
python3 - "$MINRATIO" <<'PY'
import sys
try: v=float(sys.argv[1])
except ValueError: raise SystemExit('invalid minratio')
if not (0 < v <= 1): raise SystemExit('minratio must be in (0,1]')
PY

TMP=$(mktemp -d /tmp/network-v2-surfshark-live.XXXXXX)
cleanup(){ rm -rf "$TMP"; }
trap cleanup EXIT
mkdir -p "$TMP/internal/storage"
if [ -n "$NETNS" ]; then
  ip netns list | awk '{print $1}' | grep -qx "$NETNS"
  (cd "$TMP" && ip netns exec "$NETNS" "$BINARY" update -maintainer -providers surfshark -minratio "$MINRATIO") >"$TMP/update.log" 2>&1
else
  (cd "$TMP" && "$BINARY" update -maintainer -providers surfshark -minratio "$MINRATIO") >"$TMP/update.log" 2>&1
fi
RAW="$TMP/internal/storage/servers.json"
[ -s "$RAW" ]

python3 - "$RAW" "$TMP/evidence.json" "$REVISION" "$TAG" "$EXPECTED_SHA" "$MINRATIO" "$MAX_AGE_SECONDS" "$NETNS" <<'PY'
import datetime,hashlib,json,sys,time
src,out,revision,tag,binary_sha,minratio,max_age,netns=sys.argv[1:]
max_age=int(max_age); minratio=float(minratio)
d=json.load(open(src))
s=d.get('surfshark')
if not isinstance(s,dict): raise SystemExit('missing surfshark provider data')
servers=s.get('servers')
if not isinstance(servers,list) or not servers: raise SystemExit('empty surfshark server set')
ts=int(s.get('timestamp') or 0)
now=int(time.time()); age=max(0,now-ts)
if ts<=0 or age>max_age: raise SystemExit(f'live snapshot stale: age={age}s max={max_age}s')
wg=[x for x in servers if x.get('vpn')=='wireguard' and x.get('hostname') and x.get('wgpubkey') and x.get('ips')]
ovpn=[x for x in servers if x.get('vpn')=='openvpn' and x.get('hostname') and x.get('ips')]
if not wg: raise SystemExit('no actionable wireguard candidates')
# Candidate discovery is intentionally not a completeness claim. Gluetun's default
# 0.8 gate is stronger and currently fails for Surfshark; this lower bounded gate
# exists only to obtain fresh candidates which still require physical qualification.
providers={}
for row in servers:
    host=row.get('hostname')
    if not host: continue
    ent=providers.setdefault(host,{'hostname':host,'country':row.get('country'),'region':row.get('region'),'city':row.get('city'),'wireguard':None,'openvpn':None})
    if row.get('vpn')=='wireguard':
        ent['wireguard']={'wgpubkey':row.get('wgpubkey'),'ips':sorted(set(row.get('ips') or []))}
    elif row.get('vpn')=='openvpn':
        ent['openvpn']={'tcp':bool(row.get('tcp')),'udp':bool(row.get('udp')),'ips':sorted(set(row.get('ips') or []))}
payload={
 'schemaVersion':1,
 'kind':'network-v2.surfshark-live-candidate-snapshot',
 'truthRole':'provider-live-candidate-discovery',
 'provider':'surfshark',
 'observedAt':datetime.datetime.fromtimestamp(ts,datetime.timezone.utc).isoformat().replace('+00:00','Z'),
 'observedUnix':ts,
 'ageSecondsAtProjection':age,
 'freshnessMaxAgeSeconds':max_age,
 'source':{
   'implementation':'qdm12/gluetun',
   'tag':tag,
   'revision':revision,
   'binarySha256':'sha256:'+binary_sha,
   'minRatio':minratio,
   'defaultMinRatioCompletenessSatisfied':False,
   'completenessClaim':False,
   'discoveryNetworkNamespace':netns or None,
 },
 'counts':{'normalizedServers':len(servers),'wireguardEntries':len(wg),'openvpnEntries':len(ovpn),'hostnames':len(providers)},
 'candidates':sorted(providers.values(),key=lambda x:x['hostname']),
 'standingAtObservation':'FRESH_PARTIAL_CANDIDATE_SNAPSHOT'
}
canonical=json.dumps(payload,sort_keys=True,separators=(',',':')).encode()
payload['snapshotDigest']='sha256:'+hashlib.sha256(canonical).hexdigest()
with open(out,'w') as f: json.dump(payload,f,indent=2,sort_keys=True); f.write('\n')
PY

install -d -m 0755 "$(dirname "$OUTPUT")"
PUBLISH="$OUTPUT.tmp.$$"
install -m 0644 "$TMP/evidence.json" "$PUBLISH"
mv -f "$PUBLISH" "$OUTPUT"
cat "$OUTPUT"
echo surfshark-live-candidate-discovery=PASS
