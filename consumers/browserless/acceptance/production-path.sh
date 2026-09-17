#!/usr/bin/env bash
set -euo pipefail

ENV_FILE=${ENV_FILE:-/etc/network-v2/browserless/provider.env}
if [ -f "$ENV_FILE" ]; then
  set -a
  . "$ENV_FILE"
  set +a
fi
NS=${NS:-nv2-browserless-prod}
WG_IF=${WG_IF:-nv2blwg}
HOST_IF=${HOST_IF:-nv2blph}
NS_CIDR=${NS_CIDR:-10.252.246.0/30}
FORWARD_COMMENT=network-v2-browserless-forward-v1
for unit in network-v2-browserless.target network-v2-browserless-netns.service network-v2-browserless-forward.service network-v2-browserless-wireguard.service network-v2-browserless-dns.service; do
  test "$(systemctl is-active "$unit")" = active
done
ip netns list | awk '{print $1}' | grep -qx "$NS"
# The forwarding rules are insufficient when WSL has reset the host-global forwarding
# sysctl. Treat the kernel routing switch as part of the production data-plane contract.
test "$(sysctl -n net.ipv4.ip_forward)" = 1
iptables-legacy -C FORWARD -i "$HOST_IF" -s "$NS_CIDR" -m comment --comment "$FORWARD_COMMENT" -j ACCEPT
iptables-legacy -C FORWARD -o "$HOST_IF" -d "$NS_CIDR" -m conntrack --ctstate RELATED,ESTABLISHED -m comment --comment "$FORWARD_COMMENT" -j ACCEPT

handshake_age=999999
for _ in $(seq 1 24); do
  ip netns exec "$NS" ping -4 -c1 -W1 1.1.1.1 >/dev/null 2>&1 || true
  hs=$(ip netns exec "$NS" wg show "$WG_IF" latest-handshakes 2>/dev/null | awk 'NR==1{print $2+0}')
  now=$(date +%s)
  if [ "${hs:-0}" -gt 0 ] && [ "$now" -ge "$hs" ]; then
    handshake_age=$((now-hs))
    [ "$handshake_age" -le 30 ] && break
  fi
  sleep .25
done
test "${hs:-0}" -gt 0
test "$handshake_age" -le 30

resolve4() {
  local host=$1 value
  for _ in 1 2 3 4; do
    value=$(ip netns exec "$NS" getent ahostsv4 "$host" 2>/dev/null | awk '{print $1}' | sort -u | tr '\n' ',' || true)
    if [ -n "$value" ]; then
      printf '%s' "$value"
      return 0
    fi
    sleep 1
  done
  return 1
}

openai_dns=$(resolve4 api.openai.com) || exit 21
chatgpt_dns=$(resolve4 chatgpt.com) || exit 22
# External CDN/provider edges can transiently fail one DNS/connect attempt even while the
# WireGuard data plane remains healthy.  Require a valid application consequence within a
# small bounded retry window instead of treating one sample as authoritative.
openai_http=000
openai_attempts=0
for attempt in 1 2 3 4; do
  openai_attempts=$attempt
  openai_http=$(ip netns exec "$NS" curl -4 -sS --connect-timeout 6 --max-time 12 -o /dev/null -w '%{http_code}' https://api.openai.com/v1/models 2>/dev/null || true)
  case "$openai_http" in 200|401|403|404) break ;; esac
  sleep 1
done
case "$openai_http" in 200|401|403|404) ;; *) exit 31;; esac

chatgpt_http=000
chatgpt_attempts=0
for attempt in 1 2 3 4; do
  chatgpt_attempts=$attempt
  chatgpt_http=$(ip netns exec "$NS" curl -4 -sS --connect-timeout 6 --max-time 12 -o /dev/null -w '%{http_code}' https://chatgpt.com/ 2>/dev/null || true)
  case "$chatgpt_http" in 200|301|302|403) break ;; esac
  sleep 1
done
case "$chatgpt_http" in 200|301|302|403) ;; *) exit 32;; esac
# Public egress-IP reporting is supplemental evidence. It must not invalidate an
# already-proven WireGuard/DNS/OpenAI/ChatGPT production path when the witness site is slow.
provider_ip=$(ip netns exec "$NS" curl -4 -fsS --connect-timeout 2 --max-time 5 https://api.ipify.org 2>/dev/null | tr -d '[:space:]' || true)
printf 'handshake=%s\nhandshake_age=%s\nopenai_dns=%s\nchatgpt_dns=%s\nopenai_http=%s\nopenai_attempts=%s\nchatgpt_http=%s\nchatgpt_attempts=%s\nprovider_egress=%s\n' "$hs" "$handshake_age" "$openai_dns" "$chatgpt_dns" "$openai_http" "$openai_attempts" "$chatgpt_http" "$chatgpt_attempts" "${provider_ip:-unavailable}"
echo browserless-production-network=PASS
