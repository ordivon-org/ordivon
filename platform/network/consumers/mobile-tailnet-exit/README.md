# Mobile Tailnet Exit: Tailscale over Network-v2 Gluetun

The existing Gluetun container owns one physical provider WireGuard identity.
run.sh starts a separate Tailscale userspace daemon inside the same container
network namespace using nsenter. There is no second provider WireGuard session
and no Windows or WSL host default-route takeover.

The Tailscale daemon advertises Exit Node routes. Tailnet administrative
approval and device-level selection are separate requirements. ready.py verifies
service, namespace, Tailscale online state, advertised routes, admin approval
and Gluetun's **native healthcheck** by executing `/gluetun-entrypoint healthcheck` inside the exact provider container. It does not require unrelated OKX, OpenAI, Anthropic or Docker Registry responses to report the mobile Exit Node as healthy. `clientPublicExit=NOT_EVALUATED` makes explicit that this is **not** iOS client public-exit verification. If the provider PID changes, the child daemon
is terminated and the service loops into a fresh provider namespace.

The deployment initially used constant 3-second systemd service restarts while
the provider was unavailable, causing more than 11,000 retries in one outage.
The source now uses systemd 261 native exponential backoff: 3-second first
restart, 5 steps and a 2-minute ceiling. No custom retry scheduler is needed.

This SourceCut was reimported from the deployed consumer on 2026-11-05.
Source and installed unit need a separately witnessed reconciliation. A
readiness PASS does not prove that an iPad or iPhone has selected the node.

Mobile verification: in the Tailscale iOS app select the approved exit node
ordivon-surfshark-exit, then compare its public IP and DNS on both Wi-Fi and
cellular data with the upstream provider. Disconnect/recovery tests must
confirm that traffic does not silently fall back to a direct Internet route.

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
