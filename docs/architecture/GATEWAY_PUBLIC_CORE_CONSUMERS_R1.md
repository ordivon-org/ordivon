# Gateway public Core: consumer graph and evidence obligations R1

Status: SOURCE CANDIDATE. Public external client acceptance UNKNOWN.
Updated: 2026-11-14. Canonical delivery: Gateway PR #2174.
This document is a source-derived consumer map, not a second route database.

## Consumer graph

Portable Agent Plugin (extensions/ordivon-control-plane/mcp.json)
→ one Gateway HTTPS MCP server
→ existing ingress identity / AuthZEN policy enforcement
→ Core, Collaboration, or Full process-static tools
→ Gateway Owner SDK adapter
→ Host Work/Social/Attention PG or Runtime Job/Artifact PG
→ authoritative receipt / OperationRef / Artifact → Agent → User.

Gateway does not own Runtime Jobs, Host Work, Harness Runs or Security grants.
Source tool functions, Host PEP and real Owner authority remain independent.

## Profile selection and deployment

- Core: 17 stable tools, minimum ordinary-agent knowledge.
- Collaboration: 22 tools, adds five consumer-required Host methods.
  The source Skill task-space-reentry requires space.get and
  attention.reentry; new task creation requires Actor/Space/Topic bootstrap.
- Full: 38 existing tools, reserved for explicitly administered clients.
- Profiles are **process-static** SDK tool projections, not runtime session
  routing. One running Gateway HTTP endpoint serves exactly one selected
  profile. This change DOES NOT provision a second endpoint or automatically
  authorize a specialist Agent. A second simultaneous profile requires
  separate authenticated deployment/routing and real consumer qualification;
  no hidden fallback to direct Host is permitted.
- All tools still use existing Host/Runtime Owner calls; no duplicate
  collaboration state, second PG store, or Gateway-owned actor identity.
- A newly registered unknown tool is excluded from all public profiles
  before the MCP server begins servicing external clients. Missing required
  advertised tools fail startup. Profile changes are ABI changes and must
  qualify the current and candidate tool epochs/package versions.

## Use-case map

| Normal Agent intent | Public profile | Natural consumer | Qualification |
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
| Create Space/Topic | Collaboration: space.create, topic.create | Host Social | Existing Host mutation with Security PEP |
| Full returning-Agent reentry | Collaboration: space.get, attention.reentry | Host Social/Attention | Exact task-space-reentry Skill dependency |
| Actor bootstrap | Collaboration: actor.declare | Host Work | Existing Security-bound mutation; not identity impersonation |\n| Subscription and advanced management | Full/Owner only | Host | Deliberately hidden from public profiles |
| Research composition resolve | NOT CORE | Skills/Research | Not a general runtime planner |
| Agent semantic Run | NOT INSTALLED | Harness PG | Await verified Rust Run owner |

Core = 17 tools (11 Host, 5 Runtime/Artifact, 1 catalog).
Collaboration = 22 tools (16 Host, 5 Runtime/Artifact, 1 catalog).
Full = 38 tools (29 Host, 5 Runtime/Artifact, 4 discovery).
Core hides 21; Collaboration hides 16. These counts are NOT model
selection accuracy, latency, or real Agent business-success evidence.

## Security and protocol contracts

- Compose original Owner registrars, then during SDK server lifespan,
  enumerate actual registrations using official MCPServer.list_tools and
  remove every name outside the selected explicit tool allowlist with
  official MCPServer.remove_tool before accepting client requests.
  New unknown tool registrations therefore fail closed; missing required
  public registrations fail startup. Do not implement a competing MCP
  protocol, custom Host decorator or catch-all invocation dispatcher.
- Hidden names are not callable. Since HTTP middleware can run before SDK
  unknown-tool dispatch, skip AuthZEN target resolution for public-profile-hidden names;
  leave verified ingress identity requirement unchanged.
- Visible Host calls use their original exact authorization name and full
  request-object binding. An identity is not itself an Actor grant.
- Process-static Core, Collaboration and Full yield deterministic MCP tools/list for
  caching. Refreshing an external client catalog is its consumer obligation.
- Host CAS and other multi-Owner effects remain owned by natural systems;
  Gateway must not execute unsafe cross-owner write compositions.

## Claim-evidence boundaries

| Claim | Evidence | Limitation |
|---|---|---|
| Finite visibility safety | formal/GatewayToolVisibilityR1.tla + safe/unsafe configs | Not universal source refinement |
| Actual three public profiles | official SDK Client, test_core_public_surface.py | Source-local consumer |
| Future unknown tool denied | injected Tool, SDK lifespan and denied call | No cross-process mutation after startup |
| Hidden 21 Core names | SDK negative calls, no Host Owner | Does not prove production ingress |
| Authenticated Core/Collaboration/Full | actual local TCP + fake AuthZEN | Synthetic policy, no live grant |
| Collaboration work lifecycle | 10 ordered SDK calls → existing Host stubs | Source-level only, not PG Host transaction |
| Gateway source route | existing owner SDK adapter and tests | Not a real Agent user task |
| Buildable release | installer + installed SDK verifier | Not active systemd deployment |
| External Plugin | one Gateway URL in mcp.json | Client tool cache UNKNOWN |

Old September 2026 Gateway Host acceptance and its 15-tool list are
historical snapshots, NOT current production Work/Space/Topic truth.

## P0 promotion gates

1. Gateway full verify and pinned TLA+ verification with negative controls.
2. SDK source manifest/Schema digests for Full, Core and Collaboration.
3. Installer compares the candidate with the CURRENT ACTIVE profile,
   not the unrelated Full manifest. A release supporting multiple profiles
   cannot reveal its running profile from package files alone.
4. Real Principal and Security PDP Host allow/deny, downstream Owner result.
5. Real Runtime submit -> resolve -> observe -> Artifact including lost replies.
6. Actual external Plugin client refreshed tools/list and complete business
   task. Collaboration must have a deliberate separately authenticated
   specialist deployment or be consciously chosen as the public process
   profile, never an implicit fallback to a direct Owner.
7. Then and only then promote live Core and retire stale public wrappers.

## Remaining debts

P0: Installed Security grants and external client refresh unknown.
P0: Validate current service profile via live tools/list before cutover.
P1: Actual Specialist endpoint/client deployment, Workspace/Harness Run consumption.
P1: Measured ordinary-Agent task success, latency and tool-selection quality.
P1: Model-to-SDK source refinement remains UNKNOWN beyond finite tests.
P2: Remove historical adapters and stale docs only if consumer graph
proves no active readers; preserve archival research and past evidence.
