from pathlib import Path
import json
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]

def test_public_shadow_product_closes_bounded_no_effect_feedback_loop(tmp_path):
    subprocess.run([
        sys.executable,
        str(ROOT/'scripts/consume_crypto_public_shadow_product_r1.py'),
        '--output-dir',str(tmp_path)
    ],check=True)
    r=json.loads((tmp_path/'receipt.json').read_text())
    d=json.loads((tmp_path/'decision-outcome-feedback.json').read_text())
    events=json.loads((tmp_path/'openlineage.json').read_text())
    assert r['standing']=='PASS_PRODUCT_TO_DECISION_OUTCOME_FEEDBACK_NO_EXTERNAL_EFFECT'
    assert r['productId']=='d14d7457-c9aa-59e0-8bf5-7783cea39c1c'
    assert r['productVersion']=='2026.09.14'
    assert d['claim']['standing']=='FIT_FOR_BOUNDED_PUBLIC_MARKET_MONITORING'
    assert d['decision']['standing']=='NO_EXECUTION_OR_DIRECTIONAL_ACTION_ADMITTED'
    assert d['action']['externalFinancialWriteAttempted'] is False
    assert d['outcome']['externalFinancialWriteObserved'] is False
    assert d['feedback']['changeRequired'] is False
    assert d['feedback']['collectionPolicyDisposition']=='KEEP_CURRENT_PUBLIC_OBSERVATION_BOUNDARY'
    assert d['feedback']['qualityGateDisposition']=='KEEP_FROZEN_1200MS_SOURCE_AND_RECEIVE_SPAN_GATES'
    assert d['feedback']['modelPolicyDisposition']=='NO_DIRECTIONAL_MODEL_UPDATE_FROM_THIS_PRODUCT'
    assert [x['eventType'] for x in events]==['START','COMPLETE']
    assert r['sourceSha256'] in events[0]['inputs'][0]['name']
    assert r['decisionArtifactSha256'] in events[1]['outputs'][0]['name']
