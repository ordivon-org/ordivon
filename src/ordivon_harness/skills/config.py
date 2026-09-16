from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .model import SkillSource, TrustState


@dataclass(frozen=True, slots=True)
class SkillsMcpConfig:
    sources: tuple[SkillSource, ...]
    ttl_ms: int = 30_000


def load_skills_mcp_config(path: Path) -> SkillsMcpConfig:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or raw.get("schemaVersion") != 1:
        raise ValueError("Skills MCP config schemaVersion must be 1")
    unknown = set(raw) - {"schemaVersion", "ttlMs", "sources"}
    if unknown:
        raise ValueError(f"unknown config keys: {sorted(unknown)}")
    ttl_ms = raw.get("ttlMs", 30_000)
    if type(ttl_ms) is not int or ttl_ms < 0:
        raise ValueError("ttlMs must be a non-negative integer")
    source_values = raw.get("sources")
    if not isinstance(source_values, list) or not source_values:
        raise ValueError("sources must be a non-empty list")
    sources: list[SkillSource] = []
    allowed = {
        "sourceId",
        "root",
        "scope",
        "priority",
        "trust",
        "enabled",
        "projectRoot",
        "implicitDenyPrefixes",
        "explicitDenyPrefixes",
    }
    for index, item in enumerate(source_values):
        if not isinstance(item, dict):
            raise TypeError(f"sources[{index}] must be an object")
        extra = set(item) - allowed
        if extra:
            raise ValueError(f"sources[{index}] has unknown keys: {sorted(extra)}")
        root = Path(item["root"])
        if not root.is_absolute():
            raise ValueError(f"sources[{index}].root must be absolute")
        project_root = item.get("projectRoot")
        if project_root is not None:
            project_root = Path(project_root)
            if not project_root.is_absolute():
                raise ValueError(f"sources[{index}].projectRoot must be absolute")
        try:
            trust = TrustState(item.get("trust", "APPROVED"))
        except ValueError as exc:
            raise ValueError(f"sources[{index}].trust is invalid") from exc
        implicit = item.get("implicitDenyPrefixes", [])
        explicit = item.get("explicitDenyPrefixes", [])
        if not isinstance(implicit, list) or not all(isinstance(x, str) for x in implicit):
            raise ValueError(f"sources[{index}].implicitDenyPrefixes must be string list")
        if not isinstance(explicit, list) or not all(isinstance(x, str) for x in explicit):
            raise ValueError(f"sources[{index}].explicitDenyPrefixes must be string list")
        sources.append(
            SkillSource(
                source_id=item["sourceId"],
                root=root,
                scope=item["scope"],
                priority=item["priority"],
                trust_state=trust,
                enabled=item.get("enabled", True),
                project_root=project_root,
                implicit_deny_prefixes=tuple(implicit),
                explicit_deny_prefixes=tuple(explicit),
            )
        )
    return SkillsMcpConfig(tuple(sources), ttl_ms=ttl_ms)
