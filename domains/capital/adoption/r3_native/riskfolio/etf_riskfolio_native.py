"""Read-only Riskfolio-Lib tail-risk optimizer using OpenBB captured ETF close series.

Demonstrates the mature CVaR owner; NOT investment advice, not PIT,
not a historically admitted adjustment basis, and not an executable plan.
"""
from __future__ import annotations
import hashlib
import importlib.metadata as im
import json
import os
from datetime import datetime,timezone
from pathlib import Path

import pandas as pd
import riskfolio as rp

ROOT=Path(__file__).resolve().parent
SOURCE=Path(os.environ.get("ORDIVON_FINANCE_R3_ETF_DATA_DIR",str(ROOT.parent/"output"))).resolve()
SYMBOLS=("SPY","QQQ","IWM")
frames=[]
receipts={}
for s in SYMBOLS:
    p=SOURCE/f"openbb_cboe_{s}_normalized.csv"
    if not p.is_file():
        raise FileNotFoundError(p)
    x=pd.read_csv(p,parse_dates=["session_date"],index_col="session_date")
    frames.append(x["close"].astype(float).rename(s))
    receipts[s]=hashlib.sha256(p.read_bytes()).hexdigest()
prices=pd.concat(frames,axis=1).sort_index()
returns=prices.pct_change(fill_method=None).dropna().iloc[-252:]
if len(returns)<200:
    raise RuntimeError("Not enough backfilled observations")
portfolio=rp.Portfolio(returns=returns)
portfolio.assets_stats(method_mu="hist",method_cov="hist")
weights={}
for label,risk in (("min_empirical_cvar","CVaR"),("min_covariance_variance","MV")):
    w=portfolio.optimization(model="Classic",rm=risk,obj="MinRisk",rf=0,l=0,hist=True)
    if w is None or w.isna().any().any():
        raise RuntimeError(f"Riskfolio native {risk} failed")
    vals={str(s):float(w.loc[s].iloc[0]) for s in SYMBOLS}
    if abs(sum(vals.values())-1)>1e-5 or min(vals.values())< -1e-6:
        raise RuntimeError(f"Unqualified native optimizer weights {vals}")
    weights[label]=vals
result={
    "kind":"ordivon.finance.r3.native-riskfolio-optimization-only",
    "version":im.version("riskfolio-lib"),
    "provider":"OpenBB V5 Cboe normalized historical closes",
    "provider_normalized_sha256":receipts,
    "returns_unit":"daily fractional close-to-close",
    "observations":len(returns),
    "weights":weights,
    "historical_point_in_time_qualified":False,
    "corporate_action_adjustment_basis":"UNKNOWN",
    "broker_and_accounting_effect":"NONE",
    "economic_performance_validated":False,
    "captured_at":datetime.now(timezone.utc).isoformat(),
}
(ROOT/"native_riskfolio_result.json").write_text(json.dumps(result,indent=2,sort_keys=True),encoding="utf-8")
print("NATIVE_RISKFOLIO_QUALIFICATION",json.dumps(result,sort_keys=True))
