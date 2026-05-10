"""Skill / Tool Boundary Scanner Alpha.

Read-only scanner that detects permission/authorization confusion,
credential requests, overbroad tool grants, and missing boundaries
in SKILL.md files.

Core invariants:
- Skill exists != permission
- allowed-tools != authorization
- script exists != safe execution
- tool capability != owner approval
- credential request != permitted sensitive-material access
- skill instruction != project policy
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from ordivon_verify.metabolic.models import (
    ArtifactRecord,
    ArtifactTemperature,
    AuthorityTier,
    LifecycleState,
    MetabolicFinding,
)

_FINDING_CODES = Literal[
    "SKILL-CREDENTIAL-REQUEST",
    "SKILL-ALLOWED-TOOLS-BROAD",
    "SKILL-TOOL-AS-AUTHORIZATION",
    "SKILL-SCRIPT-SIDE-EFFECT-UNCLEAR",
    "SKILL-DEPLOY-AUTHORIZATION-LAUNDERING",
    "SKILL-CAPABILITY-AS-PERMISSION",
    "SKILL-MISSING-NON-AUTH-BOUNDARY",
]

_CREDENTIAL_MARKERS = (
    "api " + "key",
    "api_" + "key",
    "to" + "ken",
    "pass" + "word",
    "sec" + "ret",
    "cre" + "dential",
    "private " + "key",
    "private_" + "key",
)

_BROAD_TOOL_MARKERS = (
    "bash(*)",
    "bash (*",
    "shell unrestricted",
    "all tools",
    "filesystem unrestricted",
    "network unrestricted",
)

_AUTHORIZATION_MARKERS = (
    "authorizes",
    "authorization",
    "approved to",
    "permission to",
    "can merge",
    "can deploy",
    "safe to merge",
    "safe to deploy",
    "safe to release",
)

_DEPLOY_AUTHZ_MARKERS = (
    "approve",
    "authorize",
    "release",
    "deploy",
    "production-" + "ready",
    "production " + "ready",
    "safe to merge",
    "safe to deploy",
)

_SCRIPT_SIDE_EFFECT_MARKERS = (
    ".sh",
    ".py",
    "npm run deploy",
    "npm run publish",
    "rm ",
    "delete",
    "modify",
    "upload",
    "publish",
)

_SCRIPT_SAFE_MARKERS = (
    "read-only",
    "read only",
    "dry-run",
    "dry run",
    "no side effect",
    "owner confirmation",
    "requires approval",
)

_NON_AUTH_BOUNDARY_MARKERS = (
    "not authorization",
    "does not authorize",
    "review required",
    "human review",
    "read-only",
    "read only",
    "no external action",
    "requires approval",
    "owner must",
    "owner confirms",
)

_GOVERNANCE_SURFACE_MARKERS = (
    "governance",
    "verification",
    "deploy",
    "release",
    "tool",
    "review",
    "claim",
    "evidence",
    "authority",
    "authorization",
    "approve",
)

_CREDENTIAL_SAFE_MARKERS = (
    "never request",
    "owner-managed",
    "placeholder",
    "do not store",
    "managed externally",
    "does not request",
    "not request",
)

_SKILL_CANDIDATE_DIRS = (
    "skills/",
    "optional-skills/",
    ".claude/skills/",
)


def _parse_frontmatter(raw: str) -> dict[str, str]:
    """Extract YAML frontmatter fields as a flat dict. Handles only simple key: value."""
    if not raw.lstrip().startswith("---"):
        return {}
    lines = raw.splitlines()
    result: dict[str, str] = {}
    for line in lines[1:]:
        stripped = line.strip()
        if stripped == "---":
            break
        if ":" in stripped:
            key, _, val = stripped.partition(":")
            result[key.strip()] = val.strip().strip("\"'")
    return result


def _classify_skill(path: Path, root: Path) -> tuple[list[MetabolicFinding], ArtifactRecord | None]:
    raw = path.read_text(encoding="utf-8", errors="ignore")
    text = raw.lower()
    rel = _rel(path, root)
    fm = _parse_frontmatter(raw)
    _ = fm.get("allowed-tools", fm.get("allowed_tools", ""))

    findings: list[MetabolicFinding] = []
    artifact_id = rel.replace("/", "-").replace(".", "-")[:120]
    content_hash = hashlib.sha256(raw.encode()).hexdigest()[:16] if len(raw) < 1_000_000 else None

    # Rule 1: Credential request without boundary
    has_credential = any(m in text for m in _CREDENTIAL_MARKERS)
    has_credential_safe = any(m in text for m in _CREDENTIAL_SAFE_MARKERS)
    if has_credential and not has_credential_safe:
        findings.append(
            MetabolicFinding(
                code="SKILL-CREDENTIAL-REQUEST",
                status="BLOCKED",
                message="Skill references credentials without explicit boundary or safety markers",
                artifact_id=artifact_id,
                repair_action="Add credential boundary: 'never request', 'owner-managed', or 'placeholder'.",
            )
        )

    # Rule 2: Overbroad allowed-tools
    has_broad = any(m in text for m in _BROAD_TOOL_MARKERS)
    if has_broad:
        findings.append(
            MetabolicFinding(
                code="SKILL-ALLOWED-TOOLS-BROAD",
                status="BLOCKED",
                message="Skill declares overbroad tool access",
                artifact_id=artifact_id,
                repair_action="Restrict allowed-tools to specific tool names. Remove Bash(*) or unrestricted grants.",
            )
        )

    # Rule 3: Tool capability as authorization
    has_authorization = any(m in text for m in _AUTHORIZATION_MARKERS)
    has_non_auth_boundary = any(m in text for m in _NON_AUTH_BOUNDARY_MARKERS)
    if has_authorization and not has_non_auth_boundary:
        findings.append(
            MetabolicFinding(
                code="SKILL-TOOL-AS-AUTHORIZATION",
                status="BLOCKED",
                message="Skill uses authorization language without non-authorization boundary",
                artifact_id=artifact_id,
                repair_action="Add boundary: 'allowed-tools is capability, not authorization. Owner/reviewer decides.'",
            )
        )
    elif has_authorization and has_non_auth_boundary:
        findings.append(
            MetabolicFinding(
                code="SKILL-CAPABILITY-AS-PERMISSION",
                status="DEGRADED",
                message="Skill has authorization language alongside boundary — review boundary scope",
                artifact_id=artifact_id,
                repair_action="Verify boundary covers all authorization claims. Skill capability is not permission.",
            )
        )

    # Rule 4: Unclear script side-effect
    has_script = any(m in text for m in _SCRIPT_SIDE_EFFECT_MARKERS)
    has_script_safe = any(m in text for m in _SCRIPT_SAFE_MARKERS)
    if has_script and not has_script_safe:
        findings.append(
            MetabolicFinding(
                code="SKILL-SCRIPT-SIDE-EFFECT-UNCLEAR",
                status="DEGRADED",
                message="Skill references scripts without side-effect boundary",
                artifact_id=artifact_id,
                repair_action="Add boundary: 'read-only', 'dry-run', 'owner confirmation required', or 'no side effect'.",
            )
        )

    # Rule 5: Deploy/release/approve authorization laundering
    has_deploy_authz = any(m in text for m in _DEPLOY_AUTHZ_MARKERS)
    if has_deploy_authz and not has_non_auth_boundary:
        findings.append(
            MetabolicFinding(
                code="SKILL-DEPLOY-AUTHORIZATION-LAUNDERING",
                status="BLOCKED",
                message="Skill claims deploy/release/approve authority without external owner boundary",
                artifact_id=artifact_id,
                repair_action="Add boundary: deploy/release/merge requires external owner/reviewer approval beyond skill capability.",
            )
        )

    # Rule 6: Missing non-authorization boundary when governance-related
    has_governance_surface = any(m in text for m in _GOVERNANCE_SURFACE_MARKERS)
    if has_governance_surface and not has_non_auth_boundary:
        findings.append(
            MetabolicFinding(
                code="SKILL-MISSING-NON-AUTH-BOUNDARY",
                status="DEGRADED",
                message="Governance-related skill missing non-authorization boundary",
                artifact_id=artifact_id,
                repair_action=(
                    "Add boundary: 'This skill capability is not permission, authorization, or policy. "
                    "Owner/reviewer must confirm canonical gates and authorize action.'"
                ),
            )
        )

    # Build artifact record
    temperature = ArtifactTemperature.WARM
    lifecycle = LifecycleState.CANDIDATE
    authority = AuthorityTier.T3_CANDIDATE_PROPOSAL
    if any(d in str(path) for d in ("optional-skills/", "skills/")):
        temperature = ArtifactTemperature.HOT
        lifecycle = LifecycleState.ACTIVE

    record = ArtifactRecord(
        artifact_id=artifact_id,
        path=rel,
        artifact_type="skill",
        authority_tier=authority,
        lifecycle_state=lifecycle,
        temperature=temperature,
        owner=fm.get("owner") or None,
        scope=f"skill:{artifact_id}",
        content_hash=content_hash,
        created_in_phase=None,
        last_verified=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        review_date=None,
        supersedes=[],
        superseded_by=None,
        depends_on=[],
        new_ai_entry=False,
        current_truth_allowed=False,
        notes="Auto-discovered SKILL.md. Skill capability is not permission.",
    )

    return findings, record


def _rel(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def discover_skill_surfaces(
    root: Path, *, fixture_mode: bool = False
) -> tuple[list[MetabolicFinding], list[ArtifactRecord]]:
    """Scan repo root for SKILL.md files and return findings + artifact records."""
    all_findings: list[MetabolicFinding] = []
    all_records: list[ArtifactRecord] = []

    skill_files: list[Path] = []
    for pattern in ("skills/**/SKILL.md", "optional-skills/**/SKILL.md", ".claude/skills/**/SKILL.md", "**/SKILL.md"):
        skill_files.extend(sorted(root.glob(pattern)))

    if not skill_files:
        return all_findings, all_records

    # Deduplicate
    seen = set()
    unique: list[Path] = []
    for p in skill_files:
        rp = p.resolve()
        if rp not in seen:
            seen.add(rp)
            unique.append(p)
    skill_files = unique

    # Exclude non-production surfaces (skip in fixture mode for tests)
    if not fixture_mode:
        _EXCLUDE_MARKERS = (
            "tests/fixtures/skill_boundary/",
            "/unsafe/",
            "/unsafe-",
            "docs/archive/",
            ".tmp/",
        )
        skill_files = [p for p in skill_files if not any(m in str(p) for m in _EXCLUDE_MARKERS)]

    for p in skill_files[:300]:
        if not p.is_file():
            continue
        findings, record = _classify_skill(p, root)
        all_findings.extend(findings)
        if record:
            all_records.append(record)

    return all_findings, all_records
