from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from agent_automation_ledger_reconcile import (  # noqa: E402
    classify_standing,
    execute_exact_reconciliation,
    plan_ledger,
)


def create_ledger(path: Path, rows: list[tuple[str, str]]) -> None:
    db = sqlite3.connect(path)
    try:
        db.execute(
            """
            CREATE TABLE requests (
                request_id TEXT PRIMARY KEY,
                request_digest TEXT NOT NULL,
                request_json TEXT NOT NULL,
                standing TEXT NOT NULL,
                provider_coordinate TEXT,
                evidence_digest TEXT,
                detail TEXT,
                effect_generation INTEGER NOT NULL DEFAULT 0,
                created_at_ms INTEGER NOT NULL,
                updated_at_ms INTEGER NOT NULL
            )
            """
        )
        for index, (effect_id, standing) in enumerate(rows):
            db.execute(
                "INSERT INTO requests VALUES(?,?,?,?,?,?,?,?,?,?)",
                (
                    effect_id,
                    f"digest-{index}",
                    json.dumps({"bootstrapPrompt": f"SECRET-{index}"}),
                    standing,
                    "https://chatgpt.com/c/bound" if standing == "bound" else None,
                    f"evidence-{index}",
                    "detail",
                    index,
                    1000 + index,
                    2000 + index,
                ),
            )
        db.commit()
    finally:
        db.close()


@pytest.mark.parametrize("standing", ["unknown", "submit-observed"])
def test_ambiguous_standings_are_reconcile_observation_only(standing: str) -> None:
    value = classify_standing(standing)
    assert value["action"] == "RECONCILE_OBSERVATION"
    assert value["providerObservationEligible"] is True
    assert value["automaticRetryAuthorized"] is False


def test_bound_is_noop() -> None:
    value = classify_standing("bound")
    assert value["action"] == "NOOP_BOUND"
    assert value["providerObservationEligible"] is False
    assert value["automaticRetryAuthorized"] is False


def test_pre_effect_failed_is_not_automatically_retried() -> None:
    value = classify_standing("pre-effect-failed")
    assert value["action"] == "EXPLICIT_RETRY_REQUIRED"
    assert value["providerObservationEligible"] is False
    assert value["automaticRetryAuthorized"] is False


def test_human_required_stays_out_of_ambiguous_reconcile() -> None:
    value = classify_standing("human-required")
    assert value["action"] == "HUMAN_CONTROL_TRANSFER_REQUIRED"
    assert value["providerObservationEligible"] is False


def test_plan_ledger_is_read_only_and_redacts_request_payload(tmp_path: Path) -> None:
    ledger = tmp_path / "materialization-ledger.sqlite"
    create_ledger(
        ledger,
        [
            ("effect-u", "unknown"),
            ("effect-s", "submit-observed"),
            ("effect-b", "bound"),
            ("effect-p", "pre-effect-failed"),
        ],
    )
    before = ledger.read_bytes()

    value = plan_ledger(ledger)

    assert value["dryRun"] is True
    assert value["requestCount"] == 4
    by_id = {row["effectId"]: row for row in value["requests"]}
    assert by_id["effect-u"]["action"] == "RECONCILE_OBSERVATION"
    assert by_id["effect-s"]["action"] == "RECONCILE_OBSERVATION"
    assert by_id["effect-b"]["action"] == "NOOP_BOUND"
    assert by_id["effect-p"]["action"] == "EXPLICIT_RETRY_REQUIRED"
    serialized = json.dumps(value, sort_keys=True)
    assert "bootstrapPrompt" not in serialized
    assert "SECRET-" not in serialized
    assert ledger.read_bytes() == before


def test_plan_can_be_bounded_to_exact_effect_ids(tmp_path: Path) -> None:
    ledger = tmp_path / "ledger.sqlite"
    create_ledger(ledger, [("effect-a", "unknown"), ("effect-b", "submit-observed")])
    value = plan_ledger(ledger, effect_ids={"effect-b"})
    assert [row["effectId"] for row in value["requests"]] == ["effect-b"]


class ReconcileRecorder:
    def __init__(self) -> None:
        self.calls = 0

    def __call__(self) -> dict[str, str]:
        self.calls += 1
        return {"disposition": "admitted", "workflowId": "wf-1"}


@pytest.mark.parametrize("standing", ["unknown", "submit-observed"])
def test_explicit_reconcile_executes_only_ambiguous_effect(
    standing: str,
) -> None:
    recorder = ReconcileRecorder()
    value = execute_exact_reconciliation(
        effect_id="effect-1",
        expected_effect_id="effect-1",
        standing=standing,
        reconcile=recorder,
    )
    assert recorder.calls == 1
    assert value["effectId"] == "effect-1"
    assert value["action"] == "RECONCILE_OBSERVATION"
    assert value["automaticRetryAuthorized"] is False


@pytest.mark.parametrize(
    "standing", ["bound", "ready-confirmed", "pre-effect-failed", "human-required", "prepared"]
)
def test_explicit_reconcile_rejects_nonambiguous_standings(standing: str) -> None:
    recorder = ReconcileRecorder()
    with pytest.raises(ValueError, match="not eligible"):
        execute_exact_reconciliation(
            effect_id="effect-1",
            expected_effect_id="effect-1",
            standing=standing,
            reconcile=recorder,
        )
    assert recorder.calls == 0


def test_explicit_reconcile_requires_exact_effect_identity() -> None:
    recorder = ReconcileRecorder()
    with pytest.raises(ValueError, match="effect identity"):
        execute_exact_reconciliation(
            effect_id="effect-1",
            expected_effect_id="effect-2",
            standing="unknown",
            reconcile=recorder,
        )
    assert recorder.calls == 0
