# Ordivon Composition Architecture — Executable LEGO Plan R1

Date: 2026-09-21  
Historical standing: EXECUTED / SUPERSEDED FOR CURRENT STATE by `CURRENT_ARCHITECTURE.md`

> This is the frozen execution plan used to reach the current architecture. Present-tense observations below are historical inputs from its baseline and MUST NOT be interpreted as current deployment status.

Baseline: `/root/projects/ordivon@a77690a72efaeb12323d01b35131e0da861e2adf`  
Workspace: `ws-composition-architecture-lego-plan-r1-20260921`

## Goal

Converge Ordivon to one default public Agent ingress — Gateway MCP — while keeping Runtime, Host, Harness, Platform, Capability, Domain, App, Study, Skills, and external providers as independent natural authorities.

This is a composition programme, not a new control plane.

## Atomicity rule

Every executable module below must have one primary responsibility, one primary authority/effect boundary, explicit inputs/outputs, an independently reviewable diff, and observable acceptance. If implementation discovers a second materially different authority, split the task before continuing.

## Frozen composition laws

1. One default public Agent ingress: Gateway MCP.
2. One truth owner per claim.
3. Gateway is a rebuildable projection/router, never semantic truth.
4. MCP is a protocol, not an Ordivon ontology.
5. Agent Plugin packages; it never becomes semantic owner.
6. Skill teaches HOW; it never grants execution/permission authority.
7. Domain owns semantic success.
8. Capability owns reusable ability, not domain verdict.
9. Platform owns substrate, not workload meaning.
10. App owns use-case/experience composition, not lower-owner truth.
11. Prefer mature external natural owners.
12. Every cross-owner edge is explicit.

## Current corrections from live inspection

- `method-router` is **not missing** from the Skills system. Unscoped search hides project Skills by design; scoped `workspaceId=ordivon-next` correctly returns `project-ordivon-next/method-router`. Therefore there is no “repair Method Router discovery” task.
- Gateway is already stateless northbound and uses `mcp==2.2.0`, but `upstream.py` still constructs legacy `ClientSession` and calls `initialize()`; this is real migration work.
- Runtime already advertises MCP 2026-07-28 discovery, but Gateway currently disables Runtime result validation through `_RuntimeCompatibilitySession`; removing that shim requires a Runtime+Gateway seam fix, not a Gateway-only workaround.
- The Cloudflare fixed-root controller already knows how to census/create the Windows Service Auth policy and materialize node-local credentials after an exact reviewed plan.
- The default Agent Plugin still points directly at Runtime and Host and must not switch until Gateway C02 live acceptance is complete.
- Root affected-owner mechanics still omit Gateway, Web, and Preservation as explicit owners.

## Dependency graph

```text
C00 ─┬─> C01 -> C02 --------------------------┐
     ├─> G01 -> G02 ─┐                        │
     ├─> G03 --------┼-> G04/G05 -> E01 -> E02 -> E03 -> E04 -> E05
     ├─> S01 --------┘                                      │
     └─> M01 -----------------------------------------------┤
                                                            v
                                                     P01 -> P02 -> P03 -> P04
                                                            │
                                                            v
                                                     S02 -> S03
                                                            │
                                                     B01 after C02/M01/P01

O01/O02/O03/O04 are on-demand only after E05.
```

## W0 — Freeze the composition contract

### C00 — Composition contract
**Owner:** root architecture  
**Produces:** canonical taxonomy + authority matrix + 12 laws.  
**Acceptance:** no universal Task/State/Registry/Workflow; Gateway explicitly non-authoritative.  
**Commit class:** docs-only architecture contract.

### C01 — Machine-readable LEGO graph
**Owner:** root architecture  
**Consumes:** C00.  
**Produces:** `docs/architecture/ordivon-composition-architecture-lego-r1.json`.  
**Acceptance:** every node has authority boundary, files, dependencies, and acceptance; every dependency resolves to a known node.

