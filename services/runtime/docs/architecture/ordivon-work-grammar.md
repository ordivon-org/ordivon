# Ordivon Work Grammar

Status: **DOCUMENTED**
Date: 2026-04-28
Wave: Docs-Lang-1
Tags: `language`, `grammar`, `constitution`, `prompt`, `thinking`

## 1. Purpose

Define a stable work language for Ordivon — a set of thinking rules that
constrain how tasks are framed, how boundaries are respected, how evidence
is demanded, and how learning is upgraded.

This is not a style guide. It is a **work grammar**: the structural rules
that prevent semantic drift, task inflation, and governance decay across
waves of development.

## 2. Why Ordivon Needs Its Own Work Language

Ordivon is no longer just a code project. It now has:

- A philosophical foundation (recursive governance externalization)
- Governance principles (Intake → Governance → Receipt → Review → Lesson)
- Core / Pack / Adapter boundaries (ADR-006 severity protocol)
- A CandidateRule → Policy upgrade path
- Two Packs (Finance + Coding) validating Core agnosticism
- T0 toolchain + dogfood evidence + repo governance baseline
- A 12-layer reflexive governance matrix

Without a unified language, each new wave risks three failures:

1. **Semantic drift** — the same word means different things across waves.
2. **Task inflation** — a small fix expands into a large refactor.
3. **Governance decay** — completing the task overrides the first principles.

A work grammar prevents these by locking not just vocabulary, but
**judgment patterns, task structure, evidence standards, and upgrade paths.**

## 3. Core Sentence

The Ordivon work grammar is summarized in one sentence:

> 先定边界，再拆假设；先看风险，再做行动；先要证据，再谈完成；先做草案，再升规则。

English:

> Define boundaries before action. Reduce claims to assumptions. Demand
> evidence before declaring completion. Draft rules before enforcing them.

## 4. The 12 Rules

### Rule 1: Stage Identity First

Every task must declare its identity before any action.

**Standard form:**
```
当前阶段：Wave X — Task Name。
任务身份：[what this wave IS].
本阶段只做 X，不做 Y。
```

**Anti-pattern:** "Let me continue working on it."
**Ordivon pattern:** "Current stage: Wave E1 — Runtime Evidence Integrity Checker. This wave only adds a read-only checker. It does not connect OpenTelemetry."

Without stage identity, tasks drift.

---

### Rule 2: Non-Goals Are Hard Boundaries

The most important part of an Ordivon prompt is what must NOT be done.

**Standard form:**
```
禁止：
- 不改 API
- 不改 ORM schema
- 不改 OpenAPI snapshot
- 不接 shell / MCP / IDE agent
- 不做 Policy promotion
- 不做大重构
```

Non-goals are the moat around the task. They prevent AI agents from
expanding a focused fix into an unrequested refactor.

---

### Rule 3: Claims Become Assumptions

A conclusion is not a fact until verified. Every claim must be stated
as a hypothesis with verification criteria.

**Standard form:**
```
当前假设：
A. L9 Runtime 是最薄弱层。
B. runtime evidence checker 是最小高杠杆修复。
C. 不需要立即接 OpenTelemetry。
请先验证这些假设是否成立。若不成立，停止并报告。
```

**Anti-pattern:** "This approach is correct."
**Ordivon pattern:** "Current assumption: approach A is correct because X. To verify: run Y and check Z."

---

### Rule 4: Experience Cannot Directly Become Policy

This is the Ordivon invariant: a single incident does not create a
permanent rule. The path is always:

```
Review → Lesson → CandidateRule(draft) → Human review → Policy (or not)
```

**Standard form:**
```
本次发现只能生成 CandidateRule draft。
不得自动 accepted_candidate。
不得自动 Policy promotion。
```

This rule governs both the system AND the human: a single CI failure
does not create a new blocking gate.

---

### Rule 5: Completion Requires Receipt

A task is not complete until there is verifiable evidence.

**Standard form:**
```
完成后必须输出：
- 修改文件列表
- 测试命令与结果
- git diff --stat
- 是否改 API
- 是否改 ORM schema
- 是否改 OpenAPI snapshot
- 是否触发副作用
- 越界检查
```

**Anti-pattern:** "Task complete."
**Ordivon pattern:** "Commit: a1b2c3d. 3 files changed. Unit: 526/526 PASS. Architecture: clean. No API/ORM/snapshot changes."

---

### Rule 6: Scope / Boundary / Evidence

Every Ordivon task prompt must have these three structural sections:

- **Scope** — what this wave handles.
- **Boundary** — what this wave must never touch.
- **Evidence** — how completion is verified.

This is the minimum grammatical structure for an Ordivon task.

---

### Rule 7: Severity Protocol

Severity is not just a code protocol — it is a thinking protocol.

| Severity | Meaning | Action |
|----------|---------|--------|
| reject | Must block | Stop, do not proceed |
| escalate | Needs human judgment | Pause, report, wait |
| execute | Safe to proceed | Continue |
| advisory | Record, don't block | Log and continue |

