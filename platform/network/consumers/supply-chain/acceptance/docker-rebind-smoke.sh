#!/usr/bin/env bash
set -euo pipefail
proxy=http://127.0.0.1:19581
pinned='openpolicyagent/opa@sha256:9c5770a0023d56a11224b0514fec2e4e0247357db4392b955c1270fd49cb1f0f'
/usr/local/libexec/network-v2/supply-chain-ready >/dev/null
mapfile -t names < <(docker ps --format '{{.Names}}')
for name in "${names[@]}"; do
  policy=$(docker inspect -f '{{.HostConfig.RestartPolicy.Name}}' "$name")
  case "$policy" in always|unless-stopped) ;; *) echo "ERROR: running container $name has non-recoverable restart policy $policy" >&2; exit 50;; esac
done
systemctl restart docker.service
for _ in $(seq 1 80); do systemctl is-active --quiet docker.service && break; sleep 0.25; done
systemctl is-active --quiet docker.service
for name in "${names[@]}"; do
  ok=0
  for _ in $(seq 1 120); do
    state=$(docker inspect -f '{{.State.Status}}' "$name" 2>/dev/null || true)
    test "$state" = running && { ok=1; break; }
    sleep 0.5
  done
  test "$ok" = 1 || { echo "ERROR: container did not recover: $name" >&2; exit 51; }
done
docker info 2>/dev/null | grep -F "HTTP Proxy: $proxy" >/dev/null
docker info 2>/dev/null | grep -F "HTTPS Proxy: $proxy" >/dev/null
timeout 120 docker pull "$pinned" >/tmp/network-v2-supply-chain-docker-pull.log 2>&1 || { cat /tmp/network-v2-supply-chain-docker-pull.log >&2; exit 52; }
docker image inspect "$pinned" >/dev/null
printf '{"schemaVersion":1,"kind":"ordivon.network-v2.supply-chain-docker-rebind","standing":"PASS","proxy":"%s","recoveredContainers":%d,"pinnedOpa":"%s"}
' "$proxy" "${#names[@]}" "$pinned"
