# AI-Native Project Object Model

> **Status:** `current`
> **Type:** `source_of_truth`
> **Canonical:** Canonical document #5. When old classification docs conflict, this wins.
> **Dogfood:** Ordivon's own project structure will be reorganized against this model.
> **Last verified:** 2026-05-20
> **Stale after:** 90 days

---

## 0. Design Premise: AI-Era Projects Have Changed

A traditional software project was:

```text
Project = code + docs + tests + CI
```

An AI-native project is no longer just a repo for humans and compilers. It is an **execution environment** shared by humans, AI agents, tools, skills, MCP connectors, evals, traces, and governance rules.

The accurate definition:

```text
AI-native Project =
  Source Code
  + Canonical Docs
  + Agent Instructions
  + Skills
  + Prompts / Templates
  + Tools / Scripts
  + MCP / Connectors
  + Agents / Subagents
  + Workflows
  + Policies / Guardrails
  + Evals / Tests
  + Traces / Receipts
  + Memory / Context
  + Registries / Ledgers
  + Governance Objects
```

This is not an invented classification. The industry is already converging:

- `AGENTS.md` is becoming the standard entry point for coding agents — "a README for agents." ([agents.md][1])
- Skills are converging around `SKILL.md`, YAML frontmatter, Markdown instructions, and optional scripts/references/assets. OpenAI defines Skills as reusable, shareable workflows following the Agent Skills open standard. ([OpenAI Help Center][2]) Claude Skills also use `SKILL.md` with progressive disclosure. ([Claude][3])
- MCP is becoming the connection protocol for external tools, data, resources, and prompts. Resources expose data via URI; prompts are predefined templates servers expose to clients. ([MCP Wiki][4])
- OpenAI Agents SDK records LLM generations, tool calls, handoffs, guardrails, and custom events as trace objects. ([openai.github.io][5])
- Production research shows 68% of agents execute ≤10 steps before human intervention, 70% rely on prompting off-the-shelf models, 74% depend primarily on human evaluation. ([IBM Research][6])

Ordivon's entry point is clear:

> **Not to invent all objects, but to classify them into a stricter governance framework that prevents them from impersonating each other.**

---

## 1. Design Goal

This Object Model establishes a foundational grammar so that subsequent work on Ordivon Skill, Templates, Checkers, and System does not descend into category confusion.

It must prevent:

```text
Skill confused with Tool
Tool access confused with execution authority
MCP discovery confused with trust
AGENTS.md overloaded into a dumping ground
Prompt treated as policy
Trace treated as receipt
Receipt treated as resolution
Checker pass treated as policy success
Generated view treated as source
AI proposal treated as decision
Memory treated as truth
```

Every object must answer four questions:

```text
1. What is it?
2. What is it NOT?
3. What is its boundary with adjacent objects?
4. How should it be governed?
```

---

## 2. Primary Classification: 15 Core Objects

```text
 1. Source Object
 2. Generated View
 3. Agent Constitution
 4. Skill
 5. Prompt / Command / Template
 6. Tool
 7. MCP / Connector
 8. Agent / Subagent
 9. Workflow
10. Policy / Guardrail
11. Checker / Gate
12. Eval / Test
13. Trace / Log
14. Receipt
15. Registry / Ledger / Governance Object
```

These objects do not occupy the same layer. Some are source, some are behavioral rules, some are execution capabilities, some are external connections, some are verification, some are governance ledgers.

---

## 3. Layered Architecture: The Four-Layer Model

```
Layer 0: Source / Reality Layer
Layer 1: Agent Operating Layer
Layer 2: Capability / Execution Layer
Layer 3: Verification / Observability Layer
Layer 4: Governance / Lifecycle Layer
```

### Layer 0: Source / Reality

**Question answered:** Where is the project's ground truth?

**Contains:** source code, schemas, configs, canonical docs, data manifests, policy files, registry ledgers, fixtures, ground-truth datasets.

