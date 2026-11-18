# Engineering Method Kernel — selective extraction from GitHub Spec Kit

Status: **REGISTERED_FOR_ENGINEERING_USE**  
Registered: 2026-09-14

## Purpose

This record captures the small set of reusable engineering practices extracted from GitHub Spec Kit that fit Ordivon's current operating model.

It is **not** a Spec Kit installation, fork, compatibility layer, workflow engine, private lifecycle standard or new source of task truth. GitHub Spec Kit remains an external reference implementation and method source. Execution stays with replaceable tools such as Codex, Git, CI, Runtime, Playwright and domain-specific validators.

## Why this subset exists

The full Spec Kit product includes CLI setup, templates, scripts, integrations, presets, extensions, bundles, workflow control, feature numbering, task artifacts and other ecosystem/product concerns. Those are useful for Spec Kit's general distribution problem but overlap with, or are unnecessary for, Ordivon's thinner compositional architecture.

Ordivon therefore retains only the cognitive and verification operations that improve real engineering work without introducing another orchestration or state layer.

## Kernel

### 1. FRAME

Capture only the information needed to define the intended change:

- **Goal** — what real state should change?
- **Scope** — what is in and out?
- **Constraints** — what conditions may not be violated?
- **Acceptance** — what observable evidence is sufficient to call the result successful?
- **Assumptions** — what material defaults or interpretations were made?

Rules:

1. Separate requirements from implementation choices.
2. Requirements must be verifiable.
3. Technical facts may themselves be requirements when the task is technical; do not force every requirement into business/user-story language.
4. Prefer a reasonable default over asking the user when uncertainty is low-impact.
5. Record material assumptions when they affect interpretation or verification.
6. Clarify only when uncertainty is both significant and decision-relevant.
7. Before trusting the frame, lint it against the risk domains relevant to the task: scope, interfaces/data, failure modes, security, operations, constraints and acceptance. Do not run irrelevant generic checklists.

A useful decision rule is:

`clarification priority ~= impact x uncertainty`

Unknown details with low expected decision value should not block work.

### 2. PLAN

Plan only to the depth justified by risk, uncertainty and coordination cost.

Record, when useful:

- **Approach** — the chosen technical direction.
- **Alternatives** — consequential mature alternatives considered or rejected.
- **Touchpoints** — systems, repositories, interfaces or external owners affected.
- **Risks** — material failure modes and rollback concerns.
- **Verification** — how acceptance will actually be demonstrated.

Rules:

8. A plan records consequential decisions, not a ceremonial step list.
9. Search mature standards, methods and implementations before inventing a local mechanism.
10. If a real unknown requires research, invoke the Research capability rather than creating an Engineering-local research subsystem.
11. Execution decomposition may express dependencies and parallelism, but it can remain transient unless coordination requires persistence.

### 3. EXECUTE

Use the most suitable mature execution provider available for the task.

Typical providers include Codex, repository-native tools, Git, build/test systems, CI, Runtime, Playwright, Ansible, OpenTofu or domain-specific tooling.

The kernel does not own an implementation command, task database, workflow engine or agent runtime.

Rules:

12. Testing is conditional on the task and evidence needs; verification is not optional.
13. Avoid adding significant work that has no originating requirement, constraint, accepted decision or discovered blocking necessity.

### 4. VERIFY

Verification compares the **current real state** with the FRAME and accepted PLAN decisions. It does not rely on completion claims, task status or tool exit status alone.

Prefer the strongest practical evidence, roughly:

1. observed target/live behavior;
2. end-to-end or integration evidence;
3. automated behavioral tests;
4. build/static/formal checks;
5. source/configuration inspection;
6. executor or agent assertion.

Lower layers may support higher layers but should not replace them when stronger evidence is feasible and material.

Classify mismatches at least as:

- **missing** — required behavior/state is absent;
- **partial** — present but insufficient;
- **contradicts** — current state conflicts with an accepted requirement/decision;
- **unrequested** — significant implementation exists without a justified originating requirement/decision.

Use bidirectional traceability without requiring a heavyweight traceability database:

- every material requirement should map to evidence;
- every significant change should map back to a requirement, constraint, accepted decision or necessary discovered dependency.

If a material gap remains: repair the gap, then verify again against current reality.

## Context discipline

Load the minimum sufficient context for the current decision or verification step. Expand only when evidence or uncertainty requires it. Do not preload every historical artifact merely because it exists.

## Risk-adaptive use

Process depth should scale approximately with:

`risk + uncertainty + coordination cost`

not with the nominal size or label of the feature.

Typical profiles:

### Small / low-risk change

`FRAME -> EXECUTE -> VERIFY`

A short in-context frame may be sufficient; no persistent planning artifact is required.

### Ordinary engineering change

`FRAME -> PLAN -> EXECUTE -> VERIFY`

Persist a short engineering note only if it improves handoff, auditability or later maintenance.

### High-risk / high-uncertainty / high-coordination change

Add only the controls justified by the task, for example:

- explicit clarification;
- mature external research;
- independent review;
- backup/rollback plan;
- staged rollout;
- observability;
- security review;
- independent or domain-specialist verification;
- durable decision records.

These controls are activated by evidence of need, not by a universal Ordivon workflow.

## What was deliberately not adopted from Spec Kit

- Spec Kit CLI or runtime dependency;
- `.specify/` project scaffolding;
- mandatory constitution lifecycle;
- mandatory user-story/P1/P2/P3 representation;
- feature numbering and branch semantics;
- standalone clarify/checklist/analyze commands;
- mandatory `spec.md`, `plan.md`, `tasks.md`, `research.md`, `data-model.md`, `contracts/` or `quickstart.md` artifacts;
- append-only task-history semantics;
- Spec Kit workflow engine;
- integrations for many coding agents;
- presets, extensions and bundles as infrastructure;
- a second orchestration layer around Codex/Runtime;
- a second task/state authority.

## Relationship to Ordivon

This kernel is an Engineering package heuristic inside the active working set. It does not define Ordivon's architecture.

Ordivon's durable rules remain external-first composition, thin ownership, replaceable providers, evidence over assertion and reality as the final verification boundary.

For any real task, the kernel should disappear into the work rather than become another thing that must be operated or maintained.
