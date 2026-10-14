#!/usr/bin/env bash
set -euo pipefail

ROOT=$(cd "$(dirname "$0")/../../.." && pwd)
LOCK="$ROOT/capabilities/gluetun/external/gluetun-image.lock"
BROWSERLESS="$ROOT/consumers/browserless/config/provider-carrier-gluetun-candidate.json"
digest=$(awk -F= '$1=="amd64Digest"{print $2}' "$LOCK")
test -n "$digest"
image="docker.io/qmcgaw/gluetun@$digest"
podman image exists "$image"
command -v wg >/dev/null
command -v sing-box >/dev/null
test -c /dev/net/tun

suffix=$$
net="nv2-r7-real-$suffix"
ctr="nv2-r7-real-$suffix"
wgif="nv2r7w$suffix"
wgif=$(printf '%s' "$wgif" | tail -c 15)
subnet="10.253.254.0/30"
gateway="10.253.254.1"
container_ip="10.253.254.2"
wg_host="198.51.100.1"
wg_client="198.51.100.2"
udp=$((52000 + suffix % 700))
http=$((18100 + suffix % 500))
tmp=$(mktemp -d /tmp/nv2-r7-real.XXXXXX)
server_pid=
adapter_pid=

cleanup() {
  set +e
  test -n "${adapter_pid:-}" && kill "$adapter_pid" >/dev/null 2>&1
  podman rm -f "$ctr" >/dev/null 2>&1
  test -n "${server_pid:-}" && kill "$server_pid" >/dev/null 2>&1
  ip link del "$wgif" >/dev/null 2>&1
  podman network rm -f "$net" >/dev/null 2>&1
  rm -rf "$tmp"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

! podman container exists "$ctr"
! podman network exists "$net"
! ip link show "$wgif" >/dev/null 2>&1
! ip route show | grep -q "^$subnet "

podman network create --driver bridge --subnet "$subnet" --gateway "$gateway" --opt isolate=strict "$net" >/dev/null
umask 077
wg genkey >"$tmp/host.key"
wg pubkey <"$tmp/host.key" >"$tmp/host.pub"
wg genkey >"$tmp/client.key"
wg pubkey <"$tmp/client.key" >"$tmp/client.pub"
hostpub=$(cat "$tmp/host.pub")
clientpub=$(cat "$tmp/client.pub")
clientkey=$(cat "$tmp/client.key")

ip link add "$wgif" type wireguard
ip addr add "$wg_host/30" dev "$wgif"
wg set "$wgif" listen-port "$udp" private-key "$tmp/host.key" peer "$clientpub" allowed-ips "$wg_client/32"
ip link set "$wgif" up

cat >"$tmp/server.py" <<PY
from http.server import BaseHTTPRequestHandler, HTTPServer
class H(BaseHTTPRequestHandler):
    def do_GET(self):
        body=b"NV2_REAL_GLUETUN_LOCAL_WG_OK"
        self.send_response(200)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
    def log_message(self,*args): pass
HTTPServer(("$wg_host",$http),H).serve_forever()
PY
python3 "$tmp/server.py" >/dev/null 2>&1 &
server_pid=$!

podman run -d --name "$ctr" --network "$net" --ip "$container_ip"   --cap-add NET_ADMIN --cap-add NET_RAW --device /dev/net/tun   -e VPN_SERVICE_PROVIDER=custom -e VPN_TYPE=wireguard   -e WIREGUARD_ENDPOINT_IP="$gateway" -e WIREGUARD_ENDPOINT_PORT="$udp"   -e WIREGUARD_PUBLIC_KEY="$hostpub" -e WIREGUARD_PRIVATE_KEY="$clientkey"   -e WIREGUARD_ADDRESSES="$wg_client/30"   -e HTTPPROXY=on -e FIREWALL_INPUT_PORTS=8888   -e DNS_SERVER=off -e PUBLICIP_ENABLED=off   -e HEALTH_TARGET_ADDRESSES="$wg_host:$http"   -e HEALTH_ICMP_TARGET_IPS="$wg_host"   "$image" >/dev/null

sleep 4
test "$(podman inspect -f '{{.State.Status}}' "$ctr")" = running
handshake=$(wg show "$wgif" latest-handshakes | awk '{print $2}')
test -n "$handshake"
test "$handshake" -gt 0
body=$(curl -fsS --connect-timeout 2 --max-time 5   -x "http://$container_ip:8888" "http://$wg_host:$http/")
test "$body" = NV2_REAL_GLUETUN_LOCAL_WG_OK

set +e
podman run --rm --network "$net" --entrypoint /bin/true "$image" >/dev/null 2>&1
second_peer_rc=$?
podman run --rm --network podman --entrypoint /bin/sh "$image"   -c "nc -z -w2 $container_ip 8888" >/dev/null 2>&1
default_peer_rc=$?
set -e
test "$second_peer_rc" -ne 0
test "$default_peer_rc" -ne 0

wg set "$wgif" peer "$clientpub" remove
sleep 0.5
set +e
curl -fsS --connect-timeout 1 --max-time 3   -x "http://$container_ip:8888" "http://$wg_host:$http/" >/dev/null 2>&1
fail_closed_rc=$?
set -e
test "$fail_closed_rc" -ne 0

wg set "$wgif" peer "$clientpub" allowed-ips "$wg_client/32"
podman restart "$ctr" >/dev/null
sleep 4
body=$(curl -fsS --connect-timeout 2 --max-time 5   -x "http://$container_ip:8888" "http://$wg_host:$http/")
test "$body" = NV2_REAL_GLUETUN_LOCAL_WG_OK

python3 - "$BROWSERLESS" "$tmp/adapter.json" "$container_ip" <<'PY'
import json, socket, sys
from pathlib import Path
source=Path(sys.argv[1]); out=Path(sys.argv[2]); container=sys.argv[3]
cfg=json.loads(source.read_text())
sock=socket.socket(); sock.bind(("127.0.0.1",0)); port=sock.getsockname()[1]; sock.close()
cfg["inbounds"][0].update(listen="127.0.0.1", listen_port=port)
cfg["outbounds"][0].update(server=container, server_port=8888)
out.write_text(json.dumps(cfg))
print(port)
PY
adapter_port=$(python3 -c "import json;print(json.load(open('$tmp/adapter.json'))['inbounds'][0]['listen_port'])")
sing-box check -c "$tmp/adapter.json"
sing-box run -c "$tmp/adapter.json" >"$tmp/adapter.out" 2>"$tmp/adapter.err" &
adapter_pid=$!
for _ in $(seq 1 50); do
  nc -z 127.0.0.1 "$adapter_port" >/dev/null 2>&1 && break
  sleep 0.1
done
body=$(curl -fsS --connect-timeout 2 --max-time 6   -x "http://127.0.0.1:$adapter_port" "http://$wg_host:$http/")
test "$body" = NV2_REAL_GLUETUN_LOCAL_WG_OK
set +e
curl -fsS --connect-timeout 1 --max-time 3   -x "http://127.0.0.1:$adapter_port" http://127.0.0.1:9/ >/dev/null 2>&1
private_rc=$?
set -e
test "$private_rc" -ne 0

printf '{"schemaVersion":1,"kind":"ordivon.network-v2.real-gluetun-local-wireguard-sandbox","standing":"PASS","imageDigest":"%s","realGluetun":true,"localWireguardHandshake":true,"httpProxyOverWireguard":true,"privatePodmanNetwork":true,"secondPeerRejected":true,"defaultBridgePeerDenied":true,"vpnPeerLossFailClosed":true,"restartRecovery":true,"browserlessCandidateAdapterTwoHop":true,"privateDestinationRejected":true,"productionProviderIdentityUsed":false,"productionConfigMutation":false}\n' "$digest"

kill "$adapter_pid" >/dev/null 2>&1 || true
wait "$adapter_pid" 2>/dev/null || true
adapter_pid=
cleanup
trap - EXIT INT TERM
! podman container exists "$ctr"
! podman network exists "$net"
! ip link show "$wgif" >/dev/null 2>&1
