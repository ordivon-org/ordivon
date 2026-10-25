from __future__ import annotations

import json
import stat
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from cft_human_session import DurableSessionAuthority, SessionConflict, SessionHold  # noqa: E402

SESSION_ID = "019a9af0-7b00-7000-8000-000000000001"
BROWSER_DIGEST = "sha256:" + "8" * 64


class FakeSystemd:
    def __init__(self) -> None:
        self.active: set[str] = set()
        self.starts: list[str] = []
        self.stops: list[str] = []

    def start(self, unit: str) -> None:
        self.starts.append(unit)
        slot = unit.removeprefix("ordivon-cft-human-session@").removesuffix(".target")
        self.active.update({
            unit,
            f"ordivon-cft-human-display@{slot}.service",
            f"ordivon-cft-human-browser@{slot}.service",
            f"ordivon-cft-human-vnc@{slot}.service",
            f"ordivon-cft-human-web@{slot}.service",
        })

    def stop(self, unit: str) -> None:
        self.stops.append(unit)
        slot = unit.removeprefix("ordivon-cft-human-session@").removesuffix(".target")
        self.active.difference_update({
            unit,
            f"ordivon-cft-human-display@{slot}.service",
            f"ordivon-cft-human-browser@{slot}.service",
            f"ordivon-cft-human-vnc@{slot}.service",
            f"ordivon-cft-human-web@{slot}.service",
        })

    def is_active(self, unit: str) -> bool:
        return unit in self.active


def browser_identity() -> dict[str, str]:
    return {
        "equipmentId": "browser:playwright-chromium",
        "browserProduct": "Google Chrome for Testing 153.0.8010.12",
        "executableDigest": BROWSER_DIGEST,
    }


def http_probe(url: str) -> dict:
    if url.endswith("/json/version"):
        return {"status": 200, "json": {"Browser": "Chrome/153.0.8010.12"}}
    return {"status": 200, "json": None}


def authority(tmp_path: Path, systemd: FakeSystemd | None = None, *, slots=(41, 42)):
    sd = systemd or FakeSystemd()
    value = DurableSessionAuthority(
        root=tmp_path / "sessions",
        slots=slots,
        systemd=sd,
        browser_identity=browser_identity,
        http_probe=http_probe,
        uuid7_factory=lambda: SESSION_ID,
        now_ms=lambda: 1_800_000_000_000,
    )
    return value, sd


def test_open_returns_durable_loopback_coordinate_and_starts_exact_target(tmp_path: Path) -> None:
    a, sd = authority(tmp_path)
    value = a.open("auth:effect-1")
    assert value["standing"] == "READY"
    assert value["sessionId"] == SESSION_ID
    assert value["slot"] == 41
    assert value["cdpEndpoint"] == "http://127.0.0.1:19241"
    assert value["operatorURL"].startswith("http://127.0.0.1:19441/")
    assert value["sessionOwner"] == "systemd"
    assert value["browserProduct"] == "Google Chrome for Testing 153.0.8010.12"
    assert value["browserExecutableDigest"] == BROWSER_DIGEST
    assert value["providerEffectAttempted"] is False
    assert sd.starts == ["ordivon-cft-human-session@41.target"]
    serialized = json.dumps(value).lower()
    assert "cookie" not in serialized
    assert "storage_state" not in serialized


def test_open_is_idempotent_by_request_identity(tmp_path: Path) -> None:
    a, sd = authority(tmp_path)
    first = a.open("auth:effect-1")
    second = a.open("auth:effect-1")
    assert second == first
    assert sd.starts == ["ordivon-cft-human-session@41.target"]


def test_different_request_gets_next_free_slot(tmp_path: Path) -> None:
    ids = iter([SESSION_ID, "019a9af0-7b00-7000-8000-000000000002"])
    sd = FakeSystemd()
    a = DurableSessionAuthority(
        root=tmp_path / "sessions", slots=(41, 42), systemd=sd,
        browser_identity=browser_identity, http_probe=http_probe,
        uuid7_factory=lambda: next(ids), now_ms=lambda: 1_800_000_000_000,
    )
    assert a.open("r1")["slot"] == 41
    assert a.open("r2")["slot"] == 42


