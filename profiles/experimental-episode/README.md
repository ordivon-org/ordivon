# Experimental Fabric Profiles R1

These schemas form the shared, non-authoritative protocol waist for Ordivon experiments. They deliberately do **not** create a global World, Evidence, Recovery, Session, Task, Checkpoint, or Evaluation authority.

The four mechanisms map to existing natural owners plus study-owned bindings:

- **Seat parity** — `experimental-design-contract-r1.schema.json` freezes owner-native observation/action/resource/authority contracts by seat and parity group. Human/agent adapters may differ; parity-group semantic contracts may not.
- **World evidence** — `experimental-episode-binding-r1.schema.json` binds exact owner-native identities and bounded evidence projections. Runtime, Harness, Host, provider, Git, and domain owners remain authoritative for their own facts.
- **Counterfactual forkability** — `experimental-intervention-contract-r1.schema.json`, `experimental-fork-manifest-r1.schema.json`, and `experimental-fork-assessment-r1.schema.json` declare controlled changes and assess contamination without performing effects or rewriting parent truth.
- **Outcome / behavior separation** — `experimental-metric-spec-r1.schema.json` declares the construct, metric class, unit of analysis, independent replication unit and minimum evidence requirement; `experimental-evaluation-record-r1.schema.json` records derived results without changing owner facts.

## Core laws

1. Observation != Evidence != Claim != Verification != Decision.
2. Adapter parity is semantic parity of the declared seat boundary, not identical UI representation.
3. Experiment bindings never grant execution/effect authority.
4. A fork is causal evidence only to the extent that its declared frozen bindings remain unchanged and its external-world mode permits the claim.
5. `reasoning`/CoT may be an evidence input but is never owner ground truth.
6. Evaluation records are append-only derived claims; changing a metric or judge creates a new record.
7. Replication is counted at `replicationUnit`, not at the number of repeated observations.

Protocol-level semantic checks and the response-loss reference fixture live under `studies/experimental-episode/protocol-r1`.
