from __future__ import annotations
from ordivon_capital.markets.fred_energy import compose_capture, parse_csv

CSV = """observation_date,DCOILBRENTEU,DCOILWTICO
2026-09-18,119.66,101.44
2026-09-19,.,.
2026-09-21,116.15,96.97
2026-09-22,114.89,96.41
"""

def test_parse_fred_energy_csv_preserves_series_identity_and_missing_values():
    rows=parse_csv(CSV)
    assert rows['2026-09-22']=={'brent':'114.89','wti':'96.41'}
    assert '2026-09-19' not in rows

def test_compose_fred_energy_capture_uses_latest_common_dates():
    result=compose_capture(CSV,123)
    assert result['latestCommonDate']=='2026-09-22'
    assert result['previousCommonDate']=='2026-09-21'
    assert result['latestUsdPerBarrel']=={'brent':'114.89','wti':'96.41'}
    assert result['change']['brentUsd']=='-1.26'
    assert result['change']['wtiUsd']=='-0.56'
    assert result['change']['brentMinusWtiUsd']=='18.48'
    assert result['aggregator']=='FRED'
    assert result['originOwner']=='U.S. Energy Information Administration'
    assert result['externalFinancialWriteAttempted'] is False
