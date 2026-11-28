# Agent Common Structure Destroyer R1 — C01

Status: **CAPTURED**
Campaign: `campaign:agent-common-structure-destroyer-20260914-r1`
Agent: `C01`
Effect: `sha256:7eef25fa2a5680336e43a39dfd87d0df0f6bdc5f004aabdb33b42ae767ff693e`
Provider resource: `https://chatgpt.com/c/6aa7afbb-c7c4-83ec-8856-7e5b3a06d472`
Assistant output digest: `sha256:3669b68e8a73f843bed70235155a6660639d26eb6712fe603abdc42f3f7693d7`
Capture standing: `CAPTURED`

---

Worked for 36s
C01 False-Commonality Destructive Review
VERDICT

Overall verdict: R1 is directionally useful but still over-promotes implementation regularities into a “common kernel.” Confidence: HIGH.

The synthesis has found a credible software-agent interaction pattern, not yet a universal architecture. The strongest invariant is much thinner than the seven-element kernel.

The largest methodological defect is that independent reports are being treated too much like independent architectural lineages. Claude Code, Devin-like coding agents, Replit-like builders, Lovable/v0/Bolt-style builders, MCP ecosystems, and modern tool-calling APIs all descend from overlapping ReAct/function-calling/shell/browser/IDE traditions. Counting several products implementing related ideas does not establish independent convergence.

The missing A02 IDE-family and A05 canonical OSS baseline materially matter. They must remain missing. Their absence prevents strong claims about IDE-native architectures and independently inspectable open-source agent harnesses. The current corpus is therefore sufficient for a provisional within-corpus abstraction, but not for a stable cross-agent ontology.

A second defect is that several candidates confuse three levels:

Architectural necessity — something an effectful agent logically cannot avoid.

Common implementation pattern — frequently useful but substitutable.

Good engineering practice — desirable but demonstrably absent from functioning agents.

R1 currently places members of all three classes into the kernel.

The defensible claim is closer to:

Within the studied software-agent family, an effectful agent arrangement connects model decisions to an environment through some action/effect boundary, obtains information from that environment when further decisions are required, and eventually terminates or yields control. Context construction, typed tools, explicit run state, verification, durability, routing, approval, and even host-visible looping are optional realizations of that relationship.

That is substantially smaller than R1.

STRONGEST_SURVIVORS
1. Effect/execution boundary — HIGH confidence

Survives, but merge EXECUTION_SUBSTRATE with the non-prompt portion of AUTHORITY_EFFECT_GATE.

Any claim that an agent actually changes a repository, browser, deployment, database, app, or external service implies some locus that turns model-produced information into physical/logical effects. It may be:

local process,

shell,

interpreter,

browser,

container,

VM,

SaaS API,

provider-hosted tool,

remote worker,

IDE host,

specialized execution service.

This is an architecture boundary, not a specific implementation component.

The important invariant is not “there is an Ordivon Runtime.” It is:

Model output is not identical to world effect. Some executor/environment/provider mediates the transition.

CodeAct does not falsify this. CodeAct deliberately broadens the action language to executable Python rather than a catalogue of narrow JSON tools, but still needs an interpreter/environment in which generated code becomes action.

Ownership: overwhelmingly Runtime/provider/sandbox/OS/API/IAM rather than Harness.

2. Decision ↔ environment feedback relation — HIGH confidence, with major wording correction

The weak form of OBSERVATION_DRIVEN_LOOP survives:

When another model decision depends on the consequences of an earlier effect, some representation of those consequences must become available to the next decision.

That is close to architectural necessity.

The strong form does not survive:

context → decision → authorize → execute → observe → state update → continue/repair/complete

because several of those boxes are optional or may be hidden inside providers.

OpenAI's current Agents SDK explicitly implements a runner loop around model outputs, handoffs, and tool calls, showing that this pattern is real and important—but also that the loop belongs to a particular runner implementation rather than to the definition of an agent.