**Ordivon invariants:**
- `Generated ≠ Source` — dashboards, summaries, AI interpretations are not source
- `Summary ≠ Truth` — compression loses detail; compressed claims must reference origin
- `Source ≠ Reality` — source captures intent; reality is what actually runs. Repo-internal source is authoritative record, not reality itself. Still requires real-world receipt verification.
- `Memory ≠ Source` — agent memory is context, not canonical origin

---

### Layer 1: Agent Operating Layer

**Question answered:** How does the AI agent understand the project and know how to act?

**Contains:** AGENTS.md, CLAUDE.md, GEMINI.md, .cursor/rules, .clinerules, skills/, prompts/, templates/, project memory, current-status docs.

**Key distinctions:**
- `AGENTS.md` = project-level agent constitution (always loaded)
- `Skill` = reusable method capsule (loaded on demand)
- `Prompt` = one-shot task instruction
- `Template` = prompt skeleton
- `Memory` = contextual aid, not truth source

**Critical constraint from external research:** A 2026 empirical study on AGENTS.md found that repository context files can make agents more respectful of instructions and explore more files and tests, but can also reduce task success rates and increase inference cost by over 20%. The conclusion: human-written context files should describe only the minimum necessary requirements. ([arXiv 2602.11988][7])

Therefore Ordivon's AGENTS.md must not be overloaded with philosophy. It should be:
- The shortest possible project constitution
- The hardest boundaries
- The most essential navigation
- The clearest prohibitions

Complex methodology belongs in Skills, not permanently in AGENTS.md.

---

### Layer 2: Capability / Execution Layer

**Question answered:** What can the agent call? How do actions happen?

**Contains:** tools, scripts, CLIs, check commands, formatters, linters, MCP servers, connectors, APIs, databases, file write access, deployment commands.

**Core invariants:**
- `Tool Access ≠ Execution Authority`
- `MCP Discovery ≠ Trust`
- `Command Ran ≠ Task Completed`
- `Tool Output ≠ Final Truth`

**MCP security:** Recent research identifies content injection, compromised servers, agents over-stepping roles, tool poisoning, and cross-system privilege escalation as MCP risks. Recommended controls: scoped authorization, provenance tracking, sandboxing, inline policy enforcement, audit logging. ([Hugging Face Papers][8]) A STRIDE/DREAD threat model of MCP identifies tool poisoning as the most common and impactful client-side vulnerability. ([arXiv 2603.22489][9])

Every MCP connection must carry:
```
permission manifest
tool allowlist
tool denylist
human approval gate
tool-call receipt
provenance chain
sandbox boundary
```

---

### Layer 3: Verification / Observability Layer

**Question answered:** How do we know what the agent did and whether it was correct?

**Contains:** unit tests, integration tests, agent evals, golden cases, red-team scenarios, LLM-as-judge rubrics, tool-call verification, database state assertions, traces, logs, runtime evidence.

OpenAI Agents SDK records LLM generations, tool calls, handoffs, guardrails, and custom events as complete traces. ([openai.github.io][5])

**Key distinctions:**
- `Trace` = process trajectory
- `Log` = event record
- `Eval` = quality assessment
- `Test` = software behavior verification
- `Receipt` = closure record

**Core invariants:**
- `Trace ≠ Receipt`
- `Eval Pass ≠ Reality Pass`
- `Test Pass ≠ Governance Success`
- `No Blocking Finding ≠ Production Ready`

---

### Layer 4: Governance / Lifecycle Layer

**Question answered:** Who has authority to confirm? What counts as done? How does failure feed back? How do objects evolve?

**Contains:** claim, evidence, authority, owner, state, gate, receipt, debt, lesson, candidate rule, policy candidate, lifecycle, registry, ledger.

This is Ordivon's home ground.

