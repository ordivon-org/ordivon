# Ordivon Harness / MCP: source-bound consumer audit (2026-11-11)

## Exact truth boundary

- Initial frozen source revision: 485fbcdc953d335465fc3a64d50284ddd854e46d; later independently tested source HEAD is tracked on Draft PR #2093, isolated workspace ws-gpt6-harness-mcp-audit-20261111-r1. Never equate initial source revision with current deployed or PR HEAD.
- This audit examines the existing Python Harness MCP adapter, Gateway Python MCP/Owner proxy, Host Python MCP, Runtime Rust MCP layout, and the released tool-surface manifests. It does not certify every deployed node or current moving HEAD.
- No changes to A's single Harness Rust/PG Draft PR #2085, B's Rust Provider/ToolSurface branches, Host, Gateway, Skills, Runtime owners, or any production PostgreSQL.
- External normative check: MCP specification 2026-07-28 tools and Streamable HTTP; pinned local Python MCP SDK is 2.3.0.
- A separate independent consumer review originally found a Rust PG Contract semantic parity failure (Python rejects an empty providerId). A has since implemented a versioned semantic reader gate in its separate Draft PR #2085; this audit neither duplicates A's source nor upgrades any source-only Reader/Lease evidence to physical dispatch authority.

## Reality-based L1 -> L2 module graph

| Logical need | Natural capability module / consumer | Actual binding / gap |
| --- | --- | --- |
| Public MCP Tool definition and stable schema | Gateway mcp_server.py + mcp-surface.json; Host mcp_server.py + mcp-surface.json | Release tests compare SDK-native tools/list to tool names and schema digest; no need for another registry |
| MCP Owner transport, retry identity and errors | Gateway upstream.py McpOwnerCaller; Official MCP Client/streamable HTTP | One process-scoped httpx2 pool per Owner is already in place; request-local protocol session, credential rotation at request time; do not rebuild a custom transport |
| Configured/available/UNKNOWN | Gateway capability_catalog.py + capability_projection.py | Projection uses Owner runtime.describe and strict booleans; 5s default read timeout can yield UNKNOWN, not prove physical unavailability |
| Host collaboration | Host mcp_tool_registration.py / PostgreSQL pool | Host owns Work/Topic/Message; Gateway proxies its tools; do not move collaborative state into Harness |
| Runtime effects and receipts | Rust ordivon-runtime-mcp crate + Gateway execution commands | Runtime Job/Attempt/Artifact is physical truth; Harness has no right to turn MCP transport failure into execution failure or retry an unknown effect |
| Model-visible Tool surface | Harness plugin_mcp.py + ToolDefinition / B's separate Rust Domain ToolSurface | Plugin observation adapter admits only observation; B's custom Domain ToolSurface is distinct and currently source-only; an MCP listed tool does not imply effect authorization |
| MCP client pagination and context | Harness mcp_http_client.py pinned MCP 2.3.0 | SDK Client.list_tools returns one page, not whole catalog. Cursor pagination was missing; fixed using the SDK's public cursor argument |
| Skills / lifecycle extensibility | Existing Skills Owner and Harness plugin composition | Keep Skills as an external capability; do not create another Harness Manager or skill store |
| Per-turn prompt compilation | Harness WorkingView/Loop and source-only Rust B | Must consume *verified* Tool definitions and exact Contract/grant identity; unresolved end-to-end Rust consumer |
| History/contract admission | Harness Python core_contracts.py and PG Store; A Rust PG Reader | Strong hashes are insufficient: complete Python versioned semantic Contract validation is a separate mandatory gate |

## Measured exposed surface (source manifests, not model prompt tokens)

- Gateway 0.10.8, surfaceEpoch 9: 38 tools.
- Host 0.8.0, surfaceEpoch 6: 31 tools.
- Identical tool names shared by both: 29; Gateway-only: 9; Host-only: 2. Two separate MCP connections exposing both full surfaces could duplicate 29 model-visible names, but this audit has **not** measured actual client prompt token use and does not claim every Host/Gateway tool is shown in the same model turn.
- Gateway-only names: system.describe, capability.describe, capability.search, capability.resolve, execution.submit/get/resolve/cancel, artifact.read. Host-only names: host.pool.stats, message.get. Those are source inventory differences, not authority differences.
- Gateway's official released MCP manifest does NOT contain continuity.get or continuity.list. The former Harness default observation bridge demanded both, making its default grant impossible against current Gateway. Historical 2026-09 fixture incorrectly modeled old names as available; source test now consumes current Gateway release manifest.