Every risk identified in a task should be classified by severity.
This prevents the collapse of all concerns into "it might be bad."

---

### Rule 8: Stop Conditions

Every prompt must define when to stop and report, not push through.

**Standard form:**
```
停止条件：
- 如果需要 ORM schema 变更，停止并报告。
- 如果 OpenAPI snapshot 出现大规模 diff，停止并报告。
- 如果发现 Core import Pack，停止并报告。
- 如果测试失败不是本阶段范围，停止并报告。
```

Stop conditions are the hard brakes against task inflation.

---

### Rule 9: Audit Before Implementation

Before any modification, do a read-only audit.

**Standard form:**
```
Phase 0: 只读审计 — 理解现状。
Phase 1: 输出计划 — 确认最小修改面。
Phase 2: 确认 — 验证假设。
Phase 3: 实现 — 最小改动。
Phase 4: 封口 — 回归验证。
```

Never let an IDE or AI agent start modifying files without first reading
and understanding the affected surface.

---

### Rule 10: Every New Capability Must Have a Dogfood Path

If a capability cannot be dogfooded, it is too abstract to ship.

**Standard form:**
```
新增能力必须回答：
- 如何构造 5-10 个真实样本？
- expected / actual 如何记录？
- 失败如何进入 Review？
- 是否产生 evidence report？
```

This ensures capabilities are testable in practice, not just in theory.

---

### Rule 11: The Codebase Is a Governed Ordivon Object

The same Ordivon governance loop applies to the repository itself:

| Ordivon Concept | Repo Governance |
|-----------------|-----------------|
| Intake | PR brief / task plan |
| Governance | CI gates / architecture checker |
| Receipt | Test logs / snapshots / diff |
| Outcome | CI result / dogfood result |
| Review | Postmortem / audit |
| Lesson | Regression test / new checker |
| CandidateRule | Proposed CI gate (advisory) |
| Policy | Required blocking gate |

Any engineering prompt must ask: does this failure warrant a test,
a checker, a doc update, or just a fix?

---

### Rule 12: Philosophy Must Externalize Into Executable Structure

A governance principle that exists only in prose is not yet real.

**Standard form:**
```
请把这个原则外化为：
- 一个术语定义；
- 一个测试；
- 一个 checker；
- 一个文档段落；
- 一个 CI gate；
- 一个 dogfood 场景。
```

This is the recursive governance externalization loop: thought → tool → behavior → thought.

## 5. Ordivon Vocabulary

| Term | Definition |
|------|-----------|
| Intake | Structured intent entry point, not action authorization |
| Governance | Pre-action risk judgment, not execution |
| Severity | Pack → Core generic risk protocol (reject/escalate/execute) |
| Receipt | Action/plan evidence index, not model self-claim of completion |
| Outcome | Result observation, not review |
| Review | Explanation of variance between expected and actual outcome |
| Lesson | Experience extracted from Review |
| CandidateRule | Reviewable rule draft, NOT Policy |
| Policy | Human-approved stable rule |
| Truth Source | Authoritative data origin (SQLAlchemy ORM for PFIOS) |
| Evidence | Material supporting a judgment |
| Source Ref | Traceable reference (e.g., `review:abc123`) |
| Boundary | Module-level constraint that must not be crossed |
| Drift | System deviation from declared identity |
| Dogfood | Testing system judgment with real/realistic samples |
| Seal | Wave closure verification |
| Hard Gate | Check that blocks on failure |
| Advisory Gate | Check that records but does not block |
| Fitness Function | Automated check of an architectural principle |
| Pack | Domain bundle (models + policy + tool refs) |
| Core | Governance engine; Pack-agnostic; never imports Pack types |
| Adapter | Execution bridge between Capability and Domain service |

## 6. Relationship to Existing Docs

| Document | Relationship |
|----------|-------------|
| `repo-governance-baseline.md` | This grammar is the *method*; that baseline is the *inventory* |
| `ADR-006-pack-policy-binding.md` | The severity protocol is the *implementation* of Rules 2 and 7 |
| `LANGUAGE.md` | That doc defines project nouns; this doc defines work verbs |
| `ordivon-system-definition.md` | That doc defines the *system*; this doc defines the *language* |

## 7. Anti-Bureaucracy Warning

This work grammar exists to **sharpen**, not to **bloat**.

Rules that must be guarded:

- **CandidateRule is not Policy.** A single CI failure does not create a
  permanent blocking gate. Three real interceptions + human review first.

- **Stop conditions prevent expansion, not progress.** If a stop condition
  fires, it means "report and wait," not "the wave failed."

- **Receipt is evidence, not ceremony.** A 2-line output block counts.
  A 20-page report is noise unless the task demands it.

- **The grammar itself is a CandidateRule.** It can be refined based on
  real use. It has not been promoted to Policy.
