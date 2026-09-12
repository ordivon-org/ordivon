# R13 — Full Revalidation and Cold-Start Harness Hardening

Date: 2026-09-12

## Purpose

R13 is a fresh recheck of the already-graduated generic Network v2 platform. It does not add a new network mechanism. It revalidates R9, R11, and R12 from the current canonical source and fixes one acceptance-harness race found by that recheck.

## Finding

The first full recheck failed inside `tests/r0-cold-start-smoke.sh` after `systemctl stop network-v2-r0.target`.

Tracing showed the target, dnsproxy, and sing-box were already inactive while blackbox_exporter was still completing its asynchronous systemd stop job. The script immediately asserted that every child was no longer active and exited before the subsequent restart.

This was a test-harness synchronization defect, not a cold-start/data-plane failure. The control plane remained healthy and the R0 target was manually restored and reverified before repair.

## Repair

The cold-start harness now:

- waits for the target and all four child services to leave `active`, `activating`, and `deactivating` states using bounded `wait_inactive` logic;
- installs an EXIT trap that starts `network-v2-r0.target` if the test exits early;
- removes the trap only after successful target restart, functional readiness, long-flow proof, and control-plane verification.

This prevents an acceptance failure from becoming an R0 service outage and avoids assuming that target stop completion implies every `PartOf=` child has already reached inactive.

## Fresh full regraduation

After the repair, R9, R11, and R12 were executed sequentially in one Runtime Job.

Runtime Job:

- Job: `job-01a0957a-6faf-7f90-8f8b-60d2705ba171`;
- operation digest: `sha256:27fffaf31c2fe01e585816723d0a2fdfd20508c047087ec4271ef98832f59ac9`;
- stdout SHA-256: `d54622a2fe40333080728edb6fd9c68f2fe5aa789c19fda5addc8c0992158bfc`;
- terminal evidence SHA-256: `5ec1f882deaa86c4aa8b84a95cabb040ee262429643aa41a362a687fa06547f1`;
- elapsed: about 86 seconds.

Fresh observed results included:

- R9 source validation, Toxiproxy, netns, A/AAAA, forced IPv4, forced IPv6, dual stack, concurrency, 5 MB flow: PASS;
- whole-R0 target stop with Runtime/Cloudflare control-plane independence: PASS;
- target cold start and 1 MB post-start flow: PASS;
- sing-box process recovery: PASS, observed about 3.3 seconds;
- HTTP/1.1 and HTTP/2: PASS;
- DNS UDP/TCP A/AAAA: PASS;
- stable public egress across five observations: PASS;
- three repeated 5 MB flows: PASS;
- isolated TUN TCP + HTTP/3/QUIC: PASS;
- IPv6-preferred fallback to IPv4: PASS;
- IPv4-preferred fallback to IPv6: PASS;
- DNS partial-upstream failure: PASS;
- all-upstream uncached/expired queries fail closed with SERVFAIL: PASS;
- DNS recovery without dnsproxy restart: PASS;
- final live verification: PASS.

## Standing

The R13 recheck found no new Network data-plane, DNS, observability, protocol, or local-resilience defect after the harness race was corrected.

**Generic Network v2 on the current WSL platform remains locally graduated.**

The remaining Network-specific gaps are still external-fidelity gates requiring a standard Linux environment: `tc/netem`, containerlab, and kernel-WireGuard differential. Windows-host reboot plus WSL auto-launch remains a Workstation/bootstrap concern.
