# Agent Product Common Structure R1 — Wave-3 Partial Contraction

Status: **PROVISIONAL_AFTER_C01 / C02-C03 PENDING**
Registered: 2026-09-14
Parent synthesis: `catalogs/knowledge/lessons/agent-product-common-structure-r1.md`
Destroyer campaign: `campaign:agent-common-structure-destroyer-20260914-r1`
Captured destroyer evidence: `evidence/agent-campaigns/agent-common-structure-destroyer-r1-C01.md`

## Evidence standing

The destroyer wave has three exact provider-bound occurrences (`C01`, `C02`, `C03`).

Current report harvest:

```text
C01  CAPTURED
C02  NOT_RETRIEVED — provider conversation remains bound; ChatGPT Web redirects to home with `Too many requests`
C03  NOT_RETRIEVED — provider conversation remains bound; ChatGPT Web redirects to home with `Too many requests`
```

Therefore this document is a **partial contraction**, not the final Wave-3 verdict.

## C01 verdict

C01's main attack is that R1 mixed three categories:

1. architecture necessity/boundary;
2. common implementation pattern;
3. good engineering/quality practice.

The result is that seven Wave-1 `STRONG_COMMON` components were too component-shaped and too strong.

C01 proposes replacing the seven-component kernel with approximately **three architecture-level invariants plus one conditional causal relation**.

---

# Provisional minimal kernel after C01

## K1 — Effective Decision Context

Standing: **ARCHITECTURE BOUNDARY / MEDIUM-HIGH**

A model decision is conditioned on some effective information/context supplied or retained by a caller, provider, environment or context source.

This does **not** imply:

- a `ContextCompiler` component;
- an explicit memory subsystem;
- one precedence ontology;
- an Ordivon-owned context object.

Possible implementations include direct concatenation, provider-held conversations, cached prefixes, dynamic retrieval, project instructions, Skills, environment state or opaque provider continuation.

Natural owner:

```text
caller/domain
+ model provider / adapter
+ provider-native session/context substrate
```

Harness should own only bounded residual cognition mechanics unsupported by those owners.

---

## K2 — Action / Output Interpretation Boundary

Standing: **ARCHITECTURE BOUNDARY / HIGH**

For an effectful Agent, model output must be interpreted before it becomes an external effect.

The representation may be:

```text
typed Tool call
executable code
shell command
patch/diff
browser action
generated program
natural-language delegation
provider-native action representation
```

Therefore Wave-1 `TYPED_ACTION_SURFACE` is too specific.

CodeAct is an explicit counterexample to a universal narrowly typed Tool surface: it consolidates actions into executable Python interpreted by an execution environment.

Natural owner:

```text
provider SDK / Tool provider / MCP / API / CLI / interpreter
```

not a universal Ordivon Tool ontology.

---

## K3 — Effect Locus + External Authority

Standing: **ARCHITECTURE BOUNDARY / HIGH**

Model output is not itself world effect.

Some external locus turns model-produced information into effects:

```text
OS process
interpreter
container
VM
browser
IDE host
SaaS API
cloud sandbox
provider-hosted Tool
specialized runtime
```

The actual environment, credentials, sandbox, IAM and provider policy determine what can happen.

Therefore Wave-1's separate `Authority / Effect Gate` and `Execution Substrate` should be contracted:

```text
invariant:
Prompt semantics != effective authority

boundary:
effect occurs in an external locus whose actual authority is external to model prose
```

An explicit policy/approval gate is a **possible control**, not a descriptive universal.

Natural owner:

```text
IAM / OS / cloud authority / provider policy
+ execution provider / sandbox / Runtime where uniquely justified
```

---

## K4 — Conditional Feedback

Standing: **CONDITIONAL CAUSAL RELATION / HIGH**

If a later model decision depends on consequences of an earlier action/effect, information about the resulting environment must somehow become available to that later decision.

This may happen through:

```text
Tool result
transcript
files
IDE state
browser state
API result
provider-hidden continuation
remote task event
```

This does **not** imply a visible Harness-owned loop.

One-shot generated programs, submit/poll/result hosted Agents, deterministic workflows with LLM nodes and provider-native hidden loops are counterexamples to treating an explicit Agent loop component as universal.

Natural owner:

```text
provider runner / caller / workflow engine / environment
```

according to where continuation actually lives.

---

# Wave-1 components provisionally demoted by C01

| Wave-1 item | C01 standing | Replacement |
|---|---|---|
| Context / Instruction Compiler | **DEMOTE** | Effective decision context |
| Typed Action / Tool Surface | **REJECT AS UNIVERSAL** | Action/output interpretation boundary |
| Observation-driven Control Loop | **DEMOTE STRONG FORM** | Conditional feedback relation |
| Explicit Working / Control State | **REJECT FROM KERNEL** | causal information may persist anywhere |
| Authority / Effect Gate | **DEMOTE COMPONENT** | prompt authority != effective authority invariant |
| Execution Substrate | **SURVIVES BUT MERGE** | effect locus / external authority boundary |
| Verification / Feedback | **REJECT AS UNIVERSAL** | robust quality pattern / domain V&V |

Additional surrounding structures rejected from the minimal kernel:

- recovery/durability;
- plugin/extensibility bus;
- model routing/specialization;
- persistent memory;
- plan/todo;
- subagents/multi-agent topology;
- browser/web;
- Git/VCS;
- mandatory approval.

These may remain highly valuable product mechanisms without being Agent-defining primitives.

