# Repo Governance Pack — Product Strategy

Status: **STRATEGY**
Date: 2026-04-28
Phase: 3.1
Tags: `product`, `repo-governance`, `wedge`, `mvp`

## 1. Purpose

Define Ordivon's first product wedge: a governance layer for AI coding agents
and repo workflows. This document answers *who*, *what problem*, *why now*,
and *what minimum version looks like*.

## 2. Target Users

- Solo developers using AI coding agents (Claude Code, Codex, Copilot)
- Small teams (2-10) sharing a codebase with AI-assisted development
- Tech leads who want to let AI help but need guardrails

## 3. Real Pain Points

| Pain Point | Current State | Ordivon Solution |
|------------|--------------|-----------------|
| "What did the AI change and why?" | Commit messages are vague or missing | Structured Intake with task_description + reasoning |
| "Did the AI touch files it shouldn't?" | Discovered in code review, too late | Pre-execution governance: forbidden path = reject |
| "Did the AI write tests?" | Optional, often skipped | Missing test_plan = escalate |
| "Was this high-risk change reviewed?" | Manual process, easily bypassed | estimated_impact=high → escalate |
| "How do we learn from AI mistakes?" | Ad-hoc postmortems | Review → Lesson → CandidateRule draft |
| "Are our governance rules actually enforced?" | Policy lives in README | CI gate + runtime evidence audit |

## 4. Why Repo Governance Is the First Product Wedge

Coding governance has structural advantages over every other Ordivon domain:

- **High frequency**: dozens of AI code changes per day vs. a few trades per week
- **Rich evidence**: git diff, CI logs, test results, PR comments already exist
- **Clear boundaries**: file paths, permissions, protected branches are well-defined
- **Immediate feedback**: CI red → fix → CI green in minutes
- **Team value**: one team's governance rules can be shared and enforced
- **Low regulatory risk**: no financial licenses, no PII, no HIPAA required

Finance remains a validated Pack. But as a product wedge, coding governance
reaches more users, generates more evidence, and proves Ordivon's value faster.

## 5. What Ordivon Provides (MVP)

```
User: "AI, refactor the auth middleware and add tests."
↓
Intake: task_description, file_paths, estimated_impact, test_plan
↓
Governance: CodingDisciplinePolicy → execute / escalate / reject
↓
Receipt: governance decision + reasons recorded
↓
Outcome: CI result (pass / fail)
↓
Review: if CI fails, structured postmortem
↓
Lesson: extracted learning
↓
CandidateRule(draft): proposed new governance rule
```

## 6. What Ordivon Does NOT Provide (MVP)

- Does NOT execute code
- Does NOT modify files
- Does NOT connect to shell, MCP, or IDE agents
- Does NOT replace CI — it *augments* CI with governance classification
- Does NOT auto-commit or auto-merge
- Does NOT auto-promote CandidateRules to active Policy

## 7. MVP Scope

| Layer | What's Included | What's Deferred |
|-------|----------------|-----------------|
| Intake | CLI: `ordivon repo-intake` with task_description, file_paths, impact, test_plan | IDE plugin, web UI |
| Governance | CodingDisciplinePolicy (reject/escalate/execute) | Custom per-repo policies |
| Receipt | JSON output with decision + reasons | Database persistence |
| Evidence | Runtime evidence checker | DB-backed audit for repo governance |
| Review | Manual review path (service layer exists) | Automated review triggers |
| Learning | Lesson → CandidateRule draft (service layer exists) | Auto-generation from CI failures |

## 8. Competitive Comparison

| Tool | Governance Classification | Pre-Execution Gate | Evidence Receipt | Rule Learning |
|------|--------------------------|-------------------|-----------------|---------------|
| CI (GitHub Actions) | No — pass/fail only | No | Logs | No |
| Claude Code permissions | Allow/deny rules | Yes — but no risk classification | No | No |
| MCP tools | Tool-level allow/deny | Yes — but binary | No | No |
| Agent frameworks (AutoGen, LangGraph) | Optional guardrails | Yes — but no structured intake | Traces | No |
| **Ordivon Repo Governance** | **3-tier: execute/escalate/reject** | **Yes — with reasons** | **Yes — structured** | **Yes — Review→Lesson→CandidateRule** |

Ordivon's differentiation: governance is not a binary yes/no. It's a
classification with reasons, evidence, and a learning loop.

## 9. Success Metrics

| Metric | Target |
|--------|--------|
| Intakes classified correctly | 100% on eval corpus (20 cases initially) |
| Forbidden path rejections | 100% catch rate |
| High-impact escalations | 100% flag rate |
| Missing test_plan escalations | 100% flag rate |
| CandidateRule drafts generated | >0 from real usage within 2 weeks |
| User-reported false positives | <10% of classifications |

## 10. Risks

| Risk | Mitigation |
|------|-----------|
| Too much friction — developers bypass governance | Make CLI fast (<2s), keep MVP minimal |
| Governance rules too strict → false rejections | Start with advisory, not blocking; iterate on eval corpus |
| Perceived as "just another CI tool" | Emphasize governance classification + learning loop vs. pass/fail |
| No adoption without IDE integration | CLI first; IDE adapter only after CLI validated |
