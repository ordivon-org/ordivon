from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

_SOURCE_ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")


class TrustState(StrEnum):
    TRUSTED = "TRUSTED"
    APPROVED = "APPROVED"
    QUARANTINED = "QUARANTINED"
    BLOCKED = "BLOCKED"
    UNTRUSTED = "UNTRUSTED"


class ConfidenceTier(StrEnum):
    THIRD_PARTY_UNREVIEWED = "THIRD_PARTY_UNREVIEWED"
    THIRD_PARTY_SCANNED = "THIRD_PARTY_SCANNED"
    THIRD_PARTY_AUDITED = "THIRD_PARTY_AUDITED"
    USER_EXPLICIT = "USER_EXPLICIT"


class EligibilityState(StrEnum):
    READY = "READY"
    BLOCKED = "BLOCKED"
    UNKNOWN = "UNKNOWN"


class SourceHealth(StrEnum):
    READY = "READY"
    DEGRADED = "DEGRADED"
    UNAVAILABLE = "UNAVAILABLE"
    DISABLED = "DISABLED"


@dataclass(frozen=True, slots=True)
class SkillContext:
    workspace_path: Path | None = None
    workspace_id: str | None = None
    agent_id: str | None = None

    def normalized_workspace_path(self) -> Path | None:
        if self.workspace_path is None:
            return None
        try:
            return Path(self.workspace_path).resolve(strict=False)
        except OSError:
            return Path(self.workspace_path).absolute()


@dataclass(frozen=True, slots=True)
class SkillSource:
    source_id: str
    root: Path
    scope: str
    priority: int
    trust_state: TrustState
    enabled: bool = True
    project_root: Path | None = None
    implicit_deny_prefixes: tuple[str, ...] = ()
    explicit_deny_prefixes: tuple[str, ...] = ()
    eligibility_adapter: str | None = None
    validation_mode: str = "strict"

    def __post_init__(self) -> None:
        if not _SOURCE_ID_RE.fullmatch(self.source_id):
            raise ValueError("source_id must match lowercase [a-z0-9][a-z0-9._-]{0,63}")
        if self.scope not in {"project", "workspace", "user", "vendor", "plugin", "managed"}:
            raise ValueError(f"unsupported scope: {self.scope}")
        if type(self.priority) is not int:
            raise ValueError("priority must be an integer")
        root = Path(self.root)
        object.__setattr__(self, "root", root)
        if self.project_root is not None:
            object.__setattr__(self, "project_root", Path(self.project_root))
        for prefix in (*self.implicit_deny_prefixes, *self.explicit_deny_prefixes):
            if not prefix or prefix.startswith("/") or ".." in Path(prefix).parts:
                raise ValueError(f"unsafe source policy prefix: {prefix!r}")
        if self.eligibility_adapter not in {None, "openclaw-metadata"}:
            raise ValueError(f"unsupported eligibility adapter: {self.eligibility_adapter}")
        if self.validation_mode not in {"strict", "lenient"}:
            raise ValueError("validation_mode must be strict or lenient")


@dataclass(frozen=True, slots=True)
class SkillRecord:
    skill_id: str
    name: str
    description: str
    source_id: str
    scope: str
    source_priority: int
    source_relative_root: str
    skill_root: Path
    main_resource: Path
    project_root: Path | None
    instruction_digest: str
    package_revision: str
    trust_state: TrustState
    eligibility_state: EligibilityState = EligibilityState.UNKNOWN
    eligibility_reasons: tuple[str, ...] = ()
    scan_state: str = "PASS"
    scan_findings: tuple[str, ...] = ()
    risk_tags: tuple[str, ...] = ()
    declared_dependencies: tuple[str, ...] = ()
    required_dependencies: tuple[str, ...] = ()
    confidence_tier: ConfidenceTier = ConfidenceTier.THIRD_PARTY_UNREVIEWED
    implicit_invocation: bool = True
    explicit_invocation: bool = True
    diagnostics: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.skill_id != f"{self.source_id}/{self.name}":
            raise ValueError("skill_id must be <source_id>/<name>")
        if not self.name or "/" in self.name:
            raise ValueError("skill name must be a non-empty path-segment-safe identifier")
        if not self.description.strip():
            raise ValueError("skill description must be non-empty")
        for digest in (self.instruction_digest, self.package_revision):
            if not digest.startswith("sha256:"):
                raise ValueError("digests must be sha256-prefixed")

    def metadata(self) -> dict:
        return {
            "skillId": self.skill_id,
            "name": self.name,
            "description": self.description,
            "sourceId": self.source_id,
            "scope": self.scope,
            "instructionDigest": self.instruction_digest,
            "packageRevision": self.package_revision,
            "trustState": self.trust_state.value,
            "eligibilityState": self.eligibility_state.value,
            "eligibilityReasons": list(self.eligibility_reasons),
            "scanState": self.scan_state,
            "riskTags": list(self.risk_tags),
            "declaredDependencies": list(self.declared_dependencies),
            "requiredDependencies": list(self.required_dependencies),
            "confidenceTier": self.confidence_tier.value,
            "instructionAuthority": "ADVISORY",
            "implicitInvocation": self.implicit_invocation,
            "explicitInvocation": self.explicit_invocation,
        }


@dataclass(frozen=True, slots=True)
class SourceScanStatus:
    source_id: str
    health: SourceHealth
    discovered: int
    valid: int
    invalid: int
    quarantined: int
    admitted: int
    diagnostics: tuple[str, ...] = ()

    def value(self) -> dict:
        return {
            "sourceId": self.source_id,
            "health": self.health.value,
            "discovered": self.discovered,
            "valid": self.valid,
            "invalid": self.invalid,
            "quarantined": self.quarantined,
            "admitted": self.admitted,
            "diagnostics": list(self.diagnostics),
        }
