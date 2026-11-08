# Harness Capability and LEGO Guide

**Scope:** source-bound navigation for `services/harness`. This is not a new capability registry or a replacement for `README.md`, `ARCHITECTURE.md`, `docs/STATUS.md`, or native verification. A filename indicates implementation presence, **not** a deployed or currently admitted capability.

## How to use (Human)

1. Choose the desired outcome: a bounded Agent Run, tool action, recovery, browser/human interaction, or analysis. The caller/Host/domain must define the actual Task acceptance criteria.
2. For a fresh Run, start at `docs/QUICKSTART.md`; supply a concrete `HarnessRunContract` plus Provider adapter. For Tool-bearing Runs, provide a real `HarnessRuntimeClient` and exact Tool grants.
3. For first-party CLI Run state, use a provisioned PostgreSQL database and `HARNESS_PG_DSN` (optional `HARNESS_PG_SCHEMA`). Use `ordivon-harness doctor`, `status`, `inspect`; never infer domain completion from a Run receipt. The legacy Python package continues to expose SQLite paths pending consumer retirement.
4. When interrupted, inspect committed Run state and exact Tool/Provider evidence. An UNKNOWN external effect needs reconciliation with its owner; do not simply click Run again.
5. For changes or releases, inspect `mise tasks ls`; run affected tests and independent PG integration/fault verification, compare committed vs installed revisions and observe the real consumer before declaring success.

## How to use (Agent)

1. Receive an exact Run contract and current user/domain context. Do not select a generic strategy/control plane that replaces caller authority.
2. At each turn distinguish **installed mechanisms → Run-admitted authority → turn-admitted actions**. Act only on the final stage, including real Tool budgets.
3. Keep source truth, selected cognition, transient Tool exchange and historical Journal distinct. Only explicitly selected WorkingSet sources count as durable model-visible cognition.
4. If using `HarnessToolProgram`, bind only exact current-turn Tools; each inner step is a physical Tool Call. Reference earlier observed structured values with `observation_ref(step_id, *path)`; after a failed/unknown step, stop later effects.
5. If a Provider or Tool response is ambiguous, preserve UNKNOWN and reconcile by receipt identity. CompletionProposal means only a bounded candidate; the caller/domain decides semantic acceptance.
6. Report provenance and currentness: SOURCE/IMPLEMENTED vs TESTED vs MERGED vs INSTALLED vs EXECUTED, never conflating these states.

## Foundation responsibilities (capability LEGO candidates / implementation map)

| Responsibility | Source / consumer boundary | Implementation status |
| --- | --- | --- |
| Run contract & admission | `core_contracts.py`, `agent_run.py` → caller | existing implementation |
| Model turn & provider adaptation | `ordivon/model.py`, `ordivon/loop.py`, `ordivon/provider_lifecycle.py` | existing implementation |
| Current cognition projection | `working_view.py`, `ordivon/cognition_admission.py` | existing implementation |
| Tool admission & observation | `ordivon/turn_projection.py`, `ordivon/tool_bridge.py` | existing implementation |
| ToolProgram contract | `tool_program_contract.py` | existing pure implementation |
| Observation reference resolution | `tool_program_resolution.py` | isolated pure implementation; no effect rights |
| ToolProgram execution/recovery | `tool_program.py`, `tool_program_recovery.py` | bounded existing implementation |
| Persistence & lease fencing | `postgres_store.py`, `store.py`, `store_ops.py` | PG-first CLI; full Python consumers not yet retired |
| Physical execution binding | `execution_binding.py`, `runtime_port.py` | Runtime owns effect truth |
| Structured result validation | `structured_result_conformance.py`, `completion.py` | structural-only; domain validates meaning |
| Provider/external adapters | `gateway_execution_port.py`, `mcp_http_client.py`, `plugin_mcp.py` | cross-owner ports; no automatic authority |
| Human interaction & browser | `scripts/browserless_*.py`, `scripts/cft_human_*.py`, `systemd/` | deployment-dependent, verify loaded units |

These are **responsibility candidates**, not formal R2.1 declarations. A declared LEGO needs the full `ell=(I,O,S,pre,post,inv,eff,c,epsilon,prov,unfold)` contract with grounded field values and current consumer verification.

## One R2.1 architectural LEGO contract: observation-reference resolution

