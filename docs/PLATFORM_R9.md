# R9 — Generic Network Platform Graduation

Date: 2026-09-12

## Scope

R9 graduates the generic Network v2 platform independently of Finance or any other consumer migration. It closes the local WSL data-plane, DNS, observability, lifecycle, long-flow, concurrency, cold-start, and process-recovery gates for the R0 platform.

Consumer-specific provider profiles and consumer authority transfer are explicitly outside this standing.

## Architecture after R9

```text
network-v2-r0.target
├─ network-v2-dnsproxy.service
├─ network-v2-singbox.service
├─ network-v2-blackbox.service
└─ network-v2-prometheus.service
```

Only `network-v2-r0.target` is enabled at boot. The four component services are active but individually disabled and are lifecycle-bound to the target with `PartOf=`.

Component responsibilities remain external-first:

- sing-box: generic dual-stack proxy/data plane;
- AdGuard dnsproxy: A + AAAA DNS carrier;
- blackbox_exporter: IPv4, IPv6, DNS A, DNS AAAA and TCP probes;
- Prometheus: evidence time series;
- Toxiproxy: deterministic L4 fault injection;
- Linux netns + veth: local controlled topology;
- iperf3/mtr/bpftrace: diagnostics and performance/forensics tools.

No new custom network daemon was introduced.

## Dual-stack falsification and repair

The WSL host itself already had working native IPv4 and IPv6 Internet access. The prior R0 limitation was self-imposed:

- dnsproxy used `--ipv6-disabled`;
- sing-box DNS used `strategy = ipv4_only`;
- the route table rejected IPv6.

Focused candidate tests proved the host and sing-box path can complete HTTPS under both forced families:

- forced `ipv4_only`: PASS;
- forced `ipv6_only`: PASS;
- normal `prefer_ipv6` dual stack: PASS;
- DNS A: PASS;
- DNS AAAA: PASS.

R9 therefore removes the artificial IPv4-only policy from generic R0.

## Small-request false-green closure

R9 expands direct-path acceptance beyond a tiny `example.com` request.

The canonical isolated direct smoke proves:

- DNS A + AAAA;
- forced IPv4 HTTPS;
- forced IPv6 HTTPS;
- normal dual-stack `prefer_ipv6` HTTPS;
- four concurrent proxied HTTPS requests;
- a 5,000,000-byte proxied transfer.

During the canonical live R9 run the 5 MB isolated transfer completed successfully. After a full R0 target cold start, a separate 1 MB transfer also completed successfully.

This closes the prior false-green class where tiny requests could pass while longer streams, MTU behavior, or readiness remained broken.

## Observability closure

Blackbox configuration now has distinct modules for:

- HTTP over IPv4;
- HTTP over IPv6;
- DNS A;
- DNS AAAA;
- TCP connect to the sing-box listener.

Prometheus scrapes each of those independent black-box paths.

A test-harness defect was discovered while building this gate: the old isolated Prometheus smoke used a fixed port that was already occupied by an Operations Prometheus instance. The test could therefore query the wrong service. R9 replaces fixed smoke ports with dynamically selected free ports and additionally verifies that the transient systemd MainPID owns the selected listener.

This is an evidence-integrity repair, not a data-plane workaround.

## Lifecycle closure

Before R9 the four R0 services were independently enabled. R9 introduces `network-v2-r0.target` as the single composition root.

The destructive cold-start acceptance performs:

1. verify Runtime and Cloudflare control plane are healthy;
2. stop the entire R0 target;
3. verify all four R0 child services are inactive;
4. verify Runtime/Cloudflare remain healthy while R0 is stopped;
5. start only `network-v2-r0.target`;
6. wait for all child services;
7. require real A + AAAA DNS answers;
8. require a real proxied HTTPS request;
9. require IPv4 and IPv6 blackbox probes;
10. require a 1 MB proxied transfer;
11. re-check Runtime/Cloudflare independence.

The canonical run passed all gates.

## Process recovery

The existing live recovery test remains valid under the new target topology. During canonical R9 acceptance sing-box was killed and systemd restored it automatically:

- old PID: `2445446`;
- new PID: `2446092`;
- restart count: `0 -> 1`;
- observed functional recovery: `3268 ms`.

