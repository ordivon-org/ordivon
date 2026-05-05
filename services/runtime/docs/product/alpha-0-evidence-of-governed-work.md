# Alpha-0 Evidence of Governed Work

Status: **ACTIVE** | Date: 2026-05-02 | Phase: Alpha-0
Tags: `alpha-0`, `agent-work`, `trust-audit`, `ordivon-verify`, `coding-pack`
Authority: `source_of_truth` | AI Read Priority: 1

## Position

Ordivon should not run agents. Ordivon should make agent work trustworthy.

Alpha-0 is the external road from the internal Ordivon phase chain to a
developer-understandable product wedge: AI coding agent trust audit before
teams trust agent output.

This is not a new agent framework, CI replacement, GitHub bot, auto-fixer,
policy enforcement engine, schema standard, SDK, MCP server, or public release.

## Product Thesis

Modern agent stacks increasingly produce plans, diffs, tool calls, receipts,
memory notes, skills, traces, and review records. Runtimes can orchestrate this
work, but teams still need an independent way to ask whether the work claim is
trustworthy.

Ordivon Verify is the Alpha-0 entry point. It checks claims, receipts, tests,
diff evidence, debt, docs, gates, and review signals. It emits trust evidence
only. `READY` remains `READY_WITHOUT_AUTHORIZATION`: evidence sufficiency, not
permission to merge, deploy, execute, trade, publish, or call external systems.

## Execution Strategy

Use one entry point:

```bash
ordivon-verify check .
```

The command is a compatibility alias for the existing all-check path. The
product surface remains one report, not separate product lines for harness,
content, memory, or skills.

The report groups findings by surfaces:

| Surface | Alpha-0 meaning |
|---------|-----------------|
| claims | Agent completion and safety statements |
| receipts | Evidence records for claimed work |
| tests | Verification commands and results referenced by receipts |
| diff | Work artifact or code-change evidence |
| debt | Known gaps and hidden failure prevention |
| docs | Current truth and stale context checks |
| gates | Boundary and checker integrity |
| review | Human or structured review evidence |

## Alpha-0 Casebook Rule

Casebook evidence comes before public schemas.

Alpha-0 must collect 5-10 governed coding work cases before any external schema
claim. Existing objects such as TaskPlan, ExecutionReceipt, ReviewRecord,
TrustReport, and GovernanceDecision remain internal governance objects until
case evidence stabilizes them.

Each case must include:

- Agent claim
- Diff or work artifact
- Receipt
- Test evidence
- Review note
- Trust report
- Final disposition

## Red-Team Priorities

| ID | Alpha-0 handling |
|----|------------------|
| RT-01 config fail-open | Mitigated: config failure exits with code 3 |
| RT-02 DEGRADED normalization | Active: missing evidence is surfaced explicitly |
| RT-03 receipt semantic evasion | Casebook exposure; not fully solved in Alpha-0 |
| RT-04 lightweight validation | Casebook exposure; strict-mode hardening later |
| RT-05 phase fact-source drift | Active: README, AGENTS, and phase boundaries must align |

## Success Criteria

Alpha-0 is successful when Ordivon can demonstrate, on real AI coding work, that
it catches or clearly degrades:

- Overclaimed completion
- Missing or contradictory test evidence
- Hidden debt
- Stale source-of-truth references
- Review language that pretends to authorize action
- CandidateRule-to-Policy confusion
- Config or mode drift that weakens checks

## Explicit Non-Goals

- No agent runner
- No CI replacement
- No GitHub bot
- No auto-fixer
- No live finance or broker access
- No policy activation
- No public package publication
- No public schema standard claim
- No MCP/SDK/API server
