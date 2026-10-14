#!/usr/bin/env bash
set -euo pipefail

mode=
while test $# -gt 0; do
  case "$1" in
    --mode) mode=${2:-}; shift 2;;
    *) echo "usage: $0 --mode candidate-exit|candidate-sigkill" >&2; exit 64;;
  esac
done
case "$mode" in candidate-exit|candidate-sigkill) ;; *) exit 64;; esac

prefix="nv2-m4-sbx-$$-$RANDOM"
unitdir=/run/systemd/system
state=$(mktemp -d /tmp/nv2-m4-systemd-manager.XXXXXX)
log=$state/order.log
: >"$log"
candidate="$prefix-candidate.service"
recovery="$prefix-recovery.service"
legacy="$prefix-legacy.service"
consumer="$prefix-consumer.service"
producer="$prefix-producer.service"
orchestrator="$prefix-orchestrator.service"
units=("$orchestrator" "$candidate" "$recovery" "$producer" "$consumer" "$legacy")

cleanup_units() {
  set +e
  systemctl stop "${units[@]}" >/dev/null 2>&1
  systemctl reset-failed "${units[@]}" >/dev/null 2>&1
  for unit in "${units[@]}"; do rm -f "$unitdir/$unit"; done
  systemctl daemon-reload >/dev/null 2>&1
  set -e
}
cleanup_all() {
  cleanup_units
  rm -rf "$state"
}
trap cleanup_all EXIT INT TERM

cat >"$state/candidate.sh" <<EOF
#!/usr/bin/env bash
set -euo pipefail
echo \$\$ >"$state/candidate.pid"
printf '%s\\n' candidate-start >>"$log"
if test "$mode" = candidate-exit; then
  sleep 1
  printf '%s\\n' candidate-fail-exit >>"$log"
  exit 23
fi
sleep 30
EOF

cat >"$state/recover.sh" <<EOF
#!/usr/bin/env bash
set -euo pipefail
pid=\$(cat "$state/candidate.pid")
if kill -0 "\$pid" >/dev/null 2>&1; then
  echo candidate-still-running >&2
  exit 70
fi
if systemctl is-active --quiet "$candidate"; then
  echo candidate-unit-still-active >&2
  exit 70
fi
printf '%s\\n' candidate-absent >>"$log"
systemctl start "$legacy"
systemctl is-active --quiet "$legacy"
printf '%s\\n' legacy-confirmed >>"$log"
systemctl start "$consumer"
systemctl is-active --quiet "$consumer"
printf '%s\\n' consumer-confirmed >>"$log"
systemctl start "$producer"
systemctl is-active --quiet "$producer"
printf '%s\\n' producer-confirmed >>"$log"
touch "$state/recovery.complete"
EOF

cat >"$state/orchestrator.sh" <<EOF
#!/usr/bin/env bash
set -euo pipefail
systemctl start --no-block "$candidate"
printf '%s\\n' initiator-started >>"$log"
sleep 30
EOF
chmod 0755 "$state/candidate.sh" "$state/recover.sh" "$state/orchestrator.sh"

cat >"$unitdir/$legacy" <<EOF
[Unit]
Description=Network-v2 M4 nonproduction legacy fallback marker
[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/usr/bin/bash -c 'echo legacy-start >>"$log"; touch "$state/legacy.ready"'
EOF
cat >"$unitdir/$consumer" <<EOF
[Unit]
Description=Network-v2 M4 nonproduction consumer marker
Requires=$legacy
After=$legacy
[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/usr/bin/bash -c 'test -e "$state/legacy.ready"; echo consumer-start >>"$log"; touch "$state/consumer.ready"'
EOF
cat >"$unitdir/$producer" <<EOF
[Unit]
Description=Network-v2 M4 nonproduction producer marker
Requires=$consumer
After=$consumer
[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/usr/bin/bash -c 'test -e "$state/consumer.ready"; echo producer-start >>"$log"; touch "$state/producer.ready"'
EOF
cat >"$unitdir/$recovery" <<EOF
[Unit]
Description=Network-v2 M4 nonproduction manager recovery
[Service]
Type=oneshot
ExecStart=$state/recover.sh
EOF
cat >"$unitdir/$candidate" <<EOF
[Unit]
Description=Network-v2 M4 nonproduction failing candidate
OnFailure=$recovery
StartLimitIntervalSec=0
[Service]
Type=simple
ExecStart=$state/candidate.sh
Restart=no
TimeoutStopSec=2s
EOF
cat >"$unitdir/$orchestrator" <<EOF
[Unit]
Description=Network-v2 M4 nonproduction disposable initiator
[Service]
Type=simple
ExecStart=$state/orchestrator.sh
Restart=no
EOF

systemctl daemon-reload
systemctl start --no-block "$orchestrator"
for _ in $(seq 1 80); do
  if systemctl is-active --quiet "$orchestrator" && systemctl is-active --quiet "$candidate"; then break; fi
  sleep 0.05
done
systemctl is-active --quiet "$orchestrator"
systemctl is-active --quiet "$candidate"

systemctl kill --kill-whom=main --signal=KILL "$orchestrator"
for _ in $(seq 1 80); do
  systemctl is-active --quiet "$orchestrator" || break
  sleep 0.05
done
initiator_result=$(systemctl show "$orchestrator" -p Result --value)
test "$initiator_result" = signal

if test "$mode" = candidate-sigkill; then
  systemctl kill --kill-whom=main --signal=KILL "$candidate"
fi

for _ in $(seq 1 160); do
  test -e "$state/recovery.complete" && break
  sleep 0.05
done
test -e "$state/recovery.complete"
candidate_result=$(systemctl show "$candidate" -p Result --value)
case "$candidate_result" in exit-code|signal) ;; *) echo "unexpected candidate result=$candidate_result" >&2; exit 71;; esac
recovery_result=$(systemctl show "$recovery" -p Result --value)
test "$recovery_result" = success
systemctl is-active --quiet "$legacy"
systemctl is-active --quiet "$consumer"
systemctl is-active --quiet "$producer"

python3 - "$log" <<'PY'
from pathlib import Path
import sys
items=Path(sys.argv[1]).read_text().splitlines()
def pos(x):
    if x not in items: raise SystemExit(f"missing order marker {x}: {items}")
    return items.index(x)
assert pos("candidate-absent") < pos("legacy-start") <= pos("legacy-confirmed")
assert pos("legacy-confirmed") < pos("consumer-start") <= pos("consumer-confirmed")
assert pos("consumer-confirmed") < pos("producer-start") <= pos("producer-confirmed")
PY

cleanup_units
for unit in "${units[@]}"; do
  test ! -e "$unitdir/$unit"
  if systemctl cat "$unit" >/dev/null 2>&1; then
    echo "sandbox unit still loaded: $unit" >&2
    exit 72
  fi
done
trap - EXIT INT TERM

printf '{"schemaVersion":1,"kind":"ordivon.network-v2.m4-systemd-manager-sandbox","standing":"PASS","mode":"%s","systemManager":"systemd-pid1","initiatorKilled":true,"candidateFailureObserved":true,"managerOnFailureTriggered":true,"candidateAbsentBeforeFallback":true,"legacyBeforeConsumer":true,"consumerBeforeProducer":true,"productionProviderIdentityUsed":false,"productionNetworkMutation":false,"sandboxUnitsRemoved":true}\n' "$mode"
rm -rf "$state"
