# Agentic Pattern Runtime Boundaries (ADP-1)

> **v0 / internal mapping / reference-only.** No live execution. No enforcement.
> **Phase:** ADP-1 | **Risk:** AP-R0

## 1. Phase Boundary

ADP-1 is **AP-R0 only** — documentation, taxonomy, and mapping.
No execution, no enforcement, no live adapter, no credential access,
no external system invocation.

The taxonomy describes AP-R1 through AP-R5 patterns but does not
enable or authorize them. This boundary is permanent for ADP-1.

## 2. Pattern Enforcement Status

All patterns in ADP-1 are **identified and documented only.**
No pattern is enforced in this phase.

| Enforcement Level | Meaning | ADP-1 Status |
|-------------------|---------|-------------|
| Documented | Pattern described in taxonomy | ✅ All 18 patterns |
| Detection | Checker/schema can detect pattern | ❌ Deferred to future phases |
| Gate | Pattern blocks Stage Gate | ❌ Deferred |
| Block | Pattern causes CI/PR block | ❌ Deferred |
| NO-GO | Pattern permanently blocked | ❌ Deferred |

## 3. Risk Ladder Boundary

| Level | Allowed in ADP-1? | If triggered |
|-------|-------------------|-------------|
| AP-R0 | ✅ Current scope | Taxonomy creation |
| AP-R1 | ❌ Not allowed | Would require observation-only detection |
| AP-R2 | ❌ Not allowed | Would require workspace boundary enforcement |
| AP-R3 | ❌ Not allowed | Would require shell execution gate |
| AP-R4 | ❌ Not allowed | Would require credential/external boundary enforcement |
| AP-R5 | ❌ NO-GO | Permanently out of scope for ADP |

If any ADP-1 artifact (doc, schema, fixture, test) triggers AP-R1+
behavior, it is out of scope and must be deferred.

## 4. What ADP-1 Does Not Authorize

- ❌ Does not authorize agent execution
- ❌ Does not authorize pattern enforcement
- ❌ Does not authorize CandidateRule→Policy promotion
- ❌ Does not authorize checker/schema implementation
- ❌ Does not authorize live adapter transport
- ❌ Does not authorize credential access
- ❌ Does not authorize external system invocation
- ❌ Does not authorize MCP server connection
- ❌ Does not authorize shell execution
- ❌ Does not authorize browser or external API usage

## 5. Boundary Confirmation

| Boundary | Confirmed |
|----------|-----------|
| ADP-1 is mapping-only | ✅ |
| Pattern identification ≠ policy activation | ✅ |
| CandidateRule ≠ binding policy | ✅ |
| Risk classification ≠ authorization | ✅ |
| External benchmark ≠ compliance | ✅ |
| Source citation ≠ endorsement | ✅ |
| HAP capability ≠ authorization | ✅ |
| Task request ≠ approval | ✅ |
| Receipt ≠ approval | ✅ |
| Evidence ≠ approval | ✅ |
| READY ≠ execution authorization | ✅ |
| Valid payload ≠ action permission | ✅ |
| No credentials accessed | ✅ |
| No external systems invoked | ✅ |
| No live adapter created | ✅ |
| No MCP server created | ✅ |
| No SDK/API/package/public standard created | ✅ |
| Financial/broker/live action remains NO-GO | ✅ |
| Phase 8 remains DEFERRED | ✅ |

## 6. Safe External Benchmark Wording

ADP-1 references external AI governance and coding-agent documentation
as benchmark inputs for internal comparison and pattern discovery only.
These references do not imply compliance, certification, endorsement,
partnership, equivalence, production readiness, or public-standard status.

*Phase: ADP-1 | AP-R0 only. No live execution.*