def test_slot_exhaustion_holds_without_reusing_active_slot(tmp_path: Path) -> None:
    a, _ = authority(tmp_path, slots=(41,))
    a.open("r1")
    with pytest.raises(SessionHold, match="no free durable human-session slot"):
        a.open("r2")


def test_observe_is_read_only_and_projects_stale_when_unit_is_down(tmp_path: Path) -> None:
    a, sd = authority(tmp_path)
    a.open("r1")
    before = a.db_path.read_bytes()
    sd.active.clear()
    value = a.observe(SESSION_ID)
    assert value["standing"] == "STALE"
    assert value["sessionActive"] is False
    assert a.db_path.read_bytes() == before


def test_resolve_requires_current_ready_session(tmp_path: Path) -> None:
    a, sd = authority(tmp_path)
    a.open("r1")
    assert a.resolve(SESSION_ID)["cdpEndpoint"] == "http://127.0.0.1:19241"
    sd.active.clear()
    with pytest.raises(SessionHold, match="not READY"):
        a.resolve(SESSION_ID)


def test_close_stops_exact_target_and_releases_slot(tmp_path: Path) -> None:
    ids = iter([SESSION_ID, "019a9af0-7b00-7000-8000-000000000002"])
    sd = FakeSystemd()
    a = DurableSessionAuthority(
        root=tmp_path / "sessions", slots=(41,), systemd=sd,
        browser_identity=browser_identity, http_probe=http_probe,
        uuid7_factory=lambda: next(ids), now_ms=lambda: 1_800_000_000_000,
    )
    a.open("r1")
    closed = a.close(SESSION_ID)
    assert closed["standing"] == "CLOSED"
    assert sd.stops == ["ordivon-cft-human-session@41.target"]
    second = a.open("r2")
    assert second["slot"] == 41


def test_close_replay_is_idempotent(tmp_path: Path) -> None:
    a, sd = authority(tmp_path)
    a.open("r1")
    first = a.close(SESSION_ID)
    second = a.close(SESSION_ID)
    assert second == first
    assert sd.stops == ["ordivon-cft-human-session@41.target"]


def test_unknown_session_fails_closed(tmp_path: Path) -> None:
    a, _ = authority(tmp_path)
    with pytest.raises(SessionConflict, match="not registered"):
        a.observe("019a9af0-7b00-7000-8000-000000000099")


def test_registry_database_is_private(tmp_path: Path) -> None:
    a, _ = authority(tmp_path)
    a.open("r1")
    assert stat.S_IMODE(a.db_path.stat().st_mode) == 0o600


def test_systemd_unit_templates_are_loopback_sandboxed_and_native_sandboxed() -> None:
    files = {p.name: p.read_text() for p in (ROOT / "systemd").glob("ordivon-cft-human-*")}
    assert {
        "ordivon-cft-human-session@.target",
        "ordivon-cft-human-display@.service",
        "ordivon-cft-human-browser@.service",
        "ordivon-cft-human-vnc@.service",
        "ordivon-cft-human-web@.service",
    } <= set(files)
    browser = files["ordivon-cft-human-browser@.service"]
    assert "User=ordivon" in browser
    assert "NoNewPrivileges=true" in browser
    assert "ProtectSystem=strict" in browser
    assert "ProtectHome=yes" in browser
    assert "--remote-debugging-address=127.0.0.1" in browser
    assert "--remote-debugging-port=192%i" in browser
    assert "--no-sandbox" not in browser
    assert "@CFT_EXECUTABLE@" in browser
    assert "127.0.0.1:193%i" in files["ordivon-cft-human-web@.service"]
    assert "127.0.0.1:194%i" in files["ordivon-cft-human-web@.service"]
    assert "-listen 127.0.0.1" in files["ordivon-cft-human-vnc@.service"]


