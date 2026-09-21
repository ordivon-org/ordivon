from __future__ import annotations

import json
from pathlib import Path

ROOT=Path(__file__).parents[1]


def load(path: str):
    return json.loads((ROOT/path).read_text())


def test_nonlive_effect_authority_is_distinct_from_real_financial_write_authority():
    nonlive=load('contracts/nonlive-effect-admission-v2.json')
    real=load('contracts/external-write-policy-input-v2.json')
    assert nonlive['state']=='ADMITTED'
    assert nonlive['providerWriteCapabilityBound'] is True
    assert nonlive['realMoney'] is False
    assert nonlive['liveEndpoint'] is False
    assert nonlive['externalFinancialWriteAllowed'] is False
    assert real['state']=='NOT_ADMITTED'
    assert real['providerWriteCapabilityBound'] is False
    assert real['externalFinancialWriteAllowed'] is False


def test_nonlive_authority_requires_reconciliation_and_capital_resolution():
    x=load('contracts/nonlive-effect-admission-v2.json')
    assert x['requiresReconciliation'] is True
    assert x['requiresCapitalResolution'] is True


def test_nonlive_effect_matrix_covers_failure_and_ambiguity_classes():
    x=load('config/nonlive_effect_authority.json')
    assert set(x['scenarios'])=={'FILL','PARTIAL_FILL_SLICES','CANCEL','DENY','UNKNOWN_AFTER_SUBMISSION'}
