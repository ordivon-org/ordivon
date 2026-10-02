# Network Capability Router R1

The Network Capability Router is a read-only pre-execution planner. Callers provide explicit
NetworkRequirement features; the router does not infer requirements from natural language.

Current routes:

- direct-linux-v1: current Network v2 core/direct Linux path.
- provider-egress-v1: semantic shared provider-egress through the current compatibility carrier.
- isolated-tun-v1: full-IP/UDP/QUIC isolated TUN route, admitted only when its qualification evidence
  is bound to the current kernel.

The router grants no Network authority and no ProviderEffect authority. A selected route is only a
current compatibility/readiness projection. Historical PASS evidence is not current readiness: an
evidence-bound route becomes QUALIFICATION_STALE when its platform kernel binding no longer matches
the observed kernel.

This is intentionally not a network controller, network DSL, credential materializer, or effect
dispatcher.
