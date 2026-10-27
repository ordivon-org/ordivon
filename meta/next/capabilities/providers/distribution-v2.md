# Provider profile: Distribution

- Source: /root/projects/ordivon/capabilities/distribution
- Role: optional effect-safety guidance, historical provider observations and the
  R7 Artifact fixture consumed by Workstation's n8n acceptance.
- The standalone carrier is retired; its identity remains historical provenance.

## Current boundary

Distribution has no active approval/authority/admission/reconciliation engine.
Those reference implementations had only self-tests and were retired.
Workstation consumes the R7 fixture to construct a synthetic blocked CloudEvent;
a separate readback branch performs a provider-native GET. This does not prove
provider-write admission.

For real delivery use the destination's native API/CLI, caller IAM/OAuth and
authoritative readback. Bind exact provider/account/payload occurrences and
reconcile ambiguous outcomes at the consuming owner. Optional carrier probes and
historical receipts are observations, not current production qualification.
