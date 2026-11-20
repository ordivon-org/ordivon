# Gateway R7 — Direct Host consumer release falsifier

**Source status:** narrow source-only deployment qualification. This file is
not proof of installed Host authorization, Cloudflare routing, or successful
migration. The latest version is bound to its Git commit.

## R43: separate software upgrade from Host/Cloudflare migration

The original R7 Host-direct-consumer negative gate is necessary when a release
**changes the Host route, Owner identity, public ingress, authorization or
Cloudflare traffic migration**. It does not, by itself, establish that an
unchanged-route Gateway software patch must first remove existing Host clients.
Treating those different changes as one mandatory migration prevented ordinary
Gateway source fixes from reaching a currently functioning Agent.

The existing official installer now derives the **actual production change
class** from the exact immutable candidate, not from a user bypass flag:

- **A / same executable behavior and authority:** entire module/resource
  inventory, Python AST and stable Security/Owner/transport/SDK surface are
  unchanged. This directly closes the previous R46 public `work.get` ->
  actual `work.snapshot.commit` release false positive. No arbitrary
  SourceCut or current `execution/commands.py` SHA-pair waiver survives.
- **C / action-code change with unchanged authority:** source inventory
  remains identical; only the existing action/Host actual Owner/PEP
  continuation code may change. Immutable interpreter/dependency package,
  systemd/Ingress/Cloudflare/Host/Runtime Owner identity, Authorization
  Target construction and public MCP SDK tool ABI retain their existing
  checks. The candidate's own native code is exercised in **isolated fake
  Owner** canaries: verified public read remains read, real AuthZEN-shaped
  DENY/STEP_UP/UNKNOWN/forged-resource cannot forward, changed authorized
  `topicRef`/`authorActorRef` never reaches a Host writer, and an ambiguous
  Runtime execution effect is never blindly retried. No production Host
  write, live Runtime Job, private credential or Principal grant is used
  in these preflight probes. Existing production systemd PID/cwd, real
  candidate Host read and local/public anonymous denial gates still apply.
  Source-level plus protected CI is not a universal Python security proof.
  Unknown code-only changes are **NO_GO** with a separate exit status and
  must not be routed into unrelated B.
- **B / real Host/Cloudflare/Principal/Owner migration or unobservable
  authority:** preserve the original `check_live_host_admission.py`
  cutover obligations. Its known direct-Host consumers, peer identity and
  Security private-credential limits still mean NO_GO unless natural
  consumer witnesses exist. An empty socket list is never migration
  completion.

A passing source A classification is not a new Principal grant, a fully
certified loaded PDP policy, a checked post-restart process, or a successful
ChatGPT MCP connector refresh. Before promoting, independently confirm a
currently authenticated Agent read through the exact live ingress. After the
promotion and service restart, verify the installed process SourceCut,
authenticated Agent read/error recovery, anonymous DENY and unchanged natural
Owner route; on failure restore the prior immutable release and recheck.
The installer itself changes the symlink but does not restart the service.

Thought: positive business continuity plus reverse authorization-drift
counterexamples. Logic: ChangeClass / SourceEquivalence /
OwnerConsumerObservation / FailClosedRecovery. Capability: original systemd,
native MCP SDK, official release installer, Security AuthZEN and Host Owner,
bounded Python tests; no second policy engine or new release registry.

## R44: physically observed post-restart temporal counterexample (2026-11-20)

**Exact production release evidence:** GitHub #2504 was merged and the real
Gateway immutable SourceCut `1f3e9e31b6c399cc607a8957c2ef6bc116d79458`
passed both the original SDK 42-Tool ABI and same-route native checks. The
original installer switched the symlink without restarting the service, as
documented. The first Agent-authored restart wrapper immediately asserted
MainPID/cwd after `systemctl restart`, failed, and restored old SourceCut.
Native systemd journal recorded the first start and immediate rollback in
the same second. Old version physically recovered and the connected ChatGPT
Host Tools still worked. The unit was independently found to use
`Type=simple`: an accepted systemd start does **not** prove application
initialization or listener readiness. The exact failing immediate predicate
was not separately logged, so don't invent which assertion fired.

The second rollout used the same official installer and unchanged PEP/Host
routes, but after restarting it performed **bounded polling** for a distinct
MainPID, `/proc/<MainPID>/cwd` equal to the new immutable SourceCut, HTTP200
on `127.0.0.1:8899/health`, and anonymous MCP initialize HTTP403. It
succeeded: installed PID 1990757, Cloudflare public unauthenticated HTTP401;
the current ChatGPT connected `host.status` and `work.get` succeeded.
The previously generic `topic.resume` error now preserved
`CONFLICT/topic_resume_cursor_ahead` with the actual Host
`observedTopicHighSequence` and suggested recovery action.

To prevent repeat false rollback without adding another deployment service,
`packaging/check_running_release.py` is a **read-only** bounded physical
readiness observer. Invoke after the existing production restart, supplying
the intended exact Git SourceCut and the true old MainPID; it prints READY
only if current symlink, running native systemd PID, exact process cwd,
local HTTP health and local anonymous denial are all proven:

```sh
python3 services/gateway/packaging/check_running_release.py \
  --expected-sourcecut "${MERGED_FULL_GIT_SHA}" \
  --previous-pid "${OLD_REAL_MAINPID}" \
  --timeout-seconds 16
```

