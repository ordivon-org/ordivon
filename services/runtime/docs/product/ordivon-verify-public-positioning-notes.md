# Ordivon Verify — Public Positioning Notes

Status: **DRAFT** | Date: 2026-05-01 | Phase: PV-10
Tags: `product`, `verify`, `positioning`, `strategy`, `internal`
Authority: `proposal`

## 1. Product Wedge

Ordivon Verify is the **first external product wedge** of the broader Ordivon governance system. It is not the whole system. It is a focused, self-contained verification CLI that can be adopted independently.

The wedge strategy:
- Verify solves a specific, painful problem (agent completion honesty)
- It is adoptable without understanding the full Ordivon architecture
- It creates a path for users to discover the broader governance system later

## 2. Audience

Primary:
- **Solo AI-heavy developer** using Claude Code, Cursor, Copilot, or similar
- **Small engineering team** where AI agents and humans both open PRs

Secondary:
- **Governance-sensitive internal teams** already tracking debt, receipts, gates
- **Teams evaluating agent workflow trust tools**

## 3. Why Not Start with SaaS

- **Local-first builds trust** — no data leaves the user's machine
- **No upload required** — works on private repos without network access
- **Easier dogfood** — we can validate on our own fixtures before external release
- **CI-compatible** — JSON output + exit codes fit existing CI pipelines
- **Agent-native** — CLI + JSON is the right interface for AI agents

SaaS may come later, after product proof and customer validation.

## 4. Why Not Open-Source Full Ordivon Now

The core Ordivon repository contains:
- The full governance operating system (RiskEngine, Policy Platform, candidate rule system)
- Internal dogfood history (Phase 1–7P, DG Pack, Post-DG hygiene, PV phases)
- Financial adapters (Alpaca, read-only observation, paper execution)
- Architecture that is still evolving

Open-sourcing the entire repo too early would:
- Expose internal design iteration without curation
- Confuse potential users with internal-only features
- Create support burden for code not yet productized

**Recommended strategy**: Keep the core private. Curate Ordivon Verify as a public wedge. Open-source Verify first, then consider broader release.

## 5. Competitive Distinction

### Ordivon Verify vs. MCP (Model Context Protocol)

| | MCP | Ordivon Verify |
|---|-----|---------------|
| Purpose | Connects AI tools to data sources | Verifies AI agent work claims |
| Interface | Server protocol | CLI + JSON |
| What it does | Provides tool access | Checks receipt/debt/gate/doc truth |

MCP gives agents tools. Verify checks whether agents honestly reported what they did.

### Ordivon Verify vs. CI

| | CI (GitHub Actions, etc.) | Ordivon Verify |
|---|--------------------------|---------------|
| What it runs | Tests, lint, build | Meta-verification of claims |
| What it catches | Code bugs, build failures | Receipt contradictions, hidden debt, gate weakening |
| Failure meaning | Code is broken | Claims don't match evidence |

CI verifies code. Verify verifies trust signals.

### Ordivon Verify vs. AI Agents

Agents generate and act. Verify validates and reports. They are complementary:
- Agent produces work + receipt
- Verify checks the receipt against evidence
- Human decides based on both

## 6. Long-Term Direction

| Stage | What | Status |
|-------|------|--------|
| PV-1→10 | CLI + fixtures + skill + CI example | ✅ Complete |
| PV-11 | Public packaging decision (npm/pypi/repo) | Proposed |
| PV-Z | Productization mini summit | Future |
| Future | GitHub Action marketplace | After customer validation |
| Future | Read-only MCP server (verification tools) | Design-only |
| Future | Hosted / enterprise layer | After product proof |

## 7. Positioning Statements

### Elevator pitch

"Ordivon Verify checks whether AI-generated work is safe to trust — before you merge, hand off, or ship."

### For developers

"You already have CI. But CI doesn't check whether your AI agent honestly reported its test results. Ordivon Verify does."

### For team leads

"Your agents are producing code faster than you can review it. Ordivon Verify gives you a trust report per PR so you know where to look."

### For governance teams

"You track debt, receipts, gates, and documentation truth. Ordivon Verify makes that tracking machine-checkable."

## 8. Anti-Positioning (What Not to Say)

| Don't Say | Why |
|-----------|-----|
| "Ordivon Verify approves PRs" | Verify is evidence, not approval |
| "Ordivon Verify replaces code review" | Verify checks claims, not business logic |
| "Ordivon Verify is production-ready" | It's v0, prototype, dogfooded on fixtures |
| "Ordivon Verify has customers" | No external customer validation yet |
| "Ordivon Verify is open source" | Public packaging not finalized |
| "Ordivon Verify authorizes live trading" | Phase 8 DEFERRED, never authorized |
