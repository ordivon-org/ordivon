# Ordivon Governance Adapter Protocol v0 (OGAP)

> **v0 / prototype / internal design.** Not a public standard. Not a release.
> Not a live API. Not an MCP server. Not an agent framework.

## Identity

OGAP = **Ordivon Governance Adapter Protocol.**

OGAP is the protocol layer for external systems to make their work
governable by Ordivon.

OGAP does not:
- Replace agents, MCP servers, CI systems, IDEs, or frameworks.
- Execute work by itself.
- Authorize action by mere compatibility.
- Grant approval because an adapter exists.

### Positioning

```
Agents act.
Tools execute.
Frameworks orchestrate.
Ordivon governs.
```

External systems may act, execute, orchestrate, or propose.
Ordivon provides governance, verification, coverage, authority,
receipt, debt, and trust-report semantics.

An OGAP-compatible adapter is governable, not approved.

## Integration Levels

### Level 1 — Verify-only

External project provides receipts and work claims.
Ordivon Verify checks claims against repository reality
and emits a trust report.

- Input: work claims, diffs, test results
- Output: READY / DEGRADED / BLOCKED trust report
- Governance: minimal — evidence check only
- Adapter effort: low

### Level 2 — Governed project

External project provides receipts, debt ledger, gate manifest,
coverage summary, and document registry (or equivalents).

Ordivon can provide READY / DEGRADED / BLOCKED over a
declared governance universe.

- Input: receipts, debt, gates, coverage, docs
- Output: scoped governance decision with coverage summary
- Governance: full passive — if all governance objects are present
- Adapter effort: medium

### Level 3 — Governance-native adapter

External system exposes capability manifest, tool-call ledger,
authority request, coverage report, execution receipt,
debt declaration, and trust report.

Designed for agent frameworks, MCP servers, CI systems, IDEs,
and enterprise workflows.

- Input: full OGAP object model
- Output: GovernanceDecision + TrustReport with evidence chain
- Governance: full active — adapter participates in governance loop
- Adapter effort: high

### Critical Boundary

Level 3 compatibility is **not** authorization.
An adapter can request governance; it cannot grant itself governance approval.

## Decision Semantics

| Decision | Meaning | NOT |
|---|---|---|
| READY | Evidence supports selected checks | Authorization to execute |
| DEGRADED | No hard contradiction; missing coverage/warnings | Clean bill of health |
| BLOCKED | Hard failure or contradiction | Partial success |
| HOLD | Insufficient information; pending human decision | Approved pending |
| REJECT | Proposal violates policy/boundary | Fixable without review |
| NO-GO | Explicitly prohibited action class | Negotiable |

Invariants:
- READY ≠ approval
- Evidence ≠ authority
- Capability ≠ authorization
- Receipt ≠ review
- Adapter-compatible ≠ governed-approved

## Capability vs Authority

A CapabilityManifest declares what an external system **can** do:

| Capability | Description |
|---|---|
| can_read | Read files/content |
| can_write | Write/delete files |
| can_run_shell | Execute shell commands |
| can_call_network | Make network requests |
| can_call_tools | Invoke external tools |
| can_modify_repo | Modify repository state |
| can_create_pr | Create pull requests |
| can_access_secrets | Access secrets/credentials |
| can_call_external_api | Call external APIs |
| can_trigger_ci | Trigger CI/CD pipelines |
| can_request_human_review | Request human review |

An AuthorityRequest declares what the system is **asking permission** to do:

| Field | Description |
|---|---|
| requested_action | What action is proposed |
| side_effect_class | Class of side effects |
| risk_level | Estimated risk |
| required_gate | Minimum gate requirement |
| human_approval_required | Whether human approval is needed |
| rollback_plan | How to undo if needed |
| evidence_required | What evidence must be provided |
| no_go_check | Whether action is explicitly prohibited |

**Core invariant: can_X does not imply may_X.**

## Side-Effect Classes

| Class | Default Decision | Evidence Required |
|---|---|---|
| read_only | READY | Self-report acceptable |
| workspace_write | DEGRADED | Diff + rollback plan |
| repo_write | DEGRADED | Diff + tests + rollback |
| shell_execution | HOLD | Command log + output |
| network_read | DEGRADED | URL + response summary |
| external_write | HOLD | Target + data + rollback |
| secret_access | HOLD | Justification + scope |
| financial_action | NO-GO | Stage Summit override only |
| production_action | NO-GO | Stage Summit override only |
| policy_activation | NO-GO | Stage Summit override only |
| irreversible_action | NO-GO | Stage Summit override only |

Financial action, broker/API, live trading, Policy activation, and
RiskEngine enforcement default to NO-GO.

## Coverage Model

OGAP adopts COV-1/COV-2 coverage principles:

1. Coverage precedes confidence.
2. PASS is scoped.
3. Silent omission is not governance.
4. Out-of-scope requires reason.
5. Registry must reconcile with reality.
6. A checker is only as trustworthy as its discovery model.

CoverageReport fields:
- claimed_universe — what the adapter claims to govern
- discovery_method — how objects were discovered
- included_objects — what was covered
- excluded_objects — what was excluded (with reason)
- unknown_objects — what was not discovered
- pass_scope_statement — what PASS actually means

## Adapter Trust Levels

| Level | Evidence Required |
|---|---|
| untrusted | None |
| self-reported | Adapter's own claims |
| evidence-backed | Diffs, logs, test results |
| coverage-aware | Declared universe + discovery method |
| governance-native | Full OGAP object model |
| human-approved | Specific decision reviewed by human |

Higher trust level requires stronger evidence and coverage.
Trust level does **not** imply action authorization.
Human-approved applies to a specific decision, not the adapter globally.

## Object Model

See `docs/governance/ogap-object-model-v0.md` for full 10-object spec.

## Future Directions (Not Implemented)

These are proposals only — no implementation exists, no commitment made:

- OGAP over HTTP/JSON-RPC
- OGAP MCP server (proof of concept)
- OGAP SDK for Python/TypeScript
- OGAP CI integration (GitHub Actions, GitLab CI)
- OGAP IDE plugin (VS Code, JetBrains)

None of these are active. None imply release plans.

---

*Created: 2026-05-01*
*Phase: OGAP-1*
*Version: v0 (prototype)*
*Authority: proposal / current_truth hybrid*