The final live verification passed again after that destructive recovery.

## PMTU and packet-fault boundary

Native IPv4 DF probes succeeded through a 1472-byte ICMP payload on the current host path, so the focused host probe did not expose a PMTU black hole.

`tc` exists locally, but the current WSL kernel rejects `netem` with:

```text
Error: Specified qdisc kind is unknown.
```

R9 records that as a host capability boundary. Network v2 does not add a compatibility daemon or pretend packet-level impairment has been proven locally.

Local deterministic fault coverage therefore remains:

- Toxiproxy for L4 faults;
- Linux netns/veth for controlled topology;
- process/target destruction for lifecycle faults.

Packet-level delay/loss/reorder and kernel-WireGuard fidelity remain requirements of the standard-Linux reference runner.

## Canonical acceptance

Canonical repository-level R9 run:

- entry point: `task test:r9`;
- Runtime Job: `job-01a09552-3a42-7d12-a95b-432a86d63231`;
- operation digest: `sha256:abb67a1556503ebfd144ba3bd94ba6eccbf7ecc070c6281b127f17bfe16f27c9`;
- stdout SHA-256: `99df745ee8727ec0ed4868655f9dbf8e289065857c0481a0bee46cdfbcb35e38`;
- terminal evidence SHA-256: `2854ef5889c904bc3b58f7c4c52f286b04ea33196a539f712732e1f69e494b5f`.

Passed inside that single entry point:

- generic R0 source validation;
- systemd unit/target verification;
- Toxiproxy smoke;
- netns smoke;
- DNS A + AAAA;
- forced IPv4 HTTPS;
- forced IPv6 HTTPS;
- prefer-IPv6 dual-stack HTTPS;
- concurrent admission;
- 5 MB isolated long flow;
- Blackbox IPv4/IPv6;
- Blackbox DNS A/AAAA;
- Prometheus evidence;
- live generation materialization;
- source/live byte identity;
- whole-target stop;
- control-plane independence while R0 is stopped;
- target-only cold start;
- 1 MB post-cold-start long flow;
- sing-box automatic process recovery;
- final live verification.

## Post-state

Post-graduation audit:

- Runtime Job: `job-01a09553-5485-7b00-999f-bad45d99eda5`;
- operation digest: `sha256:a22dea0cafbcfedcdf51a5bf69d1dfcaa68ffde1fb7ffc46d193a71b36e0c137`;
- stdout SHA-256: `d2a61603455fa7976120c4f58dca55c6d152b1d1e8a7f2e3e739bf82853a24ed`;
- terminal evidence SHA-256: `cc50027b368ee2a29d10c7c0cd570b9610b6535e74ba1165c79fa11ead2a262d`.

Final observed state:

- `network-v2-r0.target`: active + enabled;
- dnsproxy/sing-box/blackbox/Prometheus: active + individually disabled;
- source/live config and unit bytes: exact match;
- DNS A: healthy;
- DNS AAAA: healthy;
- live 1 MB proxied transfer: HTTP 200;
- Blackbox IPv4: success;
- Blackbox IPv6: success;
- Blackbox DNS A: success;
- Blackbox DNS AAAA: success;
- Blackbox sing-box TCP: success;
- Prometheus sing-box readiness: success;
- Cloudflare production A/B/canary HA: `4/4/4`;
- Runtime process remained active;
- local `tc/netem`: unsupported by current kernel, fail-closed and explicitly recorded.

## Standing

**Generic Network v2 on the current WSL execution platform: PASSED.**

This means the local platform is independently usable for generic network work and no longer depends on Finance migration to be considered complete.

The following are portability/fidelity gates, not unresolved local R0 implementation bugs:

1. packet-level `tc/netem` acceptance on a standard Linux kernel;
2. containerlab topology acceptance on the standard-Linux runner;
3. kernel WireGuard differential against the WSL userspace `wireguard-go` realization;
4. an actual machine reboot acceptance, which is intentionally not performed inside the active Runtime/Cloudflare control-plane session.

Those gates must remain visible before claiming cross-platform or reboot-complete standing, but they do not block the local WSL Network v2 platform standing.
