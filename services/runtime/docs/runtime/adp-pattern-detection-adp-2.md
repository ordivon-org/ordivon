# ADP-2 Agentic Pattern Detection v0

> **v0 / local static detection / non-executing.** Detector PASS is not authorization.
> Absence of findings is not safety proof. Findings are review evidence, not approval.
> **Phase:** ADP-2 | **Risk:** AP-R0 | **Authority:** AI-0/AI-2

## 1. Purpose

ADP-2 implements a local, static, rule-based detector that scans Ordivon docs,
fixtures, and receipts for ADP-1 agentic pattern risks using GOV-X gate semantics.

## 2. Detector Identity

The detector is:
- **Local** — runs on filesystem, no network
- **Static** — regex/string-based, no AST parsing
- **Deterministic** — same input produces same output
- **Evidence-producing** — findings are review evidence

The detector is NOT:
- A runtime monitor
- A safety verifier
- An authorization system
- A compliance tool
- An execution engine

## 3. Rule Inventory

| # | Rule | Pattern | Severity | Blocks Closure |
|---|------|---------|----------|---------------|
| 1 | READY authorization overclaim | AP-RDY | blocking | Yes |
| 2 | Capability-to-authorization collapse | AP-COL | blocking | Yes |
| 3 | Credential access confusion | AP-CRED | blocking | Yes |
| 4 | External side-effect authorization | AP-EXT | blocking | Yes |
| 5 | MCP confused deputy | AP-MCP | blocking | Yes |
| 6 | External benchmark overclaim | AP-EBO | blocking | Yes |
| 7 | CandidateRule premature promotion | AP-CRP | blocking | Yes |
| 8 | Evidence laundering | AP-EVL | degraded | Yes |
| 9 | Baseline debt masking | AP-BDM | warning | No |
| 10 | Protected path violation | AP-PPV | degraded | Yes |
| 11 | Shell risk gate mismatch | AP-SHE | degraded | Yes |
| 12 | C4/C5 gate mismatch | AP-GATE | blocking | Yes |

## 4. GOV-X Gate Coverage

All 12 rules map to GOV-X semantics:

- C4 defaults to BLOCKED: Rules 2, 3, 4, 5, 12
- C5 defaults to NO-GO: Rules 7, 12
- Evidence is not approval: Rule 8
- READY != authorization: Rule 1
- Capability != authorization: Rules 2, 3, 4, 5
- Protected paths: Rule 10
- Shell escalation: Rule 11
- Baseline classification: Rule 9
- External benchmark safe-language: Rule 6

## 5. Output Format

```
ADP-2 Agentic Pattern Detector
  Scanned: N files
  Findings: M
    blocking: B
    degraded: D
    warning: W
    info: I

  Findings:
    [BLOCKING] AP-RDY file.md:42: READY overclaim...
```

JSON: `{"findings": [...], "stats": {...}}`

Each finding: finding_id, pattern_id, severity, risk_level, capability_class,
authority_impact, gate_expected, gate_observed, file, line, evidence_snippet,
explanation, recommended_fix, blocks_closure.

## 6. Known Limitations

- Regex/static detection can produce false positives and false negatives
- Detector does not prove safety
- Detector does not authorize action
- Detector does not replace human review
- Detector does not execute tools
- Detector does not inspect live runtime behavior
- Detector does not access external systems
- Detector does not validate external framework compliance
- Same-line only matching may miss cross-line patterns

## 7. Verification

- 26 tests: 8 safe (no false positives), 12 unsafe (flagged), 3 determinism, 3 CLI
- All safe fixtures produce 0 blocking/degraded findings
- All unsafe fixtures produce findings with correct pattern IDs
- Detector output is deterministic
- No can_access_secrets in detector source

## 8. Boundary Confirmation

| Boundary | Confirmed |
|----------|-----------|
| ADP-2 is local static detection, not runtime enforcement | ✅ |
| Detector finding is evidence for review, not approval | ✅ |
| Absence of findings is not authorization | ✅ |
| Detector PASS is not execution authorization | ✅ |
| CandidateRule non-binding | ✅ |
| C4 defaults to BLOCKED | ✅ |
| C5 defaults to NO-GO | ✅ |
| No credentials accessed | ✅ |
| No external systems invoked | ✅ |
| Financial/broker/live action remains NO-GO | ✅ |

## 9. Next Phase

**ADP-3** (detector refinement with cross-line context, AST-aware scanning,
and integration with pr-fast/CI) or **HAP-3** (HarnessTaskPlan +
HarnessReviewRecord standalone fixture representation).

*Phase: ADP-2 | Local static detection only. No execution.*
