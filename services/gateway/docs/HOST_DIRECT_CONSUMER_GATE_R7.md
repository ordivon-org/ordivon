# Gateway R7 — Direct Host consumer release falsifier

**Source status:** narrow source-only deployment qualification. This file is
not proof of installed Host authorization, Cloudflare routing, or successful
migration. The latest version is bound to its Git commit.

## Real consumer observation behind the change

On 2026-11-14, a native Runtime Job inspected the **currently installed**
Host listener `127.0.0.1:8898` with Linux `ss -tnp` and saw two
simultaneous established local TCP consumers:

- `ordivon-gateway` (the expected installed Gateway→Host Owner upstream).
- `cloudflared`, whose process belonged to the already running
  `ordivon-cloudflare-production-b.service` systemd cgroup.

Another running Cloudflare production A tunnel was independently observed.
The `cloudflared` socket subsequently disappeared on one later snapshot.
That is **not** evidence the remote Cloudflare ingress no longer routes to
Host, nor that a human Agent successfully migrated. A loopback socket alone
also does not prove Internet/public unauthenticated Host access; Cloudflare
Access and other outer policy must be evaluated separately.

The source owner remains Host for Work/Social/Attention and Security for
Principal→Actor grants. Gateway remains a non-authoritative adapter. In
particular, replacing Host with a bearer-protected service without qualifying
direct consumers can break otherwise legitimate Agent tools.

## One-way addition to the existing native release checker

Existing `services/gateway/packaging/check_live_host_admission.py` now
uses original Linux `systemctl` and `ss` as a **positive falsifier**:

1. Read the actual running Gateway systemd MainPID; never infer its identity
   by binary name alone because another local Gateway instance may exist.
2. Inspect only established local TCP sockets addressed to the already
   configured Host `127.0.0.1:8898`.
3. Ignore the socket bound solely to the *exact* Gateway MainPID.
4. If any connection belongs to `cloudflared`, another PID, or has
   unattributed process identity, emit a bounded category without exposing
   process identity, request metadata, credentials, or user principal.
5. A non-empty observation produces
   `HOST_DIRECT_NON_GATEWAY_TCP_CONSUMER_OBSERVED` and a conservative
   `NO_GO`. Missing systemd/ss proof fails the existing native preflight
   closed; missing sockets never establish migration.
6. If the probe sees no external connection, status may still be only
   `NECESSARY_PRECONDITIONS_PRESENT`. The checker continues to list
   Cloudflare remote ingress and actual direct Host MCP connector migration
   as **unverified**. Neither CI nor an empty TCP snapshot upgrades it to
   `MIGRATED`.

## Required P0 Agent consumer acceptance before any production promote

- Natural Network owner identifies current Cloudflare A/B remote ingress
  mapping to Host and reports any other non-Gateway Host consumers.
- Genuine Security owner sources and loads authorized Principal→Actor
  grants. Caller-supplied ActorRef or an M2M bearer does not invent these.
- Pair real Host and Gateway Owner bearer credentials with the existing
  systemd credential facilities; prove Host anonymous native MCP initialization
  is 401/403 **and** legitimate Owner bearer allows the intended Host method.
- Migrate or otherwise explicitly qualify the original direct Host clients
  with real Agent MCP reconnect, Work read, Topic resume, Message continuation,
  Attention read/ack and read/write ALLOW/DENY canaries, including failure
  recovery. The direct ingress mapping and its outer Cloudflare Access policy
  must be independently checked against loaded state.
- Only then invoke the existing Gateway/Host official immutable release paths
  and verify exact SourceCut, Tool surface, authorization, consumer evidence.
  Retain production source and service continuity until true post-promotion
  evidence is observed.

## LEGO / bounded evidence contract

- Thought LEGO: Assume–Guarantee, representation-first, fail-closed
  authorization, independent falsification, consumer-first SRE.
