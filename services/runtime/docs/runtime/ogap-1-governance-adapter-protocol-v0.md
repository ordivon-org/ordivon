# OGAP-1 — Ordivon Governance Adapter Protocol v0

## Purpose

Define the first Ordivon Governance Adapter Protocol (OGAP) v0 —
the protocol layer for external agents, tools, MCP servers, IDEs,
CI systems, and frameworks to make their work governable by Ordivon.

## Why OGAP-1 Follows PV-NZ

PV-NZ closed the Ordivon Verify productization foundation — OV can build,
install, and verify locally. The next strategic question is how external
systems connect to the Ordivon governance layer.

OGAP-1 answers that question at the protocol/contract level, without
building a live API, MCP server, SDK, or runtime implementation.

## Strategic Positioning

```
Agents act.
Tools execute.
Frameworks orchestrate.
Ordivon governs.
```

OGAP is a protocol layer, not a product. It defines contract shapes,
semantics, and invariants. Implementation is deferred to future phases.

## What Was Created

| Artifact | Purpose |
|---|---|
| Architecture doc | OGAP identity, integration levels, decision semantics, capability vs authority, side-effect classes, coverage model, adapter trust levels |
| Object model | 10 objects: WorkClaim, EvidenceBundle, ExecutionReceipt, CoverageReport, CapabilityManifest, AuthorityRequest, ToolCallLedger, DebtDeclaration, GovernanceDecision, TrustReport |
| Integration levels | Level 1 (Verify-only), Level 2 (Governed project), Level 3 (Governance-native adapter) |
| Use cases | 6 use cases: AI agent, MCP server, CI, IDE agent, enterprise platform, financial/broker NO-GO |
| Example payloads | 5 JSON examples: WorkClaim, GovernanceDecision (READY), GovernanceDecision (BLOCKED), CapabilityManifest, CoverageReport |

## Key Invariants

- can_X does not imply may_X
- READY is evidence, not authorization
- Capability is not authority
- Evidence is not approval
- Receipt is not review
- Adapter-compatible is not governed-approved
- Financial/live/broker/Policy/RiskEngine actions default to NO-GO

## What OGAP-1 Proves

1. Ordivon's governance semantics can be expressed as a protocol.
2. External systems can be classified by integration depth (1/2/3).
3. Object model is coherent — each object has clear purpose, required fields, and prohibited overclaims.
4. Capability/authority separation is structurally encoded.
5. Coverage model generalizes COV-1 principles across adapters.

## What OGAP-1 Does NOT Prove

- That OGAP works over a network (no HTTP/JSON-RPC implementation)
- That OGAP works as an MCP server (not built)
- That any real external system has integrated (zero integrations)
- That OGAP objects validate against schemas (no runtime validation)
- That OGAP scales to multi-adapter orchestration
- That OGAP is ready for public standardization

## Boundary Confirmation

- Protocol v0 only. No live API. No MCP server. No public standard.
- No public release. No package publish. No license activation.
- No public repo created.
- Financial/live/broker/Policy/RiskEngine remain NO-GO.
- Phase 8 DEFERRED.
- COV-2 partials remain explicit.

## Next Recommended

OGAP-1 defines the contract. Next phase should prototype an actual
OGAP integration — either:
- OGAP validation checker (validate WorkClaim against evidence)
- OGAP Level 1 integration with a real external repo
- OGAP schema extraction (JSON Schema for OGAP objects)

---

*Closed: 2026-05-01*
*Phase: OGAP-1*
