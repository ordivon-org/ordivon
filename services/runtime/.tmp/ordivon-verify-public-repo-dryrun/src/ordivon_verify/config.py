"""Ordivon Verify — configuration loading and validation."""

from __future__ import annotations

import json
from pathlib import Path


def load_config(config_path: Path | None, root: Path) -> dict | None:
    """Load ordivon.verify.json, falling back to auto-detect or None."""
    if config_path:
        if not config_path.exists():
            return None
        try:
            with open(config_path) as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return None
    auto = root / "ordivon.verify.json"
    if auto.exists():
        try:
            with open(auto) as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return None
    return None


def validate_config(cfg: dict) -> list[str]:
    """Validate config dict. Returns list of error strings."""
    errors = []
    if not isinstance(cfg, dict):
        return ["config must be a JSON object"]
    version = cfg.get("schema_version", "")
    if version != "0.1":
        errors.append(f"unsupported schema_version: {version!r}")
    mode = cfg.get("mode", "")
    if mode and mode not in ("advisory", "standard", "strict"):
        errors.append(f"invalid mode: {mode!r}")
    return errors


def is_ordivon_native(root: Path) -> bool:
    """Check if root looks like an Ordivon-native repo."""
    return (root / "docs" / "governance" / "verification-debt-ledger.jsonl").exists() and (
        root / "docs" / "governance" / "verification-gate-manifest.json"
    ).exists()
