import json
import subprocess
import sys
from pathlib import Path

import pytest

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

@pytest.mark.parametrize("invalid", [
    "source_sha256", "brokerCredentialsUsed", "privateAccountDataUsed",
    "externalFinancialWritesAttempted", "governance",
])
def test_public_shadow_rejects_false_pass_under_python_optimized_mode(tmp_path, invalid):
    """Frozen public-data decisions must reject false input under python -O."""
    import hashlib
    import shutil

    owner = tmp_path / "capital"
    scripts = owner / "scripts"
    product_dir = owner / "data-products" / "crypto-public-shadow-r2"
    evidence_dir = owner / "evidence"
    scripts.mkdir(parents=True)
    product_dir.mkdir(parents=True)
    evidence_dir.mkdir(parents=True)
    script = scripts / "consume_crypto_public_shadow_product_r1.py"
    shutil.copyfile(ROOT / "scripts" / script.name, script)
    for name in ("odps.json", "acceptance.json", "governance-policy.odrl.jsonld"):
        shutil.copyfile(ROOT / "data-products" / "crypto-public-shadow-r2" / name, product_dir / name)
    source_path = evidence_dir / "crypto-public-shadow-r2-20260914.json"
    source = json.loads((ROOT / "evidence" / source_path.name).read_text())
    if invalid in ("brokerCredentialsUsed", "privateAccountDataUsed", "externalFinancialWritesAttempted"):
        source[invalid] = True
    source_path.write_text(json.dumps(source))
    acceptance_path = product_dir / "acceptance.json"
    acceptance = json.loads(acceptance_path.read_text())
    acceptance["sourceSha256"] = (
        "0" * 64 if invalid == "source_sha256"
        else hashlib.sha256(source_path.read_bytes()).hexdigest()
    )
    acceptance_path.write_text(json.dumps(acceptance))
    if invalid == "governance":
        policy_path = product_dir / "governance-policy.odrl.jsonld"
        policy = json.loads(policy_path.read_text())
        policy["prohibition"] = policy["prohibition"][:-1]
        policy_path.write_text(json.dumps(policy))

    output = tmp_path / "rejected"
    run = subprocess.run(
        [sys.executable, "-O", str(script), "--output-dir", str(output)],
        capture_output=True, text=True, check=False,
    )
    assert run.returncode != 0, "optimized Python accepted invalid frozen public observation evidence"
    assert not (output / "receipt.json").exists()
    assert not (output / "decision-outcome-feedback.json").exists()

def test_public_shadow_verified_receipt_is_equivalent_under_optimized_python(tmp_path):
    """Valid frozen input must yield the same decision and receipt under -O."""
    script = ROOT / "scripts" / "consume_crypto_public_shadow_product_r1.py"
    result = []
    for name, flags in (("normal", []), ("optimized", ["-O"])):
        output = tmp_path / name
        subprocess.run(
            [sys.executable, *flags, str(script), "--output-dir", str(output)],
            check=True, capture_output=True, text=True,
        )
        result.append((
            json.loads((output / "decision-outcome-feedback.json").read_text()),
            json.loads((output / "receipt.json").read_text()),
        ))
    assert result[0] == result[1]
    assert result[0][1]["externalFinancialWriteAttempted"] is False

@pytest.mark.parametrize("case", (
    "prepend", "append", "missing", "duplicate", "wrong-name", "wrong-version",
    "wrong-contract", "wrong-type", "wrong-product", "alias-only", "duplicate-alias",
))
def test_public_shadow_consumer_selects_exact_frozen_port_not_array_position(tmp_path, case):
    """Independent consumer identity, not a producer's list order or success."""
    import shutil

    owner = tmp_path / "capital"
    scripts = owner / "scripts"
    product_dir = owner / "data-products" / "crypto-public-shadow-r2"
    evidence_dir = owner / "evidence"
    scripts.mkdir(parents=True)
    product_dir.mkdir(parents=True)
    evidence_dir.mkdir(parents=True)
    script = scripts / "consume_crypto_public_shadow_product_r1.py"
    shutil.copyfile(ROOT / "scripts" / script.name, script)
    for name in ("odps.json", "acceptance.json", "governance-policy.odrl.jsonld"):
        shutil.copyfile(ROOT / "data-products" / "crypto-public-shadow-r2" / name, product_dir / name)
    evidence = "crypto-public-shadow-r2-20260914.json"
    shutil.copyfile(ROOT / "evidence" / evidence, evidence_dir / evidence)
    product_path = product_dir / "odps.json"
    product = json.loads(product_path.read_text())
    original = product["outputPorts"][0]
    expected = "358e57ff-d416-5dd6-a90c-f62b4bc94ff0"
    assert original["id"] == expected
    unrelated = {**original, "id": "aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee", "name": "unrelated"}
    if case == "prepend":
        product["outputPorts"] = [unrelated, original]
    elif case == "append":
        product["outputPorts"] = [original, unrelated]
    elif case == "missing":
        product["outputPorts"] = [unrelated]
    elif case == "duplicate":
        product["outputPorts"] = [original, {**original, "name": "conflicting"}]
    elif case == "wrong-name":
        original["name"] = "wrong"
    elif case == "wrong-version":
        original["version"] = "2026.09.15"
    elif case == "wrong-contract":
        original["contractId"] = unrelated["id"]
    elif case == "wrong-type":
        original["type"] = "file/csv"
    elif case == "wrong-product":
        product["id"] = unrelated["id"]
        acceptance_path = product_dir / "acceptance.json"
        acceptance = json.loads(acceptance_path.read_text())
        acceptance["productId"] = product["id"]
        acceptance_path.write_text(json.dumps(acceptance))
    elif case == "alias-only":
        original["id"] = original["id"].upper()
    else:
        product["outputPorts"].append({**original, "id": original["id"].upper()})
    product_path.write_text(json.dumps(product))
    output = tmp_path / "consumer"
    run = subprocess.run(
        [sys.executable, "-O", str(script), "--output-dir", str(output)],
        capture_output=True, text=True, check=False,
    )
    if case not in {"prepend", "append"}:
        assert run.returncode != 0, "unqualified exact port identity accepted"
        assert not output.exists()
        return
    assert run.returncode == 0, run.stderr
    receipt = json.loads((output / "receipt.json").read_text())
    decision = json.loads((output / "decision-outcome-feedback.json").read_text())
    lineage = json.loads((output / "openlineage.json").read_text())
    assert receipt["outputPortId"] == decision["product"]["outputPortId"] == expected
    assert all(f"#{expected}@" in row["inputs"][0]["name"] for row in lineage)
    assert receipt["externalFinancialWriteAttempted"] is False