Its observable state is monotonic **only within the two sequential PID
checks and local canaries of that single read**; it cannot grant policy,
restart a process, prove Cloudflare ingress mapping, confirm external
ChatGPT tool-list refresh or replace real authenticated Agent acceptance.
A negative or unobservable result is `NO_GO`, not evidence that the old
SourceCut was already physically restored; a separate authorized rollback
and readback must close that effect. The code itself is source-only until
merged and present in the installed release or invoked from an exact
verified Git worktree.

Thought: SRE consumer acceptance, temporal falsification of systemd
`Started ⇒ Ready`, and delete duplicate release/PDP logic.
Logic: `PhysicalSource+PostStartPID+Health+AnonymousDeny ⇒ LocalReady`;
`LocalReady ⇏ AuthenticatedClientAccepted`.
Capability: existing native systemd, `/proc`, Python HTTP, original
`check_same_route_admission._local_anonymous_denied`, bounded pytest
negative cases, actual ChatGPT connected MCP calls. No new long-lived state.

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

## Real Host service bearer canary (2026-11-15)

A declared `ORDIVON_GATEWAY_HOST_BEARER_TOKEN_FILE` plus a real HTTP 401/403
for an anonymous Host request does not prove the same *installed* Gateway
bearer actually authenticates with Host. A stale or different token may
strand every Agent Work/Topic call after deployment.

The existing release preflight now separately proves a positive read-only
MCP `initialize` using the credential actually declared by the primary
Gateway: first establish Host anonymous denial; then resolve its systemd
`%d` credential path (or operator-owned absolute path) and use the existing
Gateway private file reader (bounded, no-follow, same-FD checks). Never
forward the credential to an arbitrary route or any Host that has not
denied anonymous initialization. Only the original fixed `127.0.0.1:8898/mcp` or the specifically
qualified protected `127.0.0.1:19008/mcp` workload can be probed. HTTP 200 must include matching JSON-RPC request ID, MCP protocol
version, capabilities and server metadata; redirect/401/403/invalid JSON
does not qualify. No token bytes enter logs, receipts or MCP Tool arguments.

This operates in the existing immutable Gateway production activation
preflight, not the `--prepare-only` stage. Existing test fixtures cover
positive/negative/mismatched/error/unsafe-path behavior and the actual
release entrypoint. The bounded `GatewayHostCutoverR1` TLA+ model adds
`hostBearerVerified` only *after* Host protection; Gateway promotion
requires it and a separate counterexample falsifies a premature publish.

This is **not** an operator Principal→Actor grant, active peer bearer
equality proof, service secret rotation guarantee, installed Security PDP
readback or Cloudflare/Agent business migration receipt. Keep those
existing natural-owner acceptance steps independent.


### Active peer Gateway is an independent bearer consumer

The main Gateway's valid Host MCP handshake is not transferable to
`ordivon-gateway-local-r21.service` or any other active peer. For each
systemd-discovered peer whose qualified configuration points at the same
Host Owner endpoint, the original release preflight now resolves that
**peer unit's own** `%d/host-mcp-bearer` path and demands its own positive
authenticated MCP initialize. No probe may send private credentials unless
the separate Host anonymous negative canary has already succeeded.
Missing, inaccessible, mismatched or rejected peer tokens keep the active
peer in `ACTIVE_HOST_CONSUMER_MISSING_OWNER_CREDENTIAL`. Peers explicitly
routed to a different Owner target remain out of this exact Host consumer
check; unobservable `EnvironmentFiles` remain unqualified.

This uses the same native bounded Owner private-file reader and HTTP
canary, not another credential store or scheduling authority. True
authorization and business continuity still require real authenticated
Agent read/write and reviewer acceptance after the release.

## R25 Reverse-liveness: qualify protected Host before retiring Legacy

The old `127.0.0.1:8898/mcp` still has direct consumer routes. Turning on
Bearer there before migrating the Host MCP Plugin and secondary Gateway
would break those clients. Parallel Change uses an expand step: allow
exactly `http://127.0.0.1:19008/mcp` as the protected loopback candidate,
without treating the original Legacy endpoint as already retired.

The existing preflight qualifies the second route only if
`ordivon-host-v2-protected.service` is active, has `DynamicUser=yes` and
`User=ordivon-host-v2-protected`, and owns the unique native `LISTEN`
socket at `127.0.0.1:19008` according to its actual systemd `MainPID`.
An arbitrary local HTTP server that merely replies 401 is not sufficient.
Unknown routes, a mismatched PID, wildcard bind addresses, ambiguous
listeners and systemd EnvironmentFile overrides remain unqualified.
Only after the observed Host denies anonymous MCP initialize may the
existing private Gateway Owner bearer reader and positive MCP canary run.
An active peer still pointing at Legacy while the primary uses the
protected Host remains an unqualified migration consumer.

R25 physically exercised the installed Host 0.9.0 binary in a transient
real systemd service with the existing PostgreSQL14 authority, a dynamic
service identity, systemd LoadCredential, read-only PGOPTIONS and the
prepared Gateway 0.10.15 native McpOwnerCaller. It read real Work and a
fixed MessageRef, then stopped the test unit and removed temporary
credentials. It did not install a permanent protected service or change
Cloudflare, Security grants, the production Host or the main Gateway.

**The production release gate is unchanged:** qualifying a candidate route
only establishes a necessary machine workload boundary. The original
preflight continues to return NO_GO/exit 3 until trusted independently
verifiable Principal, Security, Cloudflare, direct-client and rollback
evidence has an effective pre-promotion consumer. An empty legacy TCP
socket sample does not demonstrate actual direct Host client migration.