## Confirmed actual bugs and minimal source corrections

1. P0 stale default Tool grant, Model-Surface consumer broken:
   - Python src/ordivon_harness/plugin_mcp.py default had system.describe + capability.describe + continuity.get + continuity.list.
   - Current Gateway 0.10.8 manifest and mcp_server.py only export first two.
   - Reproduced RED against current release manifest: job-01a1c8af-76aa-774b-bfb8-ee424cda0d2e.
   - GREEN removes only obsolete aliases from the observation bridge default/allowlist, updates QUICKSTART and verifies manifest-based consumer fixture; does not resurrect aliases or change Gateway/Host.
2. P0 explicit empty grant expanded privileges:
   - Existing allowed_tools or DEFAULT turned allowed_tools=() into the default non-empty grant.
   - RED job-01a1c8b2-c156-7237-a345-d73ab7de3e6d.
   - GREEN selects default only if allowed_tools is None. Empty explicit grant now rejects before any tool call.
3. P1 duplicated Tool name silently overwritten:
   - Plugin admission and resume catalog validation used dict assignment by name. A malicious or malformed tools/list with repeated granted name could masquerade as a single definition.
   - Two independent RED tests (admission and resume) job-01a1c8ad-8a47-71c1-8134-b977e89e9bcd.
   - GREEN rejects repeated granted names as PROTOCOL_INVALID. This implements MCP's unique-tool-name guidance without a new registry.
4. P1 paginated tools/list silently truncated:
   - Pinned MCP SDK 2.3.0 Client.list_tools(cursor=...) returns one ListToolsResult and **has no list_all_tools API** (verified with exact native Python introspection job-01a1c8b1-2c11-7564-a0a8-fa4de793646e).
   - Existing Harness OfficialMcpClient._list_tools consumed result.tools once, losing pages >1.
   - Two RED tests for second-page omission and repeated pagination cursor: job-01a1c8b1-ded8-73e7-953a-59aac00e4fb0.
   - GREEN uses the official SDK cursor parameter, rejects repeated/malformed cursors and bounds page traversal to 256 pages. No custom MCP implementation.

5. P0 real SDK second-page output-schema validation can silently disappear:
   - Native pinned MCP 2.3.0 HTTP fixture registers two tools with paginated tools/list. The second tool advertises JSON Schema allowing string values only, but a crafted read-only response provides {"wrong": true}.
   - The real official Client call_tool sent exactly one tool call, re-listed only the first page after the completed call, logged 'Tool capability_describe not listed by server, cannot validate any structured content', then returned (False, {"bad": True}) as if valid. Native repro Job job-01a1c8e4-23a7-7770-9920-90b5b83f6722.
   - A real MCP-over-HTTP RED test reproduces invalid post-call success: job-01a1c8e4-d779-7083-b629-9bb3745586a4.
   - GREEN reuses the same SDK-native complete page walker inside each call's active Client session, before Tool call. This provides the installed SDK with second-page outputSchema, not a custom validator. Valid second-page returns succeed. Invalid typed response is rejected by official SDK validation, with exactly one physical call and no retry. If the tool disappears from the refreshed catalog, the bridge raises a typed protocol error before any call. Native GREEN job-01a1c8e6-5bce-77cd-9a43-2c366a97410f (18 focused tests + Ruff).
   - SDK cleanup wraps a post-call schema RuntimeError in ExceptionGroup; that is post-effect UNKNOWN for physical effects, not evidence to retry. Current plugin bridge is observation-only; these tests do not authorize physical effect dispatch.

6. P0 H1 pre-call catalog drift enforcement (actual Agent Run consumer):
   - PluginMcpObservationBridge exposed validate_runtime_catalog, and ordivon/loop.py checks it at start of Run, but direct bridge.execute did not call it. Between the initial inspection and later Tool dispatch, the name/description/inputSchema can drift, and previously the bridge could invoke the MCP tool using a stale ToolSpec.
   - RED two direct consumer tests (Tool revoked, inputSchema modified after construction): job-01a1c90d-718f-728e-8cd6-2fc2e15fd8f8; both sent a Tool call without rejecting stale admission.
   - Minimal GREEN reuses the bridge's existing validate_runtime_catalog immediately before client.call_tool, without another Registry/schema validator/Writer. Focused 20 tests pass, job-01a1c90d-b49f-7478-8236-71718a68912c.
   - Real disposable PostgreSQL 18 on isolated Unix socket (no TCP): original HarnessAgentRun Skill + Gateway observation path and new Scripted Provider ToolCall with catalog drift BETWEEN Run-start inspection and later Tool Call. Both real PG consumer scenarios PASS, no physical client.call_tool on drift, Run stops invalid_tool_call with detail catalog drifted, job-01a1c912-2d34-7765-b6a5-625834e1b70e. An earlier probe confirmed Loop already rejects drift before Run start as harness_failed; this new test targets the previously unprotected interval.
   - Scope: a schema change after final list but before actual tools/call remains possible, and outputSchema is not in the historical H1 v1 catalog digest. SDK-native outputSchema validation is still used for current call. This does not establish durable external effect identity, semantic success or production readiness.

