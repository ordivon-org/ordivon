#!/usr/bin/env python3
"""Registry Transaction Layer — staged, idempotent writes to the document registry.

Usage:
    python3 scripts/governance/registry_txn.py stage <entry.json>
    python3 scripts/governance/registry_txn.py validate <submission_id>
    python3 scripts/governance/registry_txn.py commit <submission_id>
    python3 scripts/governance/registry_txn.py rollback <submission_id>
    python3 scripts/governance/registry_txn.py status <submission_id>

Semantics:
    - Each submission gets a submission_id and idempotency_key.
    - Same key + same input → returns same result (no duplicate registry entries).
    - Same key + different input → conflict.
    - Validation failure → no commit.
    - Commit writes to registry atomically and generates a receipt.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = ROOT / "docs/governance/document-registry.jsonl"
TXN_DIR = ROOT / "docs/governance/registry_txn"

STAGED = TXN_DIR / "staged"
COMMITTED = TXN_DIR / "committed"
REJECTED = TXN_DIR / "rejected"
RECEIPTS = TXN_DIR / "receipts"


def ensure_dirs():
    for d in [STAGED, COMMITTED, REJECTED, RECEIPTS]:
        d.mkdir(parents=True, exist_ok=True)


def hash_input(data: dict) -> str:
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()[:16]


def load_registry() -> dict[str, dict]:
    registry = {}
    if REGISTRY_PATH.exists():
        with open(REGISTRY_PATH) as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    entry = json.loads(line)
                    registry[entry.get("path", "")] = entry
                    registry[entry.get("doc_id", "")] = entry
                except json.JSONDecodeError:
                    continue
    return registry


def find_existing_submission(submission_id: str) -> dict | None:
    """Check if a submission already exists in any stage."""
    for d in [STAGED, COMMITTED, REJECTED]:
        path = d / f"{submission_id}.json"
        if path.exists():
            return json.loads(path.read_text())
    return None


def find_by_idempotency_key(key: str) -> dict | None:
    """Find existing submission with the same idempotency key."""
    for d in [STAGED, COMMITTED, REJECTED]:
        for f in d.glob("*.json"):
            data = json.loads(f.read_text())
            if data.get("idempotency_key") == key:
                return data
    return None


def cmd_stage(args: list[str]):
    """Stage a new registry entry for validation."""
    if not args:
        print("Usage: registry_txn.py stage <entry.json>", file=sys.stderr)
        sys.exit(1)

    entry_path = Path(args[0])
    if not entry_path.exists():
        print(f"ERROR: entry file not found: {entry_path}", file=sys.stderr)
        sys.exit(1)

    entry = json.loads(entry_path.read_text())
    submission_id = str(uuid.uuid4())[:12]
    idempotency_key = entry.get("idempotency_key", submission_id)
    input_hash = hash_input(entry)

    # Idempotency check
    existing = find_by_idempotency_key(idempotency_key)
    if existing:
        existing_hash = existing.get("input_hash", "")
        existing_status = existing.get("status", "")
        if existing_hash == input_hash:
            print(
                json.dumps({
                    "status": "DUPLICATE",
                    "message": f"Same idempotency_key, same input. Prior submission: {existing['submission_id']} ({existing_status})",
                    "submission_id": existing["submission_id"],
                })
            )
            sys.exit(0)
        else:
            print(
                json.dumps({
                    "status": "CONFLICT",
                    "message": f"Same idempotency_key, different input. Prior: {existing_hash}, Current: {input_hash}",
                    "prior_submission_id": existing["submission_id"],
                })
            )
            sys.exit(1)

    # Duplicate doc_id or path check
    registry = load_registry()
    doc_id = entry.get("doc_id", "")
    path = entry.get("path", "")
    conflicts = []
    if doc_id and doc_id in registry:
        conflicts.append(f"doc_id '{doc_id}' already registered at '{registry[doc_id].get('path', '?')}'")
    if path and path in registry:
        conflicts.append(f"path '{path}' already registered as '{registry[path].get('doc_id', '?')}'")
    if conflicts:
        print(json.dumps({"status": "CONFLICT", "message": "; ".join(conflicts)}))
        sys.exit(1)

    staged = {
        "submission_id": submission_id,
        "idempotency_key": idempotency_key,
        "input_hash": input_hash,
        "entry": entry,
        "status": "staged",
        "staged_at": datetime.now(timezone.utc).isoformat(),
    }
    ensure_dirs()
    (STAGED / f"{submission_id}.json").write_text(json.dumps(staged, indent=2))
    print(json.dumps({"status": "STAGED", "submission_id": submission_id, "idempotency_key": idempotency_key}))


def cmd_validate(args: list[str]):
    """Validate a staged submission."""
    if not args:
        print("Usage: registry_txn.py validate <submission_id>", file=sys.stderr)
        sys.exit(1)

    submission_id = args[0]
    staged_path = STAGED / f"{submission_id}.json"
    if not staged_path.exists():
        print(json.dumps({"status": "NOT_FOUND", "message": f"Submission {submission_id} not staged"}))
        sys.exit(1)

    staged = json.loads(staged_path.read_text())
    entry = staged["entry"]

    # Basic validation
    errors = []
    for field in ["doc_id", "path", "title", "doc_type", "status", "authority"]:
        if field not in entry or not entry[field]:
            errors.append(f"MISSING: {field}")

    if errors:
        staged["status"] = "rejected"
        staged["errors"] = errors
        staged_path.write_text(json.dumps(staged, indent=2))
        os.rename(staged_path, REJECTED / f"{submission_id}.json")
        print(json.dumps({"status": "REJECTED", "errors": errors}))
        sys.exit(1)

    staged["status"] = "validated"
    staged["validated_at"] = datetime.now(timezone.utc).isoformat()
    staged_path.write_text(json.dumps(staged, indent=2))
    print(json.dumps({"status": "VALIDATED", "submission_id": submission_id}))


def cmd_commit(args: list[str]):
    """Commit a validated submission to the registry."""
    if not args:
        print("Usage: registry_txn.py commit <submission_id>", file=sys.stderr)
        sys.exit(1)

    submission_id = args[0]
    staged_path = STAGED / f"{submission_id}.json"
    if not staged_path.exists():
        print(json.dumps({"status": "NOT_FOUND", "message": f"Submission {submission_id} not found in staged"}))
        sys.exit(1)

    staged = json.loads(staged_path.read_text())
    if staged.get("status") != "validated":
        print(
            json.dumps({
                "status": "NOT_VALIDATED",
                "message": f"Submission status is '{staged.get('status')}', not 'validated'",
            })
        )
        sys.exit(1)

    entry = staged["entry"]
    registry_before = sum(1 for _ in open(REGISTRY_PATH)) if REGISTRY_PATH.exists() else 0

    # Atomic append
    with open(REGISTRY_PATH, "a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    registry_after = sum(1 for _ in open(REGISTRY_PATH)) if REGISTRY_PATH.exists() else 0

    staged["status"] = "committed"
    staged["committed_at"] = datetime.now(timezone.utc).isoformat()
    staged["registry_before"] = registry_before
    staged["registry_after"] = registry_after

    # Move to committed + generate receipt
    committed_path = COMMITTED / f"{submission_id}.json"
    committed_path.write_text(json.dumps(staged, indent=2))
    staged_path.unlink()

    receipt = {
        "submission_id": submission_id,
        "operation": "registry_entry_created",
        "doc_id": entry.get("doc_id"),
        "path": entry.get("path"),
        "registry_before": registry_before,
        "registry_after": registry_after,
        "committed_at": staged["committed_at"],
    }
    (RECEIPTS / f"{submission_id}.json").write_text(json.dumps(receipt, indent=2))

    print(
        json.dumps({
            "status": "COMMITTED",
            "submission_id": submission_id,
            "registry_delta": f"{registry_before}→{registry_after}",
        })
    )


def cmd_rollback(args: list[str]):
    """Rollback a staged submission."""
    if not args:
        print("Usage: registry_txn.py rollback <submission_id>", file=sys.stderr)
        sys.exit(1)
    submission_id = args[0]
    staged_path = STAGED / f"{submission_id}.json"
    if staged_path.exists():
        staged = json.loads(staged_path.read_text())
        staged["status"] = "rolled_back"
        staged["rolled_back_at"] = datetime.now(timezone.utc).isoformat()
        (REJECTED / f"{submission_id}.json").write_text(json.dumps(staged, indent=2))
        staged_path.unlink()
        print(json.dumps({"status": "ROLLED_BACK", "submission_id": submission_id}))
    else:
        print(json.dumps({"status": "NOT_FOUND", "submission_id": submission_id}))


def cmd_status(args: list[str]):
    """Check status of a submission."""
    if not args:
        print("Usage: registry_txn.py status <submission_id>", file=sys.stderr)
        sys.exit(1)
    submission_id = args[0]
    existing = find_existing_submission(submission_id)
    if existing:
        print(
            json.dumps({
                "submission_id": submission_id,
                "status": existing.get("status"),
                "staged_at": existing.get("staged_at", ""),
                "committed_at": existing.get("committed_at", ""),
            })
        )
    else:
        print(json.dumps({"submission_id": submission_id, "status": "NOT_FOUND"}))


def main():
    if len(sys.argv) < 2:
        print("Usage: registry_txn.py <stage|validate|commit|rollback|status> [args]", file=sys.stderr)
        sys.exit(1)

    cmd = sys.argv[1]
    args = sys.argv[2:]

    ensure_dirs()

    if cmd == "stage":
        cmd_stage(args)
    elif cmd == "validate":
        cmd_validate(args)
    elif cmd == "commit":
        cmd_commit(args)
    elif cmd == "rollback":
        cmd_rollback(args)
    elif cmd == "status":
        cmd_status(args)
    else:
        print(f"Unknown command: {cmd}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
