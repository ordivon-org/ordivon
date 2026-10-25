"""A sqlite3.Connection transaction context does not close that connection."""
from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import pytest

import agent_automation_browserless as browserless


@pytest.mark.parametrize("has_table", [False, True])
def test_turn_effect_read_releases_native_sqlite_connection(
    tmp_path: Path, has_table: bool
) -> None:
    path = tmp_path / "turns.db"
    with closing(sqlite3.connect(path)) as db:
        if has_table:
            db.execute(
                "CREATE TABLE turn_effects("
                "turn_request_id TEXT PRIMARY KEY,"
                "prompt_digest TEXT, target_coordinate TEXT, state TEXT,"
                "receipt_json TEXT, updated_at_ms INTEGER)"
            )
            db.execute(
                "INSERT INTO turn_effects VALUES(?,?,?,?,?,?)",
                ("turn-1", "sha256:" + "a" * 64, "coordinate:1", "prepared", None, 7),
            )
            db.commit()

    real_connect = sqlite3.connect
    seen: list[sqlite3.Connection] = []

    class ObservedConnection(sqlite3.Connection):
        closed_count = 0

        def close(self) -> None:
            self.closed_count += 1
            return super().close()

    def observed_connect(*args, **kwargs):
        connection = real_connect(*args, factory=ObservedConnection, **kwargs)
        seen.append(connection)
        return connection

    service = object.__new__(browserless.BrowserlessAutomationService)
    service.config = SimpleNamespace(turn_ledger=path)
    try:
        with mock.patch.object(browserless.sqlite3, "connect", side_effect=observed_connect):
            result = service._turn_effect_row("turn-1")
        assert (result is not None) is has_table
        assert len(seen) == 1
        assert all(conn.closed_count == 1 for conn in seen), (
            "transaction context manager committed but leaked native connection"
        )
    finally:
        for conn in seen:
            if conn.closed_count == 0:
                conn.close()
