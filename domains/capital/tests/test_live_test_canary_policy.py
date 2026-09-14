from pathlib import Path
import json
from decimal import Decimal
ROOT=Path(__file__).resolve().parents[1]

def test_nonmatching_canary_is_separate_from_real_order():
    x=json.loads((ROOT/'config/live_test_account_policy.json').read_text())
    assert x['canaryModes']['nonMatchingValidation']['authorized'] is True
    assert x['canaryModes']['nonMatchingValidation']['financialEffectExpected'] is False
    assert x['canaryModes']['realMatchingEngineOrder']['authorized'] is False
    assert x['canaryModes']['realMatchingEngineOrder']['requiresOwnerCapitalEnvelopeChange'] is True

def test_binance_public_minimum_exceeds_current_cap():
    x=json.loads((ROOT/'config/live_test_account_policy.json').read_text())
    cap=Decimal(x['maxTestNotionalQuote'])
    for symbol in ('BTCUSDT','ETHUSDT'):
        assert Decimal(x['knownPublicConstraints']['BINANCE'][symbol]['minNotional']) > cap
    assert x['orderSubmissionAllowed'] is False
