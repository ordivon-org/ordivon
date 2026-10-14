# M3B Gluetun serialized canary: effect and restoration contract

Status: **HOLD — source-only execution design, not a permit or executable runbook**.
Work: `work:network:upstream-first-convergence-r1:20261011`.
This file does not start, stop, install or authorize any service. It defines
what an independently reviewed effect implementation and operator admission
MUST prove. Follow Human ADOPTED Flow Governance R1.

## One physical session, two modes

| Phase | Legacy WireGuard in nv2-browserless-prod | Gluetun container |
| --- | --- | --- |
| Before canary | RUNNING | ABSENT |
| After legacy shutdown | STOPPED and peer absent | ABSENT |
| Canary testing | STOPPED and peer absent | ONE pinned candidate only |
| After candidate shutdown | STOPPED and peer absent | ABSENT |
| After restore | RUNNING and qualified | ABSENT |

Never run legacy and Gluetun simultaneously with
`surfshark:linux-shared-r1`. No shadow VPN connection. Stop legacy *before*
mounting its read-only INI in a candidate process. If any physical session
state is ambiguous, HALT and restore, never retry candidate automatically.

## Admission and preimage (all required, otherwise HOLD)

1. Independently approve a fixed source HEAD, immutable image digest, Quadlet
   port map/firewall contract, protected profile compatibility and an exact
   bounded effect script. An isolated proxy fixture is not this approval.
2. Obtain **separate explicit risk-tiered production effect authorization**:
   exact host, single ClientIdentity, maintenance window, max duration, active
   consumer set, rollback authority/owner and source revision. A prior owner
   handoff does not grant this authorization.
3. Fresh-read Host Work, Topic and Runtime source, WSL/kernel revision,
   `ip netns` identity, provider service state, endpoint and open sockets.
   Verify intended active registry remains legacy and candidate non-authoritative.
4. Prove workflow drain using authoritative *current* Temporal/Browserless
   ownership; the old switch checks running `ordivon-agent-automation`
   workflows, but does **not** establish quiescence for Finance, Model
   Provider, Chrome, Claude, Discord, X or ad-hoc consumers. Each active
   consumer owner must opt into disruption or show quiescence. An
   unobservable consumer is **UNKNOWN/HOLD**, not idle. Prevent new work
   during the bounded window. If the workflow census is paginated, exhaust
   it before claiming drain.
5. Capture preimage in a protected, operator-only storage path outside Git,
   Host messages and the candidate container: exact profile and environment
   file copies, permissions/ownership, SHA-256 digests, systemd loaded-unit
   identities and dependency graph, active service states, WG interface/
   endpoint, current namespace inode, host-veth CIDR/routes and
   iptables-legacy/nft view. Evidence sent to Host contains only digests/
   artifact references, never secret or private key bytes. Verify copies
   are readable and restoration commands can access them.
6. Prove absence of port conflict with live `ss`, recognizing this is not a
   port reservation. Recheck at effect time. Verify container image is
   present by the pinned amd64 manifest digest; `Pull=never` must not fall
   back to a mutable tag. Confirm `10.252.246.1` belongs to existing
   host-veth and that Podman's `bridge` network does not overlap current
   Network-v2 routes. No re-use of the predecessor WIP's
   `10.252.246.0/30` bridge or `nv2-browserless-prod` alias.
7. Before *any* stop effect, install and dry-run the unconditional rollback
   action and fault/timeout handlers. Prove service stop/start topology is
   safe under systemd `PartOf` / `Requires` ordering. No automatic
   provider-reconnect job may defeat the serialized-session fence.

## Serialized effect sequence (not executed by this source contract)

1. Enter externally enforced consumer drain; retain the existing namespace
   and host-veth. Record the exact current service/namespace preimage.
2. Stop the legacy **provider HTTP carrier**, legacy provider DNS and legacy
   WireGuard **in safe dependency order**. Verify the legacy WG interface/
   physical session is absent and its systemd unit is inactive. On uncertain
   teardown, **do not start Gluetun**.
3. Start exactly one pinned Gluetun candidate with read-only protected INI
   and an isolated Podman-owned container namespace. Its candidate proxy
   `:8888` must publish to **host-veth only**
   `10.252.246.1:19682`; its container INPUT firewall must admit port
   `8888`, without disabling the Gluetun firewall. Never materialize
   actual private key data in a source env file or Host evidence.
