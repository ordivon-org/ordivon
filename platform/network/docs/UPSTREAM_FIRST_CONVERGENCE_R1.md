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


## M3 topology decision — R1

The first serialized canary topology uses a Gluetun-owned container/network namespace behind the existing Network-v2 compatibility namespace.

Selected shape:

    existing consumers
      -> 10.252.246.2:19680
      -> sing-box compatibility adapter in nv2-browserless-prod
      -> 10.252.246.1:19682 on the host-veth
      -> Gluetun HTTP proxy
      -> Gluetun-owned WireGuard/firewall/DNS
      -> Surfshark

This selection keeps the current consumer seam unchanged while moving VPN mechanism ownership to upstream Gluetun.

Evidence and constraints:

- Current nv2-browserless-prod can reach host-veth 10.252.246.1 directly over nv2blpn; bounded feasibility proof passed without changing routing or provider identity.
- The pinned upstream OCI image is docker.io/qmcgaw/gluetun:v3.41.3, index digest sha256:fa19cc76b2af13d57a8d3dc3066f2ada061b1c761b8aecf989b3877c0486e027, linux/amd64 manifest sha256:1baa76576dea1dfbafbd62bb635daf40fd87171f63273c2fdfe630418783011e.
- Official Gluetun supports a read-only WireGuard INI mounted at /gluetun/wireguard/wg0.conf; the live effect layer can therefore consume the existing protected combined profile without copying key/address values into Git.
- Gluetun keeps its firewall enabled and owns its own VPN-local DNS. The R1 candidate does not disable the upstream firewall.
- The compatibility sing-box config has no direct outbound and no DNS block of its own; its sole outbound is the host-veth Gluetun proxy.
- A read-only compatibility preflight verifies the current namespace-to-host-veth route, candidate config syntax, and candidate-port vacancy without starting listeners, touching provider identity, or proving the two-hop data path. The earlier bounded host-veth reachability experiment remains separate evidence; live two-hop/provider execution still requires the M3B effect gate.

### Rejected first-cut topology: Gluetun inside nv2-browserless-prod

The current namespace is deliberately fail-closed: the legacy WireGuard lifecycle supplies the provider endpoint route and VPN default path. Making Gluetun start directly inside that namespace would require reopening or redesigning the pre-VPN default route/firewall bootstrap boundary before Gluetun can discover and reach its endpoint. That would either create a direct-fallback window or require additional custom host firewall glue.

R1 therefore prefers the Gluetun-owned container namespace, where upstream owns its expected default-route/firewall lifecycle. The old namespace is retained only as a compatibility adapter and becomes a later deletion candidate after consumers can move to an upstream-owned seam directly.

### M3 source-only artifacts

- capabilities/gluetun/external/gluetun-image.lock
- capabilities/gluetun/config/serialized-candidate.env
- consumers/browserless/config/provider-carrier-gluetun-candidate.json
- capabilities/gluetun/acceptance/compatibility-hop.sh

These artifacts grant no provider effect authority and do not change the active realization.


## Ownership succession and orphaned topology decision — 2026-10-12

The human retired the previous Network source owner and appointed the GPT-6
successor on the existing Work; Host Work revision 4 records the authority
transition. This is an owner transition, **not** a provider or production
effect grant. No existing live consumer/VPN state was changed.

**Current auditable source candidate:** isolated successor Workspace
`ws-network-upstream-review-r1-20261012`, initially pinned to
`59b780ae671c4bcd2c4a920035b06bb7a7083cbf`. Its two regression fixes
enforce carrier-realization graph uniqueness and reject wildcard listener
collisions in the read-only compatibility preflight. The Network test suite
passed 60/60 and `task all:validate` passed (Runtime
`job-01a12bd4-bd11-70d1-b580-028c72e7b7a8`).

**Non-adopted predecessor WIP:** the retired owner's uncommitted workspace
`ws-network-upstream-first-r1-20261011` proposes a Podman Quadlet bridge
`10.252.246.0/30` with gateway `10.252.246.1`, a Gluetun container
at `10.252.246.2`, and an automatic stable netns alias named
`nv2-browserless-prod`. At review time, the live WSL host already had
`nv2blph` at `10.252.246.1/30` with an installed kernel route to
`10.252.246.0/30`, and `nv2-browserless-prod` was the active legacy
network namespace. Runtime read-only evidence:
`job-01a12c57-9e73-7592-a4f0-b15066a0bcb4`.