- Logic LEGO: `Native Endpoint+Gateway PID → Established TCP Client
  Projection → Positive Counterexample or UNKNOWN`.
- Ability LEGO: reuse systemd, iproute2 `ss`, existing official Gateway
  release preflight and pytest; no new policy engine, traffic proxy, Job,
  state database, or Cloudflare control plane.
- Refined contract: `ObservedNonGatewayEstablished ⇒ NO_GO`.
  **Non-implication:** `NotObserved ⇏ MigrationComplete`.
  The OS/runtime observation and external Cloudflare route are not subsumed
  by a TLA abstract model; retain native TCP and MCP canaries.

The regression tests in
`services/gateway/tests/test_live_host_release_preflight.py` specifically
cover established Host and non-Host sockets, exact PID separation,
unattributed sockets, Cloudflare direct-client blocking, missing process
information, and the non-implication from empty observations.

## R8 native MCP consumer-surface qualification (2026-11-15)

The original ChatGPT connector boundaries are explicitly documented in
`docs/architecture/AGENT_PLUGIN_BOUNDARY_R2.md`: `ordivon-host` uses
`https://host-mcp.ordivon.com/mcp`. The separately connected
`ordivon-gateway` uses `https://gateway-mcp.ordivon.com/mcp`.
The connector endpoint, Tool set, and credential/Principal identity must
be qualified separately; changing a Cloudflare origin does **not**
automatically migrate a ChatGPT Plugin.

On Git main `682e4c00dad0f9a28792049a415bb236fb0135e3`,
the **actual in-process official MCP SDK** source `tools/list` reported:

- Original Host: 31 Tools; candidate Gateway: 41 Tools; shared: 30.
- Host-only: `host.pool.stats` (operator-local diagnostic, intentionally
  not a normal Agent Gateway Tool). Gateway has 11 other tools unrelated
  to direct Host conversion.
- For all 30 shared Tools the input property *names* and *required-property*
  sets match. However, 16 input schemas differ (mostly bounded `maxBytes`,
  WorkSnapshot typing and Work revision/limit constraints), and 30 output
  schemas differ: Host publishes natural typed Pydantic response schemas
  while Gateway currently advertises a broad output object.
- This is *not* 46 independently demonstrated consumer failures. Schema
  shape mismatch is a concrete **qualification obligation** for generated
  typed clients; forwarded native Host bytes remain Host-owned.

The source-only, reproducible mature SDK audit is:

```sh
python3 tools/repo/check_host_gateway_mcp_consumer_surface.py
```

It reads the two original service `build_server` Tool contracts in
their locked `uv` environments, without a second Tool registry or a
PG/HTTP Owner effect. Its pure finite consumers live in
`services/gateway/tests/test_host_gateway_source_consumer_r8.py`.
The report always preserves
`migrationStanding=UNKNOWN_REQUIRES_INSTALLED_AUTH_AND_CONSUMER_CANARIES`;
source input parameter parity is **not** authorization, typed-output
compatibility, Plugin installation or runtime DomainSuccess.

An installed, non-mutating cross-connector Agent readback on the same
real Work and Topic matched revision=6 and snapshotDigest for
`work:ordivon:host-agent-continuation-golden-road-r1:20261114`,
five exact Topic MessageRefs/sequences/digests through sequence 27778,
and the same empty Attention view (snapshotHighSequence=77808).
This confirms **those read-only consumers only**, not general
cross-Principal write or Ack permission.

Cloudflare outer Host endpoint without credentials returned HTTP401,
while the current *loopback* Host HTTP MCP initialize earlier returned
HTTP200. Those are different trust boundaries: neither proves remote
Host plugin migration. An 80-sample native TCP observation coinciding
with six successful Host plugin `host.status` calls saw no
`cloudflared`→Host socket (Gateway→Host was seen), but a separate
earlier physical observation had seen one. Absence in a bounded sample
is not Cloudflare ingress-route removal evidence.

