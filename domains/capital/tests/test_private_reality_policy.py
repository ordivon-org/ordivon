from pathlib import Path
import json, subprocess
ROOT=Path(__file__).resolve().parents[1]

def test_private_reality_is_prepared_but_not_admitted():
    x=json.loads((ROOT/'config/private_reality_policy.json').read_text())
    assert x['standing']=='PREPARED_NOT_ADMITTED'
    assert x['credentialUseAdmission']=='NOT_ADMITTED'
    assert not x['privateAccountDataAllowed']
    assert not x['orderCapableCredentialsAllowed']
    assert not x['withdrawalCredentialsAllowed']
    assert not x['externalFinancialWritesAllowed']
    assert not x['secretDiscoveryAllowed']
    assert x['venues']['OKX']['requiredPermission']=='Read'
    assert set(x['venues']['OKX']['forbiddenPermissions'])=={'Trade','Withdraw'}
    assert x['venues']['BINANCE']['requiredSecurityType']=='USER_DATA'
    assert not x['venues']['BINANCE']['tradePermissionRequired']

def test_preflight_uses_blank_credentials_and_no_secret_discovery():
    s=(ROOT/'scripts/check-private-reality-readonly-preflight').read_text()
    assert "api_key='',api_secret=''" in s
    forbidden=('os.environ','getenv(','env |','printenv','grep -R')
    assert all(x not in s for x in forbidden)
    p=subprocess.run([str(ROOT/'scripts/check-private-reality-readonly-preflight')],cwd=ROOT,text=True,capture_output=True,check=True)
    assert 'credentialsLoaded": false' in p.stdout
    assert 'networkCalled": false' in p.stdout
