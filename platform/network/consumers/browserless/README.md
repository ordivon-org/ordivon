# Browserless consumer profile

Browserless is a consumer-specific Network v2 profile, not part of generic Network graduation. The legacy-to-Network-v2 migration is complete: steady-state source authority is the current provider profile/catalog plus `provider-switch.sh`, `provider-carrier-ready.sh`, `acceptance/production-path.sh`, and the Network-v2 systemd/config carrier.

The retired migration implementation is preserved by Git history, while the durable cutover receipt at `/var/lib/network-v2/browserless-cutover/production-cutover.json` remains provenance/currentness evidence for Harness consumers. That receipt does not make the retired migration scripts executable authority and does not restore the old ExteriorAnchor/Surfpath rollback surface.

Inside the v2 namespace, Linux NSS is explicitly reduced to `hosts: files dns` so `systemd-resolved` in the host namespace cannot bypass namespace DNS policy. AdGuard `dnsproxy` is the DNS authority already selected by Network v2: Cloudflare and Google DoH are parallel primary upstreams, while provider-native Surfshark DNS is fallback only. Current consequence validation requires WireGuard readiness, clean OpenAI/ChatGPT DNS and HTTPS consequences through the steady-state production path.

Endpoint discovery/currentness is a separate provider concern. The provider profile and pinned catalog own endpoint selection/currentness; the Browserless consumer does not mint a second durable provider catalog.
## Shared provider carrier

The Browserless production namespace is also the single physical provider-carrier owner for provider-bound Network v2 consumers. `network-v2-browserless-provider-carrier.service` exposes only the internal veth address `10.252.246.2:19680`; it is not a northbound user authority. Finance, Supply-Chain, Claude and ChatIngress retain their own destination/policy boundaries.

A single Surfshark client identity must have a single concurrent WireGuard session. Current recovery evidence showed that concurrent Browserless, Finance and Supply-Chain sessions with the same client address caused provider endpoint roaming and intermittent destination failures. Cross-consumer qualification selected `th-bkk` as the current production site because one serialized session carried OpenAI/ChatGPT network consequences, Anthropic, OCI registries, OKX and Binance in the same acceptance window. Browser process readiness is a separate Browserless lifecycle claim.

Steady-state provider selection uses `provider-switch.sh`; it preserves the existing namespace and restarts only WireGuard, DNS, and the internal carrier. Historical migration details remain available in Git and the immutable cutover receipt rather than as current executable rollback authority.
