"""Ordivon Verify — configuration loading and validation."""

from __future__ import annotations

import json
from pathlib import Path

SUPPORTED_PACKS = {"coding"}
SUPPORTED_PROFILES = {"ai_coding_trust_audit", "coding"}
SUPPORTED_RISK_STAGES = {"vibe", "merge", "release"}


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
    pack = cfg.get("pack", "")
    if pack and pack not in SUPPORTED_PACKS:
        errors.append(f"unsupported pack: {pack!r}")
    profile = cfg.get("profile", "")
    if profile and profile not in SUPPORTED_PROFILES:
        errors.append(f"unsupported profile: {profile!r}")
    risk_stage = cfg.get("risk_stage", "")
    if risk_stage and risk_stage not in SUPPORTED_RISK_STAGES:
        errors.append(f"invalid risk_stage: {risk_stage!r}")
    return errors


def default_risk_stage(mode: str) -> str:
    """Map legacy modes to Coding Trust Profile risk stages."""
    if mode == "strict":
        return "release"
    return "vibe"


def resolve_profile_context(
    cfg: dict | None,
    cli_profile: str | None,
    cli_risk_stage: str | None,
    mode: str,
) -> tuple[dict, list[str]]:
    """Resolve pack/profile/risk_stage with backward-compatible defaults."""
    cfg = cfg or {}
    profile_value = cli_profile or cfg.get("profile") or cfg.get("pack") or "coding"
    if profile_value == "coding":
        pack = "coding"
        profile = "ai_coding_trust_audit"
    elif profile_value == "ai_coding_trust_audit":
        pack = "coding"
        profile = "ai_coding_trust_audit"
    else:
        pack = cfg.get("pack") or profile_value
        profile = profile_value

    risk_stage = cli_risk_stage or cfg.get("risk_stage") or default_risk_stage(mode)
    errors = []
    if pack not in SUPPORTED_PACKS:
        errors.append(f"unsupported pack/profile for v1: {profile_value!r}")
    if profile not in {"ai_coding_trust_audit"}:
        errors.append(f"unsupported profile for v1: {profile!r}")
    if risk_stage not in SUPPORTED_RISK_STAGES:
        errors.append(f"invalid risk_stage: {risk_stage!r}")
    return {"pack": pack, "profile": profile, "risk_stage": risk_stage}, errors


def is_ordivon_native(root: Path) -> bool:
    """Check if root looks like an Ordivon-native repo."""
    return (root / "docs" / "governance" / "verification-debt-ledger.jsonl").exists() and (
        root / "docs" / "governance" / "verification-gate-manifest.json"
    ).exists()
