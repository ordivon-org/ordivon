# Ordivon Social Fabric Reality Completion R2

Truth role: rebuildable coordination/reality projection architecture. It owns no mutable domain, execution, continuity, Git, provenance, or authority truth.

## Implemented LEGO

### REAL20 — W3C PROV projection adapter

Consumes existing JSON-LD and preserves explicit node identities, `@type`, and named PROV relations such as `prov:wasDerivedFrom`, `prov:used`, `prov:wasGeneratedBy`, `prov:generated`, and `prov:wasAssociatedWith`. Relation direction is not rewritten. External targets are preserved with `targetPresentInDocument=false`; absence from one document never becomes nonexistence. No causal mechanism is inferred.

### REAL21 — Transactive Memory projection

Compiles only explicit relations from existing owners:

- Authority Catalog -> `EXTERNAL_AUTHORITY_ISSUER`;
- Gateway capability projection -> `NATURAL_CAPABILITY_OWNER`;
- Host compact Task inventory -> `CONTINUITY_OWNER`;
- caller/owner supplied verification binding -> `EXPLICIT_VERIFIER`.

It does **not** infer expertise, who “knows best”, trust score, assignment, priority, or EffectAuthority. Issuer, capability owner, continuity owner, and verifier remain distinct relations.

### REAL22 — owner-scoped Freshness / Supersession

Preserves the mature currentness vocabulary already present in Composition/Runtime research:

- `POINT_IN_TIME_OBSERVED`;
- `CURRENT_DECLARED`;
- `HISTORICAL_NOT_CURRENT`;
- `CURRENTNESS_UNKNOWN`.

Historical versions may coexist with one owner-declared current version. Two distinct simultaneous `CURRENT_DECLARED` version refs from the same owner project `CONFLICTED_CURRENT_DECLARATIONS`; the projection never elects a winner. Authority Catalog `currentnessChecked` becomes only `POINT_IN_TIME_OBSERVED`, not durable currentness.

Critical invariant from existing Runtime research: **Git tip recency does not mint semantic authority/currentness**. Likewise Host `open` is continuity state, not proof of active work/currentness or domain completion. Supersession is emitted only from explicit owner-native facts and no transitive semantic replacement is invented.

## Dogfood cut

The bounded owner cut contains:

- four real Authority Catalog entries: W3C PROV-O, OpenLineage, A2A 1.0.0, CloudEvents documented extensions;
- the live Gateway capability projection observed during this implementation: four available capabilities and their natural owners;
- the exact Host continuity inventory row for `task:social-fabric-crossdisciplinary-r2-20260923` revision 2;
- Runtime research C4 owner-currentness evidence containing one historical and one current Network `AuthorityVersionRef`.

Results:

- REAL20: 22 PROV nodes, 34 explicit edges;
- REAL21: 9 locator entries = 4 external issuers + 4 capability owners + 1 Host continuity owner, with no inferred verifier;
- REAL22: Network historical and current versions coexist correctly; four catalog standards remain point-in-time observations; no supersession edge is invented.

## Stop rules

1. No Social provenance ontology.
2. No expert/knower registry or expertise score.
3. No Git-recency-to-semantic-currentness promotion.
4. No Host-task-state-to-activity/currentness promotion.
5. No global winner across owner currentness views.
6. No inferred supersession or transitive semantic replacement.
7. No causal-mechanism claim from provenance/sequence alone.
8. No EffectAuthority is granted by any Reality projection.
