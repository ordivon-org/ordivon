# Market Capital Clean-Room — Wave A Acceptance

Date: 2026-09-12

## Standing

**PASS_BOUNDED** — the clean-room investment foundation is operational.

## Proven vertical chain

```text
CFA-informed IPS
  -> GLEIF authoritative legal-entity identities
  -> SEC Company Facts XBRL-derived fundamentals
  -> Research E2E / MLflow
  -> validated research artifact
  -> research-admission gate
  -> deterministic target portfolio
```

Parallel market-context path:

```text
Cboe public UTDF/CTS-derived market-volume data
  -> validated market-structure Parquet
  -> Research E2E / DuckDB / MLflow
```

## Milestones

- M1 reference identity and IPS -> target portfolio: PASS.
- M2 SEC issuer fundamentals -> research features: PASS.
- M3 Cboe official market-structure data: PASS_BOUNDED.
- M4 Research E2E -> portfolio handoff: PASS.

## Final Wave A portfolio

Method: `equal_weight_validation_research_gated`.

- AAPL: 1/3, LEI `HWUPKR0MPOU8FGXBT394`, research FY2025.
- MSFT: 1/3, LEI `INR2EJN1ERAN0W5ZP974`, research FY2026.
- NVDA: 1/3, LEI `549300S4KLFTLO7GSQ80`, research FY2026.

The weights are deliberately non-alpha validation weights. Research is an admission requirement only; no claim is made that the fundamental ratios predict returns.

## Test standing

12/12 unit tests pass across Wave A.

The suite now covers:

- authoritative GLEIF identity selection and lapsed-record rejection;
- portfolio constraint enforcement;
- missing reference evidence rejection;
- SEC annual-fact selection with comparative-period exclusion;
- same-accession fundamental consistency;
- financial feature calculation;
- Cboe daily aggregation and duplicate rejection;
- missing/duplicate Research E2E evidence rejection;
- valid research-gated portfolio construction.

Final M4 MLflow run: `735a3175cb6340ee9dd8044231aa8e9a`.

## Explicit bounded gaps

1. `SYMBOL_LEVEL_MARKET_DATA = CREDENTIAL_GATED`.
   Production-grade symbol bars should come from an exchange-provided source such as Nasdaq Data Link or the future selected broker/venue feed. Convenience feeds are not execution truth.

2. `SEC_RAW_FILING_TO_ARELLE = PENDING_NETWORK_ACCESS`.
   `data.sec.gov` Company Facts is operational. The current Runtime receives HTTP 403 from the `www.sec.gov/Archives/...` filing HTML path, so real filing -> local Arelle validation remains open. Arelle 2.44.7 itself is installed and previously validated locally.

3. No trading runtime exists in Wave A by design.

## Next wave

Wave B admits the trading foundation:

```text
research-gated target portfolio
  -> FIX order semantics
  -> pinned QuantConnect LEAN runtime
  -> deterministic historical execution
  -> fills / fees / slippage / buying power / portfolio state
```

The first LEAN admission must use no broker credentials and no external financial writes.
