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
