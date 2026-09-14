from pathlib import Path
import json, subprocess
ROOT=Path(__file__).resolve().parents[1]

def test_nonlive_provisioning_never_grants_live_write():
    x=json.loads((ROOT/'config/nonlive_credential_provisioning.json').read_text())
    assert x['userAuthorization']=='DEMO_TESTNET_EXTERNAL_WRITES_AUTHORIZED'
    assert x['liveWriteAuthorization']=='NOT_GRANTED'
    assert x['externalFinancialWritesAllowed'] is False
    assert x['venues']['OKX']['liveCredentialReuseForbidden'] is True
    assert x['venues']['BINANCE']['liveCredentialReuseForbidden'] is True

def test_provisioning_checker_requires_server_issued_nonlive_key():
    p=subprocess.run([str(ROOT/'scripts/check-nonlive-credential-provisioning')],cwd=ROOT,text=True,capture_output=True,check=True)
    x=json.loads(p.stdout)
    assert x['binancePrivateKeyPresent'] is True
    assert x['binancePublicKeyPresent'] is True
    assert x['liveCredentialReuseForbidden'] is True
    assert x['externalFinancialWritesAllowed'] is False
