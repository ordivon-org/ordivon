# Ordivon Governance Adapter Use Cases

> v0 / prototype. Illustrative, not contractual.

## Use Case A — AI Coding Agent Claims Task Complete

An AI coding agent finishes a task and claims completion.

**Inputs:**
- WorkClaim: task description, changed files, test results
- EvidenceBundle: diff, test output, command logs
- CoverageReport: which files were covered

**Ordivon Decision:**
- READY: evidence supports claim, coverage declared, no blockers
- DEGRADED: evidence thin, some checks skipped, coverage partial
- BLOCKED: hard failure, contradiction, or forbidden action detected

**Adapter need:** Level 1 (Verify-only)

## Use Case B — MCP Server Exposes Tools

An MCP server with file-write and network-call capabilities wants
governance over its tool usage.

**Inputs:**
- CapabilityManifest: what tools exist, side-effect classes
- ToolCallLedger: what was called, with what effect
- AuthorityRequest: for governed actions

**Ordivon Decision:**
- Whether tool usage is governable (capabilities declared, side effects classified)
- Whether specific tool calls need pre-authorization
- Whether post-hoc ledger is sufficient or real-time is needed

**Adapter need:** Level 3 (Governance-native)

## Use Case C — CI Asks if Merge Can Proceed

A CI pipeline wants governance status before allowing merge.

**Inputs:**
- TrustReport from latest verification
- Gate manifest status
- Debt ledger: any new unresolved debt?
- CoverageReport: what was tested

**Ordivon Decision:**
- Evidence status summary (not auto-merge)
- Gate status: all gates pass?
- Debt delta: new debt since last merge?

**Adapter need:** Level 2 (Governed project)

## Use Case D — IDE Agent Modifies Repo

An IDE-integrated agent proposes code changes and claims branch ready.

**Inputs:**
- ExecutionReceipt: what commands ran, what changed
- EvidenceBundle: test results, lint results
- CoverageReport: which files were touched

**Ordivon Decision:**
- Whether completion claim is honest (receipt matches evidence)
- Whether claim scope matches actual changes
- Whether debt is declared or hidden

**Adapter need:** Level 2 (Governed project)

## Use Case E — Enterprise Agent Platform Wants Governance

An enterprise deploying multiple AI agents wants a governance layer
over all agent activity.

**Inputs:**
- Adapter manifest per agent
- ToolCallLedger across agents
- AuthorityRequest for sensitive operations
- TrustReport per agent per task
- Human approval hooks for NO-GO-class actions

**Ordivon Decision:**
- Adapter readiness tier (self-reported → governance-native)
- Governance posture per agent type
- Human-in-the-loop configuration

**Adapter need:** Level 3 (Governance-native)

## Use Case F — Financial or Broker Action Requested

An agent or system requests a financial, broker, or live-trading action.

**Inputs:**
- AuthorityRequest with side_effect_class = financial_action
- Requested action details

**Ordivon Decision:**
- **NO-GO.** Under current project boundaries, all financial/live/broker
  actions are explicitly prohibited.
- Override requires Stage Summit authorization — not programmatic.

**Adapter need:** Level 3, but action class is NO-GO by policy.

---

*Created: 2026-05-01*
*Phase: OGAP-1*
*Version: v0 (prototype)*
