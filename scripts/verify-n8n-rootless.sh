#!/usr/bin/env bash
set -euo pipefail

UID_N8N=934
RUNTIME_DIR=/run/user/${UID_N8N}
run_n8n() {
  (
    cd /var/lib/n8n
    runuser -u n8n -- env -i \
      HOME=/var/lib/n8n USER=n8n LOGNAME=n8n PATH=/usr/bin:/bin \
      XDG_RUNTIME_DIR="$RUNTIME_DIR" \
      DBUS_SESSION_BUS_ADDRESS="unix:path=$RUNTIME_DIR/bus" \
      "$@"
  )
}

printf '%s\n' '== user units =='
run_n8n systemctl --user is-active ordivon-n8n-pod.service
run_n8n systemctl --user is-active ordivon-n8n.service
run_n8n systemctl --user is-active ordivon-n8n-runners.service

printf '%s\n' '== containers =='
run_n8n podman pod ps --format '{{.Name}} {{.Status}}'
run_n8n podman ps --format '{{.Names}} {{.Image}} {{.Status}}'

printf '%s\n' '== host endpoints =='
curl -fsS http://127.0.0.1:5678/healthz
printf '\n'
curl -fsS http://127.0.0.1:5678/healthz/readiness
printf '\n'

printf '%s\n' '== host listener boundary =='
ss -ltn | awk '$4 ~ /:(5678|5679|5680)$/ {print}'
if ss -ltn | awk '$4 ~ /:(5679|5680)$/ {bad=1} END {exit bad?0:1}'; then
  echo 'unexpected host task-runner listener' >&2
  exit 1
fi
if ! ss -ltn | awk '$4 == "127.0.0.1:5678" {ok=1} END {exit ok?0:1}'; then
  echo 'n8n is not bound to host loopback 127.0.0.1:5678' >&2
  exit 1
fi

printf '%s\n' '== private runner health =='
run_n8n podman exec ordivon-n8n node -e "fetch('http://127.0.0.1:5680/healthz').then(async r=>{console.log(r.status,await r.text()); if(!r.ok)process.exit(2)}).catch(e=>{console.error(e);process.exit(3)})"

printf '%s\n' '== outbound connectivity =='
run_n8n podman exec ordivon-n8n node -e "fetch('https://api.github.com',{headers:{'user-agent':'ordivon-n8n-acceptance'}}).then(r=>{console.log(r.status); if(!r.ok)process.exit(2)}).catch(e=>{console.error(e);process.exit(3)})"

printf '%s\n' '== PostgreSQL =='
runuser -u postgres -- psql -h /var/lib/postgres/ordivon-data-r5-pg-14550-v4 -p 55434 -d n8n -Atqc "select 'tables='||count(*) from pg_tables where schemaname='public';"

printf '%s\n' 'n8n rootless acceptance: PASS'
