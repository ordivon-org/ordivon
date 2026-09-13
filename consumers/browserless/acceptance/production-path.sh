#!/usr/bin/env bash
set -euo pipefail

NS=${NS:-nv2-browserless-prod}
WG_IF=${WG_IF:-nv2blwg}
for unit in network-v2-browserless.target network-v2-browserless-netns.service network-v2-browserless-wireguard.service network-v2-browserless-dns.service; do
  test "$(systemctl is-active "$unit")" = active
done
ip netns list | awk '{print $1}' | grep -qx "$NS"

for _ in $(seq 1 24); do
  ip netns exec "$NS" ping -4 -c1 -W1 1.1.1.1 >/dev/null 2>&1 || true
  hs=$(ip netns exec "$NS" wg show "$WG_IF" latest-handshakes 2>/dev/null | awk 'NR==1{print $2+0}')
  [ "${hs:-0}" -gt 0 ] && break
  sleep .25
done
test "${hs:-0}" -gt 0

openai_dns=$(ip netns exec "$NS" getent ahostsv4 api.openai.com | awk '{print $1}' | sort -u | tr '\n' ',')
chatgpt_dns=$(ip netns exec "$NS" getent ahostsv4 chatgpt.com | awk '{print $1}' | sort -u | tr '\n' ',')
test -n "$openai_dns"
test -n "$chatgpt_dns"
openai_http=$(ip netns exec "$NS" curl -4 -sS --connect-timeout 6 --max-time 20 -o /dev/null -w '%{http_code}' https://api.openai.com/v1/models)
chatgpt_http=$(ip netns exec "$NS" curl -4 -sS --connect-timeout 6 --max-time 20 -o /dev/null -w '%{http_code}' https://chatgpt.com/)
case "$openai_http" in 200|401|403|404) ;; *) exit 31;; esac
case "$chatgpt_http" in 200|301|302|403) ;; *) exit 32;; esac
# Public egress-IP reporting is supplemental evidence. It must not invalidate an
# already-proven WireGuard/DNS/OpenAI/ChatGPT production path when the witness site is slow.
provider_ip=$(ip netns exec "$NS" curl -4 -fsS --connect-timeout 2 --max-time 5 https://api.ipify.org 2>/dev/null | tr -d '[:space:]' || true)
printf 'handshake=%s\nopenai_dns=%s\nchatgpt_dns=%s\nopenai_http=%s\nchatgpt_http=%s\nprovider_egress=%s\n' "$hs" "$openai_dns" "$chatgpt_dns" "$openai_http" "$chatgpt_http" "${provider_ip:-unavailable}"
echo browserless-production-network=PASS
