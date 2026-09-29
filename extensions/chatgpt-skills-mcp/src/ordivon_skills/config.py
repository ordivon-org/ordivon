from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from .model import SkillSource, TrustState

_WORKSPACE_ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")


@dataclass(frozen=True, slots=True)
class WorkspacePolicy:
    workspace_id: str
    path: Path
    trusted: bool = False


@dataclass(frozen=True, slots=True)
class SkillsMcpConfig:
    sources: tuple[SkillSource, ...]
    workspaces: tuple[WorkspacePolicy, ...] = ()
    ttl_ms: int = 30_000
    audited_skill_ids: tuple[str, ...] = ()
    user_explicit_skill_ids: tuple[str, ...] = ()

    def workspace_path(self, workspace_id: str) -> Path | None:
        for workspace in self.workspaces:
            if workspace.workspace_id == workspace_id:
                return workspace.path
        return None


def _trust(value: object, *, field: str) -> TrustState:
    try:
        return TrustState(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} is invalid") from exc


def _source_from_row(
    item: dict,
    *,
    index: int,
    source_count: int,
    validation_mode: str,
) -> SkillSource:
    allowed = {
        "sourceId",
        "root",
        "scope",
        "trust",
        "enabled",
        "projectRoot",
        "implicitDenyPrefixes",
        "explicitDenyPrefixes",
        "eligibilityAdapter",
    }
    extra = set(item) - allowed
    if extra:
        raise ValueError(f"source has unknown keys: {sorted(extra)}")
    root = Path(item["root"])
    if not root.is_absolute():
        raise ValueError("source root must be absolute")
    project_root = item.get("projectRoot")
    if project_root is not None:
        project_root = Path(project_root)
        if not project_root.is_absolute():
            raise ValueError("source projectRoot must be absolute")
    implicit = item.get("implicitDenyPrefixes", [])
    explicit = item.get("explicitDenyPrefixes", [])
    if not isinstance(implicit, list) or not all(isinstance(x, str) for x in implicit):
        raise ValueError("source implicitDenyPrefixes must be string list")
    if not isinstance(explicit, list) or not all(isinstance(x, str) for x in explicit):
        raise ValueError("source explicitDenyPrefixes must be string list")
    return SkillSource(
        source_id=item["sourceId"],
        root=root,
        scope=item["scope"],
        # Agent Skills only requires deterministic within-scope precedence.
        # Earlier configured compatibility/additional source wins.
        priority=source_count - index,
        trust_state=_trust(item.get("trust", "APPROVED"), field="source trust"),
        enabled=item.get("enabled", True),
        project_root=project_root,
        implicit_deny_prefixes=tuple(implicit),
        explicit_deny_prefixes=tuple(explicit),
        eligibility_adapter=item.get("eligibilityAdapter"),
        validation_mode=validation_mode,
    )


def load_skills_mcp_config(path: Path) -> SkillsMcpConfig:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or raw.get("schemaVersion") != 2:
        raise ValueError("Skills MCP config schemaVersion must be 2")
    unknown = set(raw) - {
        "schemaVersion",
        "ttlMs",
        "workspaces",
        "additionalSources",
        "compatibilitySources",
        "standardDiscovery",
        "auditedSkillIds",
        "userExplicitSkillIds",
    }
    if unknown:
        raise ValueError(f"unknown config keys: {sorted(unknown)}")
    ttl_ms = raw.get("ttlMs", 30_000)
    if type(ttl_ms) is not int or ttl_ms < 0:
        raise ValueError("ttlMs must be a non-negative integer")

    def _skill_id_list(field: str) -> tuple[str, ...]:
        values = raw.get(field, [])
        if not isinstance(values, list) or not all(
            isinstance(item, str) and item and "/" in item and not item.startswith("/")
            for item in values
        ):
            raise TypeError(f"{field} must be a list of canonical <sourceId>/<name> strings")
        return tuple(dict.fromkeys(values))

    audited_skill_ids = _skill_id_list("auditedSkillIds")
    user_explicit_skill_ids = _skill_id_list("userExplicitSkillIds")

    discovery = raw.get("standardDiscovery", {})
    if not isinstance(discovery, dict) or set(discovery) - {"user", "projects"}:
        raise TypeError("standardDiscovery may contain user/projects booleans only")
    discover_user = discovery.get("user", True)
    discover_projects = discovery.get("projects", True)
    if type(discover_user) is not bool or type(discover_projects) is not bool:
        raise TypeError("standardDiscovery user/projects must be booleans")

    workspaces_raw = raw.get("workspaces", {})
    if not isinstance(workspaces_raw, dict):
        raise TypeError("workspaces must map workspaceId to policy")
    workspaces: list[WorkspacePolicy] = []
    for workspace_id, policy in sorted(workspaces_raw.items()):
        if not isinstance(workspace_id, str) or not _WORKSPACE_ID_RE.fullmatch(workspace_id):
            raise ValueError("workspaceId must match lowercase [a-z0-9][a-z0-9._-]{0,63}")
        if isinstance(policy, str):
            # Temporary migration convenience for the v1 config shape.
            policy = {"path": policy, "trusted": False}
        if not isinstance(policy, dict) or set(policy) - {"path", "trusted"}:
            raise TypeError(f"workspace policy for {workspace_id} must contain path/trusted only")
        workspace_path = Path(policy["path"])
        if not workspace_path.is_absolute():
            raise ValueError(f"workspace path for {workspace_id} must be absolute")
        trusted = policy.get("trusted", False)
        if type(trusted) is not bool:
            raise TypeError(f"workspace trusted for {workspace_id} must be boolean")
        workspaces.append(WorkspacePolicy(workspace_id, workspace_path, trusted))

    # Standard Agent Skills discovery roots. The format spec does not mandate install
    # paths, but the official client guide identifies .agents/skills as the
    # cross-client interoperability convention at project and user scopes.
    sources: list[SkillSource] = []
    if discover_user:
        sources.append(
            SkillSource(
                source_id="user-agents",
                root=Path.home() / ".agents" / "skills",
                scope="user",
                priority=10_000,
                trust_state=TrustState.APPROVED,
                validation_mode="lenient",
            )
        )
    if discover_projects:
        for ordinal, workspace in enumerate(workspaces):
            sources.append(
                SkillSource(
                    source_id=f"project-{workspace.workspace_id}",
                    root=workspace.path / ".agents" / "skills",
                    scope="project",
                    priority=10_000 - ordinal,
                    trust_state=TrustState.TRUSTED if workspace.trusted else TrustState.UNTRUSTED,
                    project_root=workspace.path,
                    validation_mode="lenient",
                )
            )

    additional = raw.get("additionalSources", [])
    compatibility = raw.get("compatibilitySources", [])
    for label, rows, mode in (
        ("additionalSources", additional, "strict"),
        ("compatibilitySources", compatibility, "lenient"),
    ):
        if not isinstance(rows, list):
            raise TypeError(f"{label} must be a list")
        for index, item in enumerate(rows):
            if not isinstance(item, dict):
                raise TypeError(f"{label}[{index}] must be an object")
            sources.append(
                _source_from_row(
                    item,
                    index=index,
                    source_count=len(rows),
                    validation_mode=mode,
                )
            )

    return SkillsMcpConfig(
        tuple(sources),
        tuple(workspaces),
        ttl_ms=ttl_ms,
        audited_skill_ids=audited_skill_ids,
        user_explicit_skill_ids=user_explicit_skill_ids,
    )