The alternative is **HOLD, not integrated**. It would require resolving
overlapping host IP/route ownership and proving the namespace alias cannot
replace or detach the live legacy namespace, including during abnormal
container termination. It also removes the initial compatibility proxy
without yet proving every scoped consumer interface and fail-closed path.
This observation is a source/topology conflict, not evidence of an actual
production collision. The discarded code remains intact in the archived
workspace for traceability; no WIP patch is auto-cherry-picked.

**Current M3B authority boundary:** source and fixture acceptance do not
authorize live Gluetun or a second session for
`surfshark:linux-shared-r1`. A serialized canary still requires an
independent fixed-HEAD Spec/Standards review, current consumer drain, exact
rollback preimage, separately admitted owner effect, pinned image
materialization, and unconditional legacy restoration plus consequence
checks. An ambiguous result is HOLD with legacy restored.

## M3 source acceptance update — independent audit 2026-10-14

Independent audit Topic seq16797 accepted owner succession and bounded source
fixes but kept M3B HOLD. P1: a source config pointed Gluetun's HTTP proxy
`:8888` at a sing-box hop expecting host `10.252.246.1:19682` without
an explicit publication path. The non-installed upstream Podman Quadlet
source candidate now declares that exact port mapping and the matching
Gluetun container-side `FIREWALL_INPUT_PORTS=8888`, with immutable OCI
image pin and no implicit installation. The native Quadlet generator's
dry-run output is tested. This is configuration evidence, **not Gluetun
runtime ingress or VPN acceptance**.

An isolated true sing-box HTTP CONNECT hop to a local proxy fixture is
exercised without production/provider effect and reports the fixture scope
explicitly. It establishes proxy protocol compatibility only; it cannot
promote any consumer to READY.

Predecessor WIP remains quarantined: its alias-deletion logic was independently
flagged as unsafe on lost container PID, in addition to the host-veth CIDR
collision. No old Quadlet files are used in the approved candidate.

P2: `carrier-realization-semantics.jq` deliberately pins legacy-active
and Gluetun-candidate **for R1**; changing the active mechanism requires
a separately reviewed registry transition, not an edit that merely flips
the existing JSON field.

The existing `provider-carrier-ready.sh` and
`consumers/browserless/acceptance/production-path.sh` explicitly check
legacy WireGuard units, namespace interface, handshakes and a fixed provider
site. They are **legacy-restoration evidence**, not candidate-neutral proof
during a Gluetun serialized canary. Windows Chrome readiness also invokes
the former. Candidate phase must use separately reviewed network/consumer
consequence probes that do not assume a concurrently running legacy WG
session, while restoration phase reruns the legacy readiness suite.
Any canary that invokes legacy-only readiness to certify Gluetun is invalid.

## M3 R3 ingress isolation and witnessed negative oracle — 2026-10-14

Independent Review R2 (Network Topic seq16861) exposed the default Podman
bridge as a bypass candidate: a host-only PublishPort bind is not a
restriction on peers of the same bridge. The R3 candidate no longer
uses rootful Network=bridge. It has a dedicated Quadlet .network,
network-v2-gluetun-private-r1, with Options=isolate=strict,
10.253.239.0/30 (gateway .1, the only container address .2),
DisableDNS=true, and the container pinned to IP=10.253.239.2.
This range is separate from live host-veth 10.252.246.0/30 and
default Podman 10.88.0.0/16. R3 changes neither of those existing
networks. Native Quadlet generator proves both network-create
and container network/IP source commands. The server publication
remains 10.252.246.1:19682:8888/tcp.

Native runtime evidence is narrower and explicit: in a disposable
unshare --net namespace, Podman created an equivalent isolated
bridge, launched a non-Gluetun cached Java test image at
10.253.239.2, and confirmed an actually listening process with
a same-container TCP probe. A second container attachment to the
/30 was rejected by Podman IPAM; a container on the default Podman
bridge failed its direct TCP probe to .2. This proves scoped
one-member allocation/cross-bridge denial for Podman 6.1/Netavark in
that nonproduction namespace. Runtime job:
job-01a13982-d235-7c62-99ad-6776237dc391.
A preceding attempt in which the test server failed to start was
explicitly discarded as a false positive: job-01a13981-f990-79b2-bd38-0ff6ea12f3f3.

Threat limits: rootful Podman administrators and processes sharing the
Gluetun container namespace are not isolated by IPAM. The bridge
separates ordinary default-network peers, not management authority.
Prior to any live candidate, independently inspect Podman network
membership/options/subnet/route currentness; no unexpected peer or
stale same-name network is acceptable. An attempt to test host-veth
port publication inside a disposable namespace was blocked by
Runtime policy (job-01a13984-a187-76f3-8747-18f6c38c7794);
no bypass was used or port runtime PASS claimed.