CodeAct likewise supports iterative action/observation revision, but its action representation is executable code rather than a conventional typed tool catalogue.

Architecture boundary: causal feedback from environment to later decision.

Implementation detail: explicit loop object, turn counter, state reducer, repair state, orchestration FSM.

3. Prompt authority ≠ effect authority — HIGH confidence

The conceptual distinction in AUTHORITY_EFFECT_GATE is one of R1's strongest findings:

Instructions presented to a model do not themselves constitute operating-system, credential, network, sandbox, API, or resource authority.

That survives attacks from almost every architecture.

OpenAI's documented Codex deployment separates sandbox boundaries, network policy, credentials, approval policies, and rules from what the model is merely instructed to do.

However, this must not be converted into the false universal:

every agent product contains an explicit authority gate.

A badly engineered agent may simply inherit ambient process privileges. It still works. Its authority is constrained by OS/API credentials, but the agent product need not implement a deliberate gate.

Therefore:

Surviving invariant: prompt semantics and effective authority are different planes.

Rejected implementation universal: every action passes a dedicated authorization component.

4. Effective decision context — MEDIUM-HIGH confidence

There is inevitably some information available to a model invocation. But CONTEXT_COMPILER overstates what follows.

The abstract survivor is:

A model decision is conditioned on an effective input/context determined by some combination of caller, provider, history, resources, tools, state, environment, or cached/provider-held continuation.

That does not imply an explicit compiler.

MCP itself is evidence against conflating agent state/context construction with a universal harness component. The current MCP specification has moved its protocol core toward stateless request/response semantics while applications may layer richer state elsewhere.

MCP also explicitly separates resources, prompts, and tools supplied by servers from the host/model interaction, reinforcing that context ownership may be distributed.

Architecture boundary: effective model input exists.

Implementation detail: ContextCompiler, deterministic compilation pipeline, instruction precedence engine, memory selector, explicit context object.

DEMOTIONS_OR_REJECTIONS
CONTEXT_COMPILER → DEMOTE

Confidence: HIGH.

Reject as a universal named component.

Direct concatenation, provider-maintained conversation state, cached prefixes, opaque server-side continuation, and dynamically loaded context all satisfy the functional requirement without resembling a compiler.

Retain only effective decision context.

TYPED_ACTION_SURFACE → REJECT AS UNIVERSAL

Confidence: HIGH.

The word typed is falsified by plausible and demonstrated designs.

CodeAct intentionally uses executable Python as a unified action space instead of requiring every capability to appear as a separately typed JSON/function affordance.

OpenAI's current agent tooling also includes generated programmatic coordination of tools, showing that the industry is already exploring layers above simple one-call-one-schema action surfaces.

What survives is only:

ACTION_CHANNEL / EFFECT_PROPOSAL: the model produces information that some executor interprets as an action or artifact.

That channel may be:

typed function call,

shell command,

source code,

patch,

diff,

browser action,

natural-language delegation,

generated program,

structured plan consumed elsewhere.

“Bounded” should refer to effective authority, not necessarily to syntactic action vocabulary.

OBSERVATION_DRIVEN_LOOP → DEMOTE STRONG FORM

Confidence: HIGH.

Reject mandatory visible looping.

Counterexamples include:

one-shot generated programs;

remote agents exposed as submit → poll → result;

provider-native loops hidden completely from the caller;

model produces patch/artifact and exits without executing it;

deterministic workflow engines containing an LLM node;

agents terminating after one execution without repair.

The architecture may contain a loop somewhere, but Ordivon cannot infer that its Harness should own it merely because repeated decisions occurred.

Retain only conditional effect → observation → subsequent decision feedback.

EXPLICIT_WORKING_STATE → REJECT AS KERNEL

Confidence: HIGH.

A multi-step system obviously has information that persists causally between steps, but it need not be represented as an explicit first-class AgentState.

Possible state locations include:

