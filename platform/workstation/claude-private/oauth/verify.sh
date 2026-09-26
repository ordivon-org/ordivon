#!/usr/bin/env bash
set -euo pipefail

target=claude-private-oauth.target
cleanup() { systemctl stop "$target" >/dev/null 2>&1 || true; }
trap cleanup EXIT INT TERM
systemctl start "$target"

for _ in $(seq 1 80); do
  cdp=0 web=0
  ip netns exec nv2-claude-client curl -fsS http://127.0.0.1:19990/json/version >/dev/null 2>&1 && cdp=1
  curl -fsS http://127.0.0.1:16090/vnc.html >/dev/null 2>&1 && web=1
  [[ $cdp == 1 && $web == 1 ]] && break
  sleep 0.25
done
ip netns exec nv2-claude-client curl -fsS http://127.0.0.1:19990/json/version >/dev/null
curl -fsS http://127.0.0.1:16090/vnc.html >/dev/null

for u in claude-private-oauth-display.service claude-private-oauth-browser.service claude-private-oauth-vnc.service claude-private-oauth-web.service; do
  systemctl is-active --quiet "$u"
done

# The browser shares the no-direct-route namespace and must carry the exact proxy/webRTC flags.
test -z "$(ip netns exec nv2-claude-client ip -4 route show default)"
test -z "$(ip netns exec nv2-claude-client ip -6 route show default)"
pid=$(systemctl show claude-private-oauth-browser.service -p MainPID --value)
[[ $pid =~ ^[1-9][0-9]*$ ]]
tr '\0' '\n' </proc/$pid/environ | grep -Fx 'TZ=UTC'
tr '\0' ' ' </proc/$pid/cmdline | grep -F -- '--proxy-server=http://10.252.247.1:19482'
tr '\0' ' ' </proc/$pid/cmdline | grep -F -- '--force-webrtc-ip-handling-policy=disable_non_proxied_udp'

# Evaluate the browser-visible timezone/locale/permission state through CDP.
ws=$(ip netns exec nv2-claude-client curl -fsS http://127.0.0.1:19990/json/list | jq -r '.[0].webSocketDebuggerUrl')
[[ $ws == ws://127.0.0.1:19990/* ]]
js='(async()=>JSON.stringify({timezone:Intl.DateTimeFormat().resolvedOptions().timeZone,offset:new Date().getTimezoneOffset(),language:navigator.language,geolocation:(await navigator.permissions.query({name:"geolocation"})).state}))()'
result=$(ip netns exec nv2-claude-client env WS="$ws" EXPR="$js" node - <<'NODE'
const ws = new WebSocket(process.env.WS);
const timer = setTimeout(() => { console.error('cdp timeout'); process.exit(3); }, 8000);
ws.onopen = () => ws.send(JSON.stringify({id:1,method:'Runtime.evaluate',params:{expression:process.env.EXPR,awaitPromise:true,returnByValue:true}}));
ws.onmessage = (event) => {
  const msg = JSON.parse(event.data);
  if (msg.id === 1) {
    clearTimeout(timer);
    if (msg.error) { console.error(JSON.stringify(msg.error)); process.exit(4); }
    console.log(msg.result.result.value);
    ws.close();
  }
};
ws.onerror = () => { clearTimeout(timer); process.exit(5); };
NODE
)
echo "$result" | jq -e '.timezone=="UTC" and .offset==0 and (.language|startswith("en")) and .geolocation=="denied"' >/dev/null

# Main Claude web origin can be opened; any transport it uses still has no direct route.
encoded=$(python3 -c 'import urllib.parse; print(urllib.parse.quote("https://claude.com", safe=""))')
ip netns exec nv2-claude-client curl -fsS -X PUT "http://127.0.0.1:19990/json/new?$encoded" >/dev/null
sleep 2
ip netns exec nv2-claude-client curl -fsS http://127.0.0.1:19990/json/list | jq -e 'map(.url)|any(startswith("https://claude.com"))' >/dev/null

# Human UI is host-loopback only.
ss -ltn | grep -q '127.0.0.1:16090'
if ss -ltn | grep -Eq '(^|[[:space:]])(0\.0\.0\.0|\[::\]):16090([[:space:]]|$)'; then
  echo 'OAuth noVNC unexpectedly exposed beyond loopback' >&2
  exit 93
fi

echo "oauth_browser_privacy=$result"
echo 'claude-private OAuth browser acceptance: PASS'
