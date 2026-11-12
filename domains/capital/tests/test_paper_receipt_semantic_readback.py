"""Accounting readback MUST refine stored input to exact pure paper valuation.

No PostgreSQL is needed: same result rows and query order as the actual
repeatable-read _read_committed_paper_receipt consumer. This does NOT verify
external market truth, database credentials, or historical PIT.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict
from datetime import date, datetime
from hashlib import sha256
from json import dumps, loads

import unittest

from ordivon_capital.accounting.paper_close import PaperBuy, PaperSell, PaperSession, value_session
from ordivon_capital.accounting.postgres_paper_close import _read_committed_paper_receipt


def _canonical_day(day: PaperSession) -> tuple[str, dict]:
    payload = asdict(day)
    if not day.sells:
        del payload["sells"]
    payload["market_evidence"] = {"standing": "CALLER_SUPPLIED_MARKS"}
    frozen = dumps(payload, default=lambda value: value.isoformat(),
                   sort_keys=True, separators=(",", ":"))
    return sha256(frozen.encode()).hexdigest(), loads(frozen)


def _receipt(day, previous, previous_digest, account):
    digest, request = _canonical_day(day)
    valuation = asdict(value_session(previous, day))
    valuation["session"] = day.session.isoformat()
    if not day.sells and not (previous and previous.pending_sales):
        for key in ("pending_sales", "sale_settlement_dates", "receivable_minor"):
            del valuation[key]
    return digest, request, {
        "schema_version": 1, "valuation": valuation,
        "mode": "PAPER", "request_sha256": digest,
        "previous_request_sha256": previous_digest,
        "account_key": account, "market_evidence": request["market_evidence"],
    }


class _Rows:
    def __init__(self, first, previous):
        self._first = first
        self._previous = previous
        self.queries = []
        self._current = None

    def execute(self, sql, parameters):
        self.queries.append((sql, parameters))
        if "session < %s" not in sql:
            self._current = self._first
        elif self._previous is None:
            self._current = None
        elif "SELECT session, request_sha256, receipt" in sql:
            self._current = self._previous
        else:
            # Exact old SQL projection before the fix, to prove RED on
            # economic content rather than an unrelated fake-DB shape.
            self._current = (self._previous[1],)
        return self

    def fetchone(self):
        return self._current


def _scenario():
    key = "readback-refine"
    d0 = PaperSession(date(2026, 1, 8), None, 1_000_000, 300_000, {}, ())
    d1 = PaperSession(
        date(2026, 1, 9), d0.session, 0, 0, {"ETF": 10_200},
        (PaperBuy(
            "fill-1", "ETF", 10, 10_000, 100,
            datetime.fromisoformat("2026-01-08T16:15:00-05:00"),
            datetime.fromisoformat("2026-01-09T09:30:00-05:00"),
        ),),
    )
    digest0, req0, rec0 = _receipt(d0, None, None, key)
    digest1, req1, rec1 = _receipt(d1, value_session(None, d0), digest0, key)
    return key, (d0.session, digest0, req0, rec0), (d1.session, digest1, req1, rec1)


def _read(current, previous, key):
    session, digest, request, receipt = current
    prior = None if previous is None else (
        previous[0], previous[1], previous[3]
    )
    rows = _Rows((digest, request, receipt), prior)
    result = _read_committed_paper_receipt(rows, key, session)
    assert len(rows.queries) == 2
    return result


class PaperReceiptReadbackSemanticTests(unittest.TestCase):
    def test_exact_open_and_trade_readback_refine_pure_value_session(self):
        key, first, second = _scenario()
        self.assertEqual(_read(first, None, key), first[3])
        self.assertEqual(_read(second, first, key), second[3])

    def test_request_bound_receipt_cannot_lie_about_economics(self):
        for field in (
            "coordinated_cash_and_nav",
            "protected_minor",
            "payable_minor",
            "positions",
            "pending",
        ):
            with self.subTest(field=field):
                key, first, second = _scenario()
                altered = deepcopy(second)
                row = altered[3]["valuation"]
                if field == "coordinated_cash_and_nav":
                    row["cash_minor"] += 100
                    row["nav_minor"] += 100
                elif field in ("protected_minor", "payable_minor"):
                    row[field] += 100
                elif field == "positions":
                    row["positions"] = {"ETF": 11}
                else:
                    row["pending"] = {"fill-1": 100_200}
                with self.assertRaisesRegex(
                    ValueError, "committed paper valuation.*stored request"
                ):
                    _read(altered, first, key)

    def test_first_session_without_predecessor_cannot_forge_cash(self):
        key, first, _ = _scenario()
        forged = deepcopy(first)
        forged[3]["valuation"]["cash_minor"] += 100
        forged[3]["valuation"]["nav_minor"] += 100
        with self.assertRaisesRegex(
            ValueError, "committed paper valuation.*stored request"
        ):
            _read(forged, None, key)

    def test_receipt_cannot_add_extra_unmodeled_valuation_property(self):
        key, first, second = _scenario()
        forged = deepcopy(second)
        forged[3]["valuation"]["fake_protected_account"] = "authorized"
        with self.assertRaisesRegex(
            ValueError, "committed paper valuation.*stored request"
        ):
            _read(forged, first, key)

    def test_disposable_real_postgres_detects_balanced_cash_nav_forgery(self):
        # Run only against an explicitly isolated/disposable ordivon_paper DB.
        import os
        from uuid import uuid4

        dsn = os.environ.get("ORDIVON_CAPITAL_PAPER_PG_TEST_DSN")
        if not dsn:
            self.skipTest("disposable PostgreSQL 18 paper DSN required")
        import psycopg

        from ordivon_capital.accounting.paper_close import decode_session
        from ordivon_capital.accounting.postgres_paper_close import (
            PostgresPaperClose,
            read_committed_paper_close,
            read_latest_committed_paper_close,
        )

        _, first, second = _scenario()
        account = "semantic-" + uuid4().hex
        restore = lambda record: decode_session({
            key: value for key, value in record[2].items()
            if key != "market_evidence"
        })
        store = PostgresPaperClose(dsn)
        store.close_session(account, restore(first))
        original = store.close_session(account, restore(second))
        self.assertEqual(read_latest_committed_paper_close(dsn, account), original)
        self.assertEqual(read_committed_paper_close(dsn, account, second[0]), original)
        # Intentionally modify the stored receipt only, leaving the
        # committed request SHA, predecessor identity and market claim intact.
        with psycopg.connect(dsn) as db:
            db.execute(
                """
                UPDATE ordivon_paper.daily_close
                SET receipt = jsonb_set(
                    jsonb_set(
                        receipt, '{valuation,cash_minor}',
                        to_jsonb((receipt->'valuation'->>'cash_minor')::bigint + 100)
                    ), '{valuation,nav_minor}',
                    to_jsonb((receipt->'valuation'->>'nav_minor')::bigint + 100)
                )
                WHERE account_key=%s AND session=%s
                """,
                (account, second[0]),
            )
        with self.assertRaisesRegex(
            ValueError, "committed paper valuation.*stored request"
        ):
            read_latest_committed_paper_close(dsn, account)
        with self.assertRaisesRegex(
            ValueError, "committed paper valuation.*stored request"
        ):
            read_committed_paper_close(dsn, account, second[0])


    def test_disposable_real_postgres_detects_ledger_cash_drift(self):
        # Exact PG Accounting owner, not a duplicate in-memory cash table.
        import os
        from uuid import uuid4

        dsn = os.environ.get("ORDIVON_CAPITAL_PAPER_PG_TEST_DSN")
        if not dsn:
            self.skipTest("disposable PostgreSQL 18 paper DSN required")
        import psycopg

        from ordivon_capital.accounting.paper_close import decode_session
        from ordivon_capital.accounting.postgres_paper_close import (
            PostgresPaperClose, read_committed_paper_close, read_latest_committed_paper_close,
        )
        from ordivon_capital.accounting.substrate import stable_accounting_id

        _, first, second = _scenario()
        account = "ledger-audit-" + uuid4().hex
        decode = lambda record: decode_session({
            key: value for key, value in record[2].items()
            if key != "market_evidence"
        })
        store = PostgresPaperClose(dsn)
        store.close_session(account, decode(first))
        legitimate = store.close_session(account, decode(second))
        self.assertEqual(read_latest_committed_paper_close(dsn, account), legitimate)
        cash_id = stable_accounting_id(
            "ordivon-capital:paper-close:usd:v1", account, "cash",
        )
        # Deliberately simulate a broken ledger storage row, while the
        # immutable request and receipt JSON continue to agree perfectly.
        # The test DB is provisioned and destroyed within one local run.
        with psycopg.connect(dsn) as db:
            updated = db.execute(
                """
                UPDATE ordivon_capital.accounts
                   SET credits_posted = credits_posted + 100
                 WHERE id = %s RETURNING id
                """, (str(cash_id),),
            ).fetchone()
            self.assertEqual(updated, (str(cash_id),))
        with self.assertRaisesRegex(
            ValueError, "committed paper ledger.*valuation"
        ):
            read_latest_committed_paper_close(dsn, account)
        with self.assertRaisesRegex(
            ValueError, "committed paper ledger.*valuation"
        ):
            read_committed_paper_close(dsn, account, second[0])




    def test_disposable_real_postgres_historical_read_after_cash_settlement(self):
        import os
        from uuid import uuid4

        dsn = os.environ.get("ORDIVON_CAPITAL_PAPER_PG_TEST_DSN")
        if not dsn:
            self.skipTest("disposable PostgreSQL 18 paper DSN required")

        from ordivon_capital.accounting.paper_close import decode_session
        from ordivon_capital.accounting.postgres_paper_close import (
            PostgresPaperClose, read_committed_paper_close, read_latest_committed_paper_close,
        )

        _, first, second = _scenario()
        account = "historic-" + uuid4().hex
        restored = lambda item: decode_session({
            name: data for name, data in item[2].items()
            if name != "market_evidence"
        })
        store = PostgresPaperClose(dsn)
        store.close_session(account, restored(first))
        old_receipt = store.close_session(account, restored(second))
        # This later session settles yesterday's buy payable. The live
        # account ledger has changed since the historic saved receipt.
        settle = PaperSession(
            date(2026, 1, 12), second[0], 0, 0, {"ETF": 10_200}, (),
        )
        settled_receipt = store.close_session(account, settle)
        self.assertEqual(
            read_committed_paper_close(dsn, account, second[0]), old_receipt,
        )
        self.assertEqual(
            read_latest_committed_paper_close(dsn, account), settled_receipt,
        )
        self.assertEqual(settled_receipt["valuation"]["payable_minor"], 0)
        self.assertEqual(settled_receipt["valuation"]["cash_minor"], 899_900)
        self.assertEqual(settled_receipt["valuation"]["nav_minor"], 1_001_900)


    def test_disposable_real_postgres_sale_receivable_and_clearing_readback(self):
        import os
        from uuid import uuid4

        dsn = os.environ.get("ORDIVON_CAPITAL_PAPER_PG_TEST_DSN")
        if not dsn:
            self.skipTest("disposable PostgreSQL 18 paper DSN required")
        from ordivon_capital.accounting.paper_close import decode_session
        from ordivon_capital.accounting.postgres_paper_close import (
            PostgresPaperClose, read_committed_paper_close, read_latest_committed_paper_close,
        )

        _, first, second = _scenario()
        key = "sale-audit-" + uuid4().hex
        store = PostgresPaperClose(dsn)
        for snapshot in (first, second):
            store.close_session(key, decode_session({
                name: item for name, item in snapshot[2].items()
                if name != "market_evidence"
            }))
        settle_buy = PaperSession(date(2026, 1, 12), second[0], 0, 0, {"ETF": 10_200}, ())
        store.close_session(key, settle_buy)
        sale = PaperSell(
            "sale-fill-1", "ETF", 10, 10_300, 100,
            datetime.fromisoformat("2026-01-12T16:15:00-05:00"),
            datetime.fromisoformat("2026-01-13T09:30:00-05:00"),
            settlement_date=date(2026, 1, 15),
        )
        sale_day = date(2026, 1, 13)
        sale_receipt = store.close_session(key, PaperSession(
            sale_day, settle_buy.session, 0, 0, {}, (), sells=(sale,),
        ))
        self.assertEqual(sale_receipt["valuation"]["receivable_minor"], 102_900)
        self.assertEqual(sale_receipt["valuation"]["pending_sales"], {"sale-fill-1": 102_900})
        store.close_session(key, PaperSession(date(2026, 1, 14), sale_day, 0, 0, {}, ()))
        settled = store.close_session(key, PaperSession(
            date(2026, 1, 15), date(2026, 1, 14), 0, 0, {}, (),
        ))
        self.assertEqual(read_committed_paper_close(dsn, key, sale_day), sale_receipt)
        self.assertEqual(read_latest_committed_paper_close(dsn, key), settled)
        self.assertEqual(settled["valuation"]["cash_minor"], 1_002_800)
        self.assertEqual(settled["valuation"]["receivable_minor"], 0)
        self.assertEqual(settled["valuation"]["nav_minor"], 1_002_800)


if __name__ == "__main__":
    unittest.main()