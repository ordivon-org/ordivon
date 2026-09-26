from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_openbb_is_external_bounded_capability_not_truth_owner():
    cfg=json.loads((ROOT/'config/research_data_aggregators.json').read_text())['aggregators']['openbb']
    assert cfg['standing']=='ADMITTED_BOUNDED_EXTERNAL_RESEARCH_DATA_CAPABILITY'
    assert cfg['stableVersion']=='4.7.2'
    assert cfg['deploymentBoundary']=='SEPARATE_EXTERNAL_ENVIRONMENT_NOT_CAPITAL_CORE_DEPENDENCY'
    assert cfg['qualifiedProviders']['federal_reserve']['standing']=='PASS_LIVE_READONLY'
    assert cfg['qualifiedProviders']['yfinance']['standing'].endswith('NOT_ADMITTED')
    assert 'not original data authority' in cfg['nonResponsibility']

def test_brent_wti_preserves_eia_origin_and_fred_mirror_identity():
    row=json.loads((ROOT/'config/macro_observation_owners.json').read_text())['observations']['brentWti']
    assert row['standing']=='ACTIVE_EIA_ORIGIN_FRED_PUBLIC_MIRROR'
    assert row['originOwner']=='U.S. Energy Information Administration'
    assert row['activeAggregator']=='Federal Reserve Bank of St. Louis FRED'
    assert row['transportAuthority']=='fredPublicCsv'
    assert row['credentialRequired'] is False
    assert row['directEiaCredentialRequired'] is True
