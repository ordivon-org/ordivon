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
