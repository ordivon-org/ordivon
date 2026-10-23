#!/usr/bin/env python3
"""Durable systemd-owned Chrome for Testing human-session authority.

Ordivon owns only slot/session identity and read-only currentness projection. systemd owns
process lifetime; Chrome for Testing owns browser/session state; Xvfb/x11vnc/noVNC own the
human surface. No cookie, storage-state, provider SEND, or workflow-wait semantics live here.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sqlite3
import subprocess
import time
import urllib.request
import uuid
from contextlib import closing
from pathlib import Path
from typing import Any, Callable, Protocol

EQUIPMENT_BINDING = Path("/root/tools/bin/equipment-binding")
SYSTEMD_RUN = Path("/usr/bin/systemd-run")
XVFB = Path("/usr/bin/Xvfb")
X11VNC = Path("/usr/bin/x11vnc")
NOVNC_ROOT = Path("/opt/ordivon/external/novnc/1.7.0")
WEBSOCKIFY_EQUIPMENT_ID = "browserless-websockify-0-13-0"
DIGEST_PREFIX = "sha256:"
STATE_ROOT = Path("/var/lib/ordivon/human-browser-session-authority")
SESSION_SLOTS = tuple(range(41, 49))
_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")


class SessionConflict(RuntimeError):
    pass


class SessionHold(RuntimeError):
    pass


class SystemdAuthority(Protocol):
    def start(self, unit: str) -> None: ...
    def stop(self, unit: str) -> None: ...
    def is_active(self, unit: str) -> bool: ...


class HostSystemd:
    def _run(self, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["/usr/bin/systemctl", *args],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=20,
            check=check,
        )

    def start(self, unit: str) -> None:
        self._run("start", unit)

    def stop(self, unit: str) -> None:
        self._run("stop", unit, check=False)

    def is_active(self, unit: str) -> bool:
        return self._run("is-active", "--quiet", unit, check=False).returncode == 0


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(block)
    return DIGEST_PREFIX + h.hexdigest()


def _binding(*args: str) -> dict[str, Any]:
    proc = subprocess.run(
        [str(EQUIPMENT_BINDING), *args],
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=15,
        check=False,
    )
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout).strip()[:500]
        raise RuntimeError(f"equipment binding failed: {detail or f'rc={proc.returncode}'}")
    try:
        value = json.loads(proc.stdout)
    except json.JSONDecodeError as error:
        raise RuntimeError("equipment binding returned non-JSON") from error
    if not isinstance(value, dict):
        raise RuntimeError("equipment binding returned non-object")
    return value


def _verify_executable_binding(
    value: dict[str, Any], *, equipment_id: str, execution_target: str = "local_linux"
) -> dict[str, Any]:
    if value.get("state") != "AVAILABLE":
        raise RuntimeError(f"{equipment_id} is not AVAILABLE")
    if value.get("equipmentId") != equipment_id:
        raise RuntimeError(f"{equipment_id} binding identity mismatch")
    if value.get("executionTarget") != execution_target:
        raise RuntimeError(f"{equipment_id} execution target mismatch")
    executable = Path(str(value.get("executable") or ""))
    expected = value.get("executableDigest")
    binding_digest = value.get("bindingDigest")
    if (
        not executable.is_absolute()
        or not executable.is_file()
        or not os.access(executable, os.X_OK)
        or not isinstance(expected, str)
        or _DIGEST_RE.fullmatch(expected) is None
        or not isinstance(binding_digest, str)
        or _DIGEST_RE.fullmatch(binding_digest) is None
    ):
        raise RuntimeError(f"{equipment_id} binding shape is invalid")
    actual = _sha256(executable)
    if actual != expected:
        raise RuntimeError(f"{equipment_id} executable digest mismatch")
    return {
        "equipmentId": equipment_id,
        "state": "AVAILABLE",
        "executionTarget": execution_target,
        "executable": str(executable),
        "executableDigest": expected,
        "bindingDigest": binding_digest,
        "provider": value.get("provider"),
        "providerIdentity": (
            value.get("providerIdentity") if isinstance(value.get("providerIdentity"), dict) else {}
        ),
    }


def browser_equipment_binding() -> dict[str, Any]:
    return _verify_executable_binding(
        _binding("browser", "--family", "chromium"),
        equipment_id="browser:playwright-chromium",
    )


def websockify_equipment_binding() -> dict[str, Any]:
    return _verify_executable_binding(
        _binding("managed", "--equipment-id", WEBSOCKIFY_EQUIPMENT_ID),
        equipment_id=WEBSOCKIFY_EQUIPMENT_ID,
    )


def browser_identity() -> dict[str, str]:
    value = browser_equipment_binding()
    executable = Path(value["executable"])
    proc = subprocess.run(
        [str(executable), "--version"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=10,
        check=False,
    )
    product = (proc.stdout or proc.stderr).strip()
    if proc.returncode != 0 or not product.startswith("Google Chrome for Testing "):
        raise RuntimeError("browser equipment is not verified Google Chrome for Testing")
    return {
        "equipmentId": value["equipmentId"],
        "browserProduct": product,
        "executableDigest": value["executableDigest"],
    }


def _default_http_probe(url: str) -> dict[str, Any]:
    request = urllib.request.Request(url, headers={"User-Agent": "ordivon-session-readiness/1"})
    with urllib.request.urlopen(request, timeout=1.5) as response:
        raw = response.read(1_048_576)
        content_type = response.headers.get_content_type()
        value = json.loads(raw) if content_type == "application/json" else None
        return {"status": int(response.status), "json": value}


def _uuid7() -> str:
    return str(uuid.uuid7())


def _validate_uuid7(value: str) -> str:
    try:
        parsed = uuid.UUID(value)
    except (ValueError, AttributeError) as error:
        raise ValueError("sessionId must be an RFC 9562 UUIDv7") from error
    if parsed.version != 7 or str(parsed) != value:
        raise ValueError("sessionId must be an RFC 9562 lowercase UUIDv7")
    return value


def _request_id(value: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or value != value.strip()
        or len(value.encode("utf-8")) > 4096
    ):
        raise ValueError("session request identity must be non-empty, trimmed, and <=4096 bytes")
    return value


def _target(slot: int) -> str:
    return f"ordivon-cft-human-session@{slot}.target"


def _units(slot: int) -> tuple[str, ...]:
    return (
        _target(slot),
        f"ordivon-cft-human-display@{slot}.service",
        f"ordivon-cft-human-browser@{slot}.service",
        f"ordivon-cft-human-vnc@{slot}.service",
        f"ordivon-cft-human-web@{slot}.service",
    )


def _cdp_endpoint(slot: int) -> str:
    return f"http://127.0.0.1:192{slot}"


def _operator_url(slot: int) -> str:
    return (
        f"http://127.0.0.1:194{slot}/vnc.html"
        f"?host=127.0.0.1&port=194{slot}&path=websockify&autoconnect=1&resize=scale"
    )


class DurableSessionAuthority:
    def __init__(
        self,
        *,
        root: Path = STATE_ROOT,
        slots: tuple[int, ...] = SESSION_SLOTS,
        systemd: SystemdAuthority | None = None,
        browser_identity: Callable[[], dict[str, str]] = browser_identity,
        http_probe: Callable[[str], dict[str, Any]] = _default_http_probe,
        uuid7_factory: Callable[[], str] = _uuid7,
        now_ms: Callable[[], int] = lambda: int(time.time() * 1000),
    ) -> None:
        self.root = Path(root)
        if self.root.exists() and (self.root.is_symlink() or not self.root.is_dir()):
            raise ValueError("human-session state root must be one real directory")
        self.root.mkdir(parents=True, exist_ok=True)
        os.chmod(self.root, 0o700)
        if not slots or len(set(slots)) != len(slots) or any(s not in SESSION_SLOTS for s in slots):
            raise ValueError("human-session slots must be a unique non-empty subset of 41..48")
        self.slots = tuple(sorted(slots))
        self.systemd = systemd or HostSystemd()
        self._browser_identity = browser_identity
        self._http_probe = http_probe
        self._uuid7_factory = uuid7_factory
        self._now_ms = now_ms
        self.db_path = self.root / "sessions.sqlite"
        self._initialize()

    def _connect(self, *, read_only: bool = False) -> sqlite3.Connection:
        if read_only:
            db = sqlite3.connect(f"file:{self.db_path}?mode=ro", uri=True, timeout=30)
        else:
            db = sqlite3.connect(self.db_path, timeout=30, isolation_level=None)
            db.execute("PRAGMA journal_mode=DELETE")
            db.execute("PRAGMA synchronous=FULL")
            db.execute("PRAGMA busy_timeout=30000")
        db.row_factory = sqlite3.Row
        return db

    def _initialize(self) -> None:
        with closing(self._connect()) as db:
            db.execute(
                """
                CREATE TABLE IF NOT EXISTS sessions(
                    session_id TEXT PRIMARY KEY,
                    request_id TEXT NOT NULL UNIQUE,
                    slot INTEGER NOT NULL,
                    lifecycle TEXT NOT NULL,
                    browser_equipment_id TEXT NOT NULL,
                    browser_product TEXT NOT NULL,
                    browser_executable_digest TEXT NOT NULL,
                    created_at_ms INTEGER NOT NULL,
                    closed_at_ms INTEGER
                )
                """
            )
            db.execute(
                """
                CREATE UNIQUE INDEX IF NOT EXISTS sessions_active_slot
                ON sessions(slot) WHERE lifecycle IN ('OPENING','ACTIVE')
                """
            )
        os.chmod(self.db_path, 0o600)

    @staticmethod
    def _base_receipt(row: sqlite3.Row) -> dict[str, Any]:
        slot = int(row["slot"])
        return {
            "schemaVersion": 1,
            "kind": "ordivon.cft-human-session",
            "sessionId": row["session_id"],
            "requestId": row["request_id"],
            "slot": slot,
            "sessionOwner": "systemd",
            "cdpAuthority": "loopback",
            "cdpEndpoint": _cdp_endpoint(slot),
            "operatorURL": _operator_url(slot),
            "browserEquipmentId": row["browser_equipment_id"],
            "browserProduct": row["browser_product"],
            "browserExecutableDigest": row["browser_executable_digest"],
            "createdAtMs": int(row["created_at_ms"]),
            "providerEffectAttempted": False,
            "sendAttempted": False,
        }

    def _row_by_session(self, session_id: str) -> sqlite3.Row:
        session_id = _validate_uuid7(session_id)
        with closing(self._connect(read_only=True)) as db:
            row = db.execute("SELECT * FROM sessions WHERE session_id=?", (session_id,)).fetchone()
        if row is None:
            raise SessionConflict("human session is not registered")
        return row

    def _row_by_request(self, request_id: str) -> sqlite3.Row | None:
        with closing(self._connect(read_only=True)) as db:
            return db.execute(
                "SELECT * FROM sessions WHERE request_id=?", (request_id,)
            ).fetchone()

    def _runtime_projection(self, row: sqlite3.Row) -> dict[str, Any]:
        base = self._base_receipt(row)
        lifecycle = str(row["lifecycle"])
        if lifecycle == "CLOSED":
            return {
                **base,
                "standing": "CLOSED",
                "sessionActive": False,
                "closedAtMs": int(row["closed_at_ms"]),
            }
        units_ready = all(self.systemd.is_active(unit) for unit in _units(int(row["slot"])))
        cdp_ready = False
        operator_ready = False
        if units_ready:
            try:
                cdp = self._http_probe(base["cdpEndpoint"] + "/json/version")
                cdp_ready = cdp.get("status") == 200 and isinstance(cdp.get("json"), dict)
            except Exception:
                cdp_ready = False
            try:
                operator = self._http_probe(base["operatorURL"].split("?", 1)[0])
                operator_ready = operator.get("status") == 200
            except Exception:
                operator_ready = False
        ready = units_ready and cdp_ready and operator_ready
        return {
            **base,
            "standing": "READY" if ready else "STALE",
            "sessionActive": ready,
            "unitsReady": units_ready,
            "cdpReady": cdp_ready,
            "operatorReady": operator_ready,
        }

    def open(self, request_id: str) -> dict[str, Any]:
        request_id = _request_id(request_id)
        existing = self._row_by_request(request_id)
        if existing is not None:
            return self._runtime_projection(existing)
        identity = self._browser_identity()
        if (
            set(identity) != {"equipmentId", "browserProduct", "executableDigest"}
            or identity["equipmentId"] != "browser:playwright-chromium"
            or not identity["browserProduct"].startswith("Google Chrome for Testing ")
            or _DIGEST_RE.fullmatch(identity["executableDigest"]) is None
        ):
            raise SessionConflict("Chrome for Testing equipment identity is invalid")
        session_id = _validate_uuid7(self._uuid7_factory())
        now = int(self._now_ms())
        with closing(self._connect()) as db:
            db.execute("BEGIN IMMEDIATE")
            existing = db.execute(
                "SELECT * FROM sessions WHERE request_id=?", (request_id,)
            ).fetchone()
            if existing is not None:
                db.execute("COMMIT")
                return self._runtime_projection(existing)
            busy = {
                int(row[0])
                for row in db.execute(
                    "SELECT slot FROM sessions WHERE lifecycle IN ('OPENING','ACTIVE')"
                )
            }
            slot = next((candidate for candidate in self.slots if candidate not in busy), None)
            if slot is None:
                db.execute("ROLLBACK")
                raise SessionHold("no free durable human-session slot")
            db.execute(
                """
                INSERT INTO sessions(
                    session_id,request_id,slot,lifecycle,browser_equipment_id,
                    browser_product,browser_executable_digest,created_at_ms,closed_at_ms
                ) VALUES(?,?,?,?,?,?,?,?,NULL)
                """,
                (
                    session_id,
                    request_id,
                    slot,
                    "OPENING",
                    identity["equipmentId"],
                    identity["browserProduct"],
                    identity["executableDigest"],
                    now,
                ),
            )
            db.execute("COMMIT")
        os.chmod(self.db_path, 0o600)
        try:
            self.systemd.start(_target(slot))
            row = self._row_by_session(session_id)
            observed = self._runtime_projection(row)
            if observed["standing"] != "READY":
                raise SessionHold("durable human session did not become READY")
            with closing(self._connect()) as db:
                db.execute("BEGIN IMMEDIATE")
                db.execute(
                    "UPDATE sessions SET lifecycle='ACTIVE' WHERE session_id=? AND lifecycle='OPENING'",
                    (session_id,),
                )
                db.execute("COMMIT")
            return self._runtime_projection(self._row_by_session(session_id))
        except Exception:
            self.systemd.stop(_target(slot))
            with closing(self._connect()) as db:
                db.execute("BEGIN IMMEDIATE")
                db.execute(
                    "UPDATE sessions SET lifecycle='FAILED' WHERE session_id=? AND lifecycle='OPENING'",
                    (session_id,),
                )
                db.execute("COMMIT")
            raise

    def observe(self, session_id: str) -> dict[str, Any]:
        return self._runtime_projection(self._row_by_session(session_id))

    def resolve(self, session_id: str) -> dict[str, Any]:
        value = self.observe(session_id)
        if value["standing"] != "READY":
            raise SessionHold(f"human session is not READY: {value['standing']}")
        return value

    def close(self, session_id: str) -> dict[str, Any]:
        row = self._row_by_session(session_id)
        if row["lifecycle"] == "CLOSED":
            return self._runtime_projection(row)
        slot = int(row["slot"])
        self.systemd.stop(_target(slot))
        now = int(self._now_ms())
        with closing(self._connect()) as db:
            db.execute("BEGIN IMMEDIATE")
            current = db.execute(
                "SELECT lifecycle FROM sessions WHERE session_id=?", (session_id,)
            ).fetchone()
            if current is None:
                db.execute("ROLLBACK")
                raise SessionConflict("human session disappeared during close")
            if current[0] != "CLOSED":
                db.execute(
                    "UPDATE sessions SET lifecycle='CLOSED',closed_at_ms=? WHERE session_id=?",
                    (now, session_id),
                )
            db.execute("COMMIT")
        return self._runtime_projection(self._row_by_session(session_id))


def resolve_session(session_id: str) -> dict[str, Any]:
    return DurableSessionAuthority().resolve(session_id)


def doctor() -> dict[str, Any]:
    failures: list[str] = []
    browser: dict[str, Any] | None = None
    browser_product: str | None = None
    websockify: dict[str, Any] | None = None
    try:
        browser = _verify_executable_binding(
            _binding("browser", "--family", "chromium"),
            equipment_id="browser:playwright-chromium",
        )
        browser_product = browser_identity()["browserProduct"]
    except Exception as error:
        failures.append(f"browser-equipment:{type(error).__name__}:{error}")
    try:
        websockify = websockify_equipment_binding()
    except Exception as error:
        failures.append(f"websockify-equipment:{type(error).__name__}:{error}")
    local = {
        "systemdRun": SYSTEMD_RUN.is_file() and os.access(SYSTEMD_RUN, os.X_OK),
        "xvfb": XVFB.is_file() and os.access(XVFB, os.X_OK),
        "x11vnc": X11VNC.is_file() and os.access(X11VNC, os.X_OK),
        "noVnc": NOVNC_ROOT.is_dir() and (NOVNC_ROOT / "vnc.html").is_file(),
    }
    failures.extend(f"missing:{name}" for name, ready in local.items() if not ready)
    healthy = browser is not None and browser_product is not None and websockify is not None and all(local.values())
    return {
        "schemaVersion": 1,
        "kind": "ordivon.cft-human-session-doctor",
        "healthy": healthy,
        "standing": "READY" if healthy else "DEPENDENCY_UNAVAILABLE",
        "sessionOwner": "systemd",
        "cdpAuthority": "loopback",
        "humanSurface": "xvfb-x11vnc-novnc",
        "browserEquipment": browser,
        "browserProduct": browser_product,
        "websockifyEquipment": websockify,
        "localDependencies": local,
        "failures": failures,
        "sideEffectsAttempted": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("doctor", "open", "observe", "resolve", "close"))
    parser.add_argument("--request-id")
    parser.add_argument("--session-id")
    args = parser.parse_args()
    try:
        if args.action == "doctor":
            value = doctor()
            rc = 0 if value["healthy"] else 2
        else:
            authority = DurableSessionAuthority()
            if args.action == "open":
                if args.request_id is None:
                    raise ValueError("--request-id is required for open")
                value = authority.open(args.request_id)
            else:
                if args.session_id is None:
                    raise ValueError("--session-id is required")
                if args.action == "observe":
                    value = authority.observe(args.session_id)
                elif args.action == "resolve":
                    value = authority.resolve(args.session_id)
                else:
                    value = authority.close(args.session_id)
            rc = 0
        print(json.dumps(value, sort_keys=True))
        return rc
    except (ValueError, SessionConflict, SessionHold, OSError, sqlite3.Error) as error:
        print(json.dumps({"schemaVersion": 1, "standing": "HOLD", "detail": str(error)}), file=__import__("sys").stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
