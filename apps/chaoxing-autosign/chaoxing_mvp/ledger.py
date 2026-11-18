from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

from .models import Activity, ActivityIdentity, ActivityState


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True, slots=True)
class LedgerRecord:
    key: str
    state: ActivityState
    attempt_count: int
    first_seen_at: str
    last_seen_at: str
    last_detail: str | None
    confirmed_at: str | None


class ActivityLedger:
    def __init__(self, path: str | Path):
        self.path = str(path)
        self._init_schema()

    @contextmanager
    def _db(self) -> Iterator[sqlite3.Connection]:
        db = sqlite3.connect(self.path)
        db.row_factory = sqlite3.Row
        try:
            yield db
            db.commit()
        finally:
            db.close()

    def _init_schema(self) -> None:
        with self._db() as db:
            db.execute(
                """
                CREATE TABLE IF NOT EXISTS activity_ledger (
                    activity_key TEXT PRIMARY KEY,
                    account_id TEXT NOT NULL,
                    course_id TEXT NOT NULL,
                    class_id TEXT NOT NULL,
                    activity_id TEXT NOT NULL,
                    acquisition_surface TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    state TEXT NOT NULL,
                    attempt_count INTEGER NOT NULL DEFAULT 0,
                    first_seen_at TEXT NOT NULL,
                    last_seen_at TEXT NOT NULL,
                    last_detail TEXT,
                    confirmed_at TEXT
                )
                """
            )

    def observe(self, activity: Activity) -> LedgerRecord:
        now = utc_now()
        ident = activity.identity
        with self._db() as db:
            db.execute(
                """
                INSERT INTO activity_ledger (
                    activity_key, account_id, course_id, class_id, activity_id,
                    acquisition_surface, kind, state, first_seen_at, last_seen_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(activity_key) DO UPDATE SET
                    last_seen_at=excluded.last_seen_at,
                    acquisition_surface=excluded.acquisition_surface,
                    kind=excluded.kind
                """,
                (
                    ident.key,
                    ident.account_id,
                    ident.course_id,
                    ident.class_id,
                    ident.activity_id,
                    ident.acquisition_surface,
                    activity.kind.value,
                    ActivityState.DISCOVERED.value,
                    now,
                    now,
                ),
            )
        return self.get(ident)

    def get(self, identity: ActivityIdentity) -> LedgerRecord:
        with self._db() as db:
            row = db.execute(
                "SELECT * FROM activity_ledger WHERE activity_key=?", (identity.key,)
            ).fetchone()
        if row is None:
            raise KeyError(identity.key)
        return LedgerRecord(
            key=row["activity_key"],
            state=ActivityState(row["state"]),
            attempt_count=row["attempt_count"],
            first_seen_at=row["first_seen_at"],
            last_seen_at=row["last_seen_at"],
            last_detail=row["last_detail"],
            confirmed_at=row["confirmed_at"],
        )

    def transition(
        self,
        identity: ActivityIdentity,
        state: ActivityState,
        *,
        detail: str | None = None,
        increment_attempt: bool = False,
    ) -> LedgerRecord:
        now = utc_now()
        with self._db() as db:
            cur = db.execute(
                """
                UPDATE activity_ledger
                SET state=?, last_seen_at=?, last_detail=?,
                    attempt_count=attempt_count + ?,
                    confirmed_at=CASE WHEN ?=? THEN ? ELSE confirmed_at END
                WHERE activity_key=?
                """,
                (
                    state.value,
                    now,
                    detail,
                    1 if increment_attempt else 0,
                    state.value,
                    ActivityState.CONFIRMED_SUCCESS.value,
                    now,
                    identity.key,
                ),
            )
            if cur.rowcount != 1:
                raise KeyError(identity.key)
        return self.get(identity)

    def recovery_required(self, identity: ActivityIdentity) -> bool:
        try:
            record = self.get(identity)
        except KeyError:
            return False
        return record.state in {
            ActivityState.SUBMITTING,
            ActivityState.SUBMITTED,
            ActivityState.VERIFYING,
            ActivityState.UNKNOWN,
        }

    def should_process(self, identity: ActivityIdentity) -> bool:
        try:
            record = self.get(identity)
        except KeyError:
            return True
        return record.state not in {
            ActivityState.CONFIRMED_SUCCESS,
            ActivityState.FAILED_TERMINAL,
            ActivityState.USER_ACTION_REQUIRED,
        }