**Core invariants:**
- `Evidence ≠ Claim`
- `READY ≠ Authorization`
- `Receipt ≠ Resolution`
- `Checker ≠ Policy`
- `AI Proposal ≠ Decision`
- `AI Draft ≠ Final Source`
- `Ignore ≠ Resolution`
- `Suppress ≠ Fix`

This layer makes an AI-native project not just "runnable" but **auditable, authorizable, closeable, and capable of absorbing failure.**

---

## 4. Detailed Object Definitions

### 4.1 Source Object

**Definition:** The project's internal authoritative origin object. Can be code, config, schema, canonical doc, policy, registry ledger, fixture, or data manifest.

**Examples:** `src/*`, `schemas/*`, `policies/*`, `document-registry.jsonl`, `claim-vocabulary.json`, `authority-policy.yaml`, `eval-fixtures.jsonl`.

**Is NOT:** Reality itself. Generated views. AI summaries. Memory.

**Ordivon rules:**
- Generated View must point back to Source Object
- AI Summary must not replace Source Object
- Source Object changes require traceable diff and verification

**Typical failures:**
- Treating `_registry-stats.md` as registry truth
- Treating AI summary as policy source text
- Treating dashboard numbers as ledger source
- Treating memory-stored project status as current truth

---

### 4.2 Generated View

**Definition:** A view derived from Source Objects.

**Examples:** registry stats markdown, wiki index, dashboard, AI-generated summary, rendered architecture map, coverage report.

**Is NOT:** Source of truth. Authority. Proof. Completion receipt.

**Ordivon rules:**
- Must declare its source
- Must be reproducible
- Drift from source must be detectable
- Cannot authorize state change

**Significance:** AI generates vast quantities of summaries, views, reports, dashboards. The greatest risk is **second-hand truth contamination.**

---

### 4.3 Agent Constitution

**Definition:** The project-level, always-resident agent action specification. Typical forms: `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`.

`AGENTS.md` is the community standard — "a README for agents" providing project context and instructions. ([agents.md][1])

**Should contain:** project purpose, repo navigation, key commands, prohibitions, security boundaries, test requirements, change requirements, handoff/receipt requirements.

**Should NOT contain:** lengthy philosophy, detailed workflows, complex task templates, all historical context, complete policy systems.

These belong in: `skills/`, `references/`, `docs/`, `policies/`.

**Ordivon rules:**
- AGENTS.md = minimal standing constitution
- Do not overload AGENTS.md
- AGENTS.md is not the sole source of project truth

**Design principle:**
- AGENTS.md: short, hard, always-resident
- Skill: specialized, triggerable, on-demand
- Docs: complete but not resident
- Registry: the object state source

---

### 4.4 Skill

**Definition:** A reusable, installable, versionable, on-demand task capability package that an agent loads when triggered.

OpenAI: Skills are reusable, shareable workflows that help ChatGPT complete specific tasks more consistently. ([OpenAI Help Center][2])
Claude: Each skill has `SKILL.md` defining when to activate and what instructions to follow, using progressive disclosure. ([Claude][3])
Microsoft Agent Framework: `SKILL.md` with YAML frontmatter and markdown body containing steps, examples, and boundaries. ([Microsoft Learn][10])

**Standard structure:**
```
skill-name/
  SKILL.md
  scripts/
  references/
  assets/
  examples/
```

**Question answered:** When encountering a class of tasks, how should the agent execute?

**Is NOT:** A tool. An agent. A project constitution. Policy itself. Authority. Source truth.

**Ordivon rules:**
- Skill output = proposal / draft / classification
- Skill cannot authorize
- Skill cannot close debt
- Skill cannot suppress risk
- Third-party skill is untrusted until reviewed

**Supply-chain risk:** A 2026 SoK study defines agentic skills as reusable procedural capabilities and discusses supply-chain risks, prompt injection via skill payloads, and trust-tiered execution. ([arXiv 2602.20867][11]) A 2026 survey defines agent skills as reusable procedural artifacts for coordinating tools, memory, and runtime context under task-specific constraints. ([arXiv 2605.07358][12])

