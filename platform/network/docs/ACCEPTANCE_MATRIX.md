# Generic Network acceptance matrix

Acceptance is capability-based rather than round-based.

| Capability | Evidence | Current local standing |
|---|---|---|
| IPv4 | forced IPv4 HTTPS | PASS |
| IPv6 | forced IPv6 HTTPS | PASS |
| DNS A / AAAA | UDP/TCP queries | PASS |
| Address-family fallback | preferred family unavailable in deterministic local origin | PASS both directions |
| HTTP/1.1 | proxied request with negotiated version assertion | PASS |
| HTTP/2 | proxied request with negotiated version assertion | PASS |
| Long flow | deterministic local 5 MB origin through isolated sing-box proxy, exact size + SHA-256 | PASS |
| Concurrency | parallel proxied external requests | PASS |
| External egress observation | one valid public IP observation through live proxy | PASS |
| UDP/QUIC | HTTP/3 through isolated TUN/netns | PASS |
| DNS partial failure | one upstream unavailable | PASS UDP/TCP |
| DNS all-upstream failure | uncached/expired query returns SERVFAIL | PASS |
| DNS recovery | upstream returns without dnsproxy restart | PASS |
| Observability | Blackbox IPv4/IPv6/A/AAAA/TCP + Prometheus | PASS |
| L4 fault injection | Toxiproxy | PASS |
| Local topology | netns + veth | PASS |
| Whole-platform cold start | stop/start target + functional readiness | PASS |
| Process recovery | kill live sing-box and observe systemd recovery | PASS |
| WSL reboot recovery | real WSL boot boundary + post-boot live verify | PASS |
| Control-plane independence | R0 stopped while Runtime/Cloudflare remain healthy | PASS |
| Packet delay/loss/reorder | tc/netem on standard-Linux KVM reference | PASS on reference Linux |
| Full topology fidelity | containerlab two-node Linux topology + data-link reachability | PASS on reference Linux |
| Kernel WireGuard differential | kernel WG lifecycle vs direct wireguard-go TUN/UAPI lifecycle | PASS on reference Linux |

## Public task entry points

```text
task core:validate
task core:verify
task core:converge

task accept:source
task accept:live
task accept:local
```

Provider and consumer acceptance use their own namespaces and are not generic graduation prerequisites.

## Evidence projection

`evidence/current-capabilities.json` is a generated acceptance projection, not hand-authored authority.

The local authority path is:

```text
task accept:local
  → every generic source/live acceptance gate passes
  → scripts/capability-report.py write-local
  → evidence/current-capabilities.json
```

The report records:

- the acceptance entry point;
- acceptance timestamp;
- source Git revision;
- a content+mode fingerprint over generic Task/config/systemd/acceptance/evidence-generator inputs;
- a stable platform fingerprint (OS, architecture, kernel release, WSL classification).

`task evidence:verify-local` fails if the checked-in report no longer matches the generic source or current platform. This prevents a historical PASS document from silently remaining current after behavior-defining files or the execution kernel change.


## Standard-Linux reference authority

The current reference standing is **STANDARD_LINUX_REFERENCE_GRADUATED**. The authority record is `evidence/reference-linux-20260912.json`. Local WSL evidence and standard-Linux reference evidence are intentionally separate projections: WSL proves the real workstation path; KVM reference Linux proves kernel capabilities unavailable to WSL.
