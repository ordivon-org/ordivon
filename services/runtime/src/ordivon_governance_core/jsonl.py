"""JSONL utilities — safe read/write for governance ledgers."""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path
from typing import Optional


def read_jsonl(path: Path, strict: bool = True) -> list[dict]:
    """Read a JSONL file. Returns list of dicts. Skips empty lines."""
    entries = []
    if not path.exists():
        return entries
    with open(path) as f:
        for lineno, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError as e:
                if strict:
                    raise ValueError(f"Invalid JSONL at {path}:{lineno}: {e}")
    return entries


def write_jsonl(path: Path, entries: list[dict], atomic: bool = True):
    """Write entries to JSONL file. If atomic, write to temp then rename."""
    if atomic:
        tmp = Path(str(path) + ".tmp")
        _write(path=tmp, entries=entries)
        os.replace(tmp, path)
    else:
        _write(path=path, entries=entries)


def append_jsonl(path: Path, entry: dict, atomic: bool = True):
    """Append a single entry to JSONL file atomically."""
    if atomic:
        tmp = Path(str(path) + ".tmp")
        if path.exists():
            shutil.copy2(path, tmp)
        with open(tmp, "a") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        os.replace(tmp, path)
    else:
        with open(path, "a") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def append_jsonl_safe(
    path: Path, entry: dict, idempotency_key: str = "", dedup_by: str = "doc_id", atomic: bool = True
) -> dict:
    """Append with idempotency and dedup. Returns {'status': 'appended'|'duplicate'|'conflict'}.

    If idempotency_key is provided, checks for prior writes with same key + same hash.
    If dedup_by is set, checks for existing entry with same value in that field.
    """
    import hashlib

    input_hash = hashlib.sha256(json.dumps(entry, sort_keys=True).encode()).hexdigest()[:16]

    # Idempotency check via a sidecar file
    if idempotency_key:
        idem_path = Path(str(path) + ".idem")
        if idem_path.exists():
            for line in open(idem_path):
                if not line.strip():
                    continue
                try:
                    rec = json.loads(line)
                    if rec.get("key") == idempotency_key:
                        if rec.get("hash") == input_hash:
                            return {"status": "duplicate", "reason": "same key, same hash"}
                        else:
                            return {"status": "conflict", "reason": "same key, different hash"}
                except json.JSONDecodeError:
                    pass

    # Dedup check
    if dedup_by and path.exists():
        existing = read_jsonl(path)
        new_val = entry.get(dedup_by)
        if new_val:
            for ex in existing:
                if ex.get(dedup_by) == new_val:
                    return {"status": "duplicate", "reason": f"{dedup_by}='{new_val}' already exists"}

    # Append
    append_jsonl(path, entry, atomic=atomic)

    # Record idempotency
    if idempotency_key:
        idem_path = Path(str(path) + ".idem")
        with open(idem_path, "a") as f:
            f.write(json.dumps({"key": idempotency_key, "hash": input_hash, "ts": ""}) + "\n")

    return {"status": "appended"}


def _write(path: Path, entries: list[dict]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        for entry in entries:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def find_by_key(path: Path, key: str, value: str) -> Optional[dict]:
    """Find an entry in a JSONL file by key=value."""
    for entry in read_jsonl(path):
        if entry.get(key) == value:
            return entry
    return None


def count_entries(path: Path) -> int:
    """Count non-empty lines in JSONL file."""
    if not path.exists():
        return 0
    return sum(1 for line in open(path) if line.strip())


def validate_entry(entry: dict, required_fields: list[str]) -> list[str]:
    """Check that all required fields are present and non-empty."""
    errors = []
    for field in required_fields:
        if field not in entry or not entry[field]:
            errors.append(f"MISSING_REQUIRED_FIELD: {field}")
    return errors
