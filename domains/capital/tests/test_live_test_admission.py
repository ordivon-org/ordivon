from pathlib import Path

from ordivon_capital.market.opa_policy import evaluate_live_test_account

ROOT = Path(__file__).resolve().parents[1]
POLICY_CONFIG = ROOT / "config/execution_policy.json"


def base(**overrides):
    x={
      'venue':'BINANCE','permissionStanding':'READ_ONLY_VERIFIED','externalFinancialWriteAttempted':False,
      'balances':[{'asset':'USDT','total':'0.2','available':'0.2','locked':'0'}],
      'positions':[],'openOrders':[],'fills':[],'orderHistory':[]
    }
    x.update(overrides); return x


def test_empty_near_zero_live_account_can_be_admitted_as_test_only():
    x=evaluate_live_test_account(repo=ROOT,config_path=POLICY_CONFIG,reality=base(),quote_asset='USDT',permission={'trade':True,'withdraw':False,'transfer':False},clock_passed=True,reconciliation_healthy=True)
    assert x['standing']=='ADMITTED_EMPTY_LIVE_TEST_ACCOUNT'
    assert x['orderSubmissionAllowed'] is True
    assert x['productionTradingAuthorized'] is False


def test_nonquote_dust_blocks_admission():
    r=base(balances=[{'asset':'USDT','total':'0.2'},{'asset':'BTC','total':'0.000001'}])
    x=evaluate_live_test_account(repo=ROOT,config_path=POLICY_CONFIG,reality=r,quote_asset='USDT',permission={'trade':True,'withdraw':False,'transfer':False},clock_passed=True,reconciliation_healthy=True)
    assert x['standing']=='BLOCKED'
    assert any(s.startswith('nonquote-balance-present') for s in x['blockingReasons'])


def test_quote_balance_over_one_blocks():
    r=base(balances=[{'asset':'USDT','total':'1.01'}])
    x=evaluate_live_test_account(repo=ROOT,config_path=POLICY_CONFIG,reality=r,quote_asset='USDT',permission={'trade':True,'withdraw':False,'transfer':False},clock_passed=True,reconciliation_healthy=True)
    assert 'quote-balance-exceeds-test-threshold' in x['blockingReasons']


def test_position_or_open_order_blocks():
    r=base(positions=[{'instrumentId':'BTC-USDT','quantity':'0.1'}],openOrders=[{'clientOrderId':'x'}])
    x=evaluate_live_test_account(repo=ROOT,config_path=POLICY_CONFIG,reality=r,quote_asset='USDT',permission={'trade':True,'withdraw':False,'transfer':False},clock_passed=True,reconciliation_healthy=True)
    assert 'nonzero-position-present' in x['blockingReasons']
    assert 'open-order-present' in x['blockingReasons']


def test_permission_or_health_failure_blocks():
    x=evaluate_live_test_account(repo=ROOT,config_path=POLICY_CONFIG,reality=base(permissionStanding='NOT_VERIFIED'),quote_asset='USDT',permission={'trade':True,'withdraw':False,'transfer':False},clock_passed=False,reconciliation_healthy=False)
    assert x['standing']=='BLOCKED'
    assert 'readonly-reality-not-verified' in x['blockingReasons']
    assert 'clock-gate-not-passed' in x['blockingReasons']
    assert 'reconciliation-not-healthy' in x['blockingReasons']


def test_opa_is_the_live_test_policy_decision_owner():
    x=evaluate_live_test_account(repo=ROOT,config_path=POLICY_CONFIG,reality=base(),quote_asset="USDT",permission={"trade":True,"withdraw":False,"transfer":False},clock_passed=True,reconciliation_healthy=True)
    assert x["policyEngine"] == "OPA"
    source=(ROOT/"src/ordivon_capital/market/opa_policy.py").read_text()
    assert "live_test_account_decision" not in source