transcript alone,

filesystem,

shell process,

browser DOM,

provider conversation ID,

remote service,

database,

environment variables,

caller-owned object,

opaque provider continuation.

OpenAI's Agents SDK exposes RunState and sessions in some configurations, which establishes that explicit state is a useful implementation, not that every agent architecture requires it.

Replace with the much weaker statement:

Multi-step continuation requires causal information preservation somewhere.

That is almost tautological but actually universal.

AUTHORITY_EFFECT_GATE → DEMOTE FROM COMPONENT TO INVARIANT

Confidence: HIGH.

The security distinction survives; the component does not.

No universal dedicated gate is required. Ambient credentials plus OS/API enforcement constitute effective authority even if the agent designer wrote no policy engine.

Do not turn a normative best practice into a descriptive universal.

EXECUTION_SUBSTRATE → SURVIVES, BUT TOO BROAD TO BE DISTINCT

Confidence: HIGH.

For effectful agents it is nearly definitional.

It should therefore probably not appear as an elaborate Ordivon primitive. Treat it as an external architecture boundary:

effects happen somewhere outside model token generation.

VERIFICATION_FEEDBACK → REJECT AS UNIVERSAL

Confidence: VERY HIGH.

This is the clearest over-promotion.

OpenAI's generic Agents SDK ends its normal loop when it receives final output with no tool calls; semantic tests, linting, browser inspection, or independent acceptance are not mandatory termination prerequisites.

Codex may be trained or configured to verify work, but that is evidence for a high-quality coding-agent practice, not universal agent structure.

Many functioning agents:

trust command exit status;

stop on model judgment;

deliver unverified patches;

delegate acceptance to CI;

delegate acceptance to a user;

have no machine-observable semantic oracle.

Verification therefore belongs under domain V&V / quality policy, not common kernel.

recovery/durability → REJECT AS COMMON KERNEL

Confidence: HIGH.

Only required when interruption tolerance or long-running resumability is a product requirement.

extensibility/plugin bus → REJECT AS COMMON KERNEL

Confidence: HIGH.

Useful ecosystem property. Not agent-defining.

MCP is an interoperability substrate, not evidence that every agent intrinsically contains a plugin bus. Its own architecture separates host/client/server concerns.

model specialization/routing → REJECT AS COMMON KERNEL

Confidence: VERY HIGH.

Single-model agents falsify universality immediately.

MISSING_COUNTEREXAMPLES

The next corpus should deliberately seek architectures least likely to reproduce the current abstraction.

1. Canonical CodeAct/programmatic-action agent.
Required specifically to attack TYPED_ACTION_SURFACE. CodeAct already demonstrates that executable code can collapse numerous narrowly typed calls into a much richer action language.

2. One-shot executable-program agents.
Needed to test whether a recurring observation loop is necessary. Research such as Tree-of-Code reports useful one-turn program-style alternatives in some settings, showing that iterative tool turns should not be treated as metaphysically necessary.

3. Stateless or almost-stateless runners.
Search explicitly for agents whose only persistence is transcript/provider continuation/environment. These attack EXPLICIT_WORKING_STATE.

4. Provider-native opaque agents.
Examples where consumers submit a task to a hosted system and see only status/events/result. These test whether Harness-visible orchestration is merely an API artifact.

5. IDE-native agent implementations.
A02 remains missing. This is important because IDE hosts can supply selection, open buffers, diagnostics, edits, terminal state, and permissions through host-native structures that may erase several proposed generic Ordivon components.

6. Inspectable OSS harness baseline.
A05 remains missing. Without it, claims are overdependent on proprietary products whose internal architecture has been inferred from documentation or behavior.

7. Patch-only agents.
Model emits patches/diffs; execution and verification are performed elsewhere. These separate agency from execution ownership.

8. Workflow systems with LLM steps but deterministic outer control.
These test whether “agent loop” is an agent property or just a workflow-engine property.