Ordivon Skills must carry not just method but safety boundaries.

---

### 4.5 Prompt / Command / Template

**Definition:**
- **Prompt** = one-shot task instruction
- **Command** = callable task entrypoint
- **Template** = reusable prompt skeleton

**Examples:** `engineering-reentry.md`, `claim-audit.md`, `release-readiness.md`, `receipt-template.md`.

**Is NOT:** Skill. Policy. Receipt. Source truth.

**Ordivon rules:**
- Prompt describes intent and scope
- Prompt may instantiate a skill
- Prompt cannot override AGENTS.md or policy
- Prompt cannot authorize forbidden tool use

**Design note:** Tasks given to Codex, OpenClaw, or IDE agents should use Ordivon prompt templates, but templates must not bloat into skills. Skill = method. Prompt = task.

---

### 4.6 Tool

**Definition:** A concrete executable capability the agent can call.

**Examples:** `read_file`, `write_file`, `run_tests`, Python script, shell command, GitHub API, send email, create PR, deploy, database query.

**Is NOT:** Authority. Policy. Proof. Tool output is not final truth.

**Ordivon rules:**
- Tool Access ≠ Execution Authority
- Tool call must be traceable
- Mutating tools require stronger gates
- High-risk tools require human approval

**Tool risk levels (T0-T3):**

| Level | Description | Examples |
|-------|-------------|----------|
| T0 | Read-only | read file, inspect logs, list resources |
| T1 | Local mutation | edit local file, run formatter |
| T2 | External mutation | create GitHub PR, update Notion, draft email |
| T3 | Irreversible / high-risk | deploy prod, delete data, send actual email, execute trade |

Each level maps to a different approval gate.

---

### 4.7 MCP / Connector

**Definition:** The connection layer for external systems, tools, data, resources, and prompts.

MCP resources expose data and content via URI; prompts are predefined templates servers expose to clients. MCP is not just tool call — it includes resource and prompt exposure. ([MCP Wiki][4])

**Examples:** GitHub MCP, Notion MCP, filesystem MCP, database MCP, browser MCP, Slack connector, Jira connector, internal API connector.

**Is NOT:** Trust. Authority. A security boundary by itself. MCP tool schema is not permission policy.

**Ordivon rules:**
- MCP Server must have trust classification
- Every exposed tool/resource must have permission metadata
- External data from MCP must be treated as untrusted until source-bound
- Mutating MCP calls require receipt

**Must record:**
```
server identity, version, source
allowed tools / forbidden tools
resource scope, auth scope
data sensitivity
audit logging support
sandboxing support
```

---

### 4.8 Agent / Subagent

**Definition:**
- **Agent** = an execution subject with goals, context, tools, workflows, and bounded autonomy
- **Subagent** = a specialized agent delegated by the main agent

OpenAI Agents SDK's unified support for handoffs, tool calls, guardrails, and tracing shows agent/subagent orchestration is now a first-class object in agent frameworks. ([openai.github.io][5])

**Is NOT:** Agent is not owner. Subagent is not responsibility transfer. Agent role is not authority. Agent plan is not approved execution.

**Ordivon rules:**
- AI may propose, classify, draft, red-team
- AI may NOT authorize, close debt, suppress risk, resolve
- Handoff transfers work, not accountability
- Agent action must produce trace

**Agent types:**
```
Research Agent, Coding Agent, Review Agent, Governance Agent,
FDE Agent, Red-team Agent, Release Agent
```

Each agent type must have: role, allowed tools, forbidden tools, input contract, output contract, approval boundary, receipt requirement.

---

### 4.9 Workflow

**Definition:** An ordered process from intent to receipt for a task.

**Examples:** Engineering Re-entry, Claim Audit, AI Output Governance, Skill Creation, Release Readiness, AOS Submission, Red-team Hardening.

