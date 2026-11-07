"""Native PostgreSQL consumer: durable Demo intent precommit and at-most-one claim."""
from __future__ import annotations

import json
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import psycopg
import pytest

from ordivon_capital.trading.postgres_demo_intent import (
    DemoIntent,
    DemoIntentConflict,
    PostgresDemoIntentStore,
)

DSN = os.environ.get("ORDIVON_CAPITAL_PG_TEST_DSN")
pytestmark = pytest.mark.skipif(not DSN, reason="isolated actual PostgreSQL test DSN required")
DIGEST = "sha256:" + "1" * 64


@pytest.fixture(autouse=True)
def disposable_table():
    if DSN is None:
        yield
        return
    PostgresDemoIntentStore(DSN)
    with psycopg.connect(DSN) as db:
        db.execute("TRUNCATE ordivon_capital.demo_order_intents")
    yield


def _intent(name: str = "one", client_id: str = "abc001") -> DemoIntent:
    return DemoIntent(
        intent_id="demo:" + name,
        account_ref="demo-account-one",
        client_order_id=client_id,
        instrument_id="BTC-USDT",
        side="buy",
        size="0.001",
        limit_price="40000",
        decision_ref="decision:investor-1",
        risk_evidence_digest=DIGEST,
        policy_evidence_digest=DIGEST,
    )


def test_pg_intent_identical_replay_and_distinct_client_id_conflict():
    assert DSN
    store = PostgresDemoIntentStore(DSN)
    initial = store.stage(_intent())
    assert initial["state"] == "STAGED"
    assert store.stage(_intent()) == initial
    with pytest.raises(DemoIntentConflict):
        store.stage(_intent("other", "abc001"))
    with pytest.raises(DemoIntentConflict):
        store.stage(DemoIntent(**{**_intent().__dict__, "size": "0.01"}))
    assert store.inspect("demo:one")["state"] == "STAGED"


def test_real_pg_commit_before_post_and_restart_readback():
    assert DSN
    store = PostgresDemoIntentStore(DSN)
    staged = store.stage(_intent())
    asserted = store.claim_once("demo:one", staged["digest"])
    assert asserted["clOrdId"] == "abc001"
    with pytest.raises(DemoIntentConflict, match="do not repeat POST"):
        store.claim_once("demo:one", staged["digest"])
    reopened = PostgresDemoIntentStore(DSN)
    assert reopened.inspect("demo:one")["state"] == "EFFECT_UNKNOWN"
    reopened.record_ack("demo:one", "123456")
    reopened.record_ack("demo:one", "123456")
    with pytest.raises(DemoIntentConflict):
        reopened.record_ack("demo:one", "999999")
    assert store.inspect("demo:one")["providerOrderId"] == "123456"
    assert store.inspect("demo:one")["state"] == "ACKNOWLEDGED"


def test_real_pg_cancel_is_separate_unknown_effect():
    assert DSN
    store = PostgresDemoIntentStore(DSN)
    staged = store.stage(_intent())
    store.claim_once("demo:one", staged["digest"])
    store.record_ack("demo:one", "123456")
    store.claim_cancel_once("demo:one", "123456")
    with pytest.raises(DemoIntentConflict):
        store.claim_cancel_once("demo:one", "123456")
    assert PostgresDemoIntentStore(DSN).inspect("demo:one")["cancelStanding"] == "EFFECT_UNKNOWN"
    store.record_cancel_ack("demo:one")
    store.record_cancel_ack("demo:one")
    assert store.inspect("demo:one")["cancelStanding"] == "ACK_ACCEPTED_NOT_FINAL"


def test_real_pg_concurrent_claims_at_most_one_accepted():
    assert DSN
    store = PostgresDemoIntentStore(DSN)
    staged = store.stage(_intent())
    def claim(_):
        try:
            PostgresDemoIntentStore(DSN).claim_once("demo:one", staged["digest"])
            return "CLAIMED"
        except DemoIntentConflict:
            return "BLOCKED"
    with ThreadPoolExecutor(max_workers=8) as pool:
        outcomes = list(pool.map(claim, range(8)))
    assert outcomes.count("CLAIMED") == 1
    assert outcomes.count("BLOCKED") == 7
    assert store.inspect("demo:one")["state"] == "EFFECT_UNKNOWN"


def test_actual_pg_cli_stage_and_policy_blocks_provider_post(monkeypatch, tmp_path: Path, capsys):
    assert DSN
    from ordivon_capital.trading.okx_demo_execution import OkxDemoError, main
    monkeypatch.setenv("ORDIVON_CAPITAL_PG_DSN", DSN)
    file = tmp_path / "request.json"
    file.write_text(json.dumps({
        "schemaVersion": 1,
        "operation": "STAGE_INTENT",
        "parameters": _intent().__dict__,
    }))
    assert main(["--request", str(file)]) == 0
    receipt = json.loads(capsys.readouterr().out)
    assert receipt["state"] == "STAGED"
    file.write_text(json.dumps({
        "schemaVersion": 1, "operation": "INSPECT_INTENT", "intentId": "demo:one",
    }))
    assert main(["--request", str(file)]) == 0
    inspect = json.loads(capsys.readouterr().out)
    assert inspect["digest"] == receipt["digest"]
    assert inspect["state"] == "STAGED"
    file.write_text(json.dumps({
        "schemaVersion": 1, "operation": "PLACE_LIMIT", "intentId": "demo:one",
        "parameters": {"instrument_id": "BTC-USDT", "side": "buy",
                       "size": "0.001", "limit_price": "40000",
                       "client_order_id": "abc001"},
    }))
    with pytest.raises(OkxDemoError, match="not admitted"):
        main(["--request", str(file)])
    assert PostgresDemoIntentStore(DSN).inspect("demo:one")["state"] == "STAGED"
