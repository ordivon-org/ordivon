#!/usr/bin/env python3
"""Freeze-proof and archive receipt generator for the retired Ordivon Host v1 authority.

This script deliberately does not mutate Host semantic state.  `preflight` proves the
legacy service has no active execution lease or live TCP consumer.  `finalize` is only
allowed after the Host service is stopped; it creates a SQLite backup plus a complete
content manifest of the durable Host state without duplicating the ~2.2 GiB object tree.
"""
from __future__ import annotations

import argparse
import datetime as dt
import gzip
import hashlib
import json
import os
import sqlite3
import subprocess
import sys
import time
from collections.abc import Iterable
from pathlib import Path

STATE_ROOT = Path("/var/lib/ordivon/host")
DB_PATH = STATE_ROOT / "host.sqlite3"
ARCHIVE_ROOT = Path("/var/lib/ordivon/retired/host-v1")
SERVICE = "ordivon-host-mcp.service"
PORT = 8898
MIN_READY_AGE_HOURS = 6.0
TRANSIENT_SUFFIXES = ("-wal", "-shm")
TRANSIENT_NAMES = {".maintenance.lock"}


def sh(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def service_active() -> bool:
    return sh("/usr/bin/systemctl", "is-active", "--quiet", SERVICE).returncode == 0


def established_consumers() -> list[str]:
    p = sh("/usr/bin/ss", "-Htnp", "state", "established")
    if p.returncode not in (0, 1):
        raise RuntimeError(f"ss failed: {p.stderr.strip()}")
    needle = f":{PORT}"
    return [line for line in p.stdout.splitlines() if needle in line]


def listener_present() -> bool:
    p = sh("/usr/bin/ss", "-Hltn")
    if p.returncode != 0:
        raise RuntimeError(f"ss failed: {p.stderr.strip()}")
    return any(f":{PORT}" in line for line in p.stdout.splitlines())


def db_connect(path: Path = DB_PATH) -> sqlite3.Connection:
    c = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    c.row_factory = sqlite3.Row
    return c


def db_snapshot() -> dict:
    now_ms = int(time.time() * 1000)
    with db_connect() as c:
        states = {row[0]: row[1] for row in c.execute(
            "select state,count(*) from task_projection group by state order by state"
        )}
        leases = c.execute("select count(*) from leases").fetchone()[0]
        ready = list(c.execute(
            "select task_id,goal_id,state,active_node_id,ready_frontier_json,revision,updated_at_ms "
            "from task_projection where state='ready' order by updated_at_ms desc"
        ))
        latest = c.execute(
            "select sequence,event_id,stream_id,event_kind,recorded_at_ms "
            "from events order by sequence desc limit 1"
        ).fetchone()
        counts = {}
        for table in (
            "events", "task_projection", "board_messages", "news_editions",
            "news_publications", "streams", "task_extension_state",
        ):
            counts[table] = c.execute(f"select count(*) from {table}").fetchone()[0]

    ages = [(now_ms - row["updated_at_ms"]) / 3_600_000 for row in ready]
    ready_youngest_age = min(ages) if ages else None
    ready_oldest_age = max(ages) if ages else None
    return {
        "capturedAtMs": now_ms,
        "capturedAt": dt.datetime.fromtimestamp(now_ms / 1000, dt.UTC).isoformat(),
        "stateCounts": states,
        "leases": leases,
        "readyCount": len(ready),
        "readyYoungestAgeHours": ready_youngest_age,
        "readyOldestAgeHours": ready_oldest_age,
        "latestEvent": dict(latest) if latest else None,
        "tableCounts": counts,
        "readyRows": [dict(row) for row in ready],
    }


def preflight_payload() -> dict:
    snap = db_snapshot()
    consumers = established_consumers()
    youngest = snap["readyYoungestAgeHours"]
    ready_old_enough = youngest is None or youngest >= MIN_READY_AGE_HOURS
    safe = snap["leases"] == 0 and not consumers and ready_old_enough
    return {
        "schemaVersion": 1,
        "kind": "ordivon.host-v1.retirement-preflight",
        "standing": "PASS" if safe else "HOLD",
        "serviceActive": service_active(),
        "listenerPresent": listener_present(),
        "establishedConsumers": consumers,
        "minimumReadyAgeHours": MIN_READY_AGE_HOURS,
        **{k: v for k, v in snap.items() if k != "readyRows"},
    }


def sha256_file(path: Path, chunk: int = 4 * 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            b = f.read(chunk)
            if not b:
                break
            h.update(b)
    return "sha256:" + h.hexdigest()


def durable_files() -> Iterable[Path]:
    for root, dirs, files in os.walk(STATE_ROOT):
        dirs.sort()
        files.sort()
        for name in files:
            p = Path(root) / name
            if name in TRANSIENT_NAMES or name.endswith(TRANSIENT_SUFFIXES):
                continue
            if p.is_symlink() or not p.is_file():
                continue
            yield p


def sqlite_backup(destination: Path) -> dict:
    destination.parent.mkdir(parents=True, exist_ok=True)
    tmp = destination.with_suffix(destination.suffix + ".tmp")
    if tmp.exists():
        tmp.unlink()
    src = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    dst = sqlite3.connect(tmp)
    try:
        src.backup(dst)
        integrity = dst.execute("pragma integrity_check").fetchone()[0]
        if integrity != "ok":
            raise RuntimeError(f"backup integrity_check={integrity!r}")
    finally:
        dst.close()
        src.close()
    os.chmod(tmp, 0o400)
    os.replace(tmp, destination)
    return {
        "path": str(destination),
        "bytes": destination.stat().st_size,
        "sha256": sha256_file(destination),
        "integrity": "ok",
        "readOnly": True,
    }


def write_tree_manifest(destination: Path) -> dict:
    destination.parent.mkdir(parents=True, exist_ok=True)
    root_hash = hashlib.sha256()
    count = 0
    total = 0
    tmp = destination.with_suffix(destination.suffix + ".tmp")
    with gzip.open(tmp, "wt", encoding="utf-8", compresslevel=6) as out:
        for path in durable_files():
            rel = path.relative_to(STATE_ROOT).as_posix()
            size = path.stat().st_size
            digest = sha256_file(path)
            rec = {"path": rel, "bytes": size, "sha256": digest}
            line = json.dumps(rec, sort_keys=True, separators=(",", ":"))
            out.write(line + "\n")
            root_hash.update(line.encode("utf-8") + b"\n")
            count += 1
            total += size
    os.chmod(tmp, 0o400)
    os.replace(tmp, destination)
    return {
        "path": str(destination),
        "files": count,
        "bytes": total,
        "manifestSha256": sha256_file(destination),
        "contentRootSha256": "sha256:" + root_hash.hexdigest(),
        "excludedTransient": ["*-wal", "*-shm", ".maintenance.lock"],
        "readOnly": True,
    }


def write_ready_rows(rows: list[dict], destination: Path) -> dict:
    tmp = destination.with_suffix(destination.suffix + ".tmp")
    with gzip.open(tmp, "wt", encoding="utf-8", compresslevel=6) as out:
        for row in rows:
            out.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")
    os.chmod(tmp, 0o400)
    os.replace(tmp, destination)
    return {
        "path": str(destination),
        "rows": len(rows),
        "sha256": sha256_file(destination),
        "readOnly": True,
    }


def finalize() -> dict:
    if service_active() or listener_present():
        raise RuntimeError("Host service/listener must be stopped before finalization")
    consumers = established_consumers()
    if consumers:
        raise RuntimeError(f"Host still has established consumers: {consumers}")

    snap = db_snapshot()
    if snap["leases"] != 0:
        raise RuntimeError(f"Host still has {snap['leases']} active leases")

    ARCHIVE_ROOT.mkdir(parents=True, exist_ok=True)
    os.chmod(ARCHIVE_ROOT, 0o700)
    source_digest = sha256_file(DB_PATH)
    token = source_digest.split(":", 1)[1][:16]
    backup = sqlite_backup(ARCHIVE_ROOT / f"host-v1-{token}.sqlite3")
    manifest = write_tree_manifest(ARCHIVE_ROOT / f"host-v1-tree-{token}.jsonl.gz")
    ready_rows = write_ready_rows(snap.pop("readyRows"), ARCHIVE_ROOT / f"host-v1-ready-{token}.jsonl.gz")

    receipt = {
        "schemaVersion": 1,
        "kind": "ordivon.host-v1.retirement",
        "standing": "RETIRED_READ_ONLY_ARCHIVE",
        "retiredAt": dt.datetime.now(dt.UTC).isoformat(),
        "service": SERVICE,
        "legacyAddress": "127.0.0.1:8898",
        "serviceActive": False,
        "listenerPresent": False,
        "establishedConsumers": [],
        "migrationDisposition": {
            "readyProjectionMeaning": "archived_resumable_continuations_not_running_executions",
            "temporalBootstrapCount": 0,
            "reason": "no leases, no live consumers, and no ready projection updated within the minimum retirement activity window",
        },
        "sourceDatabase": {
            "path": str(DB_PATH),
            "bytes": DB_PATH.stat().st_size,
            "sha256": source_digest,
        },
        "sqliteBackup": backup,
        "durableTree": manifest,
        "readyProjectionArchive": ready_rows,
        **snap,
    }
    receipt_path = ARCHIVE_ROOT / f"host-v1-retirement-{token}.json"
    tmp = receipt_path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.chmod(tmp, 0o400)
    os.replace(tmp, receipt_path)
    receipt["receiptPath"] = str(receipt_path)
    receipt["receiptSha256"] = sha256_file(receipt_path)
    return receipt


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=("preflight", "finalize"))
    args = ap.parse_args()
    try:
        payload = preflight_payload() if args.command == "preflight" else finalize()
        print(json.dumps(payload, indent=2, sort_keys=True))
        if args.command == "preflight" and payload["standing"] != "PASS":
            return 2
        return 0
    except Exception as exc:
        print(json.dumps({"standing": "FAIL", "error": str(exc)}, sort_keys=True), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