**Installation contract:** Before changing the natural Host Plugin
endpoint or promoting the bearer-protected Host/Gateway, independently
qualify Cloudflare current ingress, real authorized Principal→Actor
Security grants, exact service Bearer, all current connected Agent Tool
surface/typed-output consumers, reconnect and live allowed/denied
Work/Topic/Message/Attention operations. Do not graft original Host
output schemas into Gateway as a hand-maintained second type registry,
or add an operator-only Tool merely to make tool counts equal.

## R9 Host business-tool closure proof (2026-11-15)

The R8 native SDK report proved only *shared* Host/Gateway input-property
and required-set parity. That property alone was insufficient as a migration
gate: if an original Host adds `message.new` and Gateway has no matching
Tool, the remaining shared Tools could still all match and the old report
would exit successfully. R9 adds a separately named **source Host business
surface coverage** predicate, not an invented installed/authorization claim.

The checker uses the original Host and Gateway `tools/list` to compute
the set inclusion of all Host tools except the **one original documented
operator-only Host diagnostic**, `host.pool.stats`. It rejects any new
unrepresented Host business tool and also rejects an unexpected exposure of
`host.pool.stats` in Gateway. The exception is **not** a copied inventory
of Host business tools, and cannot silently hide future Host operations.

```text
HostBusiness = HostNativeTools − {host.pool.stats}
SourceHostBusinessCovered =
    SharedTools≠∅ ∧ HostBusiness ⊆ GatewayNativeTools
    ∧ host.pool.stats ∉ GatewayNativeTools
SourceConsumerSurfaceQualified =
    SourceHostBusinessCovered ∧ SameInputNamesAndRequiredSetsForSharedTools
SourceConsumerSurfaceQualified ⇏ ExactInputSchemaEquivalent
SourceConsumerSurfaceQualified ⇏ ExactOutputSchemaEquivalent
SourceConsumerSurfaceQualified ⇏ InstalledConsumerMigrated
```

The finite adversarial conformance in
`tests/test_host_gateway_source_consumer_r9.py` explores all **64 pairs**
of subsets of three representative Host business Tools, alongside a
known operator-only diagnostic, missing-tool regression, operator
diagnostic leakage, divergent required fields, CLI failure exit and
unobservable native source. It does **not** universally prove the
official MCP SDK or installed Cloudflare route. An unavailable native
Owner SDK environment emits `null`/UNKNOWN rather than false.
No new Tool registry, database, PEP, scheduler or service is created.


## Systemd EnvironmentFile consumer falsifier (2026-11-15)

The original live Gateway release checker inspected only `systemctl show -p
Environment` for the primary and active peer Gateway units. This property is
not the effective environment when systemd loads an `EnvironmentFile`, which
can override the Host Owner URL or its bearer path. An active peer with only a
file-sourced Host route could be silently excluded from the consumer census;
a primary Gateway could be falsely declared to use the negatively probed
`127.0.0.1:8898` endpoint.

The source now reuses one bounded native systemd read helper for *both*
primary and peer Gateway units, querying `Environment` and
`EnvironmentFiles`. An attached EnvironmentFile means the effective route
cannot be established from that read-only metadata alone: primary admission
returns `NO_GO/HOST_SECURITY_PRECONDITIONS_UNOBSERVABLE`, and an active
peer remains an unqualified potential Host consumer. This is intentionally
a **necessary-condition falsifier**, not a new policy engine, credential
reader, assertion of caller identity or claim that actual migration failed.
It never reads or logs the contents of an environment file.

Original `test_live_host_release_preflight.py` consumer tests now exercise
empty/overriding EnvironmentFiles, an unrelated-looking service URL that can
be overridden, a qualified peer with no file, and main-Gateway admission
fail-closed. The owner-native full gateway pytest and Ruff checks apply to
the exact source revision; live installed Gateway 0.10.8 remains a separate
Cut and must not be claimed to consume this source change until published.
