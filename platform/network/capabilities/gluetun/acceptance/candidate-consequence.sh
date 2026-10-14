#!/usr/bin/env bash
set -euo pipefail
if test "$#" -gt 0; then PROXY=$1; else PROXY=http://10.252.246.2:19680; fi
PRIVATE_WITNESS_BIND=${PRIVATE_WITNESS_BIND:-10.252.246.1}

head_code() {
  local url=$1 allowed=$2 code
  code=$(curl -4 --noproxy "" -x "$PROXY" -I -sS --connect-timeout 6 --max-time 15 -o /dev/null -w '%{http_code}' "$url")
  if ! [[ "$code" =~ ^($allowed)$ ]]; then
    echo "unexpected HTTP consequence $code for $url" >&2
    return 1
  fi
  printf '%s' "$code"
}

openai=$(head_code https://api.openai.com/v1/models '401|403')
anthropic=$(head_code https://api.anthropic.com/ '401|403|404|405')
registry=$(head_code https://registry-1.docker.io/v2/ '200|401')
deepseek=$(head_code https://api.deepseek.com/ '401|403|404')
xapi=$(head_code https://api.x.com/ '401|403|404')

tmpdir=$(mktemp -d)
okx_file="$tmpdir/okx.json"
binance_file="$tmpdir/binance.json"
port_file="$tmpdir/private.port"
count_file="$tmpdir/private.count"
: >"$count_file"
witness_pid=
cleanup() {
  if test -n "$witness_pid"; then kill "$witness_pid" >/dev/null 2>&1 || true; wait "$witness_pid" >/dev/null 2>&1 || true; fi
  rm -rf "$tmpdir"
}
trap cleanup EXIT INT TERM

curl -4 --noproxy "" -fsS -x "$PROXY" --connect-timeout 6 --max-time 15 \
  https://openapi.okx.com/api/v5/public/time -o "$okx_file"
jq -e '.code=="0" and (.data|type)=="array" and (.data|length>=1)' "$okx_file" >/dev/null
curl -4 --noproxy "" -fsS -x "$PROXY" --connect-timeout 6 --max-time 15 \
  https://data-api.binance.vision/api/v3/time -o "$binance_file"
jq -e '(.serverTime|type)=="number"' "$binance_file" >/dev/null

python3 -c '
import socket,sys,time
bind,portf,countf=sys.argv[1:]
s=socket.socket(); s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
s.bind((bind,0)); s.listen(8); s.settimeout(0.5)
open(portf,"w").write(str(s.getsockname()[1]))
deadline=time.time()+20
while time.time()<deadline:
    try: c,_=s.accept()
    except socket.timeout: continue
    with c:
        with open(countf,"a") as f: f.write("1\n"); f.flush()
        try: c.recv(8192)
        except Exception: pass
        try: c.sendall(b"HTTP/1.1 200 OK\r\nContent-Length: 2\r\nConnection: close\r\n\r\nOK")
        except Exception: pass
' "$PRIVATE_WITNESS_BIND" "$port_file" "$count_file" &
witness_pid=$!
for _ in $(seq 1 50); do test -s "$port_file" && break; sleep 0.05; done
test -s "$port_file"
private_port=$(cat "$port_file")
/usr/bin/curl -4 --noproxy "*" -fsS --connect-timeout 2 --max-time 4 \
  "http://$PRIVATE_WITNESS_BIND:$private_port/" >/dev/null
for _ in $(seq 1 30); do
  test "$(wc -l <"$count_file")" -ge 1 && break
  sleep 0.05
done
test "$(wc -l <"$count_file")" -eq 1

set +e
curl -4 --noproxy "" -x "$PROXY" -fsS --connect-timeout 2 --max-time 5 \
  "http://$PRIVATE_WITNESS_BIND:$private_port/" >/dev/null 2>&1
private_rc=$?
set -e
sleep 0.15
private_hits=$(wc -l <"$count_file")
test "$private_rc" -ne 0
test "$private_hits" -eq 1

printf '{"schemaVersion":1,"kind":"ordivon.network-v2.provider-carrier-candidate-consequence","standing":"PASS","proxy":"%s","openaiHttp":%s,"anthropicHttp":%s,"registryHttp":%s,"deepseekHttp":%s,"xHttp":%s,"okx":"PASS","binance":"PASS","privateDestination":"REJECTED_WITH_REACHABLE_WITNESS","mechanismNeutral":true}\n' \
  "$PROXY" "$openai" "$anthropic" "$registry" "$deepseek" "$xapi"
