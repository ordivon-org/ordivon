---
schema_version: 1
id: harness.quickstart
title: Harness Quick Start
type: guide
profile: engineering
lifecycle: active
source_role: canonical
visibility: public
owners:
  - ordivon-harness
audience:
  - builder
  - operator
  - agent
updated: 2026-11-17
summary: Minimal path from a clean checkout to deterministic verification, operator inspection and live read-only acceptance.
evidence_status: verified
readiness: READY
applies_to:
  - ordivon-harness
related:
  - harness.start
  - harness.status
  - harness.compatibility
  - harness.operations
---
# Quick start

## Set up

```bash
uv sync
uvx ruff==0.17.2 check src tests scripts
uv run python -m unittest discover -s tests -v
```

Build and verify the exact installable artifact:

```bash
rm -rf dist
uv build --wheel --out-dir dist
python scripts/check_wheel.py "$(find dist -maxdepth 1 -type f -name '*.whl' -print -quit)"
```

The base wheel keeps a small Host-free runtime dependency graph: pinned `httpx==0.28.1` for cancellable DeepSeek HTTP/TLS transport and `jsonschema` for opt-in local structured-result conformance verification. Standard Agent Plugin MCP consumption is isolated behind the exact `mcp` extra (`ordivon-harness[mcp]`), pinned to the official `mcp==2.3.0` Python SDK. Historical Harness identity canonicalization is packaged locally as the `anc_canonical` compatibility shim; it is not an external dependency and must not be extended into a new shared protocol layer. It does not install Host or expose a Host extra.

## Opt-in physical Provider + PostgreSQL acceptance

The built-in Python CLI uses the original PostgreSQL Journal and can run a
real, caller-bound, no-Tool DeepSeek task. After the ordinary deterministic
tests pass, verify the **actual** Provider/PG/CLI consumer when the test node
has a valid `~/.config/ordivon/secrets/deepseek.json` and a dedicated
PostgreSQL test DSN:

```bash
HARNESS_PG_TEST_DSN='<dedicated-test-DSN>' HARNESS_REAL_PROVIDER_TEST=1 \
  uv run --locked python -m pytest -q \
    tests/test_postgres_cli.py -k live_deepseek_cli
```

This is an explicit billable external model call; ordinary `verify`, CI and
`pg:verify` do **not** make this request. The existing test fixture creates
and drops a uniquely named temporary PG schema. It runs one model turn,
then uses separate CLI processes to retrieve the final Run and receipt.
The consumer claims only Provider execution/Run completion proposal,
never caller-domain TaskSolved, native Rust production readiness or
installed Gateway routing.

## Initialize independent state

```bash
ordivon-harness store-init
```

## Run

Create one caller-authored `HarnessRunContract` JSON. Harness begins at that exact authority boundary; cross-Run planning, resource allocation, successor selection and retry policy are external.

Harness uses one current sequential Agent-loop scheduling kernel. Workloads that need an explicit deliberation phase compose a caller/domain-owned no-Tool `AgentTurnRequest` and then pass the resulting cognition evidence into the retained `DomainToolLoopRunner`; Harness no longer owns a generic two-phase deliberation lifecycle helper.

Create a caller-authored `HarnessRunContract` JSON. The CLI does not invent Objective, Context, caller identity, Tool grant, budget or completion authority. The recommended API is closed over the values required for basic Contract authoring:

```python
from anc_canonical import canonical_digest
from ordivon_harness.api import HarnessBoundReference, HarnessRunContract, RunBudget

def bound_ref(reference_id: str, kind: str, claim: object) -> HarnessBoundReference:
    return HarnessBoundReference(reference_id, kind, canonical_digest(claim))

budget = RunBudget(
    max_model_calls=2,
    max_tool_calls=0,
    max_observation_bytes=65_536,
    max_wall_time_ms=90_000,
    max_total_tokens=16_384,
)
# Supply caller/objective/context/provider/system identities, the exact Tool catalog/grant
# digests admitted by the selected source-owned execution profile and caller Contract, and `budget.to_contract_dict()` to
# HarnessRunContract. Persist `contract.to_dict()` as RUN_CONTRACT.json.
```