**Is NOT:** Skill. Tool. Evidence. Workflow completion ≠ real resolution.

**Ordivon meta-workflow:**
```
Intent → Evaluation → Authority → Execution → Receipt → Debt → Gate → Review → Policy → Next Intent
```

**Minimum workflow fields:**
```
intent, scope, non-goals, inputs, actors, tools,
authority, verification, receipt, debt handling, exit status
```

---

### 4.10 Policy / Guardrail

**Definition:**
- **Policy** = the meaning of a rule
- **Guardrail** = a runtime constraint or check mechanism

**Examples:** AI output contract, tool-use policy, MCP permission policy, claim vocabulary, data sensitivity policy, release policy, security policy.

**Is NOT:** Policy is not checker. Guardrail is not full governance. Policy file is not automatic reality guarantee.

**Ordivon rules:**
- Checker ≠ Policy
- Guardrail Pass ≠ No Risk
- Policy Change requires authority
- Policy must bind to enforcement surface

---

### 4.11 Checker / Gate

**Definition:**
- **Checker** = a rule enforcer
- **Gate** = a blocking condition before state transition

**Examples:** `detect_overclaim.py`, authority-gate, doc-registry checker, receipt-integrity checker, architecture-boundaries checker, eval regression gate, release gate.

**Is NOT:** Checker is not policy. Gate is not authority itself. Checker pass is not production readiness.

**Ordivon rules:**
- Checker implements partial policy
- Gate requires evidence
- READY ≠ Authorization
- BLOCKED must be explicit
- DEGRADED must state remaining risk

**States:**
```
PASS / DEGRADED / BLOCKED
```
Or at project level:
```
READY / DEGRADED / BLOCKED
```
But always: `READY ≠ Authorization`.

---

### 4.12 Eval / Test

**Definition:**
- **Test** = verifies software behavior
- **Eval** = verifies AI/agent output quality, reliability, safety, task success rate

**Examples:** unit test, integration test, SWE-bench style issue task, agent golden case, red-team case, LLM-as-judge rubric, tool-call verification, database state assertion.

**Is NOT:** Eval is not reality. Benchmark is not full capability proof. Passing hidden eval ≠ no risk. LLM judge is not authority.

**Ordivon rules:**
- Eval must bind to claim
- Eval must record scope
- Eval must track regressions
- Eval must include negative cases
- Eval result must not overclaim

---

### 4.13 Trace / Log

**Definition:**
- **Trace** = structured trajectory of agent execution
- **Log** = event record

**Examples:** LLM generation trace, tool call trace, handoff trace, guardrail trace, custom event trace, command log, runtime log.

OpenAI Agents SDK records these as built-in trace objects. ([openai.github.io][5])

**Is NOT:** Trace is not receipt. Trace is not resolution. Trace is not proof of correctness. Trace can serve as evidence, but not conclusion.

**Ordivon rules:**
- Trace supports receipt
- Trace must not replace receipt
- Trace must be scoped and queryable
- Sensitive trace data must be governed

---

### 4.14 Receipt

**Definition:** A closure record for an execution, judgment, phase, or change.

**Must record:**
```
what was done
by whom / by which agent
under what authority
with what evidence
commands run
verification result
files changed
remaining debt
status: PASS / DEGRADED / BLOCKED
```

**Is NOT:** Resolution. Reality closure. Authority. Generated summary.

**Ordivon rules:**
- Receipt must declare scope
- Receipt must declare what remains unresolved
- Receipt cannot close debt without evidence
- Receipt cannot upgrade status without gate

---

### 4.15 Registry / Ledger / Governance Object

**Definition:**
- **Registry / Ledger** = state ledger for governance objects
- **Governance Object** = claim, evidence, authority, receipt, debt, lesson, policy candidate, etc.

