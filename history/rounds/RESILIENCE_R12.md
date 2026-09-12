# R12 — Generic Network Resilience Graduation

Date: 2026-09-12

## Scope

R12 closes the remaining local resilience false-green classes for generic Network v2 without changing live R0 configuration or touching any consumer migration.

It proves:

- bidirectional IPv4/IPv6 fallback under deterministic single-family failure;
- DNS partial-upstream survival;
- DNS all-upstream fail-closed behavior even while the listener remains alive;
- bounded cache semantics and expiry;
- DNS recovery without restarting dnsproxy;
- cleanup/non-interference after fault experiments;
- recovery across a real WSL instance reboot that happened independently during this work.

## Address-family fallback

The test uses sing-box's native `hosts` DNS server and route `resolve` action. The hostname `fallback.test` resolves to both `127.0.0.1` and `::1`.

Two local origin cases are created with the Python standard-library HTTP server:

1. `prefer_ipv6`, with only IPv4 origin healthy;
2. `prefer_ipv4`, with only IPv6 origin healthy.

The unhealthy preferred-family listener is explicitly absent in each case.

Canonical result:

```text
prefer_ipv6 + IPv6 failed + IPv4 healthy -> HTTP 200
prefer_ipv4 + IPv4 failed + IPv6 healthy -> HTTP 200
family-fallback-smoke=PASS
```

This is deterministic local evidence rather than a public-Internet address-family outage simulation.

## DNS upstream resilience

The DNS test uses mature existing components only:

- dnsmasq as the deterministic local healthy authoritative upstream;
- an intentionally unbound local port as the failed upstream;
- AdGuard dnsproxy with `--upstream-mode parallel --cache`, matching live R0's core DNS behavior.

The acceptance sequence is:

1. one upstream healthy, one dead from the beginning;
2. require UDP query success;
3. require TCP query success;
4. warm a short-TTL cache entry;
5. stop the only healthy upstream while dnsproxy stays active and listening;
6. permit the still-valid cached answer;
7. require an unseen name to return `SERVFAIL` despite the healthy listener;
8. wait for the authoritative TTL to expire;
9. require the formerly cached key to return `SERVFAIL`;
10. restore the healthy upstream;
11. require successful DNS again without restarting dnsproxy;
12. require the dnsproxy PID to remain unchanged.

Canonical result:

```text
partial_failure_udp=PASS
partial_failure_tcp=PASS
cached_answer_during_upstream_outage=PASS
all_upstreams_down_uncached_servfail=PASS
cache_expiry_fail_closed=PASS
dns_upstream_recovery_without_dnsproxy_restart=PASS
dns-resilience-smoke=PASS
```

This closes the listening-only DNS false green: a bound UDP/TCP socket is not accepted as DNS health when upstream resolution is unavailable.

## Canonical R12 acceptance

Entry point:

```text
task test:r12
```

The task performs `verify:live` before and after both resilience experiments.

Runtime Job:

- Job: `job-01a09569-2e1c-7be3-af6e-e074a77f386f`;
- operation digest: `sha256:d0e8f4b97e58bebf649b241861e17b3b3871d4f6a4c94aabb0db03011e106cf0`;
- stdout SHA-256: `706efd7d7a2ee5d9bff4c35d02358d4cb2b5d667f5810aa50fbedf72bd565ebb`;
- terminal evidence SHA-256: `15f4201888c6ab09f47f8b81fe09d35c199b3bac82836954f6ff090d6047f6c4`.

## Post-state

Post-state Job:

- Job: `job-01a09569-92dd-77b2-835a-45fdcab8b0b6`;
- operation digest: `sha256:202ec0bbb2f28296b52af5f8f16b27d1df5b91b97a4930138d443851505d63bf`;
- stdout SHA-256: `9118fa41ee8e352c9ba07afa4e9ffb43cd827b169381f9bac072f99faed2abc8`;
- terminal evidence SHA-256: `ab47b0e67602c00217abd2e1b203736b709d52ec87eba73182bb9ec80c883f75`.

Verified after fault cleanup:

- no resilience transient units are running;
- no resilience test ports remain bound;
- live R0 exact-byte/function verification passes;
- IPv4/IPv6 default routes remain on the native host interface;
- Cloudflare production A/B/canary HA remains `4/4/4`;
- Runtime is active.

## Real WSL reboot evidence

During the work, the Runtime MCP became briefly unavailable. Forensic inspection proved this was not an R12 fault-injection side effect. systemd journal shows a real boot boundary:

```text
previous boot: f360a63d11cb4f5cba7c8ba607167fd9
ended:         2026-09-12 19:30:11 CST

current boot:  1b265c879b954182909a8f311cae369d
started:       2026-09-12 19:30:36 CST
```

Before the boot boundary, at 19:30:01, systemd cleanly stopped `network-v2-r0.target` and its component services. On the new boot:

- dnsproxy active at 19:30:37;
- blackbox_exporter active at 19:30:37;
- Prometheus active at 19:30:37;
- sing-box active at 19:30:38;
- `network-v2-r0.target` active at 19:30:38;
- Runtime active at 19:30:38;
- Cloudflare production A/B and canary active at 19:30:39.

All four Network component services remain individually disabled while the R0 target is enabled, exactly matching the R9 lifecycle design.

A full live functional verification after reboot passed.

Reboot evidence Job:

- Job: `job-01a0956a-2da1-72d2-8916-4b55df4797d8`;
- operation digest: `sha256:4700a353d0e65ce27f3176114e93d0f4e4a4f00aceb5c481dd73d8b9760b0ceb`;
- stdout SHA-256: `02199c3d2984844fd2cc5e4d51dba95189af390fda9a4f67949b96e15ca9fd18`;
- terminal evidence SHA-256: `27bd24fc2f546e979efbed364ea67d44bdffd85b0bf4b31603b02b63f7ff5936`.

This proves **WSL instance reboot recovery**. It does not claim a Windows physical-host reboot plus WSL auto-launch; that belongs to workstation/bootstrap integration rather than the Network v2 data-plane implementation itself.

## Standing

**Generic Network v2 local WSL resilience: PASSED.**

After R12 the remaining non-consumer Network fidelity gaps are external-platform gates rather than unresolved local implementation defects:

1. `tc/netem` packet delay/loss/reorder on a standard Linux kernel;
2. containerlab full-fidelity topology on a standard Linux runner;
3. kernel WireGuard differential against the WSL userspace `wireguard-go` path.

Windows-host reboot/bootstrap is a Workstation boundary. Consumer cutover and legacy retirement remain separate migration work.
