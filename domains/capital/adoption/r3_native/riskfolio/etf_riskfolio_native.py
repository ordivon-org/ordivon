"""Riskfolio-Lib native historical tail-risk math using captured ETF bytes.

All inputs are historical backfills, not certified PIT data, adjusted total
returns, executable predictions or mandate-authorized investments. No orders.
"""
from __future__ import annotations

import hashlib
import importlib.metadata as im
import json
import os
import sys
from datetime import UTC, datetime
from io import BytesIO
from pathlib import Path

import pandas as pd
import riskfolio as rp

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parents[2] / "src"))
from ordivon_capital.markets.equity_session_calendar import require_xnys_session_grid

SOURCE = Path(
    os.environ.get("ORDIVON_FINANCE_R3_ETF_DATA_DIR", str(ROOT.parent / "output"))
).resolve()
SYMBOLS = ("SPY", "QQQ", "IWM")

# Use the SAME immutable capture receipt already consumed by Qlib and Nautilus.
# A path's name or today's checksum alone cannot prove the bytes were sourced
# from the nominated provider. Retrospective PIT remains UNKNOWN.
manifest_bytes = (SOURCE / "native_study_result.json").read_bytes()
manifest = json.loads(manifest_bytes)
rows = manifest.get("provider_receipts")
if not isinstance(rows, list):
    raise ValueError("Missing Qlib provider capture receipts")

frames = []
receipts = {}
for symbol in SYMBOLS:
    matched = [
        receipt for receipt in rows
        if isinstance(receipt, dict) and receipt.get("symbol") == symbol
        and receipt.get("provider") == "cboe"
    ]
    if len(matched) != 1:
        raise ValueError(f"Unique captured Cboe receipt required: {symbol}")
    expected = matched[0].get("normalized_sha256")
    if not isinstance(expected, str) or len(expected) != 64:
        raise ValueError(f"Invalid source digest for {symbol}")
    path = SOURCE / f"openbb_cboe_{symbol}_normalized.csv"
    pinned_bytes = path.read_bytes()  # ONE capture: hash AND parse these bytes
    digest = hashlib.sha256(pinned_bytes).hexdigest()
    if digest != expected:
        raise ValueError(f"Capture hash mismatch: {symbol}")
    frame = pd.read_csv(
        BytesIO(pinned_bytes),
        parse_dates=["session_date"],
        index_col="session_date",
    )
    require_xnys_session_grid(frame.index, symbol=symbol)
    frames.append(frame["close"].astype(float).rename(symbol))
    receipts[symbol] = digest

prices = pd.concat(frames, axis=1).sort_index()
returns = prices.pct_change(fill_method=None).dropna().iloc[-252:]
if len(returns) < 200:
    raise RuntimeError("Not enough backfilled observations")

portfolio = rp.Portfolio(returns=returns)
portfolio.assets_stats(method_mu="hist", method_cov="hist")
weights = {}
for label, risk in (
    ("min_empirical_cvar", "CVaR"),
    ("min_covariance_variance", "MV"),
):
    result = portfolio.optimization(
        model="Classic", rm=risk, obj="MinRisk", rf=0, l=0, hist=True,
    )
    if result is None or result.isna().any().any():
        raise RuntimeError(f"Riskfolio native {risk} failed")
    values = {symbol: float(result.loc[symbol].iloc[0]) for symbol in SYMBOLS}
    if abs(sum(values.values()) - 1) > 1e-5 or min(values.values()) < -1e-6:
        raise RuntimeError(f"Invalid native optimizer weights: {values}")
    weights[label] = values

evidence = {
    "kind": "ordivon.finance.r3.native-riskfolio-optimization-only",
    "version": im.version("riskfolio-lib"),
    "provider": "OpenBB V5 Cboe historical normalized capture",
    "provider_normalized_sha256": receipts,
    "source_manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
    "capture_input_consumption": "one_hash_checked_byte_image",
    "returns_unit": "daily fractional close-to-close",
    "observations": len(returns),
    "weights_math_only": weights,
    "portfolio_target": None,
    "optimizer_policy_eligible": False,
    "historical_point_in_time_qualified": False,
    "corporate_action_adjustment_basis": "UNKNOWN",
    "rights_for_redistribution": "UNKNOWN",
    "broker_and_accounting_effect": "NONE",
    "economic_performance_validated": False,
    "captured_at": datetime.now(UTC).isoformat(),
}
(ROOT / "native_riskfolio_result.json").write_text(
    json.dumps(evidence, indent=2, sort_keys=True), encoding="utf-8",
)
print("NATIVE_RISKFOLIO_QUALIFICATION", json.dumps(evidence, sort_keys=True))