9. Agents with ambient authority and no explicit policy gate.
Important negative engineering examples. They falsify the descriptive statement that all working products implement authority gating even though they strengthen the normative argument for doing so.

10. Non-software agents.
Robotics, scientific automation, financial research, customer-service execution, and other embodied/domain agents should be used primarily as a scope guard. They cannot falsify a claim explicitly limited to the studied software-agent family, but they can immediately expose terminology that has accidentally escaped that boundary.

NATURAL_OWNER_CORRECTIONS

The natural-owner map is mostly pointed in the correct direction but still leaves too much gravitational pull toward Harness.

Concern	Correct default owner
Prompt/model-input lowering	Model provider / adapter
Domain context selection	Calling application / domain
Tool schemas and discovery	MCP / native provider API / tool provider
Tool implementation	Capability provider
Shell/browser/container execution	Runtime / sandbox / provider
Credentials	IAM / OS credential store / cloud provider
Network restrictions	sandbox / network policy / infrastructure
Long-running durable workflow	Temporal-class workflow engine
Generic model/tool turn loop	provider SDK / minimal runner unless unmet requirement
Conversation persistence	provider/session store/caller
IDE state	IDE
Browser state	browser/browser-automation provider
Verification semantics	domain V&V / CI / testing/evaluation system
Telemetry	OpenTelemetry + backend
Model routing	provider/LiteLLM/caller
Human approval	domain policy / IAM / risk-control layer
Artifact publication	domain delivery system
Recovery	underlying workflow/runtime where possible

The key correction is:

“Agent-related” does not imply “Harness-owned.”

A Harness should own only the residue for which a mature provider does not already supply acceptable semantics.

ORDIVON_OVERREACH_RISKS
1. Rebuilding provider agent runners

OpenAI's SDK already exposes a generic model → tool/handoff → repeat loop.

Implementing the same abstraction inside Ordivon without a demonstrated substitution failure would create another orchestration layer rather than strategic differentiation.

2. Inventing an Ordivon-wide AgentState

This is likely to become accidental ontology.

Repository state, browser state, task state, provider continuation, workflow state, IAM state, and domain acceptance state have different owners and lifetimes.

A universal Ordivon state schema would force unrelated systems into a shared representation and eventually make Ordivon responsible for synchronizing truths it does not own.

3. Owning authorization semantics

Ordivon should not become IAM.

It may carry or request authority decisions, but credential validity, resource permissions, filesystem controls, OAuth, network boundaries, and cloud policy should remain with mature security systems.

4. Owning semantic verification

Tests, scientific validity, app preview quality, deployment health, legal correctness, financial reconciliation, UX acceptance, and game quality do not share one generic verifier.

Ordivon may orchestrate evidence collection. It should not pretend the orchestration layer supplies the domain truth.

5. Treating MCP as an internal Ordivon architecture

MCP standardizes interoperable connections among hosts, clients, servers, tools, resources, prompts, and related capabilities.

Rebuilding these semantics behind proprietary Ordivon abstractions would move in the wrong direction.

6. Confusing provenance count with architectural independence

Eight reports are not eight independent inventions.

The synthesis needs a lineage/dependence dimension:

common provider API ancestry;

common ReAct ancestry;

MCP adoption;

common IDE primitives;

copied prompt conventions;

shell-centric coding lineage;

benchmark-driven convergence.

Otherwise correlated implementations will inflate confidence.

7. Turning good coding-agent practice into agent ontology

Testing, linting, diffs, checkpoints, planning, approvals, memory, VCS, repair loops, and explicit todo lists can all be excellent engineering practices while remaining non-universal.

This is currently the main source of kernel inflation.

REQUIRED_REVISIONS

Change the promotion rule.
>=2 product-family reports is insufficient. Require at least two plausibly architecturally independent lineages, or explicitly discount correlated ancestry.

