#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/.." && pwd)
SOURCE="$ROOT/config/egress.json"
ENDPOINTS=/etc/network-v2/finance/provider-endpoints.json
SING_BOX=${SING_BOX:-/usr/bin/sing-box}
TMP=$(mktemp -d)
PID=
cleanup() {
  if [ -n "${PID:-}" ]; then
    kill "$PID" >/dev/null 2>&1 || true
    wait "$PID" >/dev/null 2>&1 || true
  fi
  rm -rf "$TMP"
}
trap cleanup EXIT
test -r "$ENDPOINTS"
make_candidate() {
  local failed_tag=$1 output=$2
  python3 - "$SOURCE" "$output" "$failed_tag" <<'PY'
import json,sys
source, output, failed = sys.argv[1:]
x=json.load(open(source))
for server in x["dns"]["servers"]:
    if server["tag"] == failed:
        server["server"] = "192.0.2.1"
for inbound in x["inbounds"]:
    inbound["listen_port"] += 10000
for service in x.get("services", []):
    if service.get("type") == "api":
        service["listen_port"] += 10000
x["dns"]["timeout"] = "3s"
x["route"]["rules"][0]["timeout"] = "3s"
json.dump(x,open(output,"w"),indent=2)
open(output,"a").write("\n")
PY
}
wait_listener() {
  local port=$1
  for _ in $(seq 1 40); do
    ss -lntH | awk -v p=":$port" '$4 ~ p"$" {found=1} END{exit !found}' && return 0
    if ! kill -0 "$PID" >/dev/null 2>&1; then
      cat "$TMP/sing-box.stderr" >&2
      return 1
    fi
    sleep 0.25
  done
  return 1
}
run_case() {
  local failed_tag=$1
  local candidate="$TMP/$failed_tag.json"
  make_candidate "$failed_tag" "$candidate"
  "$SING_BOX" check -c "$ENDPOINTS" -c "$candidate"
  "$SING_BOX" run -c "$ENDPOINTS" -c "$candidate" >"$TMP/sing-box.stdout" 2>"$TMP/sing-box.stderr" &
  PID=$!
  wait_listener 29283
  wait_listener 29299
  "$SING_BOX" api --url http://127.0.0.1:29299 group urltest provider-auto >/dev/null
  sleep 4
  "$SING_BOX" api --url http://127.0.0.1:29299 group show provider-auto >/dev/null
  local out="$TMP/$failed_tag-okx.json"
  curl -4 -sS \
    --proxy http://127.0.0.1:29283 \
    --connect-timeout 5 \
    --max-time 12 \
    --retry 2 \
    --retry-all-errors \
    --retry-delay 1 \
    https://openapi.okx.com/api/v5/public/time \
    -o "$out"
  jq -e '.code=="0" and (.data|type)=="array" and (.data|length>=1)' "$out" >/dev/null
  kill "$PID"
  wait "$PID" >/dev/null 2>&1 || true
  PID=
  echo "finance-dns-race-$failed_tag=PASS"
}
run_case provider-dns-1
run_case provider-dns-2
