# Finance R3 - Riskfolio-Lib 7.4.1 native risk-math qualification

This is a read-only, separate Python 3.11 consumer of actual OpenBB
Cboe SPY/QQQ/IWM normalized historical close captures from the
sibling OpenBB -> Qlib research script. Run the sibling script first
to produce ./output/openbb_cboe_<ETF>_normalized.csv (not committed:
provider redistribution rights UNKNOWN).

  uv venv .venv --python 3.11
  uv pip sync --python .venv/Scripts/python.exe requirements.lock
  .venv/Scripts/python.exe etf_riskfolio_native.py

Override source directory with ORDIVON_FINANCE_R3_ETF_DATA_DIR.
Native Portfolio.assets_stats(method_mu=hist,method_cov=hist) and
Portfolio.optimization(model=Classic,obj=MinRisk,rm=CVaR or MV)
are both called on trailing 252 daily close-to-close observations.
CVaR supports empirical tail loss that ordinary covariance MV
cannot represent, although particular historical weights may
coincide. This does not prove out-of-sample risk or better return.

No PIT provenance, adjustment basis, corporate-action completeness,
broker orders, live economics, risk mandate, or PG posting is inferred.
Output evidence contains native weights and captured source SHA only.
Do not treat this as a replacement for multi-stage CRRA/liability
planning, exact integer lots, or margin/multi-period constraints.