P2 oracle now uses an observable local direct destination. A deliberately
mutated unsafe sing-box route reaches that witness, receives HTTP 403,
and curl --fail returns exit 22. The fixture records the incoming
direct connection and emits DIRECT_LEAK_DETECTED rather than
FIXTURE_FAULT_PASS. Nonmutated offline paths require expected proxy/
transport failure and zero direct witness arrivals. This is qualified
loopback fixture evidence, NOT exhaustive public-egress assurance.

Pinned Gluetun OCI image pull via the existing scoped Supply-Chain
proxy 127.0.0.1:19581 failed after a registry CDN redirect and
proxy connection reset (job-01a13979-9fd3-70e0-81db-04bb5faef632).
No unapproved alternate route was used and Gluetun was not run.
Actual Gluetun firewall, HTTP proxy auth/ingress, VPN forwarding and
scoped consumer consequences remain UNPROVEN. M3B remains HOLD.

### R3 partial candidate-neutral owner consequence evidence

Existing Model Provider, Supply Chain and X Reality sing-box source
allowlists are now exercised in an isolated real sing-box + local HTTP
CONNECT fixture without legacy WG unit, Gluetun or production routing.
Each of the three known allowed domains reaches exactly one local
upstream CONNECT, while unknown destinations do not reach the fixture.
This is **consumer policy routing** evidence only: the fixture uses
plain HTTP within the CONNECT tunnel, not a real authenticated HTTPS
service. The new test does not establish actual owner readiness,
Temporal/consumer drain, Browserless/Chrome/Finance parity, or canary
rollback. Do not use it to promote M3B from HOLD.

## R4 Supply-Chain CDN and consumer policy currentness — 2026-10-14

The pinned Gluetun OCI pull previously failed when Docker Hub redirected
a blob to production.cloudfront.docker.com. Existing Supply-Chain policy
authorized the DIFFERENT hostname production.cloudflare.docker.com but
omitted production.cloudfront.docker.com. The official Docker Desktop
network allowlist names the latter for image pulls, and Docker's OCI
registry API permits 307 CDN redirects.

R4 adds the exact production.cloudfront.docker.com hostname in BOTH
consumers/supply-chain/config/authority.json and
consumers/supply-chain/config/egress.json. It preserves the former
Cloudflare host, TCP/443 policy, directFallback=false, and the terminal
catch-all reject. No wildcard or cloudfront.docker.com suffix
authorization is added. Real isolated sing-box HTTP CONNECT tests now
verify the allowed hostname and reject the suffix-confusable
production.cloudfront.docker.com.attacker.invalid.

**Source != live deployment**: /etc/network-v2/supply-chain/authority.json
still has zero entries for this hostname versus one in current source.
The existing read-only task consumer:supply-chain:verify fails at the
source-vs-installed cmp (job
job-01a139a5-ac46-77c0-ba5c-009a782f366c), even though the
network-v2-supply-chain-egress service remains active. A separately
admitted MINIMAL Supply-Chain deployment and independent runtime
redirect/OCI blob retrieval checks are required. Do not invoke
broad materialize/converge implicitly: that would touch systemd,
Docker drop-ins and other consumer integration.

R4 also extends candidate-neutral POLICY fixtures:
- Finance: original finance-okx inlet and its provider-carrier rule,
  plus unknown-domain reject; permitted Treasury/FRED public-direct
  bypasses are intentionally untouched and NOT tested.
- Windows Chrome: original mixed inlet private-address and IPv6 reject
  rules; a disposable source copy temporarily replaces the direct
  outbound with a local HTTP CONNECT stub so no live external traffic
  occurs. This is NOT full Chrome or Browserless readiness.

These bounded loopback/source tests do not prove authentic HTTPS,
Gluetun image/runtime firewall, all Finance inlets, workload drain or
fault-injected physical rollback. M3B serialized canary remains HOLD.

## R5 scoped Docker CDN preflight and nonproduction rollback evidence — 2026-10-14

R4 fixed SOURCE allowlist authorization for the exact Docker Hub blob
host production.cloudfront.docker.com, but deliberately did not restart
the running Supply-Chain proxy or broader Network-v2 consumers.

R5 now includes a **read-only, side-effect-free** file currentness gate:

    python3 consumers/supply-chain/acceptance/cdn-preflight.py --source-dir consumers/supply-chain/config --installed-dir /etc/network-v2/supply-chain

