from pathlib import Path
import json
import subprocess

ROOT=Path(__file__).resolve().parents[1]

def test_projector_is_quickfix_sessionless_thin_projection():
    s=(ROOT/'tools/fix44-projector/Program.cs').read_text()
    assert 'QuickFix.FIX44' in s
    assert 'NewOrderSingle' in s
    assert 'ExDestination' in s
    assert 'IMMEDIATE_OR_CANCEL' in s
    assert 'Socket' not in s and 'HttpClient' not in s
    assert 'networkSessionEnabled' in s

def test_r4_runner_keeps_non_live_authority_and_identity_continuity():
    s=(ROOT/'scripts/run-crypto-fix-projection-r4').read_text()
    assert 'check-execution-policy" --mode non-live' in s
    assert "'clOrdId':row['clientOrderId']" in s
    assert "'externalFinancialWritesAttempted':False" in s

def test_committed_r4_evidence_is_standard_projection_only():
    p=ROOT/'evidence/crypto-fix44-projection-r4-20260914.json'
    if not p.exists():
        subprocess.run([str(ROOT/'scripts/run-crypto-fix-projection-r4')],check=True,cwd=ROOT,capture_output=True,text=True)
    x=json.loads(p.read_text())
    assert x['standing']=='PASS_CRYPTO_MECHANICS_TO_FIX44_PROJECTION'
    assert len(x['projectedIntents'])==4
    assert not x['networkSessionEnabled']
    assert not x['brokerCredentialsUsed']
    assert not x['externalFinancialWritesAttempted']
    assert not x['economicDecisionClaimed']
    for row in x['projectedIntents']:
        assert row['protocol']=='FIX.4.4'
        assert row['msgType']=='D'
        assert row['ordType']=='1'
        assert row['timeInForce']=='3'
        assert row['exDestination'] in {'OKX','BINANCE'}


def test_fix44_is_explicit_legacy_wire_profile_not_semantic_owner():
    cfg=json.loads((ROOT/'config/fix_order_semantics.json').read_text())
    assert cfg['semanticStandard']=='FIX Latest'
    assert cfg['wireCompatibilityProfile']=='FIX.4.4'
    assert cfg['legacyProfile'] is True