**Identity:** `harness.tool-program-observation-resolution`, architectural responsibility, source-scoped DECLARED (not model-proved or installed-current). Natural Owner: Harness. Current consumer: `HarnessToolProgramExecutor.execute()` after ToolBridge produces a previously observed step.

This uses an **exact typed pure-function contract**, not a separate registry, per-file LEGO designation or execution authority. The eleven R2.1 coordinates are:

| Coordinate | Explicit representation |
| --- | --- |
| `I` | `(template: JsonValue, observations: Mapping[StepId, HarnessToolObservation])`; `StepId` comes from the validated versioned ToolProgram contract |
| `O` | `Result[JsonValue, ValueError]`; success is an exact resolved JSON value, invalid/missing/unobserved reference is an error |
| `S` | `Unit` (no mutable owned state; observations are read inputs) |
| `pre` | `template` is valid JSON; every reference marker is a versioned `$harnessObservationRef` with valid prior `stepId` and nonempty structural path; resolution does not admit a Tool |
| `post` | Every successful marker resolves to the corresponding exact previously observed structured value; missing/non-observed step and missing/index-out-of-range path raise `ValueError`, never fabricate a result |
| `inv` | No arbitrary expression evaluation, interpolation, implicit Provider/Runtime call, mutation of Tool authority, or reference to a future/unobserved step |
| `eff` | `Pure` / `∅` external effects; this operator cannot dispatch a Tool |
| `c` | `UNKNOWN(ResourceCost; reason=not yet benchmarked, scope=actual input size/JSON depth and program composition, obligation=measure bounded consumer profile)` |
| `epsilon` | `Exact[CanonicalJSON]` (claimed exact substitution, no semantic approximation); implementation refinement proof is `UNKNOWN` pending independent execution |
| `prov` | Baseline `fc0fbfdf43c5`; extracted from `tool_program.py` into `tool_program_resolution.py` in Workspace `ws-gpt6-harness-modular-audit-20261107-r1`; tests authored but `NOT_RUN` while Runtime concurrency is exhausted |
| `unfold` | `_resolve_template` → `_is_observation_ref` / `_parse_observation_ref` → `_lookup_path`; exact consumer `HarnessToolProgramExecutor.execute`; tests `test_tool_program_resolution.py`, `test_p2_tool_program.py` |

**Current acceptance status:** interface/source separation completed; executable regression, actual PG integration, current-HEAD integration, deployment and domain acceptance are independent, unclaimed obligations. A source extraction is not a theorem. To falsify the contract, try an unavailable path, a future/unobserved step, adversarial mutable input and a ToolBridge that returns a nonmatching observation.

## R2.1 architectural LEGO: bounded ToolProgram effect control

**Identity:** `harness.bounded-tool-program-effect-control`. Natural Owner: Harness.
Source-scoped **DECLARED**, not MODEL_PROVED/CODE_REFINED/INSTALLED_CURRENT.
Actual caller: Agent model turn with one admitted `HarnessToolProgram`; physical
effect truth remains with the ToolBridge's Runtime/Gateway/external owner.

| R2.1 coordinate | Typed source-bound meaning |
| --- | --- |
| `I` | `(program: HarnessToolProgram, admittedTools: tuple[AgentToolDefinition,...], remainingToolCalls: Nat, stepPrefix: NonemptyStr, bridge: ToolBridge)` |
| `O` | `Result[HarnessToolProgramResult, ValueError/BridgeError]` plus exact observed physical Tool Call trace; result status may be completed/rejected/unknown/cancel-requested/cancelled |
| `S` | `(phase, stepCursor, remainingBudget, issued, observed, stopStatus, firstNonObservedStep)`; `ToolProgramSafetyR1.tla` abstracts the relevant finite transitions |
| `pre` | Complete versioned program deep-snapshotted and revalidated; every program Tool in exact turn grant; `len(steps) <= remainingToolCalls`; no dynamic Tool grant from installed capability |
| `post` | Each bridge invocation has one exact step identity; success only after all observations; first non-observed outcome stops before later steps; invalid program/budget/tool grant is rejected before effects |
| `inv` | `issued <= remainingToolCalls_initial`, `observed <= issued`, dispatch order is program order, UNKNOWN does not imply no physical effect, no hidden grant escalation |
| `eff` | Each issued `ToolBridge.execute` may have irreversible external effect; **no atomic rollback**; output-template resolution alone has no new external Tool effect |
| `c` | `physicalCalls <= min(len(program.steps), remainingToolCalls_initial)` when admitted; bounded program size is already enforced; external latency/cost remains typed `UNKNOWN[ExternalCost]` pending owner measurement |
| `epsilon` | `Exact[AbstractOrderingAndAccounting]` under a conformant identity-preserving ToolBridge; broader Python/Runtime refinement remains `UNKNOWN[Refinement]` until native TLC and executable tests run |
| `prov` | `fc0fbfdf43c5` source baseline; `ToolProgramSafetyR1.tla`, `tests/test_tool_program_model_refinement.py`; current candidate Workspace `ws-gpt6-harness-modular-audit-20261107-r1` |
| `unfold` | `tool_program_contract.HarnessToolProgram` → `HarnessToolProgramExecutor.execute` → `ToolBridge.execute` → `HarnessToolObservation`; optional `tool_program_recovery.py` and Runtime effect reconciliation outside the abstract state machine |

