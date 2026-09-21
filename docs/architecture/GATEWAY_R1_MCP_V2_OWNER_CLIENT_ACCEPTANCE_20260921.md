# Gateway R1 — MCP v2 Owner Client and Route Surface Acceptance

Date: 2026-09-21  
Status: CANDIDATE ACCEPTED / LIVE PUBLIC C02 STILL REQUIRED

## Scope

This change modernizes the Gateway-to-owner MCP seam without changing owner truth.

- conforming owner calls use the first-class Python MCP `Client` in `mode="auto"`;
- the Client owns modern discovery, protocol negotiation, output-schema validation, and legacy fallback;
- Gateway continues to provide owner-specific HTTP authentication headers through the official Streamable HTTP transport;
- the Runtime-only `_RuntimeCompatibilitySession` validation bypass is removed;
- static capability declarations move from `registry.py` to `routes.py` to make their non-registry role explicit;
- redundant `capability.list` is removed; `capability.describe` is the canonical semantic capability projection while `system.describe` remains a small system/topology description.

## Cross-SDK finding

The historical B01 compatibility note is no longer the current SDK boundary. Runtime intentionally publishes a JSON Schema `oneOf(success-object, error-object)` ToolOutcome without a top-level `type`, which is allowed by the current MCP output-schema model. Python MCP 2.2.0 accepts that shape and validates structured content with a JSON Schema validator.

Runtime therefore should not be narrowed to an artificial top-level object schema merely to preserve an obsolete client limitation.

## Authority boundary

The migration adds no Gateway database, task state, capability truth, Skill authority, or domain semantics. Runtime remains physical execution/artifact truth; Host remains continuity truth. `routes.py` selects the natural owner and lowering contract only.

## Verification

`mise run gateway:verify` passes with:

- Ruff lint and format gates;
- the full Gateway pytest suite;
- a regression proving current Python MCP accepts Runtime-style ToolOutcome union schemas;
- a regression proving conforming owner calls are routed through the first-class `Client`;
- a regression proving `capability.list` is absent while `capability.describe` remains.

This candidate does not claim public Gateway C02 acceptance or Plugin cutover.