### C02 — Contract validator
**Owner:** repo mechanics  
**Files:** `tools/repo/check_composition_architecture.py`, test, root `mise.toml`.  
**Test cycle:** write failing graph-validation cases → implement smallest validator → `mise run repo:ci`.  
**Acceptance:** duplicate ids, unknown dependencies, and forbidden Gateway truth claims fail closed.

## W1 — Gateway protocol seam

### G01 — MCP v2 owner client
**Owner:** Gateway.  
**Files:** `services/gateway/src/ordivon_gateway/upstream.py` + Gateway tests.  
**Change:** use first-class `mcp.Client` for owner connections instead of direct `ClientSession(...); initialize(); call_tool()`.  
**Acceptance:** modern discovery and call path exercised; `mise run gateway:verify`.

### G02 — Identity preservation
**Owner:** Gateway.  
**Depends:** G01.  
**Change:** preserve Bearer-file and Cloudflare service-token header modes through the new client path.  
**Acceptance:** secrets remain file-backed; Bearer and service identity remain mutually exclusive; auth errors fail closed.

### G03 — Runtime output-schema conformance
**Owner:** Runtime, with Gateway consumer verification.  
**Files:** Runtime MCP tool/schema tests and Gateway upstream adapter.  
**Change:** make Runtime tool listing/results accepted by normal Python MCP validation. Delete `_RuntimeCompatibilitySession`.  
**Acceptance:** `mise run runtime:verify` + `mise run gateway:verify`; no validation bypass.

### G04 — Route table, not registry
**Owner:** Gateway.  
**Change:** rename/constrain `registry.py` into an explicitly static route declaration surface.  
**Acceptance:** static route chooses only the natural owner; availability remains owner-derived; no mutable registry.

### G05 — Canonical northbound surface
**Owner:** Gateway.  
**Change:** census consumers of `system.describe`, `capability.list`, `capability.describe`; remove semantic duplicates or retain one explicitly temporary compatibility alias.  
**Acceptance:** exactly one canonical Ordivon capability-description path.

## W2 — Public Gateway C02

### E01 — Exact Cloudflare plan
Run the existing fixed-root controller's plan operation.  
**Gate:** `eligible_for_apply=true`; no delete/replace; no unexpected mutation; OAuth/DCR and Windows Service Auth census pass.

### E02 — Reviewed external effect
Apply only the exact reviewed plan digest. The controller then converges the Windows Runtime Service Auth policy and materializes `/etc/ordivon/gateway/windows-access-client-{id,secret}`.  
**Gate:** zero drift; exactly one compatible policy; credentials root:root 0600; no secret in Git/receipts.

### E03 — Gateway deployment binding
Install the public Access and Windows service-identity drop-ins.  
**Gate:** origin remains loopback; Access JWT verification enabled; health green; Windows owner configured.

### E04 — Public live E2E
Prove through `gateway-mcp.ordivon.com`:
1. unauthenticated MCP stops at Cloudflare Access;
2. authenticated discovery succeeds;
3. Linux execution submit/get round trip succeeds;
4. Host continuity read succeeds;
5. Windows capability is configured and a bounded native Windows call succeeds.

### E05 — C02 acceptance
Freeze evidence, rollback coordinates, public hostname, exact Gateway release, owner identities, and non-claims. This is the gate that authorizes Plugin cutover.

## W3 — Single-Gateway Agent Plugin

### P01 — One MCP server in the portable package
Change `meta/next/plugins/ordivon-control-plane/mcp.json` from Runtime+Host endpoints to exactly one Gateway endpoint. Keep credentials out of the package.

### P02 — Materializer/conformance
Keep all three supported release modes:
- MCP-only;
- selected canonical Skill(s);
- explicit all-Skills compatibility.
Every mode must retain one Gateway MCP server. Selected Skills remain copied only from canonical `.agents/skills`.

### P03 — Real consumer E2E
Install/enable the Plugin in the target client, complete OAuth, call one Gateway capability, and separately prove selected Skill activation when using a Skill-bearing release.