`max_tool_calls=0` is valid for a no-Tool Run. Capability comes from the Tool
catalog/grant bound by the Contract; a positive Tool budget never grants a Tool by
itself. `max_tool_corrections` bounds only model-correctable Tool-call rejection;
`max_conclusion_corrections` independently bounds caller/domain conclusion-gate
rejection. Older schema-v1 Contracts that omit `maxConclusionCorrections` remain
readable with the historical default of 3.

```bash
ordivon-harness \
  run RUN_CONTRACT.json --message 'Start the bounded Run'

ordivon-harness status HARNESS_RUN_ID
ordivon-harness inspect HARNESS_RUN_ID
ordivon-harness explain HARNESS_RUN_ID
```

The former `capabilities` CLI command is retired (see `COMPATIBILITY.md`); invoking it is not a supported inspection path. Use `ordivon-harness --help` to inspect the actual installed command surface, and `ordivon-harness gateway-profile --gateway-url <authorized-endpoint>` (plus the necessary caller/transport settings) to read the current Gateway execution Tool catalog and grant digests without creating a Run. Without a configured Gateway endpoint, this inspection command fails closed instead of silently selecting one. Durable `inspect` exposes the exact retained Run/Contract/Provider/Snapshot/Recovery facts directly. CLI `explain` adds proof boundaries to that same view, while `HarnessAgentRun.explain()` reports validated in-process composition. No aggregate workbench or installed-capability registry sits between those owners and the caller.

For the built-in DeepSeek profile, the Contract must bind the canonical no-Tool catalog/grant and the configured DeepSeek Adapter/model. The current adapter reserves a conservative request-token upper bound equal to the serialized Provider request bytes plus its 8,192-token completion ceiling. A small Contract such as `max_total_tokens=4_096` can therefore be rejected safely before the first Provider dispatch; `16_384` is a practical starting bound for a small no-Tool Run, not a universal required value.

### Agent Plugin composition — H1 observation-only

Harness can consume an already selected **Agent Plugins v1** package without becoming a Plugin registry or Skill authority. The application loads the portable package, selects exact Skill/MCP components, and binds the resulting Tool catalog and grant digests into the ordinary `HarnessRunContract`.

```python
from ordivon_harness.api import (
    AgentPluginComposition,
    HarnessAgentRun,
    HarnessCognitionSeed,
    HarnessCognitionSeedSource,
    HarnessCognitionProfile,
    OfficialMcpClient,
    PluginMcpObservationBridge,
)

plugin = AgentPluginComposition.load("/path/to/materialized/plugin")

# Agent Skill remains advisory procedure content. The caller chooses it; the
# Plugin/Harness does not grant Tools or permissions by loading it.
skill_source = plugin.skill("method-router").to_working_view_source()
seed = HarnessCognitionSeed(
    attempt_id="working-attempt:plugin",
    sources=(HarnessCognitionSeedSource(slot="procedure", source=skill_source),),
    basis="caller selected this exact Skill for the bounded Run",
)

# Authentication belongs to the embedding client/application. Pass an
# httpx-compatible Auth object such as the official MCP OAuthClientProvider.
client = OfficialMcpClient(
    plugin.mcp("ordivon-gateway"),
    auth=caller_supplied_auth,
)
bridge = PluginMcpObservationBridge(
    plugin.mcp("ordivon-gateway"),
    client,
    allowed_tools=("system.describe", "capability.describe"),
)

# Author the Run Contract with:
#   tool_catalog_digest = bridge.catalog_digest
#   tool_grant_digest   = bridge.grant_digest
run = HarnessAgentRun.create(
    state_root,
    contract,
    adapter_factory,
    tool_bridge=bridge,
    cognition_profile=HarnessCognitionProfile(),
)
execution = run.run((), cognition_seed=seed)
```

This H1 bridge admits only the current Gateway observation surfaces: `system.describe` and `capability.describe`. Historical `continuity.get`/`continuity.list` aliases are not exported by the Gateway MCP release; use the Host/Work owner APIs through their appropriate client instead. Effectful Gateway composition must use the H2 durable intent/receipt/reconciliation slice below; a generic MCP call must not bypass Harness recovery semantics.

