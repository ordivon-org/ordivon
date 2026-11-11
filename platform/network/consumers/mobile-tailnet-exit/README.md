# Mobile Tailnet Exit: Tailscale over Network-v2 Gluetun

The existing Gluetun container owns one physical provider WireGuard identity.
run.sh starts a separate Tailscale userspace daemon inside the same container
network namespace using nsenter. There is no second provider WireGuard session
and no Windows or WSL host default-route takeover.

The Tailscale daemon advertises Exit Node routes. Tailnet administrative
approval and device-level selection are separate requirements. ready.py verifies
service, namespace, Tailscale online state, advertised routes, admin approval
and Gluetun's **native healthcheck** by executing `/gluetun-entrypoint healthcheck` inside the exact provider container. It does not require unrelated OKX, OpenAI, Anthropic or Docker Registry responses to report the mobile Exit Node as healthy. `clientPublicExit=NOT_EVALUATED` makes explicit that this is **not** iOS client public-exit verification. If the physical provider disappears or its network namespace identity
changes, the child daemon is terminated and the native systemd backoff starts a
new Tailscale session in the newly selected provider namespace.

The loop uses Bash's -ef test on /proc/PID/ns/net (same kernel namespace
inode) rather than asking Podman to inspect its container every second.
This maintains the existing fail-closed namespace identity predicate while
removing repeated Podman CLI launches. Process existence alone is insufficient;
the inode comparison also rejects a live process in a different namespace.
It does not prove the upstream VPN is healthy or an iOS client selected it.

The deployment initially used constant 3-second systemd service restarts while
the provider was unavailable, causing more than 11,000 retries in one outage.
The source now uses systemd 261 native exponential backoff: 3-second first
restart, 5 steps and a 2-minute ceiling. No custom retry scheduler is needed.

This SourceCut was reimported from the deployed consumer on 2026-11-05.
Source and installed unit need a separately witnessed reconciliation. A
readiness PASS does not prove that an iPad or iPhone has selected the node.

## Client-origin iPad / iPhone acceptance (N8)

The Linux exit node **cannot read another device's active exit-node choice**.
Tailscale PeerStatus showing Online, Active, direct UDP, or transmitted bytes
only proves a Tailnet path; it does not prove the remote client selected
this node to carry its public Internet traffic. The peer ExitNode flag
describes whether that *peer* is an exit node, not whether it is *using* this
exit node.

For **each** iPad and iPhone, reuse the official Tailscale iOS integration
rather than creating a second mobile agent:

1. On the device, check the Tailscale app's **Exit Node** selection for
   **ordivon-surfshark-exit**. Optionally use Apple **Shortcuts** >
   **Tailscale** > **Get Status**, which provides Connected,
   Using Exit Node, and Exit Node Name. Require Connected=true,
   Using Exit Node=true, and the exact expected exit-node name.
2. From that same device, open https://ipinfo.io/json and compare its
   actual public IP with the **contemporaneous**, Gluetun-native provider
   public IP (VPN addresses can change). The expected provider country is SG.
   This is a device-origin receipt, not a server curl substituted for it.
3. Test ordinary HTTPS hostname resolution on that same device. Record
   whether DNS succeeds, and distinguish normal domain-name lookups from
   special-use names or intentional DNS filtering. Repeat on Wi-Fi and
   cellular when both paths matter. With DNS leak testing, the visible
   resolver may be Gluetun's upstream Cloudflare or Google DoT provider;
   resolver geography need not equal Surfshark egress geography.
4. For authorized interruption/recovery experiments, observe the
   device's actual public route and DNS. Never infer universal non-bypass
   from a successful Tailscale ping, Linux socket, or server readiness.
   Do not disrupt active devices solely to generate evidence.

Tailscale's own existing native debug metrics command can assist:
tailscale --socket=EXISTING_MOBILE_SOCKET debug metrics
Aggregate dns_exit_node_query, dns_query_fwd_success and refused/error
counters should be compared as **deltas**, not historical totals.
Neither these counters nor the readiness clientPublicExit=NOT_EVALUATED
field identify which iOS client selected the exit node or prove all its
DNS requests succeeded. Intermittent REFUSED must be attributed before
changing existing Gluetun DNS DoT/filter policy; do not broadly disable
rebinding or malicious-domain protections.

Official references:
- [Tailscale iOS/macOS Shortcuts — Get Status](https://tailscale.com/docs/features/mac-ios-shortcuts)
- [Tailscale Exit Nodes](https://tailscale.com/docs/features/exit-nodes)
- [Tailscale DNS behavior with Exit Nodes](https://tailscale.com/docs/reference/dns-in-tailscale)
- [Ordivon real iOS client and DNS issue #2105](https://github.com/ordivon-org/ordivon/issues/2105)

A device-local exit-node receipt is an explicit **N8 consumer requirement**,
not another control-plane daemon or network-policy grant.

## LAN directness and remote fallback

The local iPad-to-exit Tailscale flow changed from Tokyo DERP at about
400ms to direct encrypted UDP on the existing LAN at about 8-9ms.
The mature enabling mechanism is Gluetun FIREWALL_OUTBOUND_SUBNETS in
providers/gluetun/native_profile.py, not a second Tailscale daemon or
custom polling process. That provider setting allows the entire private
LAN subnet. An off-LAN iPad can fall back to DERP automatically.

Measure separately: Tailscale peer direct/relay status, selected
provider namespace, Gluetun public VPN IP, client-side iOS IPinfo/DNS,
and no unexpected public direct route. Gluetun's successful health
check is not sufficient to claim iOS DNS or application non-bypass.
