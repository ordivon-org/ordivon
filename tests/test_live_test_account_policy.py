from pathlib import Path
import json,subprocess
from decimal import Decimal
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

def test_low_balance_claim_does_not_bypass_current_qualification():
    x=json.loads((ROOT/'config/live_test_account_policy.json').read_text())
    assert any('authoritative account balance' in g for g in x['requiredCurrentQualificationFacts'])
    assert any('withdraw permission absent' in g for g in x['requiredCurrentQualificationFacts'])
    assert any('reconciliation read path healthy' in g for g in x['requiredCurrentQualificationFacts'])

def test_policy_checker_keeps_write_blocked():
    p=subprocess.run([str(ROOT/'scripts/check-live-test-account-policy')],cwd=ROOT,text=True,capture_output=True,check=True)
    v=json.loads(p.stdout)
    assert v['liveEndpointUseAllowed'] is True
    assert v['orderSubmissionAllowed'] is False
    assert v['productionTradingAuthorized'] is False
