# Agent Concepts — Formal-First × LEGO-First (source-bound vocabulary, 2026-10-24)

Status: SOURCE-BOUND SHARED VOCABULARY for new Agent onboarding and architecture decisions; NOT a live-state authority, executable policy, Skill, registry or universal schema. Reconfirm actual behavior with the natural owner.
Initial definition anchored to origin/main SourceCut: 734af8a7368496754178c0a2c2018ca54ed0555e. Repository vocabulary only; deployment and current owner semantics require direct observation.
Consumer: Ordivon system decomposition, first-contact navigation, Harness/Runtime boundary design and Agent work-contract design.
Reuse existing owner truth: AGENTS.md; services/harness/docs/authority.md; services/runtime/formal/RuntimeDispatchR1.tla; scoped project Skill project-ordivon-next/recursive-lego-calculus if actually discoverable. Do not replace them.

## Decision

Distinguish dimensions, not brands. Formal-First states the behavioral obligations and evidence scope. LEGO-First discovers a smallest replaceable, goal-conditioned responsibility. Models, skills, tools, harnesses and runtimes are concrete mechanisms implementing or consuming these responsibilities, not additional universal top-level owners.

A LEGO is NOT synonymous with a file, package, agent, tool, skill, runtime object or MCP server. For a needed responsibility name identity, responsibility, inputs, outputs, behavioral contract and acceptance. Only add authority/effects/state/provenance where they change the real decision.

## Minimal new-Agent decision boundary

- **Goal:** the user's/domain's acceptance condition; model output is not evidence that it happened.
- **Tool:** callable owner operation with defined input/output/effects; neither tool listing nor Skill reading grants effect authority.
- **Skill:** progressive disclosure of how and when to use existing capabilities; no automatic executor or permission.
- **Agent:** makes decisions where rules or plans are not fully known; its proposals are not committed facts.
- **Harness:** assembles context and model/tool turns; successful Run is not successful business effect.
- **Runtime:** exact physical Job and Attempt standing with durable admission, dispatch, and recovery; not semantic Work completion.
- **Host Work:** only if a goal requires persistence across Agent runs; never infer it from a Session or MCP Task.
- **LEGO:** consumer-conditioned responsibility with contract, inputs/outputs and acceptance, not a synonym for Tool/Skill/Agent.
- **Formal:** define and check invariants and obligations where they matter; finite checking does not prove unrelated implementation behavior.

**Default:** Known operation → direct deterministic Tool. Uncertain operation → bounded Agent/Harness proposes a path. Both → exact owner execution boundary → scoped Formal check plus real consumer acceptance. Do not build a new common scheduler or universal LEGO registry for this diagram.

**Frequent category errors:** `ToolDiscovered != Authorized`; `SkillLoaded != Executed`; `RunSucceeded != GoalSatisfied`; `RuntimeJobTerminal != BusinessAccepted`; `MemoryRetrieved != CurrentTruth`; `MCPTask != RuntimeJob`; `IndividuallyVerifiedLegos != VerifiedComposition`.

## Concept taxonomy (do not turn into mandatory registry)

