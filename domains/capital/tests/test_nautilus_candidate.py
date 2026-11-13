import json
import os
import subprocess
import sys
import unittest
from hashlib import sha256
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "tools/nautilus_rc4/config/nautilus_candidate.json"


class NautilusCandidateBoundaryTests(unittest.TestCase):
    def test_candidate_is_non_live_only(self):
        cfg = json.loads(CONFIG.read_text())
        self.assertEqual(cfg["admissionLane"], "SHADOW_QUALIFICATION_ONLY")
        self.assertFalse(cfg["brokerConnectivityAllowed"])
        self.assertFalse(cfg["brokerCredentialsAllowed"])
        self.assertFalse(cfg["externalFinancialWritesAllowed"])
        self.assertFalse(cfg["productionLiveAdmitted"])

    @pytest.mark.provider_qualification
    def test_pinned_candidate_environment_is_available(self):
        out = subprocess.check_output([str(ROOT / "tools/nautilus_rc4/check-candidate")], text=True)
        result = json.loads(out)
        self.assertEqual(result["standing"], "NAUTILUS_CANDIDATE_BOUND_NON_LIVE")
        self.assertEqual(result["version"], "2.0.0rc4")
        self.assertEqual(result["python"], "3.12.13")


@pytest.mark.provider_qualification
@pytest.mark.native_nonlive
def test_python315_rc9_native_nonlive_reconciliation() -> None:
    # This is a real upstream BacktestEngine-to-Capital consumer, not a mock or
    # proof of external venue execution. The optional nonlive group is required.
    assert sys.version_info[:2] == (3, 15)
    from nautilus_trader import __version__ as upstream_version

    assert upstream_version == "2.0.0rc9"
    result = subprocess.check_output(
        [sys.executable, str(ROOT / "tools/nautilus_rc4/nonlive_effect_matrix.py")],
        cwd=ROOT,
        env=os.environ | {"PYTHONPATH": str(ROOT / "src")},
        text=True,
    )
    payload = json.loads(result)
    assert payload["providerVersion"] == "2.0.0rc9"
    assert payload["standing"] == "PASS_NAUTILUS_NONLIVE_EFFECT_RECONCILIATION_MATRIX"
    assert payload["observedResolutions"] == {
        "FILL": "POST_PENDING_TRANSFER",
        "PARTIAL_FILL_SLICES": "POST_PENDING_TRANSFER",
        "CANCEL": "VOID_PENDING_TRANSFER",
        "DENY": "VOID_PENDING_TRANSFER",
        "UNKNOWN_AFTER_SUBMISSION": "NO_MUTATION",
    }
    assert payload["partialFillSliceCount"] >= 2
    assert payload["externalFinancialWriteAttempted"] is False
    assert payload["realMoney"] is False


if __name__ == "__main__":
    unittest.main()


@pytest.mark.provider_qualification
@pytest.mark.native_nonlive
def test_rc9_synthetic_equity_paper_consumer(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "tools/nautilus_rc4"))
    import equity_paper_qualification as eq
    from nautilus_trader.model import ClientOrderId, OrderFilled

    for fee, nav in (("0.00", 100396), ("1.23", 100273)):
        result = eq.run_episode(fee)
        assert result["nativeNavMinor"] == result["paper"]["nav_minor"] == nav
        assert result["paper"]["cash_minor"] == 100000
        assert result["paper"]["payable_minor"] == 100000 - result["nativeCashMinor"]
        assert result["holidayPayableMinor"] == result["paper"]["payable_minor"]
        assert result["settlementCashMinor"] == result["nativeCashMinor"]
        assert result["settlementDate"] == eq.SETTLEMENT.isoformat()
        fill, event = result["fills"][0], result["events"][0]
        assert (fill["shares"], fill["price_minor"], fill["fee_minor"]) == (2, 11002, eq.minor(fee))
        assert fill["fill_id"] == event["trade_id"]
        assert fill["filled_at"] == eq.OPEN
        assert event["ts_event"] == eq.ns(eq.OPEN)
    # Same frozen target under a different opening price: no future-price sizing.
    assert eq.run_episode(ask="111.00")["fills"][0]["shares"] == 2
    for kwargs in ({"opening": False}, {"cash": "100.00"}):
        with pytest.raises(ValueError):
            eq.run_episode(**kwargs)
    for amount in ("1.001", "-1", "NaN", "Infinity"):
        with pytest.raises(ValueError):
            eq.minor(amount)
    intent = eq.Intent(eq.InstrumentId.from_str(event["instrument_id"]))
    order_id = ClientOrderId(event["client_order_id"])
    real = OrderFilled.from_dict(event)
    scope = result["expectedIdentity"]
    assert scope["account_id"] == event["account_id"]
    assert scope["trader_id"] == event["trader_id"]
    assert scope["strategy_id"] == event["strategy_id"]
    assert scope["venue_order_id"] == event["venue_order_id"]
    with pytest.raises(ValueError, match="duplicate"):
        eq.project([real, real], intent, order_id, scope)
    # Explicitly corrupted copies of native events test admission only.
    for change in ({"commission": "1.23 EUR"}, {"last_qty": "0.5"},
                   {"last_qty": "3"}, {"last_px": "110.021"},
                   {"ts_event": eq.ns(eq.OPEN) + 1}, {"client_order_id": "wrong"},
                   {"account_id": "OTHER-001"}, {"trader_id": "OTHER-001"},
                   {"strategy_id": "OTHER-001"}, {"venue_order_id": "OTHER-001"}):
        with pytest.raises(ValueError):
            eq.project([OrderFilled.from_dict(event | change)], intent, order_id, scope)