**Examples:** `document-registry.jsonl`, `tool-registry.jsonl`, `skill-registry.jsonl`, `mcp-registry.jsonl`, `receipt-ledger.jsonl`, `debt-ledger.jsonl`, `policy-candidates.jsonl`.

**Is NOT:** Ledger is not reality itself. Registry is not total truth. Registration ≠ resolution. Status field ≠ real state.

**Ordivon rules:**
- Ledger consistency must be checked
- Registry must bind to source objects
- State transitions require evidence
- Debt cannot be deleted silently

---

## 5. Object Boundary Table

This is the core material for any Ordivon Skill.

| Confusion | Correct Boundary |
|-----------|-----------------|
| AGENTS.md vs Skill | AGENTS.md = always-resident project constitution; Skill = on-demand reusable method capsule |
| Skill vs Prompt | Skill = reusable workflow; Prompt = one-shot task instruction |
| Skill vs Tool | Skill = tells agent HOW to approach; Tool = action agent can call |
| Skill vs Policy | Skill = method; Policy = rule meaning |
| Tool vs Authority | Ability to call tool ≠ authorization to execute |
| MCP vs Tool | MCP = connection layer; Tool = concrete action |
| MCP Discovery vs Trust | Finding an MCP server/tool ≠ it is trustworthy |
| Agent vs Owner | Agent can execute; owner bears responsibility |
| Handoff vs Accountability | Handoff transfers task, not responsibility |
| Eval vs Test | Test = verifies software; Eval = verifies AI/agent behavior |
| Trace vs Receipt | Trace = process; Receipt = closure |
| Receipt vs Resolution | Receipt records action; Resolution requires real-world risk change |
| Checker vs Policy | Checker = enforcer; Policy = rule itself |
| READY vs Authorization | READY = prepared state; Authorization = granted permission |
| Generated View vs Source | Derived view must not impersonate source |
| Memory vs Truth | Memory is not factual source |
| AI Proposal vs Decision | AI suggestion is not human/organizational decision |
| Summary vs Truth | Summary is not original evidence |
| Analogy vs Proof | Analogy is not evidence |

---

## 6. Suggested Repo Directory Structure

An ideal skeleton for an AI-native project. Ordivon is not required to implement all of this immediately.

```
/
├── AGENTS.md
├── README.md
├── docs/
│   ├── current-truth/
│   ├── architecture/
│   ├── governance/
│   └── ai/
├── skills/
│   └── ordivon-core-method/
│       ├── SKILL.md
│       ├── references/
│       ├── assets/
│       └── examples/
├── prompts/
│   ├── engineering-reentry.md
│   ├── claim-audit.md
│   └── receipt-seal.md
├── tools/
│   ├── scripts/
│   └── cli/
├── mcp/
│   ├── servers.json
│   ├── permissions.yaml
│   └── trust-policy.md
├── policies/
│   ├── ai-output-contract.md
│   ├── tool-use-policy.md
│   ├── skill-trust-policy.md
│   └── claim-vocabulary.json
├── evals/
│   ├── agent/
│   ├── skill/
│   ├── red-team/
│   └── fixtures/
├── tests/
├── traces/
│   └── .gitignore
├── receipts/
│   ├── engineering/
│   ├── skill/
│   └── release/
├── registries/
│   ├── source-registry.jsonl
│   ├── skill-registry.jsonl
│   ├── tool-registry.jsonl
│   ├── mcp-registry.jsonl
│   ├── receipt-ledger.jsonl
│   └── debt-ledger.jsonl
└── checkers/
    ├── claim-evidence/
    ├── receipt-integrity/
    ├── skill-safety/
    └── mcp-permissions/
```

This is a target for future object placement, not an immediate build requirement.

---

## 7. Ordivon Current Materials → Object Model Mapping

### A. Philosophy / Method Kernel
```
L0 invariants (Evidence ≠ Claim, READY ≠ Authorization, etc.)
Ordivon definition
Intent → Evaluation → Authority → Execution → Receipt → Debt → Gate → Review → Policy
AI Observer role
```
**Classification:** Governance / Method Kernel