| Term | Core identity | May do | Does not establish |
| --- | --- | --- | --- |
| Goal | Human/domain desired outcome | Define acceptance predicate | Action permission or proven reachability |
| Model | Stochastic inference/decision provider | Generate plans, summaries, candidates | Truth, authority, or actual effects |
| Prompt / instruction | Context supplied to model | Guide model behavior | Enforce a runtime invariant |
| Tool | Callable executable/read capability | Perform bounded operations via owner API | Correct goal completion by successful invocation |
| Skill | On-demand instructions + references + optional scripts/assets | Teach how to select/use tools; aid reusable processes | New effect authority, reliable execution, or a second API |
| Agent | Decision loop applying model/context/tools | Explore uncertain options, select next action | Durable execution or domain final truth |
| Harness | Agent run scaffold | Model/tool loop, context assembly/compaction, step limits, approvals, traces | Physical Job/Attempt truth, business outcome, or Host Work authority |
| Workflow / orchestrator | Explicit process/dependency logic | Sequence, branch, parallelize; resume if supported | Automatic exactly-once external side effects |
| Host Work | Durable cross-run objective/coordination under Ordivon Host | Resume objectives and collaboration | Physical Runtime effects or domain science truth |
| Runtime Job / Attempt | Runtime-owned physical execution state | Admit, dispatch, observe, reconcile, cancel | Human-goal semantic completion |
| Workspace / environment | Bounded execution or source context | Provide files, compute, dependencies | A guarantee that every host dependency was snapshotted |
| Session / thread | Model-run conversational continuity | Maintain limited run context | Cross-run Work, deployment truth or enduring memory |
| Memory / RAG | Historical/observed knowledge inputs | Retrieve context with freshness/source | Verified current reality or permission |
| Policy / guardrail | Decision constraints | Deny invalid invocation at trusted enforcement boundary | Complete correctness of arbitrary output |
| Formal specification | Explicit admissible states and transitions | Define safety, liveness, pre/post conditions | Reality assumptions or implementation refinement automatically |
| Proof / model-check result | Evidence scoped to specified claims | Rule out defined violations in proven/modelled scope | Whole-world correctness or domain acceptance |
| Eval / trace / replay | Empirical evidence and diagnostics | Find faults, measure ability, falsify assumptions | Universal theorem or authorization |
| Artifact | Deliverable/evidence payload | Be consumed by another boundary | Semantic validity without verifying consumer |
| MCP | Client/server protocol for tools, resources, prompts; optional Tasks/Skills extensions | Expose existing owner capabilities | Domain truth or an automatic substitute for Runtime |
| A2A | Protocol across independent agent systems | Advertise agents, exchange Tasks/Messages/Artifacts | Automatic replacement for local Host Work/Runtime Job |
| SDK / framework | Developer integration convenience | Expose or compose existing mechanisms | Reason to replicate same owners |
| LEGO | Replaceable responsibility, goal conditioned | Be reused/composed when contracts align | Unique executable or a universally required metadata file |

## Minimal correspondence

Goal → requirements / acceptance
Select capability → existing owner Skills method and existing owner Tool or API
Agent proposes uncertain action; deterministic code/solver handles a known action
Harness maintains the bounded model/tool Run
Host maintains durable Work if and only if cross-run objective needs it
Runtime maintains physical Job and Attempt and associated evidence
Consumer/domain source checks actual goal outcome
Formal methods check the obligations at the seams and composition

No part of this mapping asserts that the current implementation mechanically proves its complete end-to-end refinement. Distinguish available, authorized, executed, observed, and semantically accepted.

## Use formalism where it eliminates an actual class of errors

Representative *candidate* invariants to establish against real consumers:
- No conflicting durable commit for the same resource generation / fencing epoch.
- A Runtime Attempt crosses the physical dispatch boundary at most once; ambiguity blocks blind redispatch.
- Tool permission is decided from trusted current authority at the effect boundary, not a Skill description or untrusted output.
- A run claiming complete provides scoped evidence of the specific consumer acceptance predicate.
- A Skill activation does not implicitly grant a Tool or create a Work/Job.
- A cross-agent A2A task handle does not mutate local Runtime/Host authoritative state without an explicit owner operation.
- A model candidate may become an admitted LEGO only after source, effects, contract and consumer acceptance are satisfied.

Nontrivial liveness needs fairness, deadline, cancellation and failure assumptions. Proving finite model correctness alone does not prove implementation refinement. Empirical tests and reality checks remain necessary.

## Decision rules and subtraction

