# Ordivon External Adapter Integration Levels

> v0 / prototype. Not a public API commitment. Not a release.

## Level 1 — Verify-only

The simplest integration. An external project provides receipts and work
claims. Ordivon Verify checks them against repository reality.

**Required from adapter:**
- WorkClaim JSON or equivalent structured claim
- EvidenceBundle with diffs, test results, or command outputs
- Basic coverage declaration (which files were touched)

**Ordivon provides:**
- TrustReport: READY / DEGRADED / BLOCKED
- Evidence-only validation — no authority decision

**Example:** A developer claims "refactoring complete." They provide a
diff and test results. Ordivon Verify confirms the diff is consistent
with the claim and tests pass. TrustReport: READY.

## Level 2 — Governed project

The external project adopts Ordivon governance objects — debt ledger,
gate manifest, coverage summary, document registry.

**Required from adapter:**
- Receipts per governance checkpoint
- Debt ledger tracking known issues
- Gate manifest declaring verification gates
- Coverage summary per checkpoint
- Document registry or equivalent doc inventory

**Ordivon provides:**
- Scoped GovernanceDecision with declared universe
- Coverage report with discovery method
- Debt status summary

**Example:** An open-source project adopts Ordivon Verify as CI gate.
Each PR must pass gate manifest. Coverage is tracked per PR.
GovernanceDecision: READY (scoped to PR diff).

## Level 3 — Governance-native adapter

Full OGAP participation. The external system exposes all 10 OGAP objects
and participates in the governance loop.

**Required from adapter:**
- Full OGAP object model (WorkClaim, EvidenceBundle, ExecutionReceipt,
  CoverageReport, CapabilityManifest, AuthorityRequest, ToolCallLedger,
  DebtDeclaration, GovernanceDecision, TrustReport)
- Adapter trust level declared
- Side-effect classes declared per action
- Authority requested for governed actions

**Ordivon provides:**
- Full governance loop: Intent → Evaluation → Authority → Execution →
  Receipt → Debt → Gate → Review → Policy
- GovernanceDecision with evidence chain
- TrustReport for human/agent/CI consumption

**Example:** An AI coding agent framework integrates OGAP. Each agent
task produces a WorkClaim. The agent's tool calls are logged in
ToolCallLedger. Repo-modifying actions require AuthorityRequest.
Ordivon emits GovernanceDecision per task.

## Not Yet Defined (Future)

| Feature | Status |
|---|---|
| OGAP over HTTP | Not implemented |
| OGAP MCP server | Not implemented |
| OGAP SDK | Not implemented |
| OGAP CI integration | Not implemented |
| OGAP IDE plugin | Not implemented |
| OGAP real-time streaming | Not defined |
| OGAP multi-adapter orchestration | Not defined |

---

*Created: 2026-05-01*
*Phase: OGAP-1*
*Version: v0 (prototype)*
