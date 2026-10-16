# Long-Running OSS Contribution Work Composition Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** Establish a thin, reusable long-running multi-Agent work composition and apply it to the GitHub Top-1000 OSS contribution campaign without creating a new organization/task/workflow authority.

**Architecture:** Host remains semantic continuity/collaboration owner; Harness owns Agent Runs and current Agent Automation campaign/occurrence mechanics; Runtime owns Workspace/Job/Attempt execution evidence; Git/GitHub and upstream maintainers retain repository/public/acceptance truth. A generic operating profile centralizes re-entry and owner-routing law. The OSS profile specializes campaign stages and kill conditions without extending Host lifecycle state.

**Tech Stack:** Markdown capability/profile contracts, Host Social Work Fabric schema 10, Harness Agent Automation, Ordivon Runtime, Git/GitHub, pytest contract tests.

**Spec:** docs/architecture/LONG_RUNNING_MULTI_AGENT_WORK_OPERATING_PROFILE_R1.md

## Global Constraints

- Do not introduce Organization Service, Task Service, Board Service, scheduler, or another durable truth store.
- Work topology, social topology, execution topology, repository truth, and upstream acceptance remain distinct.
- Repository/Issue universe data stays dataset/provider state until durable Work admission is justified.
- Task/campaign-specific sequences are Plans/Operating Profiles; do not relabel them as industry SOPs.
- Skills provide procedure only and never effect/credential/acceptance authority.
- External GitHub writes remain separately effect-authorized.
- Current owner-native verification is mandatory before completion claims.

---

### Task 1: Add Multi-Agent Work Coordination capability package

**Files:**
- Create: catalogs/capabilities/packages/multi-agent-work.md
- Modify: catalogs/capabilities/packages/INDEX.md

**Interfaces:**
- Consumes: current capability-package contract and current Host/Harness/Runtime authority boundaries.
- Produces: one task-local package that routes durable multi-Agent work to existing mature owners.

- [x] Define outcome scope and mature external/local owners.
- [x] Define the six-step thin operating profile.
- [x] Define Work-admission and re-entry laws.
- [ ] Add the package to the common package index.
- [ ] Verify the package explicitly rejects duplicate Organization/Task/Board/scheduler ownership.

### Task 2: Add the reusable long-running operating profile

**Files:**
- Create: docs/architecture/LONG_RUNNING_MULTI_AGENT_WORK_OPERATING_PROFILE_R1.md

**Interfaces:**
- Consumes: Host Social Work Fabric, Harness/Agent Automation, Runtime, Skills/Tools, Git/GitHub natural-owner contracts.
- Produces: a small reusable interface for cold re-entry, present-state revalidation, method routing, execution, evidence, and semantic distillation.

- [x] Define system-of-interest and owner map.
- [x] Define Campaign/Wave/Case/Stage-marker vocabulary.
- [x] Define sparse Work topology and exact re-entry order.
- [x] Separate SOP/provider procedure, Plan/Operating Profile, Skill, Tool, and authority.
- [x] Record measured promotion gates for Temporal, Plane/OpenProject, MAF/LangGraph, n8n, and message bus.

### Task 3: Specialize the profile for OSS contribution

**Files:**
- Create: profiles/oss-contribution/README.md
- Create: profiles/oss-contribution/GLOSSARY.md

**Interfaces:**
- Consumes: Top-1000 census/frontier, GitHub/repository contribution rules, engineering method routing.
- Produces: campaign stage/disposition model and method bindings that a fresh Agent can recover and execute.

- [x] Define Campaign topology and stage model.
- [x] Define reproduction dispositions and minimal-repair RED/GREEN law.
- [x] Bind ECC, Matt, and Superpowers methods to the stages where they add value.
- [x] Define Host usage and cold re-entry recipe.
- [x] Define Case Work promotion law, public-write gate, security private route, and derived Contribution Ledger semantics.
- [x] Define one bounded first acceptance experiment instead of launching the full Top-1000 universe.

### Task 4: Add architectural regression tests

**Files:**
- Create: meta/next/tests/test_oss_contribution_operating_profile.py

**Interfaces:**
- Consumes: the package, generic profile, OSS profile, glossary, and package index.
- Produces: executable guards against authority collapse and state inflation.

- [ ] Assert the package is indexed and READY_FOR_REAL_WORK.
- [ ] Assert Host/Harness/Runtime/GitHub/Skill responsibilities stay separate.
- [ ] Assert the six-step thin interface is present.
- [ ] Assert the OSS profile is explicitly a Plan/Operating Profile, not an industry SOP.
- [ ] Assert stage markers do not extend Host lifecycle state.
- [ ] Assert FALSE/ALREADY_FIXED/NEEDS_INFO stop repair.
- [ ] Assert public GitHub writes remain effect-authority gated and security cases use the private route.
- [ ] Assert Work promotion remains sparse and Contribution Ledger is derived rather than authoritative.

### Task 5: Verify and adopt

**Files:**
- Review every changed file from the SourceCut.

**Interfaces:**
- Consumes: exact candidate diff and owner-native tests.
- Produces: an adopted local source candidate only if all checks are fresh-green.

- [ ] Run focused profile contract tests.
- [ ] Run the existing engineering method-routing tests that protect the same authority laws.
- [ ] Run git diff --check.
- [ ] Review the complete diff for accidental new authority/state.
- [ ] Commit the isolated candidate.
- [ ] Fast-forward canonical main only if it remains at the expected SourceCut and clean.
- [ ] Re-run focused verification on canonical main.
