# Capital contracts

Current protocol contracts use schemaVersion 2 and domain-correct identities.

- external-boundary-v2.json — current component-responsibility map.
- external-write-policy-input-v2.json — current external-effect admission input.
- nonlive-effect-admission-v2.json — current bounded non-live effect admission contract.
- portfolio-risk-budget-v2.schema.json — current Risk portfolio budget schema.

Legacy protocol-v1 contracts are retained under contracts/legacy_protocol_v1/ for provenance only. Current runtime code does not load them or auto-upgrade v1 documents. Replaying v1 evidence uses the historical source revision or frozen bundle that owned those contracts.
