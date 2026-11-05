# Mobile Tailnet Exit: Tailscale over Network-v2 Gluetun

The existing Gluetun container owns one physical provider WireGuard identity.
run.sh starts a separate Tailscale userspace daemon inside the same container
network namespace using nsenter. There is no second provider WireGuard session
and no Windows or WSL host default-route takeover.

The Tailscale daemon advertises Exit Node routes. Tailnet administrative
approval and device-level selection are separate requirements. ready.py verifies
service, namespace, Tailscale online state, advertised routes, admin approval
and upstream Gluetun readiness. If the provider PID changes, the child daemon
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
