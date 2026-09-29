# Review ledger contract

The Whole-System Review needs continuity across weeks, but continuity is not present-tense system truth.

## Natural owner

Use Host Social Work Fabric `Work` snapshots for durable semantic review continuity when available. Do not create a review database, universal registry, or Git-owned runtime state.

Recommended stable work identity:

```text
work:ordivon-whole-system-review
```

If deployment policy requires revisioned/campaign-scoped Work identities, preserve a stable relation/reference to the canonical review stream rather than inventing a second database.

## Ledger content

Persist only semantic continuity needed by the next review:

- latest accepted `reviewId` and ReviewRecord locator/digest;
- last reviewed source revision and period;
- open systemic risk themes;
- open milestone chain;
- unresolved genuine stakeholder decisions;
- recurring findings awaiting fitness/control/redesign disposition;
- evidence that has become stale and must be revalidated.

Do not persist a claim that a Runtime, release, external effect, Git ref, provider, or domain object is currently healthy/completed merely because it was true at the last review.

## Read law

At the beginning of each review:

1. read the prior semantic ledger if available;
2. treat it as `HISTORICAL_CONTEXT` / prior judgment only;
3. independently re-establish current Git and owner truth;
4. compare current evidence to prior findings;
5. mark findings `UNCHANGED`, `STRENGTHENED`, `WEAKENED`, `RESOLVED`, `REOPENED`, or `SUPERSEDED` only after current evidence supports that transition.

## Write law

Write the ledger only after the ReviewRecord passes schema + semantic verification. Use Host revision/CAS semantics. If the Host write is ambiguous, read back/reconcile before retrying; do not create a second Work identity just to escape uncertainty.

Host acceptance proves only Host semantic persistence, not the technical truth of the ReviewRecord's referenced external claims.
