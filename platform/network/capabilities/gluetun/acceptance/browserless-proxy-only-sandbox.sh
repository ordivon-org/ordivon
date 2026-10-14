#!/usr/bin/env bash
set -euo pipefail

# Real Browserless + Chromium proof with NO external route.
# Only a synthetic local HTTP proxy on the same Podman --internal network can
# satisfy the target. Without the launch proxy, the identical Browserless
# request must fail. No provider credential or production config is used.

IMAGE='ghcr.io/browserless/chromium@sha256:b1ba7b054af2891a8199f884d4bd249cf8c3bd2fa8a97b339077e40f92803ba8'
TOKEN='NV2_M4_SYNTHETIC_BROWSERLESS_TOKEN_20261014'
suffix=$$
net="nv2-m4-browserless-$suffix"
proxy="nv2-m4-proxy-$suffix"
browser="nv2-m4-browser-$suffix"
tmp=$(mktemp -d /tmp/nv2-m4-browserless.XXXXXX)

cleanup() {
  set +e
  podman rm -f "$browser" "$proxy" >/dev/null 2>&1
  podman network rm -f "$net" >/dev/null 2>&1
  rm -rf "$tmp"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

podman image exists "$IMAGE"
if podman network exists "$net"; then exit 70; fi
if podman container exists "$proxy"; then exit 70; fi
if podman container exists "$browser"; then exit 70; fi

podman network create --driver bridge --internal "$net" >/dev/null
podman run -d --pull never --name "$proxy" --network "$net"   --entrypoint node "$IMAGE" -e '
const http=require("http");
http.createServer((req,res)=>{
  const body="NV2_BROWSERLESS_PROXY_ONLY_OK";
  res.writeHead(200,{"Content-Type":"text/plain","Content-Length":Buffer.byteLength(body)});
  res.end(body);
}).listen(8888,"0.0.0.0");
' >/dev/null
proxy_ip=$(podman inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' "$proxy")
test -n "$proxy_ip"

podman run -d --pull never --name "$browser" --network "$net"   -e TOKEN="$TOKEN" -e PORT=3000 -e CONCURRENT=1 -e QUEUED=2   -e TIMEOUT=20000 -e HEALTH=false "$IMAGE" >/dev/null
browser_ip=$(podman inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' "$browser")
test -n "$browser_ip"

code=000
for _ in $(seq 1 120); do
  code=$(curl -sS --connect-timeout 1 --max-time 2 -o /dev/null     -w '%{http_code}' "http://$browser_ip:3000/pressure?token=$TOKEN" 2>/dev/null || true)
  test "$code" != 000 && break
  sleep 0.25
done
test "$code" = 200

launch=$(python3 - "$proxy_ip" <<'PY'
import json,sys,urllib.parse
proxy=sys.argv[1]
value={"args":[
    f"--proxy-server=http://{proxy}:8888",
    "--disable-quic",
]}
print(urllib.parse.quote(json.dumps(value,separators=(",",":"))))
PY
)

target='http://198.51.100.77/nv2-m4-probe'
payload=$(printf '{"url":"%s"}' "$target")
curl -fsS --connect-timeout 3 --max-time 25 -H 'Content-Type: application/json'   -d "$payload"   "http://$browser_ip:3000/content?token=$TOKEN&launch=$launch" >"$tmp/proxy.out"
grep -q 'NV2_BROWSERLESS_PROXY_ONLY_OK' "$tmp/proxy.out"

# Same Browserless image/session substrate, but without launch proxy.
# --internal gives the browser no external default path/DNS route, so bypass
# cannot accidentally succeed.
set +e
curl -fsS --connect-timeout 3 --max-time 12 -H 'Content-Type: application/json'   -d "$payload"   "http://$browser_ip:3000/content?token=$TOKEN"   >"$tmp/direct.out" 2>"$tmp/direct.err"
direct_rc=$?
set -e
test "$direct_rc" -ne 0
if grep -q 'NV2_BROWSERLESS_PROXY_ONLY_OK' "$tmp/direct.out"; then exit 71; fi

printf '{"schemaVersion":1,"kind":"ordivon.network-v2.browserless-proxy-only-sandbox","standing":"PASS","browserlessImageDigest":"sha256:b1ba7b054af2891a8199f884d4bd249cf8c3bd2fa8a97b339077e40f92803ba8","podmanInternalNetwork":true,"browserlessRealProcess":true,"chromiumRealLaunch":true,"proxyOnlySyntheticTargetReached":true,"directWithoutProxyFailedClosed":true,"productionProviderIdentityUsed":false,"productionConfigMutation":false}\n'

cleanup
trap - EXIT INT TERM
if podman container exists "$browser"; then exit 72; fi
if podman container exists "$proxy"; then exit 72; fi
if podman network exists "$net"; then exit 72; fi
