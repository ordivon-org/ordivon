# Ordivon AI Onboarding

> **Last updated**: Phase DG-2 (2026-04-30)
> **Active phase**: Phase 7P — CLOSED | DG-2 — ACTIVE (Document Registry + Checker)
> **Next**: DG-3 — Wiki surface or DG-4 — freshness checker

For any AI agent (ChatGPT, Claude, Codex, Copilot, IDE assistant) working in this repository.

## Quick Start

Read these in order on first visit:

1. **ordivon-root-context.md** — what Ordivon is (and is not)
2. **architecture-file-map.md** — where things live
3. **current-phase-boundaries.md** — what's active, what's deferred, what's NO-GO
4. **agent-output-contract.md** — required output shape for every AI task receipt
5. **agent-working-rules.md** — how to operate within Ordivon governance
6. **task-prompt-template.md** — template for compressed phase prompts

If you're a human reading this: these docs are the AI-facing root context pack. They
replace the need to paste 3000-word briefs into every prompt. A compressed phase
prompt + these docs should suffice for most tasks.

## Reference Hierarchy

```
docs/ai/README.md                          <-- you are here
docs/ai/ordivon-root-context.md            identity + governance doctrine
docs/ai/architecture-file-map.md           code tree + architecture layers
docs/ai/current-phase-boundaries.md        what's live, what's deferred
docs/ai/agent-output-contract.md           required output shape for every AI task receipt
docs/ai/agent-working-rules.md             operating rules for AI agents
docs/ai/task-prompt-template.md            reusable compressed prompt format

AGENTS.md (repo root)                      compact entry point for IDE agents
docs/governance/README.md                  Document Governance Pack (accepted)
docs/governance/ai-onboarding-doc-policy.md AI read path specification
docs/runbooks/ordivon-agent-operating-doctrine.md   full doctrine (canonical)
docs/product/ordivon-stage-summit-phase-4.md        Phase 4 close
docs/product/policy-platform-stage-summit-phase-5.md Phase 5 close
docs/product/alpaca-paper-dogfood-stage-summit-phase-7p.md Phase 7P close
```

## When to Read What

| Situation | Read |
|-----------|------|
| First time in this repo | root-context + architecture-file-map |
| Starting a new phase | current-phase-boundaries + task-prompt-template |
| Before committing | agent-working-rules §self-check |
| Writing a task output/receipt | agent-output-contract |
| Unclear what's allowed | current-phase-boundaries |
| Writing a task prompt for Ordivon | task-prompt-template |
| Understanding doc rules | docs/governance/ai-onboarding-doc-policy.md |