### B. Agent Constitution
```
AGENTS.md
docs/ai/*
agent-output-contract.md
phase boundary docs
AI onboarding docs
```
**Classification:** Agent Operating Layer

### C. Skill Candidate
```
ordivon-core-method
claim audit, execution frame
AI output governance
debt classification, receipt seal
```
**Classification:** Skill / Method Layer

### D. Prompt / Template
```
engineering-reentry prompt
stage prompts
project-ai-onboarding-playbook
minimal / standard / deep template pack
receipt template
```
**Classification:** Prompt / Command / Template Layer

### E. Tools / Scripts
```
scripts/*, scripts/governance/*
aos_submit.py, update-registry-stats.py
validate-* scripts
```
**Classification:** Tool / Script Layer

### F. Checkers / Gates
```
detect_overclaim, authority-gate
agentic-patterns, architecture-boundaries
doc-registry, receipt-integrity
update-registry-stats drift
```
**Classification:** Verification + Governance Enforcement Layer

### G. Registries / Ledgers
```
document-registry.jsonl, AOS registry
evidence ledgers, receipt ledgers
debt ledgers, gate manifests
```
**Classification:** Source + Governance Object Layer

### H. Receipts / Evidence
```
docs/governance/receipts/*
aos/receipts/*
evidence bundles, runtime evidence
```
**Classification:** Trace / Receipt Layer

### I. Product Surface
```
Ordivon Verify, AOS
template system
future skill package, future CLI
```
**Classification:** Adoption / Productization Layer

---

## 8. Minimal Ordivon Skill Scope

Derived from this object model, the `ordivon-core-method` Skill V0 must cover exactly five capabilities:

```
1. Claim Audit
2. Execution Frame
3. AI Output Governance
4. Debt Classification
5. Receipt Seal
```

It must help the agent distinguish:

```
claim vs evidence
skill vs tool
tool access vs authority
trace vs receipt
receipt vs resolution
generated view vs source
AI proposal vs decision
```

It must NOT do in V0:

```
automatically generate a complete repo governance system
automatically create MCP servers
automatically modify CI
automatically close debt
automatically authorize release
automatically declare production readiness
```

---

## 9. Governance Rules Summary

| Object | Core Governance Rule |
|--------|---------------------|
| Source Object | Must be diffable and verifiable; summary must not replace source |
| Generated View | Must declare source; must be reproducible |
| AGENTS.md | Minimal standing constitution; do not overload |
| Skill | Output = proposal; cannot authorize, close debt, suppress risk |
| Prompt | Describes intent; cannot override constitution or policy |
| Tool | Access ≠ authority; mutating tools require stronger gates |
| MCP | Discovery ≠ trust; every tool carries permission metadata |
| Agent | May propose/classify/draft; may not authorize/close/suppress |
| Workflow | Completion ≠ resolution; must declare debt |
| Policy | ≠ checker; change requires authority |
| Checker | Implements partial policy; pass ≠ policy satisfaction |
| Eval | Must bind to claim, include negatives, track regressions |
| Trace | Supports receipt; must not replace receipt |
| Receipt | Declares scope + remaining debt; cannot close without evidence |
| Registry | Consistency checked; state transitions require evidence |

---

## 10. Open Debts

These must not be silently closed. They are acknowledged gaps.

### Debt 1: Skill Trust Model Not Defined
We know skills carry supply-chain risk. Still needed:
- trusted skill / local skill / third-party skill / generated skill / experimental skill
- review gate per skill trust tier

### Debt 2: MCP Permission Model Not Defined
We know MCP is a capability surface. Still needed:
- read-only MCP / local mutation MCP / external mutation MCP / high-risk MCP
- approval gate per MCP tool class

