from pathlib import Path
import json, subprocess
ROOT=Path(__file__).resolve().parents[1]

def test_private_reality_credentials_may_be_located_but_private_data_stays_not_admitted():
    x=json.loads((ROOT/'config/private_reality_policy.json').read_text())
    assert x['standing']=='OWNER_MANDATE_PRESENT_PERMISSION_NOT_CURRENT'
    assert x['ownerCredentialUseMandate']=='AUTHORIZED_READ_ONLY_PRIVATE_REALITY_OBSERVATION'
    assert x['credentialPermissionStanding']=='PENDING_FRESH_PROVIDER_VERIFICATION'
    assert x['privateAccountDataAdmission']=='NOT_ADMITTED'
    assert not x['privateAccountDataAllowed']
    assert not x['orderCapableCredentialsAllowed']
    assert not x['withdrawalCredentialsAllowed']
    assert not x['externalFinancialWritesAllowed']
    assert not x['secretDiscoveryAllowed']
    assert x['venues']['OKX']['requiredPermission']=='Read'
    assert set(x['venues']['OKX']['forbiddenPermissions'])=={'Trade','Withdraw'}
    assert x['venues']['BINANCE']['requiredSecurityType']=='USER_DATA'
    assert not x['venues']['BINANCE']['tradePermissionRequired']
    assert x['venues']['BINANCE_USDM']['requiredSecurityType']=='USER_DATA'
    assert not x['venues']['BINANCE_USDM']['tradePermissionRequired']
    assert x['venues']['BINANCE_USDM']['permissionStanding']=='PENDING_FRESH_PROVIDER_VERIFICATION'
    assert x['venues']['BINANCE_USDM']['productEligibilityStanding']=='PENDING_PROVIDER_VERIFICATION'
    assert x['venues']['BINANCE_USDM']['tradFiAgreementAutomationAllowed'] is False

def test_preflight_uses_blank_credentials_and_no_secret_discovery():
    s=(ROOT/'scripts/check-private-reality-readonly-preflight').read_text()
    assert "api_key='',api_secret=''" in s
    forbidden=('os.environ','getenv(','env |','printenv','grep -R')
    assert all(x not in s for x in forbidden)
    p=subprocess.run([str(ROOT/'scripts/check-private-reality-readonly-preflight')],cwd=ROOT,text=True,capture_output=True,check=True)
    assert 'credentialsLoaded": false' in p.stdout
    assert 'networkCalled": false' in p.stdout