7. P0 H2 execution gateway duplicate Tool and mid-Run drift gating:
   - services/harness/src/ordivon_harness/plugin_gateway_effect.py used dictionary overwrite for repeated required remote execution.submit/get/resolve/cancel tool names both during factory admission and validate_runtime_catalog; two independently reproduced counterexamples show the first or last conflicting schema could be hidden.
   - An effectful Run checks its remote Tool Catalog before its model turn, but the prior H2 _lower_runtime_tool_call did not repeat that check just before creating the durable ToolStep intent. MCP output/input Schema changes between the initial check and execution could cause a dispatch using a previously admitted definition.
   - RED private isolated PG18 tests: factory duplicate omitted rejection, late catalog duplicate shadowed, and after-preflight schema drift still produced candidate_completed with one actual fixture execution.submit, job-01a1c938-f011-7498-8bb1-27e43d6510e7. The original factory RED also reproduced without PG as job-01a1c938-ab93-729f-94db-7488930d3c86.
   - Minimal GREEN: reject repeated required names as PROTOCOL_INVALID in both existing code paths and reuse existing H2 validate_runtime_catalog right before durable ToolStep admission (after caller argument validation, before creating the client request identity, lease/fence, or invoking an owner). Unexpected pre-admission catalog transport errors now become typed PROTOCOL_INVALID with no physical call, rather than an unstructured exception. A private PG test RED before this error classifier produced harness_failed, job-01a1c93c-3adc-765c-9c01-5bec78852edb.
   - Private real PostgreSQL 18 complete H2 original effect/recovery tests 32/32 PASS, including one-winner durable Intent/Fence before fake owner physical dispatch, response-loss resolution without replay, cancellation behavior, and four new protocol/identity test cases. Native job-01a1c93c-b813-746b-9a58-4d675db30675. An actual MCP 2.3.0 SDK + stateless HTTP MCPServer + PostgreSQL Run test changes the execution.submit inputSchema on the third tools/list and proves zero native tools/call and no persisted active Tool Step, job-01a1c93d-d31f-7161-9c96-fbbdf99b61e2.
   - Rechecking the catalog is an H2 source validity gate, not a global transaction joining Gateway and Harness. Schema can still change between final tools/list and tools/call, and post-call UNKNOWN/receipt reconciliation must still preserve the committed intent. Existing Gateway request ID and Runtime remain physical authority; no automatic retry on transport/schema failure.

## Unresolved / avoid premature 'optimization'