1. For a fixed known operation, invoke a deterministic owner Tool directly. Do not instantiate an Agent/Skill unless it improves correctness or cost.
2. For repeatable procedural uncertainty, reuse a scoped Skill, loading minimal references. A Skill may have no custom script.
3. For an open decision, use one bounded Agent run and require concrete candidate/evidence; migrate stable procedures to deterministic LEGO.
4. For multi-step predictable work, reuse existing workflow/Runtime composition. Do not add LangGraph, ADK or another orchestrator merely because it exists.
5. For cross-agent distributed integration, consider A2A only when its real external consumer exists; MCP handles tools/data entry.
6. For durable business effects, map precise authority, operation identity, commit-time checks, recovery and reconciliation to the actual owner.
7. For repeated evidence, prefer native checks, model-based testing and formal proof only where they materially strengthen the claim.
8. For redundant abstraction, attempt DELETE-CUSTOM and consume mature standards; do not add an Ordivon-wide taxonomy engine or LEGO registry.

## Local facts and unverified boundaries

- AGENTS.md distinguishes scoped owner verification and forbids cross-owner truth duplication.
- The natural owner defines Host Work, Runtime Workspace/Job/Attempt and Skill discovery. Check their actual currently published interfaces instead of trusting generic term matching.
- HarnessRunContract defines bounded context, source, model and Tool grants but is not itself domain semantic acceptance.
- RuntimeDispatchR1.tla covers a narrow physical dispatch safety model; it excludes workflow semantics and does not mechanically prove all Rust implementations.
- Current-source declarations do not prove deployed behavior. All claims about deployed state, permission or semantic completion need fresh natural-owner evidence.

## Research source index (official, reviewed 2026-10-24)

- Anthropic, Building effective agents (2024-12-19; page explicitly flags later landscape): https://www.anthropic.com/research/building-effective-agents
- Anthropic, Equipping agents for the real world with Agent Skills (2025-10-16): https://www.anthropic.com/research/equipping-agents-for-the-real-world-with-agent-skills
- Claude Managed Agents agent configuration: https://platform.claude.com/docs/en/managed-agents/agent-setup
- OpenAI, Codex as a platform / open harness (2026-08-19): https://developers.openai.com/blog/codex-as-a-platform
- OpenAI, Agents API architecture: https://developers.openai.com/api/docs/guides/agents-api/architecture
- OpenAI Agents SDK overview and orchestration: https://openai.github.io/openai-agents-python/ and https://openai.github.io/openai-agents-python/multi_agent/
- OpenAI, Harness engineering (2026-02-11): https://openai.com/index/harness-engineering/
- Microsoft Agent Framework harness and agents/workflows: https://learn.microsoft.com/en-us/agent-framework/concepts/harness and https://learn.microsoft.com/en-us/agent-framework/overview
- Anthropic Agent Skills open spec: https://agentskills.io/specification
- MCP 2026-07-28: https://modelcontextprotocol.io/specification/2026-07-28
- A2A v1.0 overview and MCP comparison: https://a2a-protocol.org/dev/specification/ and https://a2a-protocol.org/dev/topics/a2a-and-mcp/
- Google ADK multi-agent patterns: https://developers.googleblog.com/developers-guide-to-multi-agent-patterns-in-adk/
- LangGraph stack roles and persistence: https://docs.langchain.com/oss/python/langgraph/overview and https://docs.langchain.com/oss/python/langgraph/persistence
- Temporal Workflows: https://docs.temporal.io/workflows

## Stop condition

No new Agent role, new Skill, registry, approval loop, scheduler or formal DSL is justified by this document alone. Close conceptual inquiry when the existing Ordivon owner mapping is sufficient to decide a concrete Tool/Skill/Harness/Runtime boundary. Only propose owner-native changes when a consumer demonstrates actual ambiguity, duplicated authority or a reproducible failure.

## Human direction — Formal LEGO R2.1 as mathematics-backed representation; agent environment hygiene (2026-10-24)

**Standing:** scoped architecture/working-method decision from the Human, not a new LEGO definition, source of runtime truth, proof of whole-system conformance, or authorization to add infrastructure. The exact formal vocabulary remains the project Skill `project-ordivon-next/recursive-lego-calculus` and optional `references/formal-model.md` (observed model SHA-256 `6bc0427a47b69b10cf5f0d3256f3a9c8c313a4a99369de7ea7baf08422b17827`). Space broadcast: `space:ordivon-whole-system-optimization-r1:20261002`, topic `topic:ordivon-whole-system-optimization:mature-engineering-loop-r1:20261006`, message `message:recursive-lego-r21-math-kernels-agent-environment-decision:20261024`.

