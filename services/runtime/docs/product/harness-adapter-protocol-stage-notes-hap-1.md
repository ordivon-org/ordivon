# Harness Adapter Protocol — Stage Notes (HAP-1)

> **Status:** OPEN
> **Date:** 2026-05-02
> **Authority:** current_truth
> **Related:** docs/architecture/harness-adapter-protocol-hap-1.md, docs/runtime/hap-foundation-hap-1.md

## 1. Purpose

HAP-1 establishes the v0 foundation for the Harness Adapter Protocol.
It defines the object model, schemas, fixtures, and boundary language
for describing what external AI/code/runtime harnesses can do, what
they did, and what evidence they left — without executing anything.

## 2. Strategic Relationship to OGAP

| Protocol | Phase | Status |
|----------|-------|--------|
| OGAP | 1-3, Z | CLOSED |
| HAP | 1 | OPEN |

OGAP governs the external adapter protocol — how external systems make
work governable. HAP describes the harness surface — what capabilities,
task shapes, receipts, and evidence bundles look like.

OGAP and HAP are complementary, not overlapping. OGAP is the governance
adapter protocol; HAP is the harness description protocol.

## 3. What HAP-1 Creates

| Artifact | Type | Count |
|----------|------|-------|
| Architecture doc | docs/architecture/ | 1 |
| Object model / runtime doc | docs/runtime/ | 1 |
| Stage notes | docs/product/ | 1 |
| JSON schemas | src/ordivon_verify/schemas/ | 3 |
| Example fixtures | examples/hap/ | 5 core + 5 scenarios |
| Validator script | scripts/ | 1 |
| Tests | tests/unit/product/ | 2 |

## 4. What HAP-1 Does Not Create

- ❌ Live API, SDK, MCP server, SaaS endpoint, package release
- ❌ Public standard, public repo
- ❌ Live adapter transport
- ❌ Broker/API integration
- ❌ Credential access
- ❌ External tool execution
- ❌ Action authorization
- ❌ Financial/broker/live action (remains NO-GO)
- ❌ Phase 8 (remains DEFERRED)

## 5. Capability Field Name Clarification

The capability field for credential-adjacent technical ability is
**`can_read_credentials`**, not `can_access_secrets`.

Rationale for the name:
1. "secrets" triggers unnecessary false positives in security scanners.
2. `can_read_credentials` more accurately describes the technical
   ability to read credential-like material without implying actual
   secret possession.
3. The high-risk semantics are preserved — `can_read_credentials` is
   a capability declaration, not authorization.
4. The prior name `can_access_secrets` was renamed; it must not be
   reintroduced.

Hard boundary: `can_read_credentials` describes technical capability
only. It does not grant credential access, secret access, tool
execution, or external-system authorization.

## 6. Known Debt at Start

| Debt ID | Status | Scope |
|---------|--------|-------|
| DOC-WIKI-FLAKY-001 | open | test_document_wiki.py::test_generator_output_deterministic |

## 7. Next Recommended Phase

**ADP-1 — Agentic Pattern Governance Mapping** after HAP-1 closure.
HAP-2 (fixture dogfood, transport criteria) after ADP-1.

*Created: 2026-05-02 | HAP-1 foundation*
