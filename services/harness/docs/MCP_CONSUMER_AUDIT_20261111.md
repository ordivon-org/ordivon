# Ordivon Harness / MCP: source-bound consumer audit (2026-11-11)

## Exact truth boundary

- Frozen source revision: 485fbcdc953d335465fc3a64d50284ddd854e46d (the public main snapshot locally resolved by Linux Runtime), isolated workspace ws-gpt6-harness-mcp-audit-20261111-r1.
- This audit examines the existing Python Harness MCP adapter, Gateway Python MCP/Owner proxy, Host Python MCP, Runtime Rust MCP layout, and the released tool-surface manifests. It does not certify every deployed node or current moving HEAD.
- No changes to A's single Harness Rust/PG Draft PR #2085, B's Rust Provider/ToolSurface branches, Host, Gateway, Skills, Runtime owners, or any production PostgreSQL.
- External normative check: MCP specification 2026-07-28 tools and Streamable HTTP; pinned local Python MCP SDK is 2.3.0.
- A separate independent consumer review has confirmed a blocking Rust PG Contract semantic parity failure (Python rejects an empty providerId, Rust accepts a hash-valid invalid Run); A already owns that repair. This audit does not duplicate A's code or authorize B's physical dispatch.

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

## Unresolved / avoid premature 'optimization'

1. P1 Gateway installed-Runtime schema workaround: upstream.py routes a finite Linux PG business tool set through public typed send_request instead of high-level Client.call_tool because the installed Runtime advertised a stale output schema. It includes effectful workspace.exec/job.cancel as well as read calls. The code explicitly does not retry effects. Remove this temporary branch only after the natural Runtime Owner deploys the correct output schema and a Gateway native SDK test proves no post-call false errors. Do not remove it blind or route effects to another owner.
2. P1 Gateway 5s observation budget: capability_catalog.py uses asyncio.timeout(5s by default), then projects UNKNOWN on timeout, without assuming unavailable; upstream.py now logs the exact MCP phase. Collect connection/handshake/tool/list/cleanup stage timing, specifically on Windows, before tuning latency or promoting longer timeouts. Avoid one global retry loop.
3. P1 duplicated model surface: Gateway and Host manifests overlap by 29 names. Use capability discovery and owner-qualified Tool IDs at the model-visibility boundary, presenting only the tools actually needed by a Run. Do not delete stable backend APIs solely to reduce prompt size.
4. P2 Harness synchronous OfficialMcpClient creates new asyncio.run, HTTP client and MCP session for each list_tools/call_tool invocation; this is verified in source, but no live latency measurement has been made. Keep for compatibility until real consumers warrant a long-lived async port or Rust transport. Gateway already pools HTTP sockets correctly; do not transplant an unnecessary duplicate manager into Harness.
5. P1 MCP tools/list_changed / grant drift: existing Harness Loop calls validate_runtime_catalog; that is a concrete pre-call check, not a guarantee that remote capabilities remain identical at dispatch time. A versioned digest and current owner admission must still be checked for effectful Tools. This audit does not grant effectful MCP to the observation-only adapter.
6. P0 Rust PG Contract semantic parity as noted above remains independently RED. B Provider V4/Domain ToolSurface projections cannot authorize physical Provider/Tool effects before A's complete versioned Run Contract gate and Writer/Lease port.
7. Tool availability must be represented in distinct dimensions: advertised, granted, model-visible, owner-configured, owner-observed-ready, submitted, effect-observed and domain-accepted. A single boolean is not enough.

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
