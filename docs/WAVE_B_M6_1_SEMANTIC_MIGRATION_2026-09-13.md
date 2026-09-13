# Market Capital Clean-Room — Wave B / M6.1 Canonical Semantic Migration

## Standing

**PASS_CANONICAL_SEMANTICS_MIGRATED_IN_REPO**.

The temporary cross-repository authority-waist binding has been removed. The semantic core previously proven in `ordivon-market-capital-v2` is now owned directly by the canonical `ordivon-market-capital-next` repository.

## Migrated capability

The canonical repository now directly contains and tests:

- observation / same-cut semantics;
- proof binding and currentness;
- Scientific Truth != Economic Truth != Capital Truth;
- registry / parcel / scarcity identity;
- Reservation != Grant;
- EffectAuthority RETAIN / RELEASE / CONSUME disposition;
- revocation / recovery boundaries;
- ProductionAuthorization.

These semantics live under `src/market_capital/semantic.py` and canonical contracts under `contracts/`.

## Execution authority

Every current LEAN runner now invokes the in-repository `scripts/check-capital-authority` gate before execution. There is no runtime dependency on `ordivon-market-capital-v2`.

Current authority remains:

- `ProductionAuthorization = BLOCK_NOT_GRANTED`;
- `externalFinancialWriteAllowed = false`;
- `externalFinancialWriteAdmission = NOT_ADMITTED`;
- live grant mechanism = `NOT_IMPLEMENTED`.

External-write mode remains code-level unavailable.

## Historical source

The prior `ordivon-market-capital-v2` repository is retained only as migration history/evidence and is not part of the active architecture or runtime path.