4. In retained `nv2-browserless-prod`, run the scoped sing-box adapter on
   its original consumer seam `10.252.246.2:19680`, but forward to
   `10.252.246.1:19682`. No direct outbound. Actual container/published
   port/listener/route/firewall state must be independently observed.
5. During the admitted time bound, prove a real **Gluetun-backed** CONNECT
   flow and permitted destination effects, plus explicitly rejected
   private/IPv6/unknown destinations and **no direct fallback**. Verify
   source-vs-runtime IP/namespace/digest/one-session state throughout.
   Only scoped consumer owners may declare their **consequence** READY.
6. Regardless of candidate success or failure, stop sing-box candidate
   adapter, tear down Gluetun and prove no candidate WireGuard session is
   left. Reinstall original protected files byte-for-byte if modified and
   restore exact ownership/modes. Restore legacy WG, DNS and provider
   carrier/target respecting systemd order.
7. Confirm retained namespace inode, preimage hashes, legacy site and
   endpoint, legacy `provider-carrier-ready.sh` AND legacy Browserless
   `production-path.sh` success. Rerun affected Finance, Supply-Chain,
   Models, Chrome and other scoped consumer owner readiness after restore.
   Release drain only after recovery is proven and documented.
8. If any restoration stage fails: **BLOCKED_ROLLBACK**, isolate candidate,
   do not re-enable consumer work or start automatic retries; escalate to
   human-controlled recovery. A green provider health probe is insufficient.

## Differential probes: ownership and no false readiness

Candidate phase cannot use the unchanged legacy-only checks as a Gluetun
acceptance oracle:

- `consumers/browserless/provider-carrier-ready.sh`: requires legacy
  WireGuard unit/DNS and hardcodes the current provider/site endpoint.
- `consumers/browserless/acceptance/production-path.sh`: requires legacy
  WG link and latest-handshakes plus legacy service states.
- `consumers/windows-real-chrome/ready.sh`: calls the legacy provider-ready
  command transitively.

These are mandatory **restoration** checks, not candidate checks. Candidate
phase needs an independently reviewed mechanism-neutral HTTP proxy / DNS /
transport / fail-closed consequence adapter, with explicit consumer owner
evidence. The already existing scoped
`consumers/finance/ready.sh`, `consumers/supply-chain/ready.sh`,
`consumers/model-provider/ready.sh` may provide partial consumer proof,
but require dependency/currentness review before admission; they are
not inferred ready from Gluetun health.

## Fault matrix and acceptance result

| Fault injected in reviewed, isolated test or admitted bounded canary | Required outcome |
| --- | --- |
| Missing image or wrong digest | Fail before legacy stop |
| Running/unknown consumer workflow | Fail before legacy stop |
| Port occupied (exact/IPv4 wildcard/IPv6 wildcard) | Fail before legacy stop |
| Legacy WG fails to stop cleanly | Candidate never starts |
| Gluetun proxy not published or firewall blocked | Candidate FAIL; unconditional restore |
| Candidate DNS/CONNECT returns forbidden direct/unknown path | Candidate FAIL; unconditional restore |
| Gluetun process exits mid-test | Candidate FAIL; unconditional restore |
| SIGINT/SIGTERM or timeout after legacy stop | Candidate teardown then legacy restore |
| Rollback re-start/legacy consequence fails | BLOCKED_ROLLBACK, escalate |
| Consumer owner evidence missing or stale | No parity claim; HOLD |

Do not label a proxy-fixture pass, HTTP 401/403 reachability, source
qualification or Quadlet generator success as authenticated workload
completion. Evidence must distinguish
`PROXY_FIXTURE_PASS`, `SOURCE_CONFIG_PASS`,
`CANDIDATE_CONSEQUENCE_PASS`, `RESTORATION_PASS` and
`ROLLBACK_FAILED` without silently promoting between categories.

**Retirement gate:** the original `wg-quick`, provider-switch scripts,
legacy namespace and DNS pieces remain until Gluetun has qualified
consequence parity, an independent review, and a separately accepted
longitudinal production ownership transition. Source-only R1 jq intentionally
keeps legacy active; it cannot be switched by simply changing one JSON field.

## R3 network isolation and admission delta