The portable package contains component identity, not credentials. OAuth/token storage and interactive authorization remain application/client concerns. Harness accepts the official MCP SDK Auth port and does not define a second OAuth protocol or credential database.

### Agent Plugin composition — H2 durable Gateway execution

For effectful execution, do **not** add `execution.submit` to the H1 observation bridge. Bind a narrow caller-authored execution grant and pass a `PluginGatewayExecutionBridgeFactory` to `HarnessAgentRun`.

```python
from ordivon_harness.api import (
    PluginGatewayExecutionBridgeFactory,
    PluginGatewayExecutionGrant,
)

grant = PluginGatewayExecutionGrant(
    capability="execution.linux",
    workspace_id="ws-bounded-run",
    executable_allowlist=("/usr/bin/rg",),
    env_allowlist=(),
    max_timeout_ms=30_000,
)
factory = PluginGatewayExecutionBridgeFactory(
    plugin.mcp("ordivon-gateway"),
    client,
    grant,
)

# Author the Run Contract with:
#   tool_catalog_digest = factory.catalog_digest
#   tool_grant_digest   = factory.grant_digest
run = HarnessAgentRun.create(
    state_root,
    contract,
    adapter_factory,
    tool_bridge_factory=factory,
)
```

The model-facing Tool deliberately omits `capability`, `workspaceId`, `context`, `requestId`, credentials, and authority references. Those values are caller-owned authority and are injected only after the Harness has durably committed the Tool intent and dispatch fence.

The effect path is:

```text
model Tool call
  -> durable Harness Tool intent
  -> durable dispatch fence
  -> Gateway execution.submit
  -> Runtime workspace.exec
  -> Gateway execution.get
  -> durable Harness receipt/observation
```

If the submit response is lost, Harness does **not** blindly redispatch the effect. Gateway `execution.resolve` performs a read-only lookup by the already frozen `clientRequestId`; only a unique owner Job is observed. Absent or ambiguous resolution remains unknown. The Gateway forwards the Harness authority references to Runtime but does not own or reinterpret them.

If execution control is cancelled or its deadline expires after the owner Job is known, the H2 bridge sends exactly one cooperative `execution.cancel` through Gateway. A non-terminal cancellation acknowledgement is durably recorded as `cancel-requested`, and the Run stops as `cancel_unknown` rather than claiming that the process was cancelled. A later resume reconciles the original request identity and observes the owner state; the Job may legitimately finish in another terminal state if cancellation lost the race. This mirrors the adopted MCP Tasks cancellation semantics: cancellation is a signal/ack, not proof of terminal cancellation.

This is an incremental compatibility path over the current Gateway execution projection. MCP 2026-07-28 defines a standard Tasks extension for long-running work; the current pinned Python SDK surface used here does not expose that extension through `Client`, so Harness does not hand-roll a competing MCP Tasks implementation. The custom Gateway lifecycle remains isolated behind this adapter and can be retired when the adopted SDK exposes the standard extension with the required recovery semantics.

### Supported Python Agent Run surface

### PostgreSQL-only independent CLI (fresh Run epoch)

The supported CLI now reuses the existing PostgreSQL HarnessStore port.
A new PG Run epoch does not implicitly import SQLite historical Run records.
Provide the SQL connection and optional selected Harness schema through the
operator-controlled environment, then use the standard CLI verbs:

```sh
export HARNESS_PG_DSN='postgresql://<operator-provisioned-private-role>'
export HARNESS_PG_SCHEMA=ordivon_harness_runs
ordivon-harness store-init
ordivon-harness doctor
ordivon-harness run /path/to/contract.json --message 'start'
ordivon-harness status HARNESS_RUN_ID
ordivon-harness resume HARNESS_RUN_ID --message 'continue'
```

The PostgreSQL DSN is operator-provisioned; `store-init` initializes only
the selected Harness schema/tables within that existing database. Without a DSN
the CLI fails without opening SQLite. The retired SQLite backup/restore CLI
subcommands are no longer exposed; use PostgreSQL-native backup and recovery
under the database owner's authority. No Provider effect,
Runtime physical execution, Host Work authority, or external domain completion
is inferred from a successful PG Store operation. The public Python Agent Run entrypoints now require PostgreSQL; Browserless materialization and installed Agent Automation versions still need their own production consumer qualification.

