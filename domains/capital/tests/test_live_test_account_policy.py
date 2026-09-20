import json
import subprocess
from decimal import Decimal
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def test_live_accounts_may_be_test_accounts_without_becoming_demo():
    x=json.loads((ROOT/'config/live_test_account_policy.json').read_text())
    assert x['ownerUseMandate']=='AUTHORIZED_NON_PRODUCTION_LIVE_ENDPOINT_QUALIFICATION'
    assert x['accountQualificationStanding']=='PENDING_FRESH_PRIVATE_ACCOUNT_VERIFICATION'
    assert x['orderSubmissionAdmission']=='NOT_ADMITTED'
    assert x['liveEndpointUseAllowed'] is True
    assert x['productionTradingAuthorized'] is False
    assert x['orderSubmissionAllowed'] is False
    assert Decimal(x['maxTestNotionalQuote']) <= Decimal('1')
    for venue in ('OKX','BINANCE'):
        assert x['venues'][venue]['endpointClass']=='LIVE'
        assert x['venues'][venue]['role']=='TEST_ACCOUNT_BY_OWNER_POLICY'
    assert x['venues']['BINANCE']['executorCredentialBinding']=='UNBOUND_NOT_ADMITTED'
    okx=x['venues']['OKX']
    assert okx['executorCredentialBinding']=='/root/.config/ordivon/secrets/okx/live-trade/config.toml'
    assert okx['qualificationStanding']=='PASS_CURRENT_PROVIDER_BINDING_NO_ORDER_ADMISSION'
    assert okx['providerTradePermissionCurrent'] is True
    assert okx['providerWithdrawPermissionCurrent'] is False
    assert 'executorCredential' not in okx

def test_low_balance_claim_does_not_bypass_current_qualification():
    x=json.loads((ROOT/'config/live_test_account_policy.json').read_text())
    assert any('authoritative account balance' in g for g in x['requiredCurrentQualificationFacts'])
    assert any('withdraw permission absent' in g for g in x['requiredCurrentQualificationFacts'])
    assert any('reconciliation read path healthy' in g for g in x['requiredCurrentQualificationFacts'])

def test_bound_provider_capability_does_not_bypass_order_admission():
    x=json.loads((ROOT/'config/live_test_account_policy.json').read_text())
    assert x['venues']['OKX']['providerTradePermissionCurrent'] is True
    assert x['orderSubmissionAdmission']=='NOT_ADMITTED'
    assert x['orderSubmissionAllowed'] is False
    assert x['productionTradingAuthorized'] is False

def test_policy_checker_keeps_write_blocked():
    p=subprocess.run([str(ROOT/'scripts/check-live-test-account-policy')],cwd=ROOT,text=True,capture_output=True,check=True)
    v=json.loads(p.stdout)
    assert v['liveEndpointUseAllowed'] is True
    assert v['okxProviderTradePermissionCurrent'] is True
    assert v['orderSubmissionAllowed'] is False
    assert v['productionTradingAuthorized'] is False
