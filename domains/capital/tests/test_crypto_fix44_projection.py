import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_canonical_projector_is_local_bounded_and_quickfix_is_oracle_only():
    local = (ROOT / "src/ordivon_capital/trading/fix44_projection.py").read_text()
    oracle = (
        ROOT / "tools/quickfixn_1_14_1/fix44-projector/Program.cs"
    ).read_text()
    runner = (ROOT / "scripts/run-crypto-fix-projection-r4").read_text()

    assert "LOCAL_BOUNDED_FIX44_TAGVALUE_PROJECTOR" in local
    assert "BodyLength (9)" in local
    assert "CheckSum (10)" in local
    assert "QuickFix.FIX44" in oracle
    assert "NewOrderSingle" in oracle
    assert "quickfixn_1_14_1" not in runner
    assert "ordivon_capital.trading.fix44_projection" in runner


def test_r4_runner_keeps_non_live_authority_and_identity_continuity():
    s = (ROOT / "scripts/run-crypto-fix-projection-r4").read_text()
    assert 'check-execution-policy" --mode non-live' in s
    assert "'clOrdId':row['clientOrderId']" in s
    assert "'externalFinancialWritesAttempted':False" in s


def _assert_r4_projection_evidence(x):
    assert x["standing"] == "PASS_CRYPTO_MECHANICS_TO_FIX44_PROJECTION"
    assert len(x["projectedIntents"]) == 4
    assert x["composition"]["fixImplementation"] == "LOCAL_BOUNDED_FIX44_TAGVALUE_PROJECTOR"
    assert "120/120 byte-exact" in x["composition"]["quickfixDifferentialReference"]
    assert not x["networkSessionEnabled"]
    assert not x["brokerCredentialsUsed"]
    assert not x["externalFinancialWritesAttempted"]
    assert not x["economicDecisionClaimed"]
    for row in x["projectedIntents"]:
        assert row["protocol"] == "FIX.4.4"
        assert row["msgType"] == "D"
        assert row["ordType"] == "1"
        assert row["timeInForce"] == "3"
        assert row["exDestination"] in {"OKX", "BINANCE"}


def test_committed_r4_evidence_is_frozen_standard_projection_only():
    p = ROOT / "evidence/crypto-fix44-projection-r4-20260914.json"
    before = p.read_bytes()
    _assert_r4_projection_evidence(json.loads(before))

    subprocess.run(
        [str(ROOT / "scripts/run-crypto-fix-projection-r4")],
        check=True,
        cwd=ROOT,
        capture_output=True,
        text=True,
    )

    assert p.read_bytes() == before
    dynamic = ROOT / ".artifacts/crypto-fix-r4/evidence.json"
    dynamic_doc = json.loads(dynamic.read_text())
    _assert_r4_projection_evidence(dynamic_doc)
    assert dynamic_doc["composition"]["sourceMechanicsStanding"] == "HISTORICAL_CANDIDATE_EVIDENCE_ONLY"
    assert dynamic_doc["composition"]["sourceMechanics"] == "frozen historical NautilusTrader rc4 mechanics evidence"
    assert dynamic_doc["identityContinuity"] == "frozen mechanics evidence clientOrderId == FIX ClOrdID"


def test_fix44_is_explicit_legacy_profile_not_semantic_owner():
    cfg = json.loads((ROOT / "config/fix_order_semantics.json").read_text())
    assert cfg["semanticStandard"] == "FIX Latest"
    assert cfg["wireCompatibilityProfile"] == "FIX.4.4"
    assert cfg["legacyProfile"] is True
    assert cfg["implementation"] == "LOCAL_BOUNDED_FIX44_TAGVALUE_PROJECTOR"
    assert cfg["wireFrameComplete"] is False
    assert cfg["quickfixDifferentialReference"]["standing"] == (
        "DIFFERENTIAL_ORACLE_NOT_CANONICAL_RUNTIME"
    )
