import json
import subprocess
from pathlib import Path

import pytest

ROOT=Path(__file__).resolve().parents[1]


def test_demo_execution_stays_not_admitted():
    x=json.loads((ROOT/'config/demo_execution_policy.json').read_text())
    assert x['standing']=='PREPARED_NOT_ADMITTED'
    assert x['demoWriteAdmission']=='NOT_ADMITTED'
    assert x['liveWriteAdmission']=='NOT_ADMITTED'
    assert x['externalFinancialWritesAllowed'] is False
    assert x['venues']['OKX']['environment']=='DEMO'
    assert x['venues']['BINANCE']['environment']=='TESTNET'
    assert x['venues']['BINANCE']['productType']=='SPOT'
    assert x['venues']['OKX']['credentialBinding'] is None
    assert x['venues']['BINANCE']['credentialBinding'] is None
    assert x['venues']['OKX']['candidateStanding']=='NOT_ADMITTED_CANDIDATE_EVIDENCE_ONLY'
    assert x['venues']['BINANCE']['candidateStanding']=='NOT_ADMITTED_CANDIDATE_EVIDENCE_ONLY'


@pytest.mark.provider_qualification
def test_nautilus_candidate_execution_configs_construct_without_credentials_or_network():
    p=subprocess.run([str(ROOT/'tools/nautilus_rc4/check-demo-execution-configs')],cwd=ROOT,text=True,capture_output=True,check=True)
    assert 'okxConfigConstructed": true' in p.stdout
    assert 'binanceConfigConstructed": true' in p.stdout
    assert 'credentialsPassed": false' in p.stdout
    assert 'networkCalled": false' in p.stdout