The candidate cannot join the shared Podman default bridge.
The only source-selected candidate network is
network-v2-gluetun-private-r1, Options=isolate=strict, with subnet
10.253.239.0/30, gateway 10.253.239.1, and candidate IP
10.253.239.2. Before actual candidate start, inspect the actual
network name, options, route, subnet, gateway and members; a stale
same-name network must FAIL CLOSED rather than be silently reused
by Podman network create --ignore. Verify no unapproved members,
and recheck at effect time. Source generator PASS does not qualify
this runtime identity/membership proof.

Peer-denial evidence exists only in a disposable nonproduction
namespace. Real pinned Gluetun image is not cached/qualified;
an explicit host-veth port-publish experiment was blocked by Runtime
safety admission and must not be bypassed. M3B remains HOLD.

## R3 fixture-qualified candidate-neutral consumer policies

The test-only acceptance script
consumers/acceptance/candidate-neutral-route-fixture.py operates entirely
under temporary loopback sing-box configs with a local HTTP CONNECT witness.
It executes the EXISTING source policies of Model Provider, Supply Chain
and X Reality, changing only source frontend/backhaul listener endpoints
in transient files. For each allowed domain it verifies one upstream
CONNECT; for an unknown destination it verifies no new upstream CONNECT.
It does NOT read /etc/network-v2, open any actual provider session or
declare production-ready consumers. The fixture sends a plain HTTP GET
through an upstream CONNECT for route verification; no actual TLS,
provider authentication, Gluetun/VPN or live API behavior is asserted.

The other owners (Browserless, Windows Chrome, Finance and other users)
still require candidate-neutral readiness tests and authoritative drain
currentness. In particular the existing legacy WG-bound ready.sh and
production-path.sh are RESTORATION oracles only. This test is not evidence
that a consumer has finished work, that a VPN has egress, or that rollback
was fault-tested.

## R4 Supply-Chain source-vs-deployment prerequisite

OCI artifact admission requires exact Docker blob CDN domain
authorization AND observed installed Supply-Chain config currentness.
Source now authorizes production.cloudfront.docker.com; deployed
Supply-Chain configuration still omitted it at R4 readback. The
pre-existing task consumer:supply-chain:verify is the source/deployed
equality gate, currently failing. No source-only fixture can promote
this missing live config. Avoid broad convergence affecting Docker or
Browserless as an accidental side effect.

Complete separately reviewed minimum-scope service config
reconciliation, prove live redirect and pinned image digest bytes
through approved scoped egress, and only then revisit sandbox Gluetun
runtime. This is NOT production canary effect authorization.

## R5 live-source drift / drain non-admission fence

The narrow read-only CDN preflight detects a second live mismatch:
deployed Supply-Chain authority networkAuthority.name=browserless-prod
versus canonical source provider-egress. It emits
HOLD_LEGACY_AUTHORITY_ALIAS instead of allowing an undocumented
semantic authority migration bundled with the CDN host change.
Do not replace both installed config files or restart any service as
a purported source-only policy edit; the owner must obtain an
independent migration decision and separately admitted scoped effect.
The R5 synthetic file rollback rehearsal restored sandbox bytes/modes
after injected faults but did not call systemd, exercise a Gluetun
session or prove consumer readiness.

Live R5 read-only target census showed six active consumer targets
and a zero count only for the specifically queried Temporal automation
TaskQueue. A zero for that one query is not an authoritative drain,
nor a fence against future workflow launch. No M3B canary may proceed
without owner-by-owner currentness/maintenance participation and a
positive mechanism preventing newly admitted work while the shared
physical provider identity is unavailable.

## R6 stronger nonproduction restoration and source integrity (not admission)

The R4 exact Docker CDN source policy is pinned by SHA256 in
consumers/supply-chain/acceptance/cdn-preflight.py. If ANY other
Supply-Chain source authorization changes, the R4 one-host update
preflight now fails until separately re-reviewed/re-pinned.

The test-only cdn-singbox-service-rehearsal.py runs real ephemeral
loopback sing-box proxy processes with local HTTP CONNECT witness and
faults at before-stop, after-stop and after-new-run boundaries. It
must restore byte-exact temporary config and old proxy consequences
after each. No production services or provider identities are used.
An actual production rollback still needs a separately admitted
live service effect implementation and fault-recovery acceptance.
A cross-consumer Temporal census that was blocked by environment
policy is not evidence of zero global workflows or work admission
fencing. M3B HOLD unchanged.

