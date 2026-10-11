# Network Upstream-First Convergence R1

## Purpose

Network-v2 progressively moves mechanism ownership to mature upstream projects while keeping Ordivon-specific semantic policy, authority, capability routing, evidence, acceptance, reconciliation, and rollback.

This is a strangler migration, not a rewrite.

## Architecture law

    workload requirement
      -> Ordivon semantic policy / authority
      -> Ordivon capability selection
      -> thin Ordivon adapter
      -> mature upstream mechanism
      -> operating-system / kernel substrate

Mechanism health never proves workload consequence readiness.

## Canonical terms

- **Mechanism**: a reusable implementation such as WireGuard, Gluetun, sing-box, HAProxy, dnsproxy, Prometheus, blackbox_exporter, cloudflared, or Toxiproxy.
- **Semantic authority**: Ordivon-owned permission and policy describing what a consumer may do.
- **Physical realization**: one concrete running mechanism graph that realizes a semantic route.
- **Carrier realization**: a physical realization that provides provider egress.
- **Active realization**: the only realization currently admitted for production effects.
- **Candidate realization**: a source/config realization under qualification with no production authority.
- **Serialized candidate**: a candidate that may only be exercised while the active realization is stopped because both would use the same single-session ClientIdentity.
- **Consequence readiness**: owner-specific proof that the destination/policy behavior required by a consumer is currently satisfied.
- **Adapter**: thin Ordivon code/config that translates upstream state into an Ordivon-owned contract; it must not reimplement the upstream mechanism.

## Current boundary

The current production provider egress remains:

    ClientIdentity surfshark:linux-shared-r1
      -> nv2-browserless-prod
      -> wg-quick + wireguard-go
      -> provider DNS
      -> sing-box HTTP carrier :19680
      -> scoped consumers

The ClientIdentity concurrency policy is single-physical-session. Therefore a Gluetun candidate using that identity is serialized, not concurrently shadowed.

## First upstream target: Gluetun

Official upstream for the R1 candidate:

- repository: https://github.com/passteque/gluetun.git
- source tag: v3.41.3
- tag revision: 3d1e20c5551e9cae1f9d938dc7b7214a6987f27e

Gluetun is evaluated as a replacement for physical VPN mechanism ownership only. It does not receive Ordivon consumer authority.

Target ownership split:

    Gluetun owns:
      provider server selection/filtering
      WireGuard/OpenVPN process lifecycle
      VPN liveness/reconnect
      VPN-local firewall/kill-switch behavior
      VPN-local DNS/proxy features when qualified

    Ordivon owns:
      ClientIdentity authority and concurrency policy
      ProviderProfile semantics
      consumer destination policy
      directFallback policy
      route/capability selection
      live consequence acceptance
      effect admission
      rollback evidence

## Realization contract

Source describes current and candidate realizations without installing either.

Required R1 state:

    activeRealizationId = legacy-wireguard-r1
    candidateRealizationId = gluetun-v3.41.3-r1
    candidate activationMode = serialized-only
    candidate productionAuthority = false
    candidate concurrentWithActive = false

The realization registry contains no secret bytes and points to the existing ProviderProfile and ClientIdentity descriptors.

## Migration gates

### M0 — Freeze and currentness

- freeze custom VPN/control-plane growth;
- bind current source revision and owner;
- retain current production realization unchanged.

### M1 — Typed source contract

- pin official Gluetun source;
- add typed carrier-realization registry;
- represent current legacy realization and serialized Gluetun candidate;
- validate no secret projection and no concurrent identity use.

### M2 — Source-only candidate

- materialize or build Gluetun only in an isolated test carrier;
- use fixture/non-production material for source behavior tests;
- prove source/config contract, health surface, fail-closed startup, and teardown;
- no provider credential or production network effect.

### M3 — Serialized live canary

Requires a separate natural-owner effect admission.

- prove no active consumer workflow depends on the sole provider session;
- record current realization and rollback preimage;
- stop current provider session;
- start Gluetun with the same identity exactly once;
- run bounded provider and consumer consequence acceptance;
- stop Gluetun and restore current realization;
- prove namespace/route/consumer recovery.

A failed or ambiguous canary restores legacy and does not retry automatically.

### M4 — Review and ownership decision

Independent Spec and Standards review must both pass. Only then may the natural owner decide whether Gluetun becomes the active physical realization.

## Retirement ledger

| Current surface | R1 disposition | Retirement gate |
|---|---|---|
| scripts/network_capability_router.py | KEEP | Ordivon semantic/capability ownership |
| config/provider-egress.json | KEEP / THIN | Point to realization contract, not implement mechanism |
| ProviderProfile / ClientIdentity schemas | KEEP | Ordivon authority boundary |
| provider-profile.json | KEEP | Provider semantic projection |
| client-identity-linux-shared.json | KEEP | Concurrency/secret ownership |
| Gluetun server catalog pin | REUSE | May move under Gluetun capability ownership after cutover |
| provider:surfshark:profiles generation | DELETE_AFTER_GATE | Gluetun active + rollback qualified |
| network-v2-browserless-wireguard.service | DELETE_AFTER_GATE | Gluetun active + lifecycle parity |
| consumers/browserless/provider-switch.sh | DELETE_AFTER_GATE | Gluetun server-selection/reconnect parity |
| provider-carrier-ready.sh | KEEP_AS_ADAPTER | Separates mechanism liveness from consequences |
| acceptance/production-path.sh | KEEP | Consequence evidence |
| consumer scoped sing-box policies | KEEP | Consumer fail-closed policy |
| provider sing-box HTTP carrier | HOLD | Delete only if Gluetun proxy preserves exact consumer seam |
| provider dnsproxy service | HOLD | Delete only after DNS consequence parity |
| netns/veth/forwarding composition | HOLD | WSL substrate boundary remains until replacement proves parity |
| HAProxy failover capability | KEEP_DORMANT | Activate only with independent physical identities/carriers |
| Prometheus + blackbox | KEEP | Current observability requirement already satisfied |
| OpenTelemetry Collector | FUTURE_CONDITIONAL | Adopt only for a real cross-service telemetry gap |
| NetBird / Headscale | FUTURE_CONDITIONAL | Adopt only after a real multi-node requirement |

## Acceptance invariants

A candidate fails if any of these regress:

- one ClientIdentity maps to at most one concurrent physical session;
- provider credentials remain outside Git;
- no direct fallback for consumers that currently prohibit it;
- unknown destinations remain rejected where currently required;
- consumer readiness is not inferred from VPN health alone;
- Direct Linux path remains independent;
- Windows Real Chrome projection remains fail-closed;
- rollback restores the previous admitted realization;
- no candidate source path silently becomes a production systemd dependency.

## Non-goals

- No universal Ordivon network controller.
- No custom VPN implementation.
- No host-wide default-route takeover.
- No multi-node mesh deployment in R1.
- No replacement of mature upstream components without a demonstrated requirement gap.
