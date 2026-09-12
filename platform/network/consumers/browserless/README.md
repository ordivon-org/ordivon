# Browserless consumer profile

Browserless is a consumer-specific Network v2 migration gate, not part of generic Network graduation.

The current production carrier and Network v2 use the same Surfshark WireGuard client identity. Running both identities concurrently is not a valid differential experiment because the provider may move the same client address between sessions. Therefore the authoritative migration gate is serial: fail closed if Agent Automation has a running workflow, acquire the existing Surfpath graduation lease to drain/fence legacy physical mutation, stop one exact legacy ExteriorAnchor generation through its owner protocol, prove the v2 namespace, release the lease, and then recover/rebind the legacy carrier.

Inside the v2 namespace, Linux NSS is explicitly reduced to `hosts: files dns` so `systemd-resolved` in the host namespace cannot bypass namespace DNS policy. AdGuard `dnsproxy` is the DNS authority already selected by Network v2: Cloudflare and Google DoH are parallel primary upstreams, while provider-native Surfshark DNS is fallback only. Acceptance then requires WireGuard handshake, clean OpenAI/ChatGPT DNS, HTTPS consequences, the exact production Browserless image, and real `/content` navigation to `chatgpt.com`.

Endpoint discovery/currentness is a separate provider concern. This migration gate intentionally reuses the endpoint proven healthy immediately before the exact legacy generation is quiesced; it does not make that endpoint a durable catalog authority.