Its decisions distinguish READY_TO_DEPLOY_NARROW_SCOPE (only exact CDN
hostname absent in both installed files), ALREADY_DEPLOYED,
HOLD_PARTIAL_DEPLOYMENT, HOLD_UNEXPECTED_DRIFT,
HOLD_LEGACY_AUTHORITY_ALIAS, HOLD_SOURCE_INVALID, and
HOLD_UNREADABLE_OR_INVALID. A READY decision is a diff classification,
not human permission for effect. Digests, not file contents, are its
readback evidence. It does not edit bytes, call systemctl or fetch OCI.

The actual installed Supply-Chain pair is **NOT** merely source-minus-CDN.
The deployed egress.json is source-minus-CDN, but deployed
authority.json additionally has networkAuthority.name=browserless-prod.
The frozen SOURCE uses provider-egress, the canonical Network-v2 semantic
authority. R5 reproducibly detects exactly this known legacy alias and
returns HOLD_LEGACY_AUTHORITY_ALIAS (nonzero). Do not use a broad
materialize/converge step for a purported one-host-only repair: it
would also silently change an existing semantic authority binding.

For a narrow **test-only** recovery rehearsal, the source includes
consumers/supply-chain/acceptance/cdn-file-rollback-rehearsal.py.
It strictly accepts a marked temporary fixture under /tmp, refuses
production directories and symlink/hardlinked config files, verifies
the exact preimage state using cdn-preflight.py, atomically stages
both source files, injects faults after the first write, after the
second write, and after the synthetic post-stage boundary, then
restores each original byte stream and file mode. No service restart,
Docker operation, VPN identity or production network effect is possible
from this fixture. Therefore PASS proves bounded sandbox FILE
restoration only, **not live systemd/session rollback**.

R5 read-only consumer census found Browserless, Finance, Supply-Chain,
Model Provider, Windows Chrome and X Reality target units all active.
A bounded Temporal query returned zero running workflows on the
ordivon-agent-automation task queue at that instant; this does NOT
prove cross-consumer quiescence or prevent new workloads. M3B remains
HOLD. Production Supply-Chain config changes require independently
accepted authority-alias reconciliation, live-source currentness,
consumer/drain consent, precise effect/rollback admission and readiness
proof. A policy source test is never a Gluetun container or provider
session test.

## R6 bounded source-integrity and actual process recovery — 2026-10-14

The Supply-Chain CDN preflight remains READ ONLY and fail-closed. R6
strengthens it with **exact source byte SHA-256 pins** for the one
approved R4 host addition, not a generic mutable allowlist. This
prevents a pair of self-consistent but unauthorized source changes
(e.g. adding attacker.invalid to both authority and sing-box egress)
or replacing the localhost proxy address from passing as a one-host
deployment. A later intentional authorization edit requires a separate
review and explicit re-pinning of the current preflight; it must not
inherit production rollout authority from R4.

R6 additionally adds a **REAL sing-box process-level** restart and
failure recovery fixture:

    python3 consumers/supply-chain/acceptance/cdn-singbox-service-rehearsal.py --fault after-new-run

The script creates only an ephemeral localhost HTTP CONNECT proxy and
sing-box process using a temporary config file under /tmp. It starts
the old source-minus-CDN policy, verifies registry allow/unknown deny/
CDN deny, stages the new allowed CDN policy and injects failure at
three process boundaries: before stopping the old process, after
stopping the old process, and after starting/validating the new process.
It restores original TEMPORARY config file bytes and, when needed,
starts a replacement process; then proves the OLD registry/unknown/CDN
routing consequences again through actual sing-box and a real
observed localhost HTTP CONNECT witness.

This provides much stronger **process-level** evidence than a file-only
rollback. It does not use the installed Supply-Chain service, Docker,
Podman, a real registry/TLS session, systemd, Surfshark or Gluetun.
It DOES NOT prove a production systemd restart, loss-of-connection
recovery for in-flight consumers, real VPN rollback or owner drain.
The previous R5 real-world preflight still returns
HOLD_LEGACY_AUTHORITY_ALIAS until separately reviewed config authority
reconciliation. NO LIVE PRODUCTION CHANGE is authorized by these tests.

One subsequent bounded global Temporal census attempt was rejected by
the surrounding tool safety gate; no global count is claimed. The
prior snapshot of zero Running workflows in one specified automation
TaskQueue remains insufficient for cross-owner drain. The M3B
serialized production canary remains HOLD.