For PostgreSQL-backed Python execution, use `HarnessAgentRun.create(dsn, schema, ...)` and `HarnessAgentRun.open(dsn, schema, ...)` rather than composing Store, Continuity and Provider bridge manually. This is an intentional public API migration; old state-root arguments are no longer accepted. The caller still owns the exact Contract and Provider choice; Harness passes the persisted Contract to the caller-supplied Adapter factory before execution. On reopen/resume, Harness mechanically reconstructs Continuity and the exact Snapshot-bound Provider source.

```python
from ordivon_harness.api import HarnessAgentRun, DeepSeekTurnAdapter

import os

run = HarnessAgentRun.create(
    os.environ["HARNESS_PG_DSN"],
    os.environ.get("HARNESS_PG_SCHEMA", "harness"),
    contract,
    lambda exact_contract: DeepSeekTurnAdapter(
        settings, completion_contract=exact_contract.completion_contract
    ),
)
execution = run.run(({"role": "user", "content": "Start the bounded Run"},))

run = HarnessAgentRun.open(
    os.environ["HARNESS_PG_DSN"],
    os.environ.get("HARNESS_PG_SCHEMA", "harness"),
    contract.harness_run_id,
    lambda exact_contract: DeepSeekTurnAdapter(
        settings, completion_contract=exact_contract.completion_contract
    ),
)
execution = run.resume(
    additional_messages=({"role": "user", "content": "Additional caller input"},)
)
```

The Adapter factory is caller policy, not Harness policy. Static composition is admitted before durable Run creation: unsupported Tool/cognition/Runtime-binding combinations fail before the factory when the Adapter is irrelevant, and Adapter/model/structured-completion mismatches fail after the factory returns but before `harness.run-created`. This preflight does not probe Provider or Runtime liveness.

For Agent-owned durable cognition, the same surface accepts `HarnessCognitionProfile` plus an exact caller-authored `HarnessCognitionSeed`. Build seed sources with `HarnessWorkingViewSource`/`HarnessCognitionSeedSource`; Harness does not discover, rank or summarize them.

For already-selected cross-Run knowledge/procedure sources, the external application/Host/domain owns repository identity, discovery/ranking, semantic evaluation, canonical promotion, and any digest/currentness fence. After verifying one exact `HarnessWorkingViewSource`, it supplies that source directly as a `HarnessCognitionSeedSource`. Harness performs the normal Run privacy and WorkingSet admission only; there is no Harness reusable-reference/resolver/topology subsystem, and external procedure classification grants no Tool authority.

A Tool-bearing application normally supplies a `HarnessRuntimeClient` through the Python API; the explicit CLI Gateway profile now composes the same official MCP Client and existing Tool Bridge for `execution.linux` without adding another Runtime client. `call_tool()` is only the success-shape Protocol. The caller must also translate its transport and Runtime rejection failures into `HarnessRuntimeClientError` / `HarnessRuntimeToolRejected` with a `HarnessRuntimeErrorDetail`. In particular, a Runtime rejection with `commit_state` `not_started` or `not_committed` remains model-correctable; passing an unrelated client exception through unchanged loses that recovery meaning and is treated as a Harness failure. The recommended API exports `HarnessExecutionBinding` and the independent search catalog/grant digests required by the current `HarnessRuntimeBridge`. `HarnessExecutionBinding.runtime_references` accepts Runtime-native `foreignReferences` mappings directly (`namespace`, `type`, `id`, optional `generation`/`digest`); Harness no longer mints a duplicate Python reference value type.

Advanced integrations may opt a Run loop into bounded ToolProgram actions. When admitted, the Provider sees a Harness control action that can compose a linear sequence over only the exact Runtime/World Tools present on that `AgentTurnRequest`. Later step arguments may reference exact JSON values from prior observations; every inner step remains a normal physical Tool Call with the existing Tool budget, intent/fence/receipt, cancellation and UNKNOWN handling. Intermediate Tool content is consumed mechanically and is not replayed into model context; the next Provider turn receives one compact program result. This is not a new Runtime Tool, does not grant additional Tools, and is not a general code-execution surface.

