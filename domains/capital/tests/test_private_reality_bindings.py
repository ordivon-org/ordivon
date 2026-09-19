from pathlib import Path
import json, subprocess
ROOT=Path(__file__).resolve().parents[1]

def test_observer_bindings_are_external_and_executor_is_excluded():
    x=json.loads((ROOT/'config/private_reality_policy.json').read_text())
    assert x['credentialBindings']['OKX']['role']=='observer'
    assert x['credentialBindings']['BINANCE']['role']=='observer'
    assert x['credentialBindings']['BINANCE_USDM']['role']=='observer-candidate'
    assert x['credentialBindings']['BINANCE_USDM']['permissionStanding']=='PENDING_FRESH_PROVIDER_VERIFICATION'
    assert x['credentialBindings']['OKX']['copyIntoRepository'] is False
    assert x['credentialBindings']['BINANCE']['copyIntoRepository'] is False
    assert x['credentialBindings']['BINANCE']['executorBindingExplicitlyExcluded'].endswith('/binance/executor')
    assert x['privateAccountDataAllowed'] is False
    assert x['externalFinancialWritesAllowed'] is False

def test_binding_checker_only_checks_paths_and_modes():
    p=subprocess.run([str(ROOT/'scripts/check-private-reality-credential-bindings')],cwd=ROOT,text=True,capture_output=True,check=True)
    assert 'secretBytesRead": false' in p.stdout
    assert 'binanceExecutorExcluded": true' in p.stdout
