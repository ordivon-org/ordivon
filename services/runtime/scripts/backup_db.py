#!/usr/bin/env python3
"""Ordivon database backup utility.

Dumps PostgreSQL (or SQLite) to compressed SQL, optionally uploading to S3.

Usage:
    python3 scripts/backup_db.py                          # Local backup only
    python3 scripts/backup_db.py --s3                     # Backup to S3
    python3 scripts/backup_db.py --list                   # List S3 backups
    python3 scripts/backup_db.py --restore <key>          # Restore from S3
"""

import argparse
import gzip
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

BACKUP_DIR = ROOT / "data/backups"
S3_EXTRA_HINT = "Install S3 support with: uv sync --extra s3"


def _pg_dump(output_path: Path) -> bool:
    """Dump PostgreSQL database using pg_dump (via docker exec if needed)."""
    import subprocess

    # Try native pg_dump first, then docker exec
    pg_dump_path = shutil.which("pg_dump")
    container = "ordivon-pg"

    if pg_dump_path:
        cmd = [
            pg_dump_path,
            "-h",
            "localhost",
            "-p",
            "5432",
            "-U",
            "ordivon",
            "-d",
            "ordivon",
            "--no-owner",
            "--no-acl",
        ]
        env = os.environ.copy()
        env["PGPASSWORD"] = "ordivon"
    else:
        # Use docker exec
        cmd = ["docker", "exec", container, "pg_dump", "-U", "ordivon", "ordivon", "--no-owner", "--no-acl"]
        env = os.environ.copy()

    try:
        with gzip.open(output_path, "wb") as f:
            proc = subprocess.run(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
            if proc.returncode == 0:
                f.write(proc.stdout)
                return True
            else:
                print(f"  pg_dump failed: {proc.stderr.decode()[:200]}")
                return False
    except Exception as e:
        print(f"  pg_dump error: {e}")
        return False


def _sqlite_backup(output_path: Path) -> bool:
    """Backup SQLite database."""

    db_path = ROOT / "data/ordivon.sqlite"
    if not db_path.exists():
        return False

    import sqlite3

    try:
        # Dump SQL
        conn = sqlite3.connect(str(db_path))
        with gzip.open(output_path, "wb") as f:
            for line in conn.iterdump():
                f.write((line + ";\n").encode())
        conn.close()
        return True
    except Exception as e:
        print(f"  sqlite backup error: {e}")
        return False


def backup_local() -> Path | None:
    """Create a local database backup."""
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    path = BACKUP_DIR / f"ordivon_backup_{ts}.sql.gz"

    print(f"Backing up to: {path}")

    if _pg_dump(path):
        print(f"  ✓ PG dump: {path.stat().st_size:,} bytes")
        return path
    elif _sqlite_backup(path):
        print(f"  ✓ SQLite dump: {path.stat().st_size:,} bytes")
        return path
    else:
        print("  ✗ No database available to back up")
        return None


def backup_to_s3() -> bool:
    """Backup database and upload to S3."""
    local_path = backup_local()
    if not local_path:
        return False

    try:
        from ordivon_governance_core.s3_client import get_client

        client = get_client()
        if not client.available():
            print("  ✗ S3 not available")
            return False

        key = f"backups/{local_path.name}"
        client.upload_file(key, local_path)
        print(f"  ✓ Uploaded to S3: {key}")

        # Clean up old local backups (keep last 5)
        backups = sorted(BACKUP_DIR.glob("ordivon_backup_*.sql.gz"))
        for old in backups[:-5]:
            old.unlink()
        return True
    except ImportError:
        print(f"  ✗ boto3 not installed. {S3_EXTRA_HINT}")
        return False


def list_s3_backups() -> bool:
    """List backups in S3."""
    try:
        from ordivon_governance_core.s3_client import get_client

        client = get_client()
        items = client.list_evidence("backups/")
        if not items:
            print("No backups found in S3")
            return True
        for item in sorted(items, key=lambda i: i["key"], reverse=True)[:10]:
            print(f"  {item['key']}  ({item['size']:,} bytes, {item['last_modified'][:19]})")
        return True
    except ImportError:
        print(f"boto3 not installed. {S3_EXTRA_HINT}")
        return False


def restore_from_s3(key: str, output_dir: str = "") -> bool:
    """Restore database from S3 backup."""
    try:
        from ordivon_governance_core.s3_client import get_client

        client = get_client()
        data = client.download_evidence(key)
        if not data:
            print(f"Backup not found: {key}")
            return False

        out = Path(output_dir or BACKUP_DIR) / Path(key).name
        out.write_bytes(data)
        print(f"Restored to: {out} ({len(data):,} bytes)")
        print(f"To restore: gunzip {out} | psql ...")
        return True
    except ImportError:
        print(f"boto3 not installed. {S3_EXTRA_HINT}")
        return False


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Back up the Ordivon database locally or to S3-compatible storage.")
    parser.add_argument("--s3", action="store_true", help="Create a local backup and upload it to S3/MinIO")
    parser.add_argument("--list", action="store_true", help="List S3/MinIO backups")
    parser.add_argument("--restore", metavar="KEY", help="Download a backup object from S3/MinIO")
    return parser.parse_args(argv)


def main() -> int:
    args = parse_args()
    if args.list:
        return 0 if list_s3_backups() else 1
    if args.restore:
        return 0 if restore_from_s3(args.restore) else 1
    if args.s3:
        ok = backup_to_s3()
    else:
        path = backup_local()
        ok = path is not None

    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
