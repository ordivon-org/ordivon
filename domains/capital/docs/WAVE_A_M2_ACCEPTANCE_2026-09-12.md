# Wave A / M2 Acceptance — 2026-09-12

## Result

**PASS** — authoritative issuer/fundamental data path is operational using SEC Company Facts, Research E2E, Pandera, Parquet, DuckDB and MLflow.

## Executed path

```text
SEC CIK configuration
  -> data.sec.gov Company Facts API
  -> latest annual 10-K fact selection
  -> same-accession/same-period consistency check
  -> Research E2E Python environment
  -> Pandera dataframe validation
  -> Parquet artifact
  -> DuckDB independent readback
  -> MLflow tracking
```

## Selected annual filings

- AAPL — FY2025, period end 2025-09-27, accession `0000320193-25-000079`, filed 2025-10-31.
- MSFT — FY2026, period end 2026-06-30, accession `0001193125-26-323660`, filed 2026-07-29.
- NVDA — FY2026, period end 2026-01-25, accession `0001045810-26-000021`, filed 2026-02-25.

Each feature row uses `us-gaap:NetIncomeLoss`, `us-gaap:Assets`, and `us-gaap:StockholdersEquity` selected from one annual 10-K filing. The build fails closed if the selected concepts do not share one fiscal year, period end, and accession.

## Validation features

These are architecture-validation calculations, **not alpha claims**:

| Symbol | ROA proxy | ROE proxy | Equity / Assets |
|---|---:|---:|---:|
| AAPL | 0.311796 | 1.519130 | 0.205247 |
| MSFT | 0.176362 | 0.302335 | 0.583335 |
| NVDA | 0.580586 | 0.763333 | 0.760593 |

ROA proxy = annual NetIncomeLoss / year-end Assets.  
ROE proxy = annual NetIncomeLoss / year-end StockholdersEquity.  
Equity/assets = year-end StockholdersEquity / year-end Assets.

## Test evidence

Seven unit tests passed across M1+M2, including:

- exact GLEIF ISSUED selection;
- lapsed GLEIF rejection;
- portfolio constraint enforcement;
- missing reference identity failure;
- comparative-period exclusion inside a newer filing;
- same-filing fundamental consistency enforcement;
- ratio calculation.

Final MLflow run: `111e4d5ad4fa40a3abe74f6d089a2a4b`.

DuckDB independently read the produced Parquet and reproduced all three rows and calculated values.

## Artifact digests

- SEC issuer configuration: `77945a961448c6fa83c57cc09fe1b5e8d99521ce31a7028c02ec8d3789c71918`
- fundamental JSON: `bef0a2fd20f3ca73821fc52a383eafc957bcee3ab81d33eb45076c6bd49f8dcd`
- fundamental Parquet: `54b0a012f34034b6845dca7201b9b6d514a81d4995547508dada05a38fd09ecb`
- research summary: `77720991ad9167658294577064ecfce08679d7422630c42ca03b99787c961de8`

Raw Company Facts responses are retained as generated local data and are not committed.

## Arelle / raw filing gate

Arelle 2.44.7 remains selected and installed. SEC `data.sec.gov` Company Facts is reachable and authoritative SEC-published XBRL-derived data. Direct access from the current Runtime to the `www.sec.gov/Archives/...` filing HTML path returns HTTP 403 on direct and both configured local proxy paths, so real SEC filing -> local Arelle validation remains **PENDING_NETWORK_ACCESS** rather than being falsely marked complete.

## Boundary

No broker, LEAN runtime, FIX session, order, transfer, withdrawal, or external financial write occurred in M2.
