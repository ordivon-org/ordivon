"""Metabolic governance data models for Ordivon Verify.

Artifact lifecycle, authority tiers, and temperature tracking.
Part of the Entropy Governance protocol.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Literal


class AuthorityTier(str, Enum):
    T0_CURRENT_TRUTH = "T0_CURRENT_TRUTH"
    T1_ACTIVE_SPEC = "T1_ACTIVE_SPEC"
    T2_ACTIVE_RUNTIME_EVIDENCE = "T2_ACTIVE_RUNTIME_EVIDENCE"
    T3_CANDIDATE_PROPOSAL = "T3_CANDIDATE_PROPOSAL"
    T4_HISTORICAL_ARCHIVE = "T4_HISTORICAL_ARCHIVE"
    T5_DEPRECATED_TOMBSTONED = "T5_DEPRECATED_TOMBSTONED"


class ArtifactTemperature(str, Enum):
    HOT = "hot"
    WARM = "warm"
    COLD = "cold"
    TOMBSTONED = "tombstoned"


class LifecycleState(str, Enum):
    DRAFT = "draft"
    CANDIDATE = "candidate"
    ACTIVE = "active"
    STABLE = "stable"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"
    TOMBSTONED = "tombstoned"


@dataclass(frozen=True)
class ArtifactRecord:
    artifact_id: str
    path: str
    artifact_type: str
    authority_tier: AuthorityTier
    lifecycle_state: LifecycleState
    temperature: ArtifactTemperature
    owner: str | None = None
    scope: str = ""
    content_hash: str | None = None
    created_in_phase: str | None = None
    last_verified: str | None = None
    review_date: str | None = None
    supersedes: list[str] = field(default_factory=list)
    superseded_by: str | None = None
    depends_on: list[str] = field(default_factory=list)
    new_ai_entry: bool = False
    current_truth_allowed: bool = True
    notes: str | None = None


@dataclass(frozen=True)
class MetabolicFinding:
    code: str
    status: Literal["READY_WITHOUT_AUTHORIZATION", "DEGRADED", "BLOCKED"]
    message: str
    artifact_id: str | None = None
    repair_action: str | None = None


@dataclass(frozen=True)
class GeneratedRegistry:
    generated_at: str
    repo_root: str
    records: list[ArtifactRecord] = field(default_factory=list)
    findings: list[MetabolicFinding] = field(default_factory=list)