### P04 — Direct public owner retirement
Only after P03, census all Runtime/Host public consumers. Remove default public exposure only where no consumer remains. Keep direct internal/operator recovery surfaces.

## W4 — Skill lifecycle convergence

### S01 — Freeze scope semantics
Add regression coverage proving:
- unscoped project Skill visibility is false;
- scoped `ordivon-next` visibility includes Method Router;
- snapshot/trust fences remain exact.

### S02 — Three consumption modes
Run and record:
1. native `.agents/skills` consumption;
2. selected Skill bundled into Plugin;
3. remote Skills MCP bridge for clients that genuinely cannot consume native assets.

### S03 — Per-consumer bridge retirement
Every retained Skills MCP consumer must name the exact client gap. No registry/marketplace/workflow semantics may be added to justify keeping the bridge.

## W5 — Monorepo mechanics and boundary enforcement

### M01 — Explicit owner graph completeness
Register `services/gateway`, `apps/web`, and `capabilities/preservation` in:
- root `mise.toml`;
- `.github/CODEOWNERS`;
- `.github/workflows/ci.yml`;
- `tools/repo/affected_owners.py`;
- affected-owner tests.

**Acceptance:** touching each owner selects its native verify task; cross-cutting paths still select all owners; `mise run repo:ci` green.

### B01 — Narrow composition boundary checks
After P01 and M01, enforce only demonstrated laws:
- default portable Plugin cannot point at direct Runtime/Host public MCP endpoints;
- Gateway routes cannot declare domain semantic authority;
- node-local Workstation paths/secrets cannot enter portable Plugin metadata.

Do **not** build a generic cross-language dependency framework.

## W6 — On-demand standards experiments

These are deliberately excluded from the critical path.

- **O01 MCP Tasks:** shadow only; Runtime Job remains canonical; no Gateway Task DB.
- **O02 MCP Resources:** pilot only for truly stable/read-only/addressable projections.
- **O03 MCP Apps:** only for concrete agent-embedded UI; never replace `apps/web`.
- **O04 A2A:** only when an independently owned peer Agent boundary exists; never replace Host.

## Parallel execution lanes

After C00 is frozen, these lanes are independent enough for separate Runtime workspaces:

```text
Lane A — Gateway:      G01 -> G02 -> G04 -> G05
Lane B — Runtime:      G03
Lane C — Skills:       S01
Lane D — Monorepo:     M01
```

Then integrate and run both Gateway + Runtime acceptance before E01.

External-effect lane is strictly serialized:

```text
E01 plan -> human/owner review of exact digest -> E02 apply -> E03 deploy -> E04 live proof -> E05 freeze
```

Plugin is also strictly post-C02:

```text
P01 -> P02 -> P03 -> P04
```

## Critical path

```text
C00
→ G01/G02 + G03
→ G04/G05
→ E01
→ E02
→ E03
→ E04
→ E05
→ P01
→ P02
→ P03
→ P04
```

M01 and S01 should run in parallel with early Gateway work and must be integrated before final composition acceptance.

## Do-not-build list

- Gateway database
- Gateway Task/Workflow engine
- Universal capability registry
- Agent Service 2.0
- Rich private Ordivon Plugin schema
- Skill authorization model
- root shared dependency workspace
- universal MCP proxy for third-party providers
- mandatory Distribution control plane
- A2A without a real peer-agent boundary

## Whole-program acceptance

The programme is complete only when all of the following are simultaneously true:

1. External Agent clients need one default Ordivon MCP endpoint.
2. Plugin default package names only that Gateway endpoint.
3. Runtime/Host/Harness remain independent truth owners.
4. Gateway can be rebuilt from owner observations without restoring a Gateway database.
5. Project Skills remain canonical under standard `.agents/skills`.
6. Plugin Skill composition is optional and byte-stable.
7. Skills MCP is treated as compatibility debt per consumer.
8. Gateway/Web/Preservation are first-class monorepo owners in affected CI.
9. Direct public owner endpoints have either an explicit remaining consumer or are retired.
10. No new universal Ordivon registry/workflow/task/domain model has been introduced.