### Debt 3: Trace-to-Receipt Relationship Not Formalized
Trace supports receipt but must not replace it. Still needed:
- which trace fields are required for which receipt type
- how to cite traces
- how to redact sensitive trace data
- how to prevent trace theater

### Debt 4: AI Memory Governance Not Defined
Memory is useful but easily contaminates truth. Still needed:
- user preference memory / project context memory / task-local memory / generated summary memory
- canonical source pointer
- staleness rules

### Debt 5: External Validation Not Done
This object model is internally consistent within Ordivon, but must be validated with real agent tasks:
- does it reduce overclaim?
- does it reduce false completion?
- does it make prompts clearer?
- does it improve agent output quality?
- does it reduce context burden?

---

## 11. Next Gate

Before entering Ordivon Skill Draft, these conditions must be met:

```
1. Object categories are frozen
2. Skill / Tool / MCP / AGENTS.md / Prompt / Receipt / Policy boundaries are explicit
3. Ordivon current materials are initially classified
4. V0 Skill scope is bounded to five capabilities:
   Claim Audit / Execution Frame / AI Output Governance / Debt Classification / Receipt Seal
5. Explicit declaration that V0 Skill does not authorize, close debt, or replace system
```

If these hold, we enter:

```
Phase 2: Ordivon Core Method Skill Design
```

---

## 12. Conclusion

This phase is not "sorting nouns" — it is building the foundation for all subsequent Ordivon engineering.

The real objects of AI-era projects are already forming rapidly across leading companies and communities:

```
AGENTS.md = project-level agent entry
Skills = reusable workflows
Prompts/Commands = task entrypoints
Tools = execution actions
MCP = external connection layer
Agents/Subagents = acting subjects
Evals/Tests = behavior verification
Traces = execution process evidence
Receipts = closure records
Policies/Guardrails = rules and boundaries
Registries/Ledgers = state and lifecycle
```

Ordivon's value is not replacing them, but giving them a stricter governance grammar:

```
Skill output is not authority.
Tool access is not execution authority.
MCP discovery is not trust.
Trace is not receipt.
Receipt is not resolution.
Eval pass is not reality pass.
Checker is not policy.
Generated view is not source.
Memory is not truth.
AI proposal is not decision.
```

This is the foundation for building Ordivon Skills.

**Define the object universe first. Encapsulate the method kernel second.**
This is the Ordivon way of constructing complex systems.

---

## References

[1]: https://agents.md/ "AGENTS.md — a README for agents"
[2]: https://help.openai.com/articles/20001066-skills-in-chatgpt/ "Skills in ChatGPT — OpenAI Help Center"
[3]: https://claude.com/docs/skills/overview "Skills overview — Claude.ai Documentation"
[4]: https://modelcontextprotocol.wiki/en/docs/concepts/resources "Resources — Model Context Protocol Wiki"
[5]: https://openai.github.io/openai-agents-js/guides/tracing/ "Tracing — OpenAI Agents SDK"
[6]: https://research.ibm.com/publications/measuring-agents-in-production "Measuring Agents in Production — IBM Research (ICLR 2026)"
[7]: https://arxiv.org/abs/2602.11988 "Evaluating AGENTS.md: Are Repository-Level Context Files Helpful for Coding Agents?"
[8]: https://huggingface.co/papers/2511.20920 "Securing the Model Context Protocol (MCP): Risks, Controls, and Governance"
[9]: https://arxiv.org/abs/2603.22489 "Model Context Protocol Threat Modeling and Analyzing Vulnerabilities to Prompt Injection with Tool Poisoning"
[10]: https://learn.microsoft.com/en-us/agent-framework/agents/skills "Agent Skills — Microsoft Learn"
[11]: https://arxiv.org/abs/2602.20867 "SoK: Agentic Skills -- Beyond Tool Use in LLM Agents"
[12]: https://arxiv.org/abs/2605.07358 "A Comprehensive Survey on Agent Skills: Taxonomy, Techniques, and Applications"
