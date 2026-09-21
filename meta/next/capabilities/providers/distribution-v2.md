# Provider: Distribution v2

- Source: /root/projects/ordivon/capabilities/distribution
- Current owner path revision: 6cf76a49140d8d928dd4bb73904d38fa6819dac2
- Historical standalone observation revision: 03ccc562160b
- Role: provider distribution/effect execution and readback capability provider
- Migration mode: canonical monorepo owner; standalone Distribution-v2 identity retained only as historical/recovery provenance

## Current capability standing

- GitHub authenticated observation/readback proven;
- durable Temporal -> integration-edge paths proven for non-effectful/read-only cases;
- exact approval ingress exists;
- real provider writes remain authority-gated and were not performed at the observed standing.

## Reusable rules

1. bind one external effect to one exact intent/account/payload occurrence;
2. reusable credentials do not replace exact effect authority for write/destructive actions;
3. local execution/upload/scheduler success is not provider acceptance;
4. ambiguous external outcomes cannot be blindly retried without provider idempotency or authoritative absence evidence.

These rules are candidates for broader effect-management knowledge, not justification for a permanent Distribution layer in Core.