When a caller needs a typed semantic result instead of free-form summary text, bind the result shape into the existing completion authority:

```python
from ordivon_harness.api import (
    DeepSeekTurnAdapter,
    HarnessRunContract,
    decode_structured_completion_result,
)

completion_contract = {
    "mode": "structured-result-v1",
    "resultKind": "my-domain-result",
    "resultSchema": {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "additionalProperties": False,
        "properties": {"choice": {"type": "string", "enum": ["a", "b"]}},
        "required": ["choice"],
    },
}
contract = HarnessRunContract(..., completion_contract=completion_contract, ...)
adapter = DeepSeekTurnAdapter(
    settings, completion_contract=contract.completion_contract
)
# after the Run, with a non-null conclusion:
value = decode_structured_completion_result(contract, execution.loop_result.conclusion)
```

Current authoring opts into local structural validation with the standard JSON Schema Draft 2020-12 `$schema` URI. Historical `structured-result-v1` Contracts that have neither `$schema` nor the retained legacy `conformancePolicy` remain provider-constrained but **not locally schema-verified**, preserving their exact behavior. The old `local-json-schema-draft-2020-12-profile-v1` token remains reader compatibility only for already-persisted Contracts; new examples do not mint it. Local Draft 2020-12 validation rejects structurally invalid Provider results before candidate completion through the existing model-correctable conclusion path. Provider-specific schema compatibility is an Adapter/provider concern rather than a Harness conformance ontology; the DeepSeek Adapter removes the local `$schema` annotation before embedding the caller schema into its function-tool parameters. Structural conformance still does **not** establish semantic correctness, evidence sufficiency, or caller/domain admission.

A candidate-completed Run may still carry explicit unresolved unknowns in
`unresolved_unknowns`; that means the bounded Run produced its candidate while
honestly reporting facts that remain unknown. The caller/domain, not Harness,
decides whether those unknowns block acceptance, justify another strategy, or are
irrelevant. Harness-owned execution stops such as `no_progress` do not synthesize
an Agent conclusion; inspect the stop code/detail and resume state instead. This
keeps a caller-bound structured completion result distinct from Harness execution
disposition.

The exact completion Contract is part of `HarnessRunContract.digest`. `StandaloneHarnessRunner` fails closed if a `structured-result-v1` Contract is paired with an Adapter that was not bound to the same completion Contract. DeepSeek receives the caller schema as the `submit_run_conclusion.result` Tool schema. Harness carries the returned JSON in the optional versioned `AgentRunConclusion.structured_result` field, whose canonical value is explicitly bounded to one MiB; the ordinary `summary` remains compact human/control metadata containing only the result digest. When model-content retention is authorized, the existing terminal conclusion CAS object durably stores the carrier—there is no second result store and no Host-specific result type. `decode_structured_completion_result` reads the carrier first and remains backward-compatible with historical results encoded directly in `summary`; when the local conformance policy is bound it also enforces the same mechanical schema check. **Caller/domain verification remains mandatory**: a result carrier and local schema conformance are not semantic admission.

## Gateway Tool CLI（R45/R46：复用现有 MCP/Tool Bridge）

默认 `ordivon-harness run` 仍只执行原来的 no-Tool Run。启用 `execution.linux` 须显式提供原始 PostgreSQL Run Contract、实际 Gateway MCP 服务、已有 Workspace 和可执行程序；不自动继承运行者的额外权限。

R46 修复实际 DeepSeek API 拒绝模型工具名 `execution.submit` 的消费者断点：模型只看到符合 OpenAI/DeepSeek Chat Completions 命名规则的 `execution_submit`；已有 Gateway MCP 物理工具仍为 `execution.submit`，既有 PG Intent/Fence/Owner Receipt 不变。现役本机 Gateway 可使用**已有**的精确 `http://127.0.0.1:<port>/mcp` LoopbackMcpEndpoint 与第一方私有 Bearer 文件；其他 HTTP 地址一律拒绝，外部 Agent Plugin 仍必须 HTTPS。

