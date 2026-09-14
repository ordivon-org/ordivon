from market_capital.live_test_admission import evaluate_live_test_account


def base(**overrides):
    x={
      'venue':'BINANCE','permissionStanding':'READ_ONLY_VERIFIED','externalFinancialWriteAttempted':False,
      'balances':[{'asset':'USDT','total':'0.2','available':'0.2','locked':'0'}],
      'positions':[],'openOrders':[],'fills':[],'orderHistory':[]
    }
    x.update(overrides); return x


def test_empty_near_zero_live_account_can_be_admitted_as_test_only():
    x=evaluate_live_test_account(reality=base(),quote_asset='USDT',permission={'trade':True,'withdraw':False,'transfer':False},clock_passed=True,reconciliation_healthy=True)
    assert x['standing']=='ADMITTED_EMPTY_LIVE_TEST_ACCOUNT'
    assert x['orderSubmissionAllowed'] is True
    assert x['productionTradingAuthorized'] is False


def test_nonquote_dust_blocks_admission():
    r=base(balances=[{'asset':'USDT','total':'0.2'},{'asset':'BTC','total':'0.000001'}])
    x=evaluate_live_test_account(reality=r,quote_asset='USDT',permission={'trade':True,'withdraw':False,'transfer':False},clock_passed=True,reconciliation_healthy=True)
    assert x['standing']=='BLOCKED'
    assert any(s.startswith('nonquote-balance-present') for s in x['blockingReasons'])


def test_quote_balance_over_one_blocks():
    r=base(balances=[{'asset':'USDT','total':'1.01'}])
    x=evaluate_live_test_account(reality=r,quote_asset='USDT',permission={'trade':True,'withdraw':False,'transfer':False},clock_passed=True,reconciliation_healthy=True)
    assert 'quote-balance-exceeds-test-threshold' in x['blockingReasons']


def test_position_or_open_order_blocks():
    r=base(positions=[{'instrumentId':'BTC-USDT','quantity':'0.1'}],openOrders=[{'clientOrderId':'x'}])
    x=evaluate_live_test_account(reality=r,quote_asset='USDT',permission={'trade':True,'withdraw':False,'transfer':False},clock_passed=True,reconciliation_healthy=True)
    assert 'nonzero-position-present' in x['blockingReasons']
    assert 'open-order-present' in x['blockingReasons']


def test_permission_or_health_failure_blocks():
    x=evaluate_live_test_account(reality=base(permissionStanding='NOT_VERIFIED'),quote_asset='USDT',permission={'trade':True,'withdraw':False,'transfer':False},clock_passed=False,reconciliation_healthy=False)
    assert x['standing']=='BLOCKED'
    assert 'readonly-reality-not-verified' in x['blockingReasons']
    assert 'clock-gate-not-passed' in x['blockingReasons']
    assert 'reconciliation-not-healthy' in x['blockingReasons']