The formal model checks **sequential accounting and stop barriers**, not general
Tool idempotency, delivery, language-model cognition, serializable PostgreSQL
transactions or domain completion. An abstract truth without a concrete
refinement map cannot retire a physical consumer check.

### Observation snapshot law

`HarnessToolObservation.structured_content` is a mutable convenience view;
the durable canonical bytes and `observation.digest` are authoritative.
ToolProgram reference resolution must therefore use the sealed
`observation.to_dict()["structuredContent"]` projection, **not** the mutable
view. This prevents a subsequent Tool Call from receiving a value inconsistent
with the persisted evidence digest. The focused negative case is
`tests/test_tool_program_resolution.py::ToolProgramResolutionTests::test_mutable_observation_projection_cannot_redirect_next_tool`.
Source-equal isolated component tests have passed; the native package and
real ToolBridge acceptance still require independent verification.

## R2.1 pure decision LEGO: Run deadline and Provider retry

The former 2,121-line `OrdivonAgentLoop._run` mixed coordination with
side-effect-free deadline arbitration and retry selection. The production
loop now consumes two stateless, source-local operators; it still owns
Provider lifecycle, dynamic clock reads and physical dispatch. Neither
operator allocates a Job, grants a Tool, or independently retries an effect.

| R2.1 coordinate | `select_run_deadline` | `pre_dispatch_retry_permitted` / `bounded_retry_delay_ms` |
| --- | --- | --- |
| `I` | exact active budget, previous elapsed time, wall/monotonic observations, optional absolute deadlines | failure class and dispatch safety, used/allowed retries, cancellation, remaining time, one-based retry index |
| `O` | `SelectedRunDeadline` (expiry, effective budget, source, assignment remainder) | candidate eligibility and bounded backoff milliseconds |
| `S` | empty: all inputs passed explicitly | empty: all inputs passed explicitly |
| `pre` | caller supplies actual observed clocks and Run-authorized budgets | caller supplies actual error classification and Run retry budget |
| `post` | earliest deadline wins; assignment wins active-budget ties; external wins internal ties | only pre-dispatch-safe transport/unavailable failures can be retry candidates; delay is capped and cannot outlast remaining budget |
| `inv` | no deadline expands the available run time; original tie order preserved | ambiguous physical dispatch never becomes retry safe; clock/deadline checks are skipped when the prior eligibility gate rejects |
| `eff` | none | none |
| `c` | bounded O(1) arithmetic and memory | bounded O(1) classification and capped arithmetic |
| `epsilon` | `Exact[FiniteDifferentialDomain]`; `UNKNOWN[AllIntegerInputs]` | `Exact[FiniteDifferentialDomain]`; `UNKNOWN[UnboundedImplementation]` |
| `prov` | original `ordivon/loop.py` baseline `fc0fbfdf43c5`; candidate source not released | same exact baseline; no Provider retry guarantee beyond the admitted dispatch classification |
| `unfold` | `ordivon/run_deadline_selection.py` → `ordivon/loop.py` → `tests/test_loop_decision_operators.py` → `tests/test_loop_decision_consumer.py` | `ordivon/provider_retry_policy.py` → same loop and tests |

**Human:** Inspect the actual `OrdivonAgentLoop._run` call sites, the pure
deadline/retry operators, and the tests above. Before changing a priority,
preserve the original external/deadline tie behavior and prove the real
consumer still rejects an expired run before Provider dispatch. Before
changing retry, distinguish `PRE_DISPATCH_SAFE` from
`DISPATCH_AMBIGUOUS`; the latter must not be redispatched.