@pytest.mark.provider_qualification
@pytest.mark.native_nonlive
def test_rc9_equity_orderfilled_persists_in_real_postgres_paper_close(monkeypatch):
    # Physical integration only: no DSN means no persistence proof.
    # The test DSN MUST reference a disposable, dedicated ordivon_paper DB.
    dsn = os.environ.get("ORDIVON_CAPITAL_PAPER_PG_TEST_DSN")
    if not dsn:
        if os.environ.get("ORDIVON_FINANCE_REQUIRE_PHYSICAL_PG") == "1":
            pytest.fail("native CI requires a disposable PostgreSQL database, not SKIP")
        pytest.skip("independent disposable ordivon_paper PostgreSQL is required")

    from dataclasses import replace
    from hashlib import sha256
    from uuid import uuid4

    import psycopg
    from nautilus_trader.model import ClientOrderId, OrderFilled

    from ordivon_capital.accounting.paper_close import PaperBuy, PaperSession
    from ordivon_capital.accounting.postgres_ledger import PostgresAccountingLedger
    from ordivon_capital.accounting.postgres_paper_close import (
        PostgresPaperClose,
        read_committed_paper_close,
        read_latest_committed_paper_close,
    )
    from ordivon_capital.accounting.substrate import stable_accounting_id

    monkeypatch.syspath_prepend(str(ROOT / "tools/nautilus_rc4"))
    import equity_paper_qualification as eq

    native = eq.run_episode("1.23")
    assert native["synthetic"] is True
    assert native["providerVersion"] == "2.0.0rc9"
    assert len(native["fills"]) == len(native["events"]) == 1
    assert native["fills"][0]["fill_id"] == native["events"][0]["trade_id"]
    # Rebind the observed upstream event through the same identity-qualified
    # projection: no manual fill, copied bar open, or trusted JSON price.
    event = native["events"][0]
    native_fill = OrderFilled.from_dict(event)
    intent = eq.Intent(eq.InstrumentId.from_str(event["instrument_id"]))
    buys = eq.project(
        [native_fill], intent, ClientOrderId(event["client_order_id"]),
        native["expectedIdentity"],
    )
    assert len(buys) == 1
    buy = buys[0]
    assert buy == PaperBuy(**native["fills"][0])
    assert buy.price_minor == 11002 and buy.fee_minor == 123
    account = "native-etf-" + uuid4().hex
    opened = PaperSession(eq.PREVIOUS, None, 100000, 0, {}, ())
    trade = PaperSession(eq.SESSION, eq.PREVIOUS, 0, 0, {"SPY": 11200}, (buy,))
    holiday = PaperSession(eq.BANK_HOLIDAY, eq.SESSION, 0, 0, {"SPY": 11200}, ())
    settled = PaperSession(eq.SETTLEMENT, eq.BANK_HOLIDAY, 0, 0, {"SPY": 11200}, ())
    calendar_digest = sha256(eq.CALENDAR).hexdigest()
    calendar = {"calendar_bytes": eq.CALENDAR, "calendar_sha256": calendar_digest}

    def account_id(*parts):
        return stable_accounting_id(
            "ordivon-capital:paper-close:usd:v1", account, *parts,
        )

    def persisted_rows():
        # Only the dedicated disposable PG DB. Read-only snapshot proves
        # replay/readback does not silently create another financial row.
        with psycopg.connect(dsn) as db:
            db.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY")
            return tuple(
                db.execute(statement).fetchall()
                for statement in (
                    "SELECT * FROM ordivon_paper.daily_close ORDER BY account_key, session",
                    "SELECT * FROM ordivon_capital.accounts ORDER BY id",
                    "SELECT * FROM ordivon_capital.transfers ORDER BY id",
                )
            )

    store = PostgresPaperClose(dsn)
    initial = store.close_session(account, opened, **calendar)
    executed = store.close_session(account, trade, **calendar)
    assert executed["valuation"]["nav_minor"] == native["nativeNavMinor"] == 100273
    assert executed["valuation"]["payable_minor"] == 22127
    assert executed["valuation"]["cash_minor"] == 100000
    assert executed["market_evidence"]["standing"] == "CALLER_SUPPLIED_MARKS"
    assert executed["execution_evidence"]["calendar_sha256"] == calendar_digest
    assert executed["execution_evidence"]["clearing_days"]["2026-11-11"] is False
    assert executed["execution_evidence"]["settlement_date"] == "2026-11-12"
    assert executed["previous_request_sha256"] == initial["request_sha256"]
    assert executed["previous_receipt_sha256"]

    ledger = PostgresAccountingLedger(dsn)
    settlement_id = account_id("settle", buy.fill_id)
    assert ledger.transfer(settlement_id) is None
    # Read-only receipt verification and a fresh connection: no duplicate
    # credit/debit on an exact replay of the same upstream fill.
    assert read_committed_paper_close(dsn, account, eq.SESSION) == executed
    before_replay = persisted_rows()
    assert PostgresPaperClose(dsn).close_session(account, trade, **calendar) == executed
    assert persisted_rows() == before_replay
    on_holiday = store.close_session(account, holiday, **calendar)
    assert on_holiday["valuation"]["payable_minor"] == 22127
    assert on_holiday["valuation"]["cash_minor"] == 100000
    assert ledger.transfer(settlement_id) is None
    final = PostgresPaperClose(dsn).close_session(account, settled, **calendar)
    assert final["valuation"]["payable_minor"] == 0
    assert final["valuation"]["cash_minor"] == native["nativeCashMinor"] == 77873
    assert final["valuation"]["nav_minor"] == native["nativeNavMinor"]
    assert read_latest_committed_paper_close(dsn, account) == final
    assert read_committed_paper_close(dsn, account, eq.SESSION) == executed

    posted = ledger.transfer(settlement_id)
    assert posted is not None
    assert posted.operation == "POST" and posted.status == "POSTED"
    assert posted.amount == buy.cost_minor == 22127
    assert posted.pending_id == account_id("buy", buy.fill_id)
    cash = ledger.account(account_id("cash"))
    assert cash.credits_posted - cash.debits_posted == native["nativeCashMinor"]
    assert cash.debits_pending == 0

    before_replay = persisted_rows()
    assert PostgresPaperClose(dsn).close_session(account, settled, **calendar) == final
    assert persisted_rows() == before_replay
    # The PostgreSQL client is re-created, but this is not a server restart
    # claim; an independent physical-restart qualification is run separately.

    # Old committed economics must reject a changed mark or fee, not silently
    # overwrite the receipt/ledger head after later settlement.
    with pytest.raises(ValueError, match="conflicting inputs"):
        store.close_session(account, replace(trade, marks={"SPY": 11300}), **calendar)
    with pytest.raises(ValueError, match="conflicting inputs"):
        store.close_session(
            account, replace(trade, buys=(replace(buy, fee_minor=124),)), **calendar,
        )
    assert read_latest_committed_paper_close(dsn, account) == final
    assert persisted_rows() == before_replay



