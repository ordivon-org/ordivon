#!/usr/bin/env bash
set -euo pipefail
target=network-v2-x-reality.target
egress=network-v2-x-reality-egress.service
carrier=network-v2-browserless-provider-carrier.service
proxy=http://127.0.0.1:19681
carrier_was=$(systemctl is-active "$carrier" 2>/dev/null || true)
cleanup(){ if [ "$carrier_was" = active ]; then systemctl start "$carrier" >/dev/null 2>&1 || true; fi; systemctl start "$target" >/dev/null 2>&1 || true; }
trap cleanup EXIT
/usr/local/libexec/network-v2/x-reality-ready >/dev/null
systemctl stop "$carrier"
for _ in $(seq 1 80); do [ "$(systemctl is-active "$carrier" 2>/dev/null || true)" = inactive ] && break; sleep .25; done
[ "$(systemctl is-active "$carrier" 2>/dev/null || true)" = inactive ]
systemctl is-active --quiet "$target"
systemctl is-active --quiet "$egress"
set +e
curl -4 -sS -o /dev/null --proxy "$proxy" --connect-timeout 2 --max-time 5 https://api.x.com/2/users/me >/dev/null 2>&1
x_rc=$?
set -e
[ "$x_rc" -ne 0 ]
systemctl start "$carrier"
for _ in $(seq 1 80); do systemctl is-active --quiet "$carrier" && break; sleep .25; done
systemctl is-active --quiet "$carrier"
/usr/local/libexec/network-v2/x-reality-ready >/dev/null
echo x-reality-network-v2-carrier-failclosed=PASS
