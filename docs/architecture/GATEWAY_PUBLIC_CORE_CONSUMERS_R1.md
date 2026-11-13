# Gateway public Core: consumer graph and evidence obligations R1

Status: SOURCE CANDIDATE. Public external client acceptance UNKNOWN.
Date: 2026-11-13. Canonical delivery: Gateway PR #2174.
This document is a source-derived consumer map, not a second route database.

## Consumer graph

Portable Agent Plugin (extensions/ordivon-control-plane/mcp.json)
→ one Gateway HTTPS MCP server
→ existing ingress identity / AuthZEN policy enforcement
→ Core or Full process-static public tools
→ Gateway Owner SDK adapter
→ Host Work/Social/Attention PG or Runtime Job/Artifact PG
→ authoritative receipt / OperationRef / Artifact → Agent → User.

Gateway does not own Runtime Jobs, Host Work, Harness Runs or Security grants.
Source tool functions, Host PEP and real Owner authority remain independent.

## Use-case map

| Normal Agent intent | Public Core | Natural consumer | Qualification |
|---|---|---|---|
| Find or resume existing Work | work.get, work.list | Host Work | Same typed Host read |
| Begin Work | work.create | Host Work | Same Owner operation |
| Persist progress/finish | work.snapshot.commit | Host CAS | expectedRevision preserved |
| Read collaborations | space.list, topic.list, topic.resume, message.search | Host Social | No Gateway message index |
| Write a message | message.post | Host Social | Existing Host write and AuthZEN |
| Read and acknowledge changes | attention.delta, attention.ack | Host Attention | Exact cursor contracts |
| Find a capability | capability.search | Gateway catalog | UNKNOWN readiness preserved |
| Execute and recover | execution.submit/resolve/get/cancel | Runtime PG | Principal-bound RequestId/OperationRef |
| Fetch results | artifact.read | Runtime PG | Artifact AuthZEN and native evidence |
| Create Space/Topic | NOT CORE | Host specialist/Owner | Missing in ordinary Core |
| Full returning-Agent reentry | NOT CORE | Host attention.reentry | Pending specialist workflow |
| Actor and subscription administration | NOT CORE | Host operator/specialist | Deliberately hidden |
| Research composition resolve | NOT CORE | Skills/Research | Not a general runtime planner |
| Agent semantic Run | NOT INSTALLED | Harness PG | Await verified Rust Run owner |

Core = 17 public tools (11 Host, 5 Runtime/Artifact, 1 catalog).
Full = 38 tools (29 Host, 5 Runtime/Artifact, 4 discovery).
Hidden = 21 (18 Host, 3 metadata). Tool counts are not model
selection accuracy, latency, or business success evidence.

## Security and protocol contracts

- Compose original Owner registrars, then use official MCPServer.remove_tool
  before publishing the server. Do not implement a competing MCP protocol,
  custom Host decorator, or catch-all invocation dispatcher.
- Hidden names are not callable. Since HTTP middleware can run before SDK
  unknown-tool dispatch, skip AuthZEN target resolution for Core-hidden names;
  leave verified ingress identity requirement unchanged.
- Visible Host calls use their original exact authorization name and full
  request-object binding. An identity is not itself an Actor grant.
- Process-static Core and Full yield deterministic MCP tools/list for
  caching. Refreshing an external client catalog is its consumer obligation.
- Host CAS and other multi-Owner effects remain owned by natural systems;
  Gateway must not execute unsafe cross-owner write compositions.

## Claim-evidence boundaries

| Claim | Evidence | Limitation |
|---|---|---|
| Finite visibility safety | formal/GatewayToolVisibilityR1.tla + safe/unsafe configs | Not universal source refinement |
| Actual Core tool set | official SDK Client, test_core_public_surface.py | Source-local consumer |
| Hidden 21 names | SDK negative calls, no Host Owner | Does not prove production ingress |
| Authenticated Core vs Full | actual local TCP + fake AuthZEN | Synthetic policy, no live grant |
| Gateway source route | existing owner SDK adapter and tests | Not a real Agent user task |
| Buildable release | installer + installed SDK verifier | Not active systemd deployment |
| External Plugin | one Gateway URL in mcp.json | Client tool cache UNKNOWN |

Old September 2026 Gateway Host acceptance and its 15-tool list are
historical snapshots, NOT current production Work/Space/Topic truth.

## P0 promotion gates

1. Gateway full verify and pinned TLA+ verification with negative controls.
2. SDK source manifest/Schema digests for both Full and Core.
3. Installer compares the candidate with the CURRENT ACTIVE profile,
   not the unrelated Full manifest. A release supporting both profiles
   cannot reveal its running profile from package files alone.
4. Real Principal and Security PDP Host allow/deny, downstream Owner result.
5. Real Runtime submit -> resolve -> observe -> Artifact including lost replies.
6. Actual external Plugin client refreshed tools/list and complete business
   task. Space/Topic creation or returning-Agent Attention must have a
   deliberate Specialist path, never an implicit backdoor.
7. Then and only then promote live Core and retire stale public wrappers.

## Remaining debts

P0: Installed Security grants and external client refresh unknown.
P0: Validate current service profile via live tools/list before cutover.
P1: Specialist Space/Topic/Attention, Workspace, Harness Run consumption.
P1: Measured ordinary-Agent task success, latency and tool-selection quality.
P1: Model-to-SDK source refinement remains UNKNOWN beyond finite tests.
P2: Remove historical adapters and stale docs only if consumer graph
proves no active readers; preserve archival research and past evidence.
