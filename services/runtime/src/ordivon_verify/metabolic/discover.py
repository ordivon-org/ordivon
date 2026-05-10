"""Auto-discovery of artifacts by convention patterns.

First version uses convention-based rules to classify files into artifact types.
Does not read file contents deeply — it classifies by path/name patterns.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path

from ordivon_verify.metabolic.models import (
    ArtifactRecord,
    ArtifactTemperature,
    AuthorityTier,
    LifecycleState,
)

_CONVENTION_RULES: list[tuple[str, str, AuthorityTier, LifecycleState, ArtifactTemperature]] = [
    ("*.schema.json", "schema", AuthorityTier.T1_ACTIVE_SPEC, LifecycleState.ACTIVE, ArtifactTemperature.WARM),
    (
        "*receipt*.md",
        "receipt",
        AuthorityTier.T2_ACTIVE_RUNTIME_EVIDENCE,
        LifecycleState.ACTIVE,
        ArtifactTemperature.HOT,
    ),
    (
        "*ledger*.jsonl",
        "ledger",
        AuthorityTier.T2_ACTIVE_RUNTIME_EVIDENCE,
        LifecycleState.ACTIVE,
        ArtifactTemperature.HOT,
    ),
    ("SKILL.md", "skill", AuthorityTier.T1_ACTIVE_SPEC, LifecycleState.ACTIVE, ArtifactTemperature.WARM),
    ("*manifest*.json", "manifest", AuthorityTier.T1_ACTIVE_SPEC, LifecycleState.ACTIVE, ArtifactTemperature.WARM),
    (
        "CURRENT_TRUTH.md",
        "current_truth",
        AuthorityTier.T0_CURRENT_TRUTH,
        LifecycleState.ACTIVE,
        ArtifactTemperature.HOT,
    ),
    (
        "PROJECT_AI_LOCALIZATION.md",
        "onboarding_doc",
        AuthorityTier.T1_ACTIVE_SPEC,
        LifecycleState.ACTIVE,
        ArtifactTemperature.WARM,
    ),
    (
        "AI_TRUST_LEVELS.md",
        "active_spec",
        AuthorityTier.T1_ACTIVE_SPEC,
        LifecycleState.ACTIVE,
        ArtifactTemperature.WARM,
    ),
    (
        "*closure*.md",
        "receipt",
        AuthorityTier.T2_ACTIVE_RUNTIME_EVIDENCE,
        LifecycleState.ACTIVE,
        ArtifactTemperature.WARM,
    ),
    ("*seal*.md", "receipt", AuthorityTier.T2_ACTIVE_RUNTIME_EVIDENCE, LifecycleState.ACTIVE, ArtifactTemperature.WARM),
    ("*.verify.json", "config", AuthorityTier.T0_CURRENT_TRUTH, LifecycleState.ACTIVE, ArtifactTemperature.HOT),
    ("*ordivon.verify.json", "config", AuthorityTier.T0_CURRENT_TRUTH, LifecycleState.ACTIVE, ArtifactTemperature.HOT),
    (
        "*agent-claim*.jsonl",
        "evidence_ledger",
        AuthorityTier.T2_ACTIVE_RUNTIME_EVIDENCE,
        LifecycleState.ACTIVE,
        ArtifactTemperature.HOT,
    ),
    (
        "*debt-ledger*.jsonl",
        "ledger",
        AuthorityTier.T2_ACTIVE_RUNTIME_EVIDENCE,
        LifecycleState.ACTIVE,
        ArtifactTemperature.HOT,
    ),
    ("*gate-manifest*.json", "manifest", AuthorityTier.T1_ACTIVE_SPEC, LifecycleState.ACTIVE, ArtifactTemperature.WARM),
    (
        "*discovery-candidates*.json",
        "candidate",
        AuthorityTier.T3_CANDIDATE_PROPOSAL,
        LifecycleState.CANDIDATE,
        ArtifactTemperature.COLD,
    ),
    (
        "*candidate-rule*.jsonl",
        "candidate_rule",
        AuthorityTier.T3_CANDIDATE_PROPOSAL,
        LifecycleState.CANDIDATE,
        ArtifactTemperature.COLD,
    ),
    (
        "*lesson*.jsonl",
        "ledger",
        AuthorityTier.T2_ACTIVE_RUNTIME_EVIDENCE,
        LifecycleState.ACTIVE,
        ArtifactTemperature.WARM,
    ),
    (
        "*onboarding*.md",
        "onboarding_doc",
        AuthorityTier.T1_ACTIVE_SPEC,
        LifecycleState.ACTIVE,
        ArtifactTemperature.WARM,
    ),
    ("*playbook*.md", "onboarding_doc", AuthorityTier.T1_ACTIVE_SPEC, LifecycleState.ACTIVE, ArtifactTemperature.WARM),
    ("*quickstart*.md", "quickstart", AuthorityTier.T1_ACTIVE_SPEC, LifecycleState.ACTIVE, ArtifactTemperature.HOT),
    ("*alpha-0*.md", "product_doc", AuthorityTier.T1_ACTIVE_SPEC, LifecycleState.ACTIVE, ArtifactTemperature.HOT),
    (
        "generated-artifact-registry.json",
        "registry",
        AuthorityTier.T1_ACTIVE_SPEC,
        LifecycleState.ACTIVE,
        ArtifactTemperature.HOT,
    ),
    (
        "metabolic-summary.json",
        "report",
        AuthorityTier.T2_ACTIVE_RUNTIME_EVIDENCE,
        LifecycleState.ACTIVE,
        ArtifactTemperature.HOT,
    ),
]

_SKIP_PATTERNS = {
    ".git/",
    ".venv/",
    "__pycache__/",
    "node_modules/",
    ".tmp/",
    ".pytest_cache/",
    "__pycache__/",
}

_SKIP_EXTENSIONS = {".pyc", ".pyo", ".so", ".dll", ".exe", ".bin"}


def _compute_hash(path: Path) -> str | None:
    try:
        data = path.read_bytes()
        if len(data) > 1_000_000:
            return None
        return hashlib.sha256(data).hexdigest()[:16]
    except OSError:
        return None


def _matches_pattern(filename: str, pattern: str) -> bool:
    if pattern.startswith("*."):
        suffix = pattern[1:]
        return filename.endswith(suffix)
    if "*" in pattern:
        import fnmatch

        return fnmatch.fnmatch(filename, pattern)
    return filename == pattern


def _should_skip(rel: str) -> bool:
    for skip in _SKIP_PATTERNS:
        if skip in rel:
            return True
    return False


def _classify_file(path: Path, root: Path) -> ArtifactRecord | None:
    rel = _rel(path, root)
    filename = path.name
    if _should_skip(rel):
        return None
    if path.suffix in _SKIP_EXTENSIONS:
        return None
    for pattern, artifact_type, tier, lifecycle, temp in _CONVENTION_RULES:
        if _matches_pattern(filename, pattern):
            hash_val = _compute_hash(path)
            return ArtifactRecord(
                artifact_id=rel.replace("/", "-").replace(".", "-")[:120],
                path=rel,
                artifact_type=artifact_type,
                authority_tier=tier,
                lifecycle_state=lifecycle,
                temperature=temp,
                scope="discovered-by-convention",
                content_hash=hash_val,
                created_in_phase=None,
                last_verified=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                review_date=None,
                supersedes=[],
                superseded_by=None,
                depends_on=[],
                new_ai_entry=(artifact_type in ("current_truth", "onboarding_doc", "quickstart")),
                current_truth_allowed=(tier in (AuthorityTier.T0_CURRENT_TRUTH, AuthorityTier.T1_ACTIVE_SPEC)),
                notes=f"Auto-discovered by convention: matched pattern '{pattern}'",
            )
    return None


def _rel(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def discover_artifacts(root: Path) -> list[ArtifactRecord]:
    records: list[ArtifactRecord] = []
    if not root.is_dir():
        return records
    for p in sorted(root.rglob("*")):
        if not p.is_file():
            continue
        if p.suffix in _SKIP_EXTENSIONS:
            continue
        record = _classify_file(p, root)
        if record is not None:
            records.append(record)
    return records