@pytest.mark.parametrize("fault", ["erase", "forge"])
def test_session_open_never_starts_systemd_without_exact_durable_reservation(
    tmp_path: Path, fault: str
) -> None:
    """SQLite native AFTER INSERT corruption must be rolled back pre-effect."""
    import sqlite3

    a, sd = authority(tmp_path)
    with sqlite3.connect(a.db_path) as db:
        corruption = (
            "DELETE FROM sessions WHERE session_id=NEW.session_id;"
            if fault == "erase"
            else "UPDATE sessions SET slot=42 WHERE session_id=NEW.session_id;"
        )
        db.executescript(
            f"""
            CREATE TABLE corruption_witness (mark INTEGER);
            CREATE TRIGGER corrupt_session AFTER INSERT ON sessions BEGIN
                INSERT INTO corruption_witness VALUES (1);
                {corruption}
            END;
            """
        )
    with pytest.raises(SessionConflict, match="reservation.*receipt"):
        a.open("auth:effect-bounded")
    assert not sd.starts, "physical browser startup preceded durable reservation proof"
    assert not sd.stops
    with sqlite3.connect(a.db_path) as db:
        assert db.execute("SELECT COUNT(*) FROM sessions").fetchone()[0] == 0
        assert db.execute("SELECT COUNT(*) FROM corruption_witness").fetchone()[0] == 0


def test_session_activation_cannot_report_ready_after_durable_state_corruption(
    tmp_path: Path,
) -> None:
    """Rollback failed ACTIVE transition, compensate physical systemd start."""
    import sqlite3

    a, sd = authority(tmp_path)
    with sqlite3.connect(a.db_path) as db:
        db.executescript(
            """
            CREATE TABLE corrupt_activation_witness (marker INTEGER);
            CREATE TRIGGER corrupt_activation AFTER UPDATE OF lifecycle ON sessions
            WHEN NEW.lifecycle='ACTIVE'
            BEGIN
                INSERT INTO corrupt_activation_witness VALUES (1);
                UPDATE sessions SET lifecycle='FAILED' WHERE session_id=NEW.session_id;
            END;
            """
        )
    with pytest.raises(SessionConflict, match="activation.*receipt"):
        a.open("auth:activation-fault")
    assert sd.starts == ["ordivon-cft-human-session@41.target"]
    assert sd.stops == ["ordivon-cft-human-session@41.target"]
    with sqlite3.connect(a.db_path) as db:
        assert db.execute("SELECT lifecycle FROM sessions").fetchone()[0] == "FAILED"
        assert db.execute("SELECT COUNT(*) FROM corrupt_activation_witness").fetchone()[0] == 0


@pytest.mark.parametrize("fault", ["erase", "forge"])
def test_close_requires_exact_durable_closed_receipt_after_systemd_stop(
    tmp_path: Path, fault: str
) -> None:
    """SQLite post-UPDATE corruption cannot turn a stopped target into fake CLOSED."""
    import sqlite3

    owner, sd = authority(tmp_path)
    owner.open("r1")
    with sqlite3.connect(owner.db_path) as db:
        corrupt = (
            "DELETE FROM sessions WHERE session_id=NEW.session_id;"
            if fault == "erase"
            else "UPDATE sessions SET lifecycle='ACTIVE',closed_at_ms=NULL "
                 "WHERE session_id=NEW.session_id;"
        )
        db.executescript(
            f"""
            CREATE TABLE corrupted_close_witness (marker INTEGER);
            CREATE TRIGGER corrupt_close AFTER UPDATE OF lifecycle ON sessions
            WHEN NEW.lifecycle='CLOSED' BEGIN
                INSERT INTO corrupted_close_witness VALUES (1);
                {corrupt}
            END;
            """
        )
    with pytest.raises(SessionConflict, match="close.*receipt"):
        owner.close(SESSION_ID)
    assert sd.stops == ["ordivon-cft-human-session@41.target"]
    with sqlite3.connect(owner.db_path) as db:
        assert db.execute("SELECT COUNT(*) FROM corrupted_close_witness").fetchone()[0] == 0
        row = db.execute("SELECT lifecycle,closed_at_ms FROM sessions").fetchone()
        assert row == ("ACTIVE", None)