Add a classification field to every candidate:
LOGICAL NECESSITY / ARCHITECTURE BOUNDARY / COMMON PATTERN / QUALITY PRACTICE / PRODUCT-SPECIFIC.

Replace CONTEXT_COMPILER with EFFECTIVE_DECISION_CONTEXT. Do not require a compiler component.

Replace TYPED_ACTION_SURFACE with ACTION_OR_OUTPUT_CHANNEL. Typing is optional. Code, patches, text delegation, or provider-native representations must fit without distortion.

Replace OBSERVATION_DRIVEN_LOOP with a conditional relation:
if an additional model decision depends on prior effects, effect information must become available to that decision.
Do not require a Harness-owned loop.

Delete EXPLICIT_WORKING_STATE from the common kernel.
Retain only optional CONTINUATION_STATE, with no universal representation or owner.

Split AUTHORITY_EFFECT_GATE into two claims:

invariant: prompt semantics are not effective authority;

optional mechanism: explicit policy/approval gate.

Fold EXECUTION_SUBSTRATE into EFFECT_BOUNDARY.
It does not need to become a rich Ordivon primitive.

Move VERIFICATION_FEEDBACK out of the kernel.
Register it as ROBUST_AGENT_PATTERN / DOMAIN_V&V, with particularly high prevalence in coding and app-building systems.

Do not promote recovery, plugins, routing, memory, planning, multi-agent topology, browser use, VCS, or approvals.

Keep A02 and A05 explicitly UNKNOWN/MISSING.
Do not fill them from adjacent reports.

Rewrite the scope label everywhere.
Use “studied software-agent/product family”, never unqualified “AI Agents.”

Add a hidden-loop test.
For every proposed Harness responsibility ask:
Would the architecture still function if the provider internally performed this operation and exposed only task/result events?
If yes, it is probably not a Harness invariant.

Add a provider-substitution test.
Before registering an Ordivon-native component require concrete evidence that MCP, provider SDK, workflow engine, sandbox, IAM, telemetry stack, IDE, browser automation framework, or domain V&V cannot satisfy the requirement.

FINAL_MINIMAL_KERNEL

Confidence: MEDIUM-HIGH for the stated studied family; LOW for AI agents in general.

I would reduce R1 to only three architecture-level invariants, with a fourth conditional relation:

K1 — EFFECTIVE_DECISION_CONTEXT

A model decision is conditioned on some effective information/context supplied or retained by the caller, provider, environment, or other context source.

No compiler, explicit state object, memory system, or universal precedence schema is implied.

K2 — ACTION / OUTPUT INTERPRETATION BOUNDARY

For an effectful agent, model output crosses an interpretation boundary before becoming an external effect.

The representation may be a typed tool call, executable code, shell command, patch, browser action, generated program, delegation, or another provider-native form.

No universal typed action surface is implied.

K3 — EFFECT LOCUS AND EXTERNAL AUTHORITY

Effects occur in some environment/provider/runtime whose actual capabilities—not Prompt prose—determine what can happen.

Explicit sandboxing, IAM gates, approval steps, and policy engines are implementations or controls around this invariant, not universally agent-owned components.

K4 — CONDITIONAL FEEDBACK

If the system makes a later decision based on earlier execution, information about the resulting environment must somehow reach that later decision.

That feedback may be explicit structured tool output, transcript text, files, IDE state, browser state, provider-hidden state, API results, or another representation.

A visible iterative Harness loop is not required.

Everything else in R1—explicit working state, context compiler, typed actions, verification/repair, durability, plugins, routing, planning, memory, approvals, and multi-agent structure—should remain outside the minimal kernel until independent counterexample-oriented evidence justifies promotion.

The destructive result is therefore:

R1 did discover a real recurring software-agent pattern, but the defensible universal core is approximately 3–4 relations, not seven components. The biggest revision should be from a component ontology to a boundary/causal-relations ontology.

Resolve the three-versus-four kernel inconsistency
Add an evidence ledger for each claim