**Why:** An Agent's observations and available actions are strongly shaped by paths, refs, tool exposure, installed versions, workspace contents and historical artifacts. The Agent then modifies those same surroundings. Stale sources, missing tools, repeated local patches, uncleared workspaces and unintegrated commits can therefore compound across Agent runs. Environment correctness is a prerequisite for trustworthy reasoning *and* actual effect execution; cleanup prevents feedback-driven duplication. This is a causal hypothesis to test on concrete runs, not a proof about all Agents.

**R2.1 implications for real Ordivon work:**
- Treat LEGO as the existing recursive problem/representation/contract/realization/verification calculus, **not** as a file, Unix Tool, new registry row, or mandatory universal schema. Select actual goal and real consumers before decomposition.
- Use mature mathematical **semantic dependencies**, not reimplemented Ordivon kernels: contract algebra/assume-guarantee for composition; SMT for constraints; transition-system model checking for temporal states; designated behavioral equivalence/refinement for replacement; planning for legal operator programs; proof checking where it adds a distinct guarantee. Bind their assumptions, model identity and exact scope. Never infer `phi` from verifier `psi` without a justified bridge.
- The scope is **properties needed by real Ordivon consumers**, not universal correctness. Prefer preventing invalid effects at owner admission/commit with exact source/authority/environment checks; distinguish model proof, implementation refinement, external assumptions and domain acceptance. Keep PASS/FAIL/UNKNOWN separate.
- First representative vertical slice: local/remote Git refs and commits + paths/Workspace + dependency inputs + consumer relationships + CI/evidence. Derive candidate invariants (stale-ref write rejection, dependency/consumer compatibility, no loss of unique dirty changes, recoverable deletion, version-bound evidence); discharge with existing Git, Runtime, natural-owner tests and an admitted mathematical kernel as appropriate, then perform bounded end-to-end read-back.
- Lifecycle subtraction is part of correctness: close clean, unused workspaces; preserve/reconcile dirty, unique contributions and recoverable points before close; do not leave unowned duplicate implementations or orphan PRs by default. Never use a source scan alone as proof of absent external consumers.
- Move gradually, one verified actual consumer slice at a time, then remove superseded custom code/tests when justified. Reuse existing Cognitive Circuit, Verification Obligation, Runtime, Git and Host boundaries; do not create a universal mathematical gateway, another test regime, new management Agent, second owner or parallel ledger.

**Operational stopping rule:** one needed property, one appropriate mature owner/kernel, one scoped verification/effect witness, followed by read-back and cleanup. If none materially improves real consumer outcomes, do not add it.


### R2.1 live-observation contract algebra pilot (2026-10-25)

The existing optional Pacti 0.3.1 shadow now also provides a task-local mathematical operation on supplied typed Harness grant snapshots and Runtime status.config.maxRuntimeMs observations. It uses actual Pacti polyhedral composition and refinement; the result binds both supplied inputs by canonical digest. This is a semantic dependency in the original verification-obligation seam, not a new registration format, execution authority, proof kernel, or production package dependency.

The former frozen example grantMaxMs=300000 / runtimeMaxMs=900000 is not a claim about deployed Runtime: Runtime max_runtime_ms is configuration-dependent. The native pilot tests supplied typed owner-style projections, including a negative smaller-runtime model and missing, zero or boolean Runtime observation counterexamples. Runtime and Harness natural owners, not a Next cross-owner file scan, own source and API conformity. A positive result means ONLY that the two SUPPLIED owner-bound numeric models are compatible in Pacti. Runtime observation authentication/currentness, time-of-check/time-of-use continuity, implementation-to-model refinement, actual effect admission and domain goal acceptance remain unproven. Keep Runtime's own fail-closed timeout admission authoritative.