## R7 critical-path execution — scoped runtime CDN, pinned image, real Gluetun sandbox

R7 removes the earlier false coupling between the Supply-Chain semantic
authority metadata and the sing-box runtime file. The running unit
`network-v2-supply-chain-egress.service` consumes only
`/etc/network-v2/supply-chain/egress.json`. The source/runtime CDN delta
was exactly one domain, `production.cloudfront.docker.com`; the separately
stale `authority.json` name (`browserless-prod` instead of
`provider-egress`) is metadata convergence and is not a prerequisite for
the runtime CDN route.

The scoped production runtime transaction changed only egress.json from
SHA-256 `0327fdd0617d126b18747e5d70e803b6f73e6502a43b119f7a064c6bd0378600`
to source SHA-256
`c5fa529080f3eb0ede04c14bfca4f4699a7973e1fe3e013f3a704045a58cb377`,
preserved the authority.json digest, restarted only
`network-v2-supply-chain-egress.service`, and ran the existing scoped
readiness probes. Receipt: Runtime
`job-01a13a3e-151b-7f33-8fbe-f2d52d7620ce`. Registry/auth/GCR/Artifact
Registry/Elastic remained reachable through the scoped proxy and unknown
destinations remained rejected. A direct CDN probe through 127.0.0.1:19581
then produced proxy CONNECT 200 and CloudFront HTTP 403 rather than the
former connection reset (`job-01a13a3e-62df-7920-b14a-38e367de7664`).

Using that already-authorized Supply-Chain route, Podman materialized the
exact pinned Gluetun linux/amd64 manifest
`sha256:1baa76576dea1dfbafbd62bb635daf40fd87171f63273c2fdfe630418783011e`
(`job-01a13a3e-87dc-7851-9502-324d3b123a65`). No direct-egress bypass or
alternate mirror was used.

The new `capability:gluetun:local-real-sandbox` acceptance uses that real
pinned image with a generated, throwaway local WireGuard peer. It does not
load the Surfshark production identity. It proves:
- real Gluetun v3.41.3 starts with kernel WireGuard, firewall and HTTP
  proxy enabled;
- traffic through Gluetun :8888 crosses the local WireGuard tunnel;
- the private Podman /30 admits no second ordinary peer and a default
  bridge peer cannot reach :8888;
- removing the local WireGuard peer makes proxy traffic fail closed;
- restoring the peer and restarting the candidate restores consequence;
- the real Browserless candidate sing-box adapter can forward through
  real Gluetun to the local WireGuard destination while preserving the
  private-destination rejection rule;
- teardown removes the container, network and test WireGuard interface.

Primary real execution receipt:
`job-01a13a46-157a-7f80-9587-43043c69179c`.
Real Browserless adapter -> Gluetun -> local WireGuard two-hop:
`job-01a13a48-d1ea-79d1-924f-7747c7d86000`.
The reproducible source harness:
`capabilities/gluetun/acceptance/local-wireguard-real-sandbox.sh`,
validated independently of production identity at
`job-01a13a4c-0cc6-7862-8440-e279cbf474b4`. A forced TERM test
`job-01a13a4d-0fec-76c2-99a0-dea196becf35` confirms its temporary
container/network/WireGuard resources are removed.

R7 also closes the Finance policy-fixture breadth gap: all seven
provider-bound Finance inlet/domain/port routes are independently
executed through the candidate-neutral real sing-box local carrier
fixture, including the OKX 8443 WebSocket lane. Treasury/FRED direct
lanes remain explicitly separate and are not sent through that fixture.

The Supply-Chain preflight now reports runtime and metadata independently:
real installed state is `runtimeEgressStanding=CURRENT` and
`metadataStanding=HOLD_LEGACY_AUTHORITY_ALIAS`, summarized as
`RUNTIME_EGRESS_CURRENT_METADATA_DRIFT`. Runtime CDN delivery is no longer
incorrectly blocked by the metadata alias.

These results still do NOT prove the production host-veth
10.252.246.1:19682 publication (a prior Runtime attempt was safety
rejected), the unique Surfshark production session cutover, complete
cross-owner blackout, or production systemd/provider rollback. M3B
remains a separate high-risk serialized effect.

## R7 critical-path execution — scoped runtime CDN, pinned image, real Gluetun sandbox

