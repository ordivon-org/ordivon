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


## Native neutral Target alias migration

The canonical network-v2-browserless.target now provides the
network-v2-shared-egress.target systemd Alias, not a duplicate Target.
Codex, Windows Chrome, Chat Ingress and Claude systemd sources depend
on the neutral alias. The existing namespace and legacy rollback
identities remain unchanged for other consumers. See
formal/shared_egress_alias_refinement.py for the exact, source-bound
graph refinement against the merged #1783 baseline, then verify
native loaded unit dependency state and real Consumer requests.


## Owner-local stop propagation (systemd.unit native semantics)

The live, legacy-named namespace/forward units now declare
`PartOf=network-v2-shared-egress.target`; the inactive rollback
WireGuard/DNS/carrier units declare
`PartOf=network-v2-browserless-legacy-provider.target`.
Stopping the latter must not stop or disable the shared target,
forwarding, namespace, or unrelated Consumer. This is the same
alias-backed physical shared Target, not a new Unit or VPN identity.
The source-bound stop-closure regression in
`tests/test_shared_provider_carrier.py` rejects an accidental
shared-forwarding dependency on the Browserless legacy target.
Production installation requires native source/install/loaded-unit readback;
the static closure is not a substitute for a real cold recovery test.

## Non-disruptive legacy Docker FORWARD convergence

The legacy Docker FORWARD policy remains in force; this project owns only
the two exact IPv4 veth/CIDR exceptions. The source-installed
`shared-egress-forward ensure` uses native iptables-legacy `-S`,
`-C`, and `-I` with xtables lock waiting. Existing rules are reused
without delete/reinsert, missing exact rules are inserted and verified,
and unexpected or duplicated Owner marker rules fail closed. A systemd
stop/restart does not automatically delete live shared forwarding rules.
The native Task materializes the helper before its Unit and verifies
installed-byte equality. Deliberate final removal requires quiescing
all consumers and an explicit operator-owned retirement action.

This reduces the restart interruption path but does not prove cross-process
atomicity between discovery and rule insertion. Docker/other concurrent
iptables writers remain an external stability assumption, with the exact
kernel count and real Carrier HTTP checks required after installation.
Do not replace this with nftables-only ACCEPT until the Docker FORWARD
backend/consumer effects justify the change.

## Cold-boot independence from external network availability

The shared namespace/veth Unit creates a **local kernel topology** and does
not need DNS, a WAN default route, a VPN handshake, or `network-online.target`.
The systemd native network-online synchronization point is intentionally
absent from this Unit: external network outages must not block creation of
the local substrate. This is a startup-order refinement only, not a change
to Provider readiness or a claim that applications have Internet access.
The existing Carrier and Consumer verifiers remain the liveness authority.

## Non-destructive namespace lifecycle (native systemd + iproute2)

`network-v2-browserless-netns.service` remains the same installed identity,
but it now runs the one-shot `shared-egress-netns ensure` under systemd.
On an empty cold boot it creates the named namespace and its veth once;
when the topology already exists it verifies both veth peer ifindices,
exact IPv4 addresses, link-UP flags, and absence of any IPv4/IPv6 default
route, then **reuses existing resources without changes**. Partial or
mismatched resources fail closed, without `ip netns del` or `ip link del`.
No extra scheduler, daemon, registry, or restart loop is introduced.

A systemd stop/restart of this shared Unit no longer implicitly deletes
kernel namespace or veth resources; existing sockets can keep using their
current namespace identity. The stop of a **dependent application Unit**
can still stop that application; preserving the kernel topology does not
promise zero application downtime for all systemd operations. Linux
releases the namespace on reboot; deliberate retirement must first stop
all consumers, verify namespace PIDs and dependencies, and explicitly
remove the resource using native `ip netns del` / `ip link del` under
operator control. A failed cold creation intentionally retains partial
evidence for investigation rather than guessing ownership and deleting.

The source `substrates/shared-egress/netns.py` is installed as one
executable helper *before* the systemd Unit is updated. The source check
`task substrate:shared-egress:netns:verify` is read-only; the substrate
`verify` additionally checks installed bytes, exact kernel forwarding
exceptions and real allowed HTTPS Carrier consequences.

This follows the Linux network namespace lifetime model and the
non-destructive resource persistence approach in systemd-networkd;
it does not claim that networkd itself owns these manually-placed veths.