# Upstream Nautilus is an OPTIONAL native qualification dependency.
# Ordinary Capital tests must not silently require the nonlive extra.
@pytest.mark.provider_qualification
@pytest.mark.native_nonlive
def test_qlib_prediction_snapshot_cannot_claim_original_model_after_rewrite(tmp_path):
    # This is a source-to-consumer authority boundary, not a strategy test.
    study = tmp_path / "native_study_result.json"
    original = (
        b"datetime,instrument,predicted_next_open_to_next_open_fractional_return\n"
        b"2025-10-01,IWM,0.01\n"
        b"2025-10-01,QQQ,0.02\n"
        b"2025-10-01,SPY,0.03\n"
    )
    study.write_text(
        json.dumps({
            "signal_quality": {
                "holding_sessions": 5,
                "exit_price_kind": "next_open",
                "matches_native_fixed_holding_exit_event": True,
            },
            "portfolio_target": None,
            "forecast": {
                "point_in_time_eligible": False,
                "native_strategy_exit_event_matches_target": True,
            },
            "qlib_prediction_sha256": sha256(original).hexdigest(),
        }),
        encoding="utf-8",
    )
    tampered = original.replace(b"IWM,0.01", b"IWM,0.90")
    assert tampered != original
    (tmp_path / "qlib_test_predictions.csv").write_bytes(tampered)
    output = tmp_path / "native_output"
    proc = subprocess.run(
        [
            sys.executable,
            str(ROOT / "adoption/r3_native/tests/probe_native_buy_hold_exit.py"),
        ],
        cwd=ROOT,
        env=os.environ | {
            "PYTHONPATH": str(ROOT / "src"),
            "ORDIVON_FINANCE_R3_HOLD_SESSIONS": "5",
            "ORDIVON_FINANCE_R3_RESEARCH_OUT_DIR": str(tmp_path),
            "ORDIVON_FINANCE_R3_RUN_OUT_DIR": str(output),
        },
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode != 0
    assert "Qlib prediction snapshot does not match recorded study" in proc.stderr
    assert not (output / "native_holding_result.json").exists()
