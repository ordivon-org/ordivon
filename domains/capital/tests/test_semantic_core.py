from __future__ import annotations

from pathlib import Path
import json
import pytest

from market_capital.semantic import (
    BLOCK_NOT_GRANTED,
    EffectDisposition,
    ProofObject,
    ProductionAuthorization,
    SemanticViolation,
    WitnessRecord,
    classify_effect_disposition,
    reject_false_green,
    validate_effect_authority_inputs,
    validate_same_cut,
    witness_field_names,
)

D = "sha256:" + "a" * 64


def witness(seq: int, ns: int, *, instance: str = "recorder:a", session: str = "session:1", clock: str = "clock:mono-a") -> WitnessRecord:
    return WitnessRecord.build(
        venue="OKX" if seq % 2 else "BINANCE",
        connection_id=f"conn:{seq}",
        raw_bytes=f"frame-{seq}".encode(),
        recv_monotonic_ns=ns,
        recv_wall_time="2026-09-11T07:00:00Z",
        venue_sequence_if_any=None,
        append_sequence=seq,
        recorder_instance=instance,
        recorder_session=session,
        clock_domain=clock,
        config_digest=D,
        code_digest=D,
    )


def current_proof() -> ProofObject:
    return ProofObject(
        issuer="issuer:1",
        subject="effect:1",
        resource_identity="scarcity:capital/usdt/1",
        generation="generation:1",
        source_cut="cut:1",
        digest=D,
        current=True,
    )


def test_production_is_blocked_by_default():
    p = ProductionAuthorization()
    assert p.state == BLOCK_NOT_GRANTED
    assert p.granted is False


def test_reservation_is_not_grant_and_policy_is_only_an_input():
    with pytest.raises(SemanticViolation, match="reservation is not a grant"):
        validate_effect_authority_inputs(
            proof=current_proof(), reservation_ref="reservation:1", grant_ref=None,
            policy_allowed=True, production=ProductionAuthorization(),
        )
    with pytest.raises(SemanticViolation, match="production authorization not granted"):
        validate_effect_authority_inputs(
            proof=current_proof(), reservation_ref="reservation:1", grant_ref="grant:1",
            policy_allowed=True, production=ProductionAuthorization(),
        )


def test_revoked_or_superseded_proof_cannot_be_current_authority():
    for kwargs in ({"revoked": True}, {"superseded": True}, {"current": False}):
        base = current_proof().__dict__ | kwargs
        with pytest.raises(SemanticViolation):
            ProofObject(**base).validate_current()


def test_same_cut_requires_one_instance_session_clock_and_serial_order():
    rows = validate_same_cut([witness(1, 100), witness(2, 110)])
    assert [r.append_sequence for r in rows] == [1, 2]
    with pytest.raises(SemanticViolation, match="one recorder instance"):
        validate_same_cut([witness(1, 100), witness(2, 110, instance="recorder:b")])
    with pytest.raises(SemanticViolation, match="strictly monotone"):
        validate_same_cut([witness(2, 100), witness(2, 110)])


def test_witness_recorder_does_not_own_strategy_or_capital_semantics():
    forbidden = {"strategy", "pnl", "capital", "grant", "portfolio", "position", "order"}
    names = witness_field_names()
    assert not forbidden.intersection(names)


@pytest.mark.parametrize(
    "standing,expected",
    [
        ("UNKNOWN", EffectDisposition.RETAIN),
        ("AMBIGUOUS", EffectDisposition.RETAIN),
        ("PARTIAL_OPEN", EffectDisposition.RETAIN),
        ("CONTRADICTORY", EffectDisposition.RETAIN),
        ("PROVEN_NO_EFFECT", EffectDisposition.RELEASE),
        ("RECONCILED_ZERO_FILL_TERMINAL", EffectDisposition.RELEASE),
        ("POSITIVE_EXECUTION", EffectDisposition.CONSUME),
    ],
)
def test_effect_disposition_is_fail_closed(standing, expected):
    assert classify_effect_disposition(standing) is expected


def test_false_green_corpus_is_rejected():
    corpus = json.loads((Path(__file__).parents[1] / "destroyer" / "false-green-corpus-v0.json").read_text())
    for case in corpus["cases"]:
        with pytest.raises(SemanticViolation):
            reject_false_green(case["claim"])


def test_clean_room_module_has_no_legacy_imports():
    text = (Path(__file__).parents[1] / "src" / "market_capital" / "semantic.py").read_text()
    for legacy in ("from kernel", "import kernel", "from executor", "from mcp", "scripts/"):
        assert legacy not in text