1. P1 Gateway installed-Runtime schema workaround: upstream.py routes a finite Linux PG business tool set through public typed send_request instead of high-level Client.call_tool because the installed Runtime advertised a stale output schema. It includes effectful workspace.exec/job.cancel as well as read calls. The code explicitly does not retry effects. Remove this temporary branch only after the natural Runtime Owner deploys the correct output schema and a Gateway native SDK test proves no post-call false errors. Do not remove it blind or route effects to another owner.
2. P1 Gateway 5s observation budget: capability_catalog.py uses asyncio.timeout(5s by default), then projects UNKNOWN on timeout, without assuming unavailable; upstream.py now logs the exact MCP phase. Collect connection/handshake/tool/list/cleanup stage timing, specifically on Windows, before tuning latency or promoting longer timeouts. Avoid one global retry loop.
3. P1 duplicated model surface: Gateway and Host manifests overlap by 29 names. Use capability discovery and owner-qualified Tool IDs at the model-visibility boundary, presenting only the tools actually needed by a Run. Do not delete stable backend APIs solely to reduce prompt size.
4. P2 Harness synchronous OfficialMcpClient creates new asyncio.run, HTTP client and MCP session for each list_tools/call_tool invocation. Local official MCP SDK + uvicorn Streamable HTTP, 12 calls per scenario: fresh list 52.08ms median; fresh call 99.99ms; H1 recheck + fresh call 148.47ms; persistent SDK ClientSession 44.04ms, with one tools/list versus 24 lists for 12 H1 calls (Runtime job-01a1c91a-2564-74fe-92e1-1bd2f877931f). Single host, sequential, local synthetic measurement only; not a remote production comparison or speedup guarantee. Reuse mature SDK and wait for actual Rust consumer evidence; do not introduce another independent connection Manager. Gateway already pools HTTP sockets correctly.
5. P1 MCP tools/list_changed / grant drift: both H1 observation and H2 execution bridges now independently recheck their originally granted catalog before calls/intent. The gap between the final tools/list and actual tools/call is still non-atomic. A versioned digest and current Owner admission must enforce effect authority. This audit does not grant effectful MCP to the observation-only adapter.
6. P0 Rust PG Contract semantic parity had a confirmed RED and A has since repaired the versioned semantic reader gate in separate Draft PR #2085. Independent C acceptance, Rust native durable append+fenced Tool Intent+physical Provider/Runtime receipts remain unproven; B's Provider V4/Domain ToolSurface projections cannot authorize physical effects from a source-only Reader or locally validated Lease candidate.
7. Tool availability must be represented in distinct dimensions: advertised, granted, model-visible, owner-configured, owner-observed-ready, submitted, effect-observed and domain-accepted. A single boolean is not enough.

### R14 full test and no-production qualification

- H2 effectful execution/preflight patch validated against a private PostgreSQL 18 instance with Unix-domain socket only, initialized and destroyed by the Runtime Job. Entire installed Harness Python suite with HARNESS_PG_TEST_DSN set: 1447 passed, 73 skipped, 2 deselected, 386 subtests passed; Ruff check, compileall, targeted Ruff formatter, and documentation contract pass. Gateway Tool Surface release contract, Owner HTTP pool, MCP protocol mode, and readiness projection test files also pass. Runtime job-01a1c93f-b798-7320-b8ce-8d7e02bbb735 terminal succeeded. This is local source qualification only, not production deployment or independent C signoff.
- The same private-PostgreSQL test run preserved the existing receipt-loss reconciliation case: no duplicate execution.submit after an owner response-loss simulation, and ToolStep Intent/Fence is committed before the fixture's physical dispatch. It does NOT test production Runtime identity, installed SDK transport against real external effects or every historical Run.
- The native SDK stateless HTTP + private PG source scenario proves an altered remotely advertised execution.submit inputSchema is refused before any owner tools/call and before durable ToolStep admission. This avoids mistaking a model-visible tool or a stale plugin catalog for external execution authority.
- Next testable boundary remains the exact last-moment catalog/owner TOCTOU interval and A-owned native Rust durable Writer/Lease/Fence plus real Provider/Runtime Receipt or UNKNOWN reconstruction.

## Regression evidence and next handoff

- Target Python pytest + Ruff GREEN after MCP fixes: 17 tests passed, job-01a1c8b2-e6e5-7077-a01d-9d14b806f4d4.
- Release-contract test against current Gateway manifest and stale aliases GREEN: job-01a1c8b0-2c2f-77df-a4f2-6df553cc5810.
- Separate real MCP text-only error native test remains in tests/test_mcp_http_client.py; it is included in target checks.
- Full Harness regression and final Git source commit must be recorded independently after this document is added; the above evidence does not imply production deployment or completed Rust cutover.
- Handoff to A: keep unique PR/PG Contract semantics; do not cherry-pick this audit into A PR without reviewing the moving main and consumer contracts.
- Handoff to B: consume only verified catalog/grant/contract identity from current Gateway and Domain tools; do not treat observation-only MCP support as a dispatch port.
- Handoff to independent C and Gateway Owner: falsify this source branch with a real paginated MCP server, authoritative current Gateway tool listing and post-call SDK timing; decide whether the temporary Linux PG typed bridge can be deleted after Runtime schema deployment.

References:
- https://github.com/modelcontextprotocol/modelcontextprotocol/blob/main/docs/specification/2026-07-28/server/tools.mdx
- https://github.com/modelcontextprotocol/modelcontextprotocol/blob/main/docs/specification/2026-07-28/basic/transports/streamable-http.mdx
- https://github.com/modelcontextprotocol/python-sdk/blob/main/docs/client/index.md
