# Runtime Governance Alignment

Status: `current`
Authority: `source_of_truth`
Purpose: Position Ordivon relative to runtime governance, policy, provenance, reconciliation, and AI risk frameworks.
Supersedes: historical framework comparison and future-architecture audit notes.
Verification: certification evidence package, policy decision tests, red-team runner scenarios, external source review.

## Position

Existing frameworks cover important sections of the governance line. Ordivon
connects those sections into one stateful loop:

```text
Norm
-> Declaration
-> Object
-> Policy Decision
-> Runtime Mediation
-> Execution
-> Receipt
-> Reconciliation
-> Debt / Rule / Methodology
```

The system is closer to a governance operating layer than a checklist.

## Framework Mapping

| Framework | What it contributes | Ordivon role |
| --- | --- | --- |
| NIST AI RMF | Govern, Map, Measure, Manage risk functions | Translate governance goals into objects, gates, receipts, and evidence |
| OWASP / MAESTRO | Agentic threat vocabulary and risk categories | Convert risks into red-team scenarios and policy candidates |
| OPA / OpenFGA | Policy decision and authorization substrate | Record allow, deny, and error decisions before dispatch |
| Kubernetes Controller | Desired/current reconciliation pattern | Apply reconciliation to claims, obligations, receipts, and debt |
| W3C PROV | Entity/activity/agent provenance grammar | Use provenance as evidence, then apply authority and closure rules |
| OpenAI Agents SDK | Traces, tool calls, handoffs, guardrail hooks | Treat traces as runtime substrate, not governed closure |
| MI9-style runtime governance | Semantic telemetry, FSM conformance, drift detection, containment | Runtime governance plane inside Ordivon's broader loop |

No single framework above is the complete Ordivon line. Each is a component or
analogy.

## Ordivon Planes

```text
L0 Norm / Risk Plane
L1 Declaration Plane
L2 Governance Object Plane
L3 Policy Decision Plane
L4 Runtime Execution Plane
L5 Runtime Governance Plane
L6 Receipt / Provenance Plane
L7 Reconciliation Plane
```

The invariant is:

```text
L4 execution cannot bypass L2/L3 governance or L6 receipt.
```

## Failure Modes

- Treating NIST or OWASP alignment as runtime control.
- Treating OPA allow as receipt.
- Treating trace availability as closure.
- Treating Kubernetes-style desired state as authorization.
- Treating provenance as enough to prove correctness.
- Treating agent guardrails as covering every handoff, hosted tool, or adapter
  path.

## What This Changes In Implementation

- `kernel_policy_decisions` must exist as audit evidence for every dispatch
  decision.
- Deny and policy-evaluation errors must be recorded before fail-closed return
  when safe to record.
- Successful dispatch must reference authority use, policy decision, ledger
  event, adapter source, observation, and comparator receipt.
- Red-team runner must execute through real Rust/Postgres APIs, not fixture
  outcomes.
- External standards are mapped to named invariants and tests; they do not
  replace tests.
