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
| Long flow | repeated 5 MB proxied transfer | PASS |
| Concurrency | parallel proxied requests | PASS |
| Stable egress identity | repeated public egress observation | PASS |
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
| Packet delay/loss/reorder | tc/netem | EXTERNAL — current WSL kernel lacks netem |
| Full topology fidelity | containerlab | EXTERNAL — standard Linux runner required |
| Kernel WireGuard differential | kernel WG vs wireguard-go | EXTERNAL — standard Linux runner required |

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