按需执行一个真实 DeepSeek → 本机 Gateway → Linux Runtime → 同一 PostgreSQL Run 的付费物理验收：

```bash
HARNESS_PG_TEST_DSN='<dedicated-test-DSN>' \
HARNESS_REAL_GATEWAY_TOOL_TEST=1 \
HARNESS_REAL_GATEWAY_URL='http://127.0.0.1:8899/mcp' \
HARNESS_REAL_GATEWAY_BEARER_TOKEN_FILE='/path/to/existing/private-client-token' \
HARNESS_REAL_GATEWAY_WORKSPACE_ID='ws-existing-operator-selected' \
  uv run --locked python -m pytest -q \
  tests/test_gateway_cli_consumer.py -k live_deepseek_gateway_tool
```

该验收通过原有 `pg_schema` fixture 使用独立临时 Schema；普通 CI/Owner `queue` 不会触发真实外部 API。只有明示配置的测试节点才调用模型并执行单条 `/usr/bin/python3 -c print(...)`；验证原 PG ToolStep、物理 Gateway Owner Receipt 与独立 CLI 再读取，**不**把物理完成当作用户领域 TaskSolved。

先读取当前 Tool Schema 和当前授权工具摘要，不连接 PostgreSQL、不创建 Run：

```bash
ordivon-harness gateway-profile \
  --gateway-url https://YOUR-GATEWAY.example/mcp \
  --gateway-bearer-token-file /private/gateway-bearer \
  --gateway-workspace-id YOUR-EXISTING-WORKSPACE \
  --gateway-executable /usr/bin/python3 \
  --gateway-max-timeout-ms 300000
```

输出的 `toolCatalogDigest` 和 `toolGrantDigest` 必须由 Caller 原样写入普通 `HarnessRunContract`，不得让 CLI 隐式修改来源授权。使用同样的选项运行已绑定 Contract：

```bash
ordivon-harness run ./authorized-gateway-contract.json \
  --message 'Use the caller-approved tool to inspect the task' \
  --gateway-url https://YOUR-GATEWAY.example/mcp \
  --gateway-bearer-token-file /private/gateway-bearer \
  --gateway-workspace-id YOUR-EXISTING-WORKSPACE \
  --gateway-executable /usr/bin/python3 \
  --gateway-max-timeout-ms 300000
```

暂停 Run 的 `resume` 同样显式传递这一组配置并通过当前 Source Tool 校验。可选 `--gateway-env-variable NAME` 和 `--gateway-context NAME`，复用已有 `PluginGatewayExecutionGrant`。官方 MCP 客户端来自现有 `ordivon-harness[mcp]`；私有 Bearer 文件通过原有读取器使用，不会进入 Run Contract、PG 对象或模型上下文。

**证据边界：** R45 的真实一次性 PG18 5/5 消费者测试使用脚本化模型和测试 Gateway MCP；其中一次由测试 Gateway 客户端在已提交的原始 PG Tool Intent/Fence 后实际运行 `/usr/bin/rg` 并将 Owner 观察提交到同一 Run。它不是现役 Gateway 服务的远程 Tool 调用，也不能与 R44 独立的真实 DeepSeek/真实 Gateway 两条链路混同。当前生产仍缺少跨自然 Owner 的完整同 Run Issuer/物理接收与独立 DomainVerifier 验收。

### 2026-11-16 Real Coding Agent single-business acceptance (candidate, not release)

