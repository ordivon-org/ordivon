# R4 — Provider Priority Failover / Failback

## Purpose

R4 turns the previously successful provider-failover experiment into canonical Network v2 acceptance equipment without importing legacy Network ownership or inventing a new scheduler.

The required policy is strict: use the admitted provider carrier while it is healthy; use native direct only as backup; when the same provider carrier becomes healthy again, new connections return to it.

## Mature composition

- an already-existing provider namespace remains externally owned;
- sing-box exposes one temporary HTTP CONNECT carrier inside that provider namespace;
- a second temporary sing-box carrier exposes native direct on loopback;
- HAProxy operates in TCP mode in front of those carriers;
- the provider carrier is the normal HAProxy server;
- the native carrier is marked `backup`;
- HAProxy active TCP checks send an HTTP CONNECT for `example.com:443` through each carrier and require a successful CONNECT response;
- failure injection stops only the temporary provider carrier, never the provider tunnel or namespace;
- restoration starts the same carrier and HAProxy returns it to service only after the configured success threshold.

HAProxy TCP mode relays the caller's HTTP CONNECT stream without terminating caller TLS. sing-box retains CONNECT and transport mechanics. Network v2 adds no custom proxy parser, path scheduler, provider lifecycle daemon, or machine-wide proxy.

## Rejected canonicalization path: sing-box URLTest

The first R4 canonicalization attempt reproduced the earlier URLTest design. It proved `provider -> direct` failover, but after provider recovery it remained on direct during the bounded observation window. That is valid URLTest behavior because URLTest is a latency-selection group; it is not a strict primary/backup contract. The earlier POC's failback was therefore evidence for that observation window, not authority for deterministic production policy.

R4 records that falsification and uses a mature component whose native semantics match the actual requirement instead of adding Ordivon code to force URLTest to behave differently.

## Safety boundary

The test MUST NOT mutate:

- the external provider namespace or provider tunnel;
- the machine default route;
- Windows system proxy or TUN state;
- Cloudflare production/canary tunnels or their direct-route tables;
- Runtime or Host MCP listeners;
- legacy consumer bindings.

It uses temporary systemd units and temporary configuration files and removes them on exit.

## Acceptance

`task smoke:priority-failover` passes only when all of the following are observed in one run:

1. an existing provider namespace has a root-reachable carrier-side address and a public egress identity distinct from direct;
2. both sing-box carriers pass HAProxy's CONNECT-based active health check;
3. new workload connections through HAProxy use the provider path while it is healthy;
4. stopping only the temporary provider carrier makes new workload connections use native direct;
5. restarting the same provider carrier and satisfying HAProxy's rise threshold makes new workload connections return to provider.

`task test:r4` combines this with the existing external-provider carrier smoke.

## Standing after R4

R4 proves deterministic carrier-level primary/backup policy composed from mature external projects. It does **not** grant production provider authority, select a real consumer, or retire any legacy Network component. A later consumer differential must bind destination-specific requirements and current provider authority before cutover.
