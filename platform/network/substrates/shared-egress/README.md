# Shared Egress Substrate | Source owner

The shared Linux network namespace, veth forwarding and provider carrier
readiness were previously misplaced under the Browserless consumer.
This module owns the source/install/readback for those four existing
resources. It is not an additional physical VPN or a second control plane.

- `systemd/network-v2-browserless-netns.service`: existing namespace/veth.
- `systemd/network-v2-browserless-forward.service`: bounded forward exception.
- `systemd/network-v2-browserless.target`: existing shared substrate target.
- `carrier-ready.sh`: actual Gluetun/legacy selection, no namespace default
  route, and permitted HTTPS CONNECT/origin evidence.
- `Taskfile.yml`: source validation, materialization and byte/live verification
  by native systemd and Go Task.

The installed `network-v2-browserless*` and `nv2-browserless-prod` labels
remain compatibility identifiers consumed by many scoped applications.
Moving source does not authorize renaming or restarting running units.
Browserless retains inactive serial rollback and browser acceptance.
Gluetun retains the single physical Surfshark identity.

Human: from platform/network run `task substrate:shared-egress:verify`,
then `task consumer:<application>:verify` and a real app request.
The substrate verifier now composes the independent, read-only
`task substrate:shared-egress:kernel:verify`: actual veth interface/IPv4
addresses, the two exact `iptables-legacy -C FORWARD` exceptions, and no
surplus rules carrying this Owner's comment marker. Unit `active` is not
considered proof that the kernel still has those rules. The existing Carrier
witness continues to check no default namespace route and actual HTTPS.

**Firewall succession boundary:** Production currently has Docker-managed
legacy iptables chains and Netavark nftables tables. An nftables `accept`
verdict cannot override a separate legacy `DROP`; replacing these two
legacy exceptions with only nftables would be an unproved (and potentially
broken) transition. Do not mutate Docker's chains, flush host rules, or
restart the shared namespace to modernize the syntax. Qualify the native
Docker firewall backend and the full consumer forwarding behavior before
retiring legacy rules; the read-only kernel witness is the present authority.
For iPad use Exit Node verify AND actual iPad IPinfo/DNS.

Agent: bind source/installed bytes/loaded namespace/consumer; prove the
namespace has no default route; inspect systemd dependency graphs;
falsify unauthorized destinations and confirm HTTPS origin effects.
Retain stable installed unit names until consumer-by-consumer migration.

Upstream primitives: iproute2 netns/veth, systemd units/dependencies,
Gluetun provider/firewall/health, Tailscale Exit Node.
No duplicate namespace manager, VPN identity, registry or watchdog.
