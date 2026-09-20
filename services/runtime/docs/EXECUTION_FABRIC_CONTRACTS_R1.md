# Execution Fabric Contracts R1

Status: RETIRED 2026-09-19

The generic Ordivon Execution Fabric contract crate was deleted.

The retired crate re-described Runtime-owned facts as local Resource, Capability, Provider,
Node, Controller, Authority and Evidence types, but had no external repository consumer.
Its only production consumer was Runtime MCP itself, which projected RuntimeCapabilities
into the custom schema and returned that projection through runtime.describe.

The projection did not own new physical truth and therefore failed the standards-first
retention rule.

Current ownership:
- Runtime native node/target/provider/availability fields -> Runtime physical capability truth;
- durable workflow -> Temporal or a standards-native process owner when required;
- workload identity / authorization / policy -> SPIFFE/OAuth/OPA/provider owners as applicable;
- generic provenance -> W3C PROV adapter when required;
- telemetry -> OpenTelemetry only with a real consumer;
- domain reconciliation -> domain-specific controller/operator;
- semantic completion -> domain owner.

No replacement Ordivon fabric ontology is planned.