**Agent:** Resolve the natural source Owner first. Change pure operator
semantics in one place; retain lazy `control.remaining_ms` and assignment
deadline reads *after* the retry eligibility gate in the effectful loop.
Evaluate concrete input/output equivalence and run the actual loop consumer.
Do not infer external-effect idempotence from a pure function proof. Unknown
counterexamples stay typed `UNKNOWN`, not success.

**Verification standing (2026-11-08):** Windows Python 3.12.13 ran
11/11 focused pure + real-loop tests, and a wider 15-module set yielded
106 passed / 3 legacy SQLite Windows-only failures (`os.O_NONBLOCK`),
95 passing subtests. Separate Provider/ToolProgram/transport suite yielded
20 passed. These scopes overlap: do not add their counts. Project-pinned
Python 3.15.1, real PostgreSQL integration, native TLC and installed
consumer read-back remain `NOT_RUN` for this candidate.

## Formal safety model and real executor trace boundary

The existing Harness TLC toolchain can check `formal/ToolProgramSafetyR1.tla` with
`mise run formal:tool-program`, which uses three intentionally false reachability
probes. The model binds one three-step program, permitted/denied admission,
budgets 0–3, observed and non-observed outcomes. It does not claim actual
ToolBridge effects, domain success or global Python refinement.

`tests/test_tool_program_model_refinement.py` contrasts 1,000 bounded
admission/budget/status combinations against the actual
`HarnessToolProgramExecutor` and recorded ToolBridge invocations. This is
a stronger *finite implementation trace* check than a single isolated
UNKNOWN test, but still not an unbounded proof. Keep the original
Provider/Runtime/PG consumer checks until the abstraction/realization
boundary has been validated. See `docs/VERIFICATION.md` for the exact
evidence ladder and retirement rule. **TLC and project-pinned Python 3.15.1 remain NOT_RUN**.
The independent Python 3.13 six-method stubbed-component check passed;
a subsequent Windows Python 3.12 real-package run also passed all six
methods and all 1,000 finite ToolBridge traces. Neither establishes an
installed release or external Tool effect proof.

## Thought LEGO: reusable invariants

- **History ≠ cognition:** persistence does not imply that the Agent must see the record on every turn.
- **Observation ≠ selection:** a read Tool does not automatically add a source to durable WorkingSet.
- **Intent ≠ effect ≠ completion:** a valid action proposal does not prove physical delivery or Task acceptance.
- **UNKNOWN ≠ failure:** a dropped response cannot authorize blind resending of effectful Tools.
- **Authority is turn-relative:** an installed tool never grants itself permission to act.
- **A correct model answer is not evidence authority:** final completion remains with the domain/caller.
- **Refinement before equivalence:** a formal state model's PASS is not implementation equivalence without a verified refinement map.

## External mature substrates: reuse decisions, not imported competing frameworks