## R7 critical-path evidence now closed before M3B

The exact Docker CDN runtime route is installed in the live Supply-Chain
sing-box egress while `authority.json` retains its older semantic alias.
`cdn-preflight.py` now separates those layers and reports the runtime
egress CURRENT rather than falsely blocking on metadata drift.

The exact pinned Gluetun amd64 OCI manifest is now present locally.
`local-wireguard-real-sandbox.sh` runs the real image with no Surfshark
credential, a disposable local WireGuard peer, private Podman /30,
firewall and HTTP proxy. It proves tunnel traffic, default/same-network
peer exclusion, fail-closed peer loss, restart recovery and the
Browserless candidate sing-box -> Gluetun -> WireGuard two-hop. It also
has explicit TERM cleanup and leaves no named sandbox resources.

The previous R6 planned-checkpoint process rehearsal is also hardened:
candidate startup failure and candidate SIGKILL enter the same
unconditional temporary-preimage restoration path before old-policy
consequence is rechecked.

What remains specific to M3B is therefore narrower: production
10.252.246.1:19682 publication, authoritative all-consumer drain/no-new-
work fence, exact systemd/provider preimage and rollback, and the single
shared Surfshark identity stop -> candidate -> unconditional legacy
restore. Do not repeat source/CDN/image/local-Gluetun qualification as
new gates unless their bytes change.

## R7 critical-path evidence now closed before M3B

The exact Docker CDN runtime route is installed in the live Supply-Chain
sing-box egress while authority.json retains its older semantic alias.
cdn-preflight.py now separates those layers and reports runtime egress
CURRENT rather than falsely blocking on metadata drift.

The exact pinned Gluetun amd64 OCI manifest is now present locally.
local-wireguard-real-sandbox.sh runs the real image with no Surfshark
credential, a disposable local WireGuard peer, private Podman /30,
firewall and HTTP proxy. It proves tunnel traffic, default/same-network
peer exclusion, fail-closed peer loss, restart recovery and the
Browserless candidate sing-box -> Gluetun -> WireGuard two-hop. It also
has explicit TERM cleanup and leaves no named sandbox resources.

The previous R6 planned-checkpoint process rehearsal is hardened:
candidate startup failure and candidate SIGKILL enter the same
unconditional temporary-preimage restoration path before old-policy
consequence is rechecked.

What remains specific to M3B is therefore narrower: production
10.252.246.1:19682 publication, authoritative all-consumer drain/no-new-
work fence, exact systemd/provider preimage and rollback, and the single
shared Surfshark identity stop -> candidate -> unconditional legacy
restore. Do not repeat source/CDN/image/local-Gluetun qualification as
new gates unless their bytes change.

## R8 exact bounded effect executable

R8 adds acceptance/m3b-serialized-canary.sh. Its default mode is read-only
preflight. The effect mode is deliberately one bounded transaction:
it records exact source HEAD and script/config hashes, requires a clean Git
workspace, exact pinned image, live namespace/host-veth identity, zero current
Agent Automation workflows, zero established provider-carrier flows and no
candidate network/container/port conflict.

At effect entry it stops the Agent Automation MCP/Temporal worker and every
currently active systemd service in the reverse dependency graph of the shared
provider carrier. This creates a network-level blackout for canonical
provider-dependent consumers instead of relying on per-owner idle assertions.
It then stops carrier -> DNS -> legacy WG, proves the old WG interface absent,
starts exactly one pinned Gluetun candidate, starts the mechanism-neutral
candidate adapter on the unchanged 10.252.246.2:19680 seam, and runs the
cross-provider consequence probe.

The same shell owns an internal 150-second watchdog. EXIT, ERR, INT and TERM
all enter one restore function: candidate adapter/container/network teardown,
protected profile/env preimage restoration if bytes changed, legacy
WG -> DNS -> carrier/target restore, prior active dependent services restore,
legacy provider/path acceptance, mechanism-neutral consequence acceptance, and
finally the previously active worker/MCP restore. Candidate success still
returns to legacy; it never transfers permanent ownership.

The executable does not remove the need for one independent integrated review
of its exact fixed HEAD before the first production run. It replaces the
previous prose-only effect sequence; unchanged source/CDN/image/local-sandbox
facts should not be re-gated.
