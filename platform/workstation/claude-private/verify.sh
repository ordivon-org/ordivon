#!/usr/bin/env bash
set -euo pipefail

EXPECTED_SHA256=15e2d05148f801b5774032faad87e624ecd172e9903288bda448b892eb58fa07
BIN=/opt/claude-private/versions/2.1.274/claude

[[ "$(sha256sum "$BIN" | awk '{print $1}')" == "$EXPECTED_SHA256" ]]
systemctl is-active --quiet network-v2-claude-client.target

# Verify the exact privacy boundary without contacting the model.
out=$(ip netns exec nv2-claude-client unshare --mount --uts --fork --propagation private /bin/bash -lc '
  set -euo pipefail
  P=/etc/claude-private
  hostname claude-workspace
  mount --bind "$P/nsswitch.conf" /etc/nsswitch.conf
  mount --bind "$P/resolv.conf" /etc/resolv.conf
  mount --bind "$P/hosts" /etc/hosts
  mount --bind "$P/hostname" /etc/hostname
  mount --bind "$P/machine-id" /etc/machine-id
  export TZ=UTC LANG=C.UTF-8 LC_ALL=C.UTF-8
  printf "hostname=%s\n" "$(hostname)"
  printf "timezone=%s\n" "$(date +%Z)"
  if timeout 4 getent ahostsv4 example.com >/dev/null 2>&1; then echo dns_escape=1; else echo dns_escape=0; fi
  if curl -4 -I -fsS --connect-timeout 2 --max-time 5 https://api.anthropic.com/ >/dev/null 2>&1; then echo direct_escape=1; else echo direct_escape=0; fi
  code=$(curl -x http://10.252.247.1:19482 -I -sS --connect-timeout 8 --max-time 20 -o /dev/null -w "%{http_code}" https://api.anthropic.com/)
  echo proxy_code=$code
')
printf '%s\n' "$out"
grep -qx 'hostname=claude-workspace' <<<"$out"
grep -qx 'timezone=UTC' <<<"$out"
grep -qx 'dns_escape=0' <<<"$out"
grep -qx 'direct_escape=0' <<<"$out"
grep -Eq '^proxy_code=[1-5][0-9][0-9]$' <<<"$out"

/usr/local/bin/claude-private --version | grep -Fx '2.1.274 (Claude Code)'
set +e
auth_json=$(/usr/local/bin/claude-private auth status 2>/dev/null)
auth_rc=$?
set -e
jq -e '.loggedIn==false or .loggedIn==true' <<<"$auth_json" >/dev/null
# Claude Code returns 1 for the valid signed-out state and 0 for signed-in.
if [[ $auth_rc -ne 0 && $auth_rc -ne 1 ]]; then
  echo "unexpected claude auth status rc=$auth_rc" >&2
  exit 91
fi

echo 'claude-private workstation acceptance: PASS'
