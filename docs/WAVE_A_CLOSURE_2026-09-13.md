# Market Capital Clean-Room — Wave A Closure

Date: 2026-09-13

## Canonical standing

Wave A is merged into `main` at `4d2a779664f4216207e9b41c87bad01463b3a68f`.

The current investment-side chain remains:

`IPS -> GLEIF -> SEC Company Facts -> Research Capability -> research admission -> target portfolio`.

The full Wave A unit suite is reproducible through the admitted Research Capability environment: 12/12 tests pass.

## Capability ownership

Market Capital no longer pretends its empty `pyproject.toml` owns the scientific Python stack. `config/capability_dependencies.json` explicitly delegates dataframe validation, Parquet and experiment lineage to the Research Capability environment. Market Capital owns its thin domain mappings, schemas and acceptance gates.

## Raw SEC filing / Arelle boundary

The previous SEC network blocker is no longer current: the Apple 2025 10-K filing URL returns HTTP 200 from the Runtime host.

Arelle core 2.44.7 is installed. However, the installed Arelle distribution does not contain the SEC-maintained EDGAR/EFM plugin bundle. An attempted `--efm` validation reports that disclosure system `efm` is not recognized. Therefore raw filing -> EFM validation remains **PENDING_SEC_PLUGIN_ADMISSION**, not `PENDING_NETWORK_ACCESS` and not PASS.

This does not invalidate the operational SEC Company Facts path used by Wave A; it leaves the stronger raw-filing validation path open.

## Next wave

Wave B admits an external trading engine with no broker credentials and no external financial writes. First target:

`research-gated target portfolio -> LEAN historical execution -> fills/fees/slippage -> resulting portfolio state`.