| Mature source | Relevant pattern | Harness decision / qualification |
| --- | --- | --- |
| [OpenAI Agents SDK](https://openai.github.io/openai-agents-python/) | narrow Agent/Runner/tool/trace interfaces | reference for minimal interfaces and tracing; no parallel Agent Runner without real consumer |
| [LangGraph persistence](https://github.com/langchain-ai/docs/blob/main/src/oss/langgraph/persistence.mdx) | per-thread checkpoints vs cross-thread Store | preserve Harness Run continuity separately from domain knowledge; don't reimplement generic Store |
| [Temporal Workflow](https://docs.temporal.io/workflows) | durable history, deterministic replay, side effects in Activities | reuse existing Temporal worker for cross-Run scheduling, not for re-owning Harness Provider/Tool truth |
| [Anthropic Claude Agent SDK](https://github.com/anthropics/claude-agent-sdk-python) | sessions, hooks, tool permissions | adapter/consumer candidate only after actual provider + execution contract qualification |
| [MCP specification](https://modelcontextprotocol.io/specification) | interoperable tool schemas/results and transport | prefer SDK/protocol; keep scope-bound authority and UNKNOWN reconciliation |
| [OpenTelemetry](https://opentelemetry.io/docs/) | traces/spans and causal context | use existing OTel sink; trace data is evidence, not the durable Run Journal |

**Adoption sequence:** discover external project → identify unmet capability and owner-native consumer → check license/version/maintenance/trust → compare semantics and fault boundaries → run a representative differential or integration test → adopt through owner dependency/lockfile → independently verify installed consumer. Discovery alone is not adoption.

## Directory audit, normalization, retirement

| Directory | Current purpose | Decision |
| --- | --- | --- |
| `src/` | executable contracts, loop, ports, persistence | KEEP; extract only real cohesion boundaries; `tool_program_resolution.py` is pure separation |
| `config/` | model/browser/automation config and evaluation datasets | KEEP; distinguish deployed inputs vs corpus data |
| `scripts/` | entrypoints, deployment and research helpers | REVIEW per reference and installed service before deletion |
| `systemd/`, `containers/` | deployment manifests | KEEP until installed unit/container consumer audit |
| `schemas/` | machine-readable contracts | KEEP where validated/consumed |
| `formal/` | bounded TLA+ models/probes | KEEP as independent model evidence, not universal proof |
| `tests/`, `evals/`, `fixtures/` | implementation validation and benchmark inputs | KEEP consumer-qualified cases; prune superseded artifacts after coverage comparison |
| `research/`, `planning/` | historical hypotheses and LEGO planning | REVIEW historical authority/current pointer before moving/removing |
| `evidence/` | exact evidence artifacts | KEEP where indexed/digest-cited; no age-only delete |
| `docs/`, `.ordivon/`, `.github/` | current guidance, publication and release configuration | update current docs; do not rename paths before reference checks |

### Current backend-neutral owner split and residual naming debt

**Post-rebase consumer inspection at `4ec1ba906`:** The upstream
Harness changes have already retired `ordivon/sqlite_run_store.py`,
`ordivon/sqlite_agent_bridge.py` and
`ordivon/sqlite_runtime_bridge.py`. Do **not** recreate these modules
or tell Agents to migrate their former consumers a second time.

| Exact current code | Owner responsibility / consumer evidence | Next safe step |
| --- | --- | --- |
| `ordivon/run_continuity.py` / `EventSourcedRunContinuity` | backend-neutral Run continuity; consumed by `agent_run.py` and PG CLI `independent_cli.py` | Keep the canonical behavior; verify its PG persistence and recovery consumers |
| `ordivon/agent_bridge.py` / `HarnessAgentBridge` | backend-neutral Agent and Tool authorization bridge | Keep; no SQLite-named forwarding wrapper |
| `ordivon/runtime_bridge.py` / `HarnessRuntimeBridge` | backend-neutral Runtime Tool integration, consumed by `agent_run.py`, `plugin_gateway_effect.py` and `adaptive_edit_bridge.py` | Keep effects with Runtime, not a second Harness dispatcher |
| `sqlite_store.py` / `SQLiteHarnessStore` | still imported by `agent_run.py` and `ordivon/continuity_guards.py`; direct-Python consumers remain | Retire only once corresponding PG/native consumers and recovery qualify |
| `independent_cli.py` | current first-party PostgreSQL CLI, old name | Consider `run_cli.py` only if public entrypoints and all imports can change atomically |
| `ordivon_harness/ordivon/` | existing Python import namespace with real consumers | Keep until proved safe; avoid alias-only reorganization |
| `anc_canonical` | canonical evidence/digest codec currently consumed by issued wire values | Keep exact identities; do not rename without protocol/byte evidence |
| Browserless `sqlite_*.py` scripts | separate materialization, wake and effect consumers with mixed backing stores | Determine installed worker consumers independently of PG-only Run CLI |

**Consumer-ranked deletion:** The remaining `sqlite_store.py`, its
direct Python API and browserless SQLite paths require source, installed-worker
and native PG readback evidence before deletion. Old H1/H5 research materials
can retain historical names without becoming active code. No disposable
Runtime SQLite data migration is required by this audit. The evidence index
must not be treated as a backup of active run state.

**Safe cleanup:** inspect `git status --short`, `git clean -ndX -- services/harness`, `git grep -n` and current unit/entrypoint references. Delete only confirmed ignored generated files inside this owner root, or tracked files with zero active consumers and verified replacement. System directories, external state roots, databases and other agents' workspaces are out of scope. Avoid unexplained abbreviations/new aliases; prefer full terms such as `tool_program_resolution` and keep wire IDs stable unless versioned intentionally.