On source candidate `a2d5a30a40c57b299e9b203b531e93f0511c35da`
(Draft PR #2311), a **real DeepSeek Flash model** used the existing
`execution_submit` Gateway Tool three times in one original scratch
PostgreSQL 18 Run. The caller provided a separate ephemeral Git Workspace
containing only `SPEC.md`, `feature_flags.py` and `test_feature_flags.py`;
the canonical hidden `HARNESS-EDIT-ADDRESSING-002` verifier and reference
oracle were never included in the model-visible Git source.

- Provider: four real model calls, 9,452 total tokens, no provider retries.
- Gateway/Runtime: three physical Tool calls, original PG Tool Receipt `observed`.
- Candidate Run: `completed` / `candidate_completed`, never treated as a
  substitute for independent domain acceptance.
- Independent verifier: **visible PASS and hidden PASS**, with only
  `feature_flags.py` modified (`alpha_enabled=False`, `beta_enabled=True`).
- One observed trial elapsed 9.94 seconds; not a benchmark distribution
  and not evidence that this candidate is installed in production.

The source-equivalent CLI smoke also passed a real DeepSeek → installed
Gateway → Runtime → original PostgreSQL Run and fresh status readback.
Both are deliberately opt-in, billable consumer checks; ordinary CI remains
scripted/offline. Retain the real SourceCut and the independent verifier
as distinct authorities. No second Journal, editing framework, or token
reader is introduced by this acceptance.
## Pause and resume

```bash
ordivon-harness \
  resume HARNESS_RUN_ID --message 'Additional caller input'
```

### R46：Tool 结果不确定时保留可恢复的原始 Run

当 `execution.submit` 已有 PG Tool Intent/Fence、真实 Owner 可能已经执行、但回复/查询失败时，
原有 `HarnessToolStepReceipt` 记录 `unknown`。此前 Python Harness 在这里把 `runtime_unknown`
写为 `harness.run-stopped`，后续 CLI `resume` 会拒绝这个终态 Run。

现在只有**当前原始 ToolStep 是 UNKNOWN，且成功提交了 `harness.run-paused`** 时，
才沿用已存在的 `HarnessRunPauseReason.EFFECT_DISPATCH_PENDING` 和同一个原始 Tool Intent。
其 Snapshot 维持派发前的 Tool Batch 游标，UNKNOWN 仅保存在 Tool Receipt，不能把它当成
已经消费的 Tool Observation。调用者在 Owner 可查询后通过同一 Run `resume`，
Harness 使用原有 `execution.resolve/get` 对账，不额外执行 `execution.submit`。

其他没有原始待对账 Tool 的 `runtime_unknown` 仍按原先的停止语义处理；
此修复不新增重放缓存、Runtime Writer 或授权系统。真实一次性 PG18 测试使用
脚本化模型和可模拟回复丢失的 Gateway MCP 测试客户端，验证一个 Run 内先暂停再
Owner 对账完成、物理 Tool 请求提交次数严格等于 1。这不是已安装 Gateway 的
端到端验收，也不是 Agent 业务结果已被独立 DomainVerifier 接受。

### R45 installed Owner response-loss qualification (2026-11-16)

A separate opt-in regression now exercises an **actual** authenticated Gateway
and Linux Runtime, not just the scripted Gateway used by normal CI. The
client deliberately discards the first genuine `execution.submit` response
and temporarily makes `execution.resolve` unavailable. The original
PostgreSQL Run must persist an `effect-dispatch-pending` Pause. Reopening
the same Run reconciles the one original Owner Job; it never submits another
physical effect.

The standalone test uses an existing Bearer client file, a separately admitted
Workspace and a disposable PostgreSQL 18 database/schema. Its Provider is
`ScriptedTurnAdapter` to avoid charging for a fault-injection test; it is
**not** a model quality or semantic TaskSolved claim. Run only on an explicitly
qualified node:

```bash
HARNESS_PG_TEST_DSN='<disposable-postgresql-18-DSN>' \
HARNESS_REAL_GATEWAY_UNKNOWN_TEST=1 \
HARNESS_REAL_GATEWAY_URL='http://127.0.0.1:8899/mcp' \
HARNESS_REAL_GATEWAY_BEARER_TOKEN_FILE='<existing-private-bearer-file>' \
HARNESS_REAL_GATEWAY_WORKSPACE_ID='<separate-existing-workspace>' \
  uv run --locked python -m pytest -q -s \
  tests/test_live_gateway_unknown_recovery.py
```

Original-source result for merged `acbb494a3d9f8c811093a0eab1b1c16e33f2bdfc`:
native verification Job `job-01a1e0fe-e3cb-75ca-bb68-6319b1d70c4c`
reported 1 PASS; real Runtime Owner Job
`job-01a1e0fe-f7cd-740f-9d2e-56ca9b8152a3` was admitted exactly once,
reconciled from the original PostgreSQL Intent and then independently
resolved again by the official Gateway client. This is a single bounded
scenario, not a production failure-rate or liveness guarantee.

### 2026-11-16 R4: live autonomous coding task and hidden-domain acceptance

On exact main source `659e526e60bd6bf02ed068fa92be49819a12e4c4`,
one independent DeepSeek Flash autonomous coding task used the installed
authenticated Gateway (`execution.linux`) and native Linux Runtime in one
disposable PostgreSQL 18.7 Harness Run. The model-visible Git Workspace
contained only the three public `HARNESS-EDIT-ADDRESSING-002` task files,
never the hidden verifier or reference oracle. The Agent first read the
source, then changed `feature_flags.py`, then ran its public unittest.

- 4 genuine model calls; 3 original physical Owner tool calls; 9,550 total tokens.
- Original PG Run `harness-run:real-coding-r4-c4cc2d5ff6e340c5`: `completed`;
  latest physical ToolStep Receipt `observed`, independent Gateway Owner
  `execution.get` confirmed native Job/exit0/delivery committed.
- Independent domain verifier: public test **PASS**, hidden QA **PASS**;
  only `feature_flags.py` modified, `SPEC.md` and test unmodified.
- Live source test Job: `job-01a1e2f7-73d7-721e-a9be-944da28967dd`,
  `1 passed in 15.59s`. Evidence summary:
  `evidence/r4-real-coding-deepseek-gateway-postgres-hidden-qa-20261116.json`.

To reproduce, supply a fresh separate Git Workspace containing only the
three public fixture files, an existing first-party Gateway bearer file,
an existing DeepSeek secret file, and an isolated scratch PostgreSQL 18 DSN.
Then explicitly run the opt-in `tests/test_live_coding_task_r4.py` with
`HARNESS_REAL_CODING_TASK_R4=1`, `HARNESS_REAL_CODING_WORKSPACE_ID`,
`HARNESS_REAL_GATEWAY_URL`, `HARNESS_REAL_GATEWAY_BEARER_TOKEN_FILE`,
`HARNESS_REAL_DEEPSEEK_SECRET_FILE`, `HARNESS_PG_TEST_DSN` set.
Ordinary CI skips this test; it does not mint credentials or charge models.

The verified result is one genuine Domain TaskSolved case, **not**
a statistical success rate and **not** a machine-checked Rust production
AgentLoop refinement. The original PG18 scratch server was removed after
the test, while the retained native Owner Jobs and source/QA evidence can
be independently re-observed. `candidate_completed` alone is not TaskSolved.

## Recovery

Inspect the exact durable Run first, then resume only through the normal execution path when its concrete Provider/Runtime boundary admits that action:

```bash
ordivon-harness inspect HARNESS_RUN_ID
ordivon-harness resume HARNESS_RUN_ID --message 'Additional caller input'
```

Harness does not maintain a generic `recover` command or write a second Recovery Assessment. Provider/Tool response loss is reconciled by the existing durable call/intent identities and the concrete owner that can observe the physical effect. An ambiguous physical outcome is never converted into safe redispatch merely by an operator projection.

## Python API

Use `ordivon_harness.api` for applications. Advanced persistence/continuity composition imports the explicit caller-neutral owner modules directly; the duplicate `ordivon_harness.core` aggregation facade is retired, and the current package does not ship a Host-specific external adapter.

### Durable Tool physical handoff — source boundary

Harness persists the exact original Runtime request digest in the Tool
Intent before dispatch. For workspace.exec, it appends one V2 DispatchFence
reference only after the Run Store has committed the prepared Event.
Immediately before calling the existing Runtime/Gateway adapter, the
_require_exact_owner_effect_handoff guard checks the original request SHA
against the durable Intent and checks that outgoing request differs
ONLY by that exact Fence reference. This guards post-Journal lowering,
adapter and reference drift. It does NOT grant execution, renew an expired
Fence, replace Runtime's principal-scoped (principal, clientRequestId)
durable idempotency key, imply that job.observe means physical success,
or permit blind retry after UNKNOWN. The Rust migration's read-only
matching consumer is b-loop-probe::owner_effect_handoff and consumes
the same Python/PG18 fixture. Physical Owner admission remains separate.