R7 removes the earlier false coupling between the Supply-Chain semantic
authority metadata and the sing-box runtime file. The running unit
network-v2-supply-chain-egress.service consumes only
/etc/network-v2/supply-chain/egress.json. The source/runtime CDN delta
was exactly one domain, production.cloudfront.docker.com; the separately
stale authority.json name (browserless-prod instead of provider-egress)
is metadata convergence and is not a prerequisite for the runtime CDN route.

The scoped production runtime transaction changed only egress.json from
SHA-256 0327fdd0617d126b18747e5d70e803b6f73e6502a43b119f7a064c6bd0378600
to source SHA-256
c5fa529080f3eb0ede04c14bfca4f4699a7973e1fe3e013f3a704045a58cb377,
preserved the authority.json digest, restarted only the Supply-Chain
egress service, and ran the existing scoped readiness probes.
Receipt: job-01a13a3e-151b-7f33-8fbe-f2d52d7620ce. A direct CDN probe
through 127.0.0.1:19581 then produced proxy CONNECT 200 and CloudFront
HTTP 403 rather than the former connection reset
(job-01a13a3e-62df-7920-b14a-38e367de7664).

Using that scoped Supply-Chain route, Podman materialized the exact pinned
Gluetun linux/amd64 manifest
sha256:1baa76576dea1dfbafbd62bb635daf40fd87171f63273c2fdfe630418783011e
(job-01a13a3e-87dc-7851-9502-324d3b123a65). No direct-egress bypass or
alternate mirror was used.

The new capability:gluetun:local-real-sandbox acceptance uses that real
pinned image with a generated throwaway local WireGuard peer. It does not
load the Surfshark production identity. It proves real Gluetun v3.41.3
kernel WireGuard, firewall and HTTP proxy operation; traffic through
Gluetun :8888 crossing the local WireGuard tunnel; private Podman /30
peer isolation; tunnel-loss fail-closed behavior; restart recovery; the
real Browserless candidate sing-box adapter forwarding through real
Gluetun to the local WireGuard destination while preserving the private
destination reject; and residue-free teardown.

Primary real execution receipt:
job-01a13a46-157a-7f80-9587-43043c69179c.
Real Browserless adapter -> Gluetun -> local WireGuard two-hop:
job-01a13a48-d1ea-79d1-924f-7747c7d86000.
Reproducible harness:
capabilities/gluetun/acceptance/local-wireguard-real-sandbox.sh,
validated at job-01a13a4c-0cc6-7862-8440-e279cbf474b4. Forced TERM
cleanup job-01a13a4d-0fec-76c2-99a0-dea196becf35 confirms temporary
container/network/WireGuard resources are removed.

R7 also closes the Finance policy-fixture breadth gap: all seven
provider-bound Finance inlet/domain/port routes are independently
executed through the candidate-neutral real sing-box local carrier
fixture, including OKX WebSocket port 8443. Treasury/FRED direct lanes
remain separate and are not exercised through the provider fixture.

The Supply-Chain preflight now reports runtime and metadata independently:
real installed state is runtimeEgressStanding=CURRENT and
metadataStanding=HOLD_LEGACY_AUTHORITY_ALIAS, summarized as
RUNTIME_EGRESS_CURRENT_METADATA_DRIFT. Runtime CDN delivery is no longer
incorrectly blocked by that metadata alias.

These results do not prove production host-veth
10.252.246.1:19682 publication, the unique Surfshark production session
cutover, complete cross-owner blackout, or production systemd/provider
rollback. M3B remains a separate serialized production effect.

### R10 bounded production canary outcome

A bounded single-identity M3B canary has now completed successfully.
job-01a13a88-189a-72a2-a82f-88a2bd6e4ecd temporarily stopped the
legacy physical WireGuard session, ran the exact pinned Gluetun candidate,
passed mechanism-neutral provider consequences, then restored legacy by
design. job-01a13a89-042b-7060-9bf1-7b85a0fc155c immediately verified
zero candidate residue, original namespace/config identity, fresh legacy
handshake, all 17 reverse-dependent services and Agent Automation
producers active, runtime Supply-Chain egress current, and legacy
provider/path/consequence PASS.

This closes the bounded M3B physical-session feasibility question. It
does not itself authorize permanent ownership transfer or legacy
retirement. Topic seq17038 found reusable-effect failure-path defects
after the successful run; the source now fails closed on ambiguous
candidate teardown, preserves protected recovery state on incomplete
rollback, positively reads back producers, rejects HTTP 5xx consequence
false positives, forces proxy use, and uses a reachable private leak
witness. The short canary watchdog remains process-signal scoped; M4
permanent ownership requires a lifecycle surface that can recover
independently of the initiating shell.