---

# Verification is demoted, not discarded

C01's strongest quality correction is that `Verification / Feedback` is not descriptively universal.

A functioning Agent may:

- stop on final model output;
- trust command exit status;
- emit an unverified patch;
- leave acceptance to CI;
- leave acceptance to a user/domain system.

Current OpenAI Agents SDK documentation corroborates this distinction: its generic Runner terminates when the model produces final output with no Tool calls, while tests/domain verification are not mandatory parts of the generic loop.

Therefore Ordivon should retain:

```text
VERIFY = mandatory for Ordivon claims that require verified outcomes
```

but should not claim:

```text
verification component = universal descriptive Agent primitive
```

This is the difference between **Ordivon's quality contract** and **Agent architecture ontology**.

---

# Natural-owner contraction

C01's corrections reinforce `DELETE CUSTOM BY DEFAULT`:

| Concern | Default natural owner |
|---|---|
| model-input lowering | model provider / adapter |
| domain context selection | caller / domain |
| Tool schemas/discovery | MCP / provider API / Tool provider |
| Tool implementation | capability provider |
| shell/browser/container execution | runtime / sandbox / provider |
| credentials | IAM / OS credential store / cloud provider |
| network boundaries | sandbox / network policy / infrastructure |
| durable workflow | Temporal-class engine |
| generic model/tool loop | provider SDK / minimal runner unless substitution failure |
| conversation persistence | provider/session store/caller |
| IDE state | IDE |
| browser state | browser/browser automation provider |
| semantic verification | domain V&V / CI / evaluation provider |
| telemetry | OpenTelemetry + backend |
| model routing | provider / LiteLLM / caller |
| human approval | domain policy / IAM / risk-control layer |
| artifact publication | domain delivery system |
| recovery | underlying workflow/runtime/provider where possible |

Key rule:

> **Agent-related does not imply Harness-owned.**

---

# Promotion-rule correction

Wave-1's rule:

```text
>= 2 product-family reports
```

is not enough because products may share ancestry:

- common ReAct lineage;
- common function-calling APIs;
- shared IDE primitives;
- MCP adoption;
- copied prompt conventions;
- shell-centric coding-agent lineage;
- benchmark-driven convergence.

Future common-structure promotion should require **plausibly independent architectural lineages**, or explicitly discount correlated ancestry.

Every candidate should also carry one category:

```text
LOGICAL_NECESSITY
ARCHITECTURE_BOUNDARY
COMMON_PATTERN
QUALITY_PRACTICE
PRODUCT_SPECIFIC
```

This prevents useful practices from becoming ontology by frequency.

---

# Hidden-loop test

For every proposed Harness responsibility ask:

> Would the system still function if the provider performed this internally and exposed only task/status/result events?

If yes, that responsibility is probably not a Harness invariant.

Examples:

- provider-native loop;
- provider-held conversation state;
- provider-managed Tool dispatch;
- provider-managed compaction;
- hosted sandbox execution.

Harness should not mirror internal provider mechanics merely to make them visible.

---

# Provider-substitution test

Before creating an Ordivon-native Agent component, require evidence that mature natural owners cannot satisfy the requirement:

```text
provider SDK
MCP
Temporal
Runtime
sandbox/container/VM
IAM
OpenTelemetry
IDE
browser automation provider
domain V&V
```

No substitution failure -> no new Ordivon primitive.

---

# External corroboration performed after C01

## OpenAI Agents SDK

Current official SDK documentation explicitly distinguishes the higher-level `Agent + Runner` loop from using the Responses API directly. The Runner may manage turns, Tool execution, handoffs and sessions, but callers can instead own that loop themselves. This supports C01's claim that a generic explicit loop is an implementation/runtime choice rather than an Agent ontology requirement.

Official sources:

- https://openai.github.io/openai-agents-python/agents/
- https://openai.github.io/openai-agents-python/ref/run/
- https://openai.github.io/openai-agents-python/tools/

## CodeAct

The CodeAct paper proposes executable Python code as a unified action space instead of requiring a fixed catalogue of JSON/text actions. This directly falsifies `typed Tool surface` as a universal representation while preserving the deeper action-to-environment interpretation boundary.

Source:

- https://arxiv.org/abs/2402.01030

## MCP

Current MCP remains an interoperability standard connecting AI applications to external systems rather than an Agent state/loop ontology. Its 2026 evolution toward a stateless request/response core further warns against treating protocol/tool connectivity as proof of a universal Harness state machine.

Sources:

- https://modelcontextprotocol.io/
- https://blog.modelcontextprotocol.io/

---

# Current provisional conclusion

C01 materially contracts the Wave-1 synthesis.

The most defensible current representation is no longer a seven-component `COMMON AGENT KERNEL`.

It is a small set of **relations/boundaries**:

```text
EFFECTIVE DECISION CONTEXT
        ↓
MODEL DECISION / OUTPUT
        ↓
ACTION / OUTPUT INTERPRETATION BOUNDARY
        ↓
EFFECT LOCUS + EXTERNAL AUTHORITY
        │
        └── if another decision depends on the result ──>
             CONDITIONAL FEEDBACK
```

Everything richer should remain a provider/product/domain mechanism until C02/C03 and further counterexample-oriented evidence justify promotion.

## Standing

**PROVISIONAL.** Do not overwrite the full Wave-3 verdict until C02 and C03 reports are retrieved or explicitly superseded by a separately identified replacement review wave.
