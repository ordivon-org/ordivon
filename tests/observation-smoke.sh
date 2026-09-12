#!/usr/bin/env bash
set -euo pipefail
DNS_UNIT=network-v2-r0-observe-dns-smoke.service
BB_UNIT=network-v2-r0-blackbox-smoke.service
PROM_UNIT=network-v2-r0-prometheus-smoke.service
DATA=$(mktemp -d /tmp/network-v2-prometheus.XXXXXX)
pick_port(){ for p in "$@"; do if ! ss -ltnH "sport = :$p" | grep -q .; then echo "$p"; return 0; fi; done; return 1; }
BB_PORT=$(pick_port 39115 39116 39117 39118)
PROM_PORT=$(pick_port 39090 39091 39092 39093)
cleanup(){
  systemctl stop "$PROM_UNIT" "$BB_UNIT" "$DNS_UNIT" 2>/dev/null || true
  systemctl reset-failed "$PROM_UNIT" "$BB_UNIT" "$DNS_UNIT" 2>/dev/null || true
  rm -rf "$DATA"
}
trap cleanup EXIT
cleanup
mkdir -p "$DATA"

systemd-run --quiet --unit="$DNS_UNIT" --property=Type=simple --property=Restart=no \
  /usr/bin/dnsproxy -l 127.0.0.1 -p 25355 -u 1.1.1.1:53 -u 8.8.8.8:53 \
  --upstream-mode parallel --cache --refuse-any --pending-requests-enabled --timeout 5s
for _ in $(seq 1 50); do
  if dig @127.0.0.1 -p 25355 example.com A +time=1 +tries=1 +short 2>/dev/null | grep -Eq '^[0-9]+\.' && \
     dig @127.0.0.1 -p 25355 example.com AAAA +time=1 +tries=1 +short 2>/dev/null | grep -q ':'; then break; fi
  sleep 0.1
done

bb=$(realpath config/blackbox/blackbox.yml)
prom=$(realpath config/prometheus/prometheus.yml)
systemd-run --quiet --unit="$BB_UNIT" --property=Type=simple --property=Restart=no /usr/bin/prometheus-blackbox-exporter --config.file="$bb" --web.listen-address="127.0.0.1:$BB_PORT"
for _ in $(seq 1 50); do curl -fsS "http://127.0.0.1:$BB_PORT/-/healthy" >/dev/null 2>&1 && break; sleep 0.1; done
curl -fsS "http://127.0.0.1:$BB_PORT/-/healthy" >/dev/null
probe(){ module=$1; target=$2; curl -fsS -G --data-urlencode "module=$module" --data-urlencode "target=$target" "http://127.0.0.1:$BB_PORT/probe" | awk '/^probe_success / {print $2}' | grep -qx 1; }
probe http_2xx_ipv4 https://example.com/
probe http_2xx_ipv6 https://example.com/
probe dns_a 127.0.0.1:25355
probe dns_aaaa 127.0.0.1:25355

# Rewrite only local smoke endpoints; source config remains canonical.
tmp_prom="$DATA/prometheus.yml"
sed -e "s/127\\.0\\.0\\.1:29115/127.0.0.1:$BB_PORT/g" -e 's/127\.0\.0\.1:25353/127.0.0.1:25355/g' "$prom" >"$tmp_prom"
systemd-run --quiet --unit="$PROM_UNIT" --property=Type=simple --property=Restart=no /usr/bin/prometheus --config.file="$tmp_prom" --storage.tsdb.path="$DATA/tsdb" --storage.tsdb.retention.time=1h --web.listen-address="127.0.0.1:$PROM_PORT"
for _ in $(seq 1 60); do curl -fsS "http://127.0.0.1:$PROM_PORT/-/ready" >/dev/null 2>&1 && break; sleep 0.1; done
curl -fsS "http://127.0.0.1:$PROM_PORT/-/ready" >/dev/null
ok=0
for _ in $(seq 1 12); do
  count=$(curl -fsS -G --data-urlencode 'query=probe_success == 1' "http://127.0.0.1:$PROM_PORT/api/v1/query" | jq '[.data.result[]?] | length')
  if [ "$count" -ge 5 ]; then ok=1; break; fi
  sleep 2
done
test "$ok" = 1

# The test must be talking to the transient units it created, not a pre-existing service.
BB_PID=$(systemctl show -p MainPID --value "$BB_UNIT")
PROM_PID=$(systemctl show -p MainPID --value "$PROM_UNIT")
test "$BB_PID" -gt 0; test "$PROM_PID" -gt 0
ss -ltnp | grep -F "pid=$BB_PID" | grep -q ":$BB_PORT"
ss -ltnp | grep -F "pid=$PROM_PID" | grep -q ":$PROM_PORT"

echo blackbox-ipv4=PASS
echo blackbox-ipv6=PASS
echo blackbox-dns-a=PASS
echo blackbox-dns-aaaa=PASS
echo prometheus-dualstack-evidence=PASS
echo observation-smoke=PASS
