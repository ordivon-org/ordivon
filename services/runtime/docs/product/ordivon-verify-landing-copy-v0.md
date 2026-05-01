# Ordivon Verify — Landing Copy v0

Status: **DRAFT** | Date: 2026-05-01 | Phase: PV-10
Tags: `product`, `verify`, `landing`, `public`, `draft`
Authority: `proposal`

---

## Hero

### Verify AI-generated work before you trust it.

Ordivon Verify checks receipts, debt, gates, and documentation truth so AI-assisted teams can detect skipped verification, hidden debt, and overclaimed completion — before merge or handoff.

[Run Ordivon Verify locally](#quickstart) · [Read the quickstart](ordivon-verify-quickstart.md)

---

## AI can move faster than your trust layer.

Coding agents produce output fast. But they also:

- Claim "all tests pass" — when tests were skipped
- Mark work "sealed" — with pending checks still open
- Write completion receipts that contradict themselves
- Hide pre-existing debt in prose without registering it
- Weaken verification gates without detection
- Confuse advisory rules with active policy

**Traditional CI verifies code. Ordivon Verify verifies claims.**

---

## How It Works

```
Step 1: Agent or human runs Ordivon Verify
Step 2: Ordivon checks receipts, debt, gates, docs
Step 3: Trust report returns READY / DEGRADED / BLOCKED
```

---

## Trust Report

| Status | Meaning | Action |
|--------|---------|--------|
| **BLOCKED** | Hard failure — contradictory claims detected | Fix before proceeding |
| **DEGRADED** | Clean receipts, missing governance | Human review recommended |
| **READY** | Selected checks passed | Evidence, not authorization |

---

## Built for Agent-Native Workflows

- **CLI-first** — single command, local-only
- **JSON output** — programmatic CI integration
- **Agent skill** — `SKILL.md` for AI coding agents
- **CI example** — GitHub Actions reference workflow
- **PR comments** — READY/BLOCKED/DEGRADED templates

---

## Trusted by Evidence, Not Authority

Ordivon Verify is evidence, not authorization:

- READY means selected checks passed. It does not approve merge, authorize deployment, or enable live trading.
- BLOCKED means contradictory claims were found. It is not tool failure — it is governance success.
- DEGRADED means warnings exist. It is not failure — it is an honest midpoint before full governance.

---

## Current Maturity

Prototype / v0. Local-first CLI. Dogfooded on fixtures.

Not yet:
- Published as a package
- Validated by external customers
- Open-sourced (public repo boundary under design)
- Available as SaaS or hosted service

---

## Private Core, Public Wedge

Ordivon Verify is the first product wedge of the broader Ordivon governance system. The core repository contains the full governance OS and internal dogfood history. Public packaging of Ordivon Verify is under design.

---

## Next Steps

- [Quickstart](ordivon-verify-quickstart.md)
- [Adoption Guide](ordivon-verify-adoption-guide.md)
- [Agent Skill](../../skills/ordivon-verify/SKILL.md)
- [CI Example](../../examples/ordivon-verify/README.md)
