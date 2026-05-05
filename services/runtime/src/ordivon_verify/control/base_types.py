"""Shared types for Ordivon Control Plane.

DriftEntry and RepoSnapshot are used by both reconciler and rule_registry.
They live here to break the circular import.
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path


@dataclass
class DriftEntry:
    """A single deviation between desired and actual state."""
    category: str          # boundary, verification, evidence, closure, authority
    severity: str          # BLOCKED, DEGRADED, ADVISORY
    description: str
    detail: str = ""


@dataclass
class RepoSnapshot:
    """A point-in-time capture of actual repo state."""
    timestamp: str = ""
    head_commit: str = ""
    modified_files: list[str] = field(default_factory=list)
    untracked_files: list[str] = field(default_factory=list)
    dg_entry_count: int = 0
    checker_count: int = 0
    manifest_gate_count: int = 0

    @classmethod
    def capture(cls, root: Path) -> RepoSnapshot:
        """Capture actual repo state."""
        snap = cls(timestamp=datetime.now(timezone.utc).isoformat())

        try:
            r = subprocess.run(
                ["git", "rev-parse", "--short", "HEAD"],
                cwd=root, capture_output=True, text=True,
            )
            snap.head_commit = r.stdout.strip()
        except Exception:
            snap.head_commit = "unknown"

        try:
            r = subprocess.run(
                ["git", "diff", "--name-only", "HEAD"],
                cwd=root, capture_output=True, text=True,
            )
            snap.modified_files = [f.strip() for f in r.stdout.split("\n") if f.strip()]
        except Exception:
            pass

        try:
            r = subprocess.run(
                ["git", "ls-files", "--others", "--exclude-standard"],
                cwd=root, capture_output=True, text=True,
            )
            snap.untracked_files = [f.strip() for f in r.stdout.split("\n") if f.strip()]
        except Exception:
            pass

        dg_path = root / "docs" / "governance" / "document-registry.jsonl"
        if dg_path.exists():
            with open(dg_path) as f:
                snap.dg_entry_count = sum(1 for _ in f)

        checkers_dir = root / "checkers"
        if checkers_dir.exists():
            snap.checker_count = sum(
                1 for d in checkers_dir.iterdir()
                if d.is_dir() and not d.name.startswith(".")
            )

        manifest_path = root / "docs" / "governance" / "verification-gate-manifest.json"
        if manifest_path.exists():
            with open(manifest_path) as f:
                m = json.load(f)
                snap.manifest_gate_count = len(m.get("gates", []))

        return snap
