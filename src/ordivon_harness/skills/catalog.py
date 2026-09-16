from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from .model import EligibilityState, SkillRecord, SkillSource, TrustState
from .parser import SkillParseError, parse_skill_frontmatter


class SkillCatalogError(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True, slots=True)
class SkillResolution:
    resolved: SkillRecord
    shadowed: tuple[SkillRecord, ...]
    reason: str
    snapshot_revision: str


def _sha256(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _contained(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _canonical_snapshot_payload(records: Iterable[SkillRecord]) -> bytes:
    payload = [
        {
            "skillId": record.skill_id,
            "name": record.name,
            "description": record.description,
            "sourceId": record.source_id,
            "scope": record.scope,
            "priority": record.source_priority,
            "instructionDigest": record.instruction_digest,
            "trust": record.trust_state.value,
            "eligibility": record.eligibility_state.value,
        }
        for record in sorted(records, key=lambda item: item.skill_id)
    ]
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


class SkillCatalog:
    """Immutable raw inventory plus an admissible effective Skill projection."""

    def __init__(self, records: Iterable[SkillRecord]) -> None:
        inventory = tuple(sorted(records, key=lambda item: item.skill_id))
        seen: set[str] = set()
        for record in inventory:
            if record.skill_id in seen:
                raise SkillCatalogError("DUPLICATE_SKILL_ID", record.skill_id)
            seen.add(record.skill_id)
        self._inventory = inventory
        self._records = tuple(
            record
            for record in inventory
            if record.trust_state in {TrustState.TRUSTED, TrustState.APPROVED}
        )
        self.catalog_revision = _sha256(_canonical_snapshot_payload(inventory))
        self.snapshot_revision = _sha256(_canonical_snapshot_payload(self._records))

    @property
    def inventory(self) -> tuple[SkillRecord, ...]:
        return self._inventory

    @property
    def records(self) -> tuple[SkillRecord, ...]:
        return self._records

    @classmethod
    def scan(cls, sources: Iterable[SkillSource]) -> SkillCatalog:
        records: list[SkillRecord] = []
        for source in sources:
            if not source.enabled:
                continue
            records.extend(cls._scan_source(source))
        return cls(records)

    @staticmethod
    def _scan_source(source: SkillSource) -> list[SkillRecord]:
        try:
            root = source.root.resolve(strict=True)
        except FileNotFoundError:
            return []
        if not root.is_dir():
            return []

        records: list[SkillRecord] = []
        local_ids: set[str] = set()
        for main_resource in sorted(root.rglob("SKILL.md")):
            try:
                if not main_resource.is_file() or main_resource.is_symlink():
                    continue
                skill_root = main_resource.parent.resolve(strict=True)
                resolved_resource = main_resource.resolve(strict=True)
            except (FileNotFoundError, OSError):
                continue
            if not _contained(skill_root, root) or not _contained(resolved_resource, skill_root):
                continue
            try:
                body = resolved_resource.read_bytes()
            except OSError:
                continue
            try:
                parsed = parse_skill_frontmatter(body.decode("utf-8"))
            except (UnicodeDecodeError, SkillParseError):
                continue
            skill_id = f"{source.source_id}/{parsed.name}"
            if skill_id in local_ids:
                raise SkillCatalogError("DUPLICATE_SKILL_ID", skill_id)
            local_ids.add(skill_id)
            records.append(
                SkillRecord(
                    skill_id=skill_id,
                    name=parsed.name,
                    description=parsed.description,
                    source_id=source.source_id,
                    scope=source.scope,
                    source_priority=source.priority,
                    skill_root=skill_root,
                    main_resource=resolved_resource,
                    instruction_digest=_sha256(body),
                    trust_state=source.trust_state,
                    eligibility_state=EligibilityState.UNKNOWN,
                )
            )
        return records

    def by_skill_id(self, skill_id: str) -> SkillRecord:
        for record in self._records:
            if record.skill_id == skill_id:
                return record
        raise SkillCatalogError("SKILL_NOT_FOUND", skill_id)

    def candidates(self, name: str) -> tuple[SkillRecord, ...]:
        return tuple(record for record in self._records if record.name == name)

    def resolve(self, ref: str) -> SkillResolution:
        if "/" in ref:
            record = self.by_skill_id(ref)
            return SkillResolution(
                resolved=record,
                shadowed=(),
                reason="explicit-skill-id",
                snapshot_revision=self.snapshot_revision,
            )

        candidates = list(self.candidates(ref))
        if not candidates:
            raise SkillCatalogError("SKILL_NOT_FOUND", ref)
        candidates.sort(key=lambda item: (-item.source_priority, item.source_id, item.skill_id))
        winner = candidates[0]
        return SkillResolution(
            resolved=winner,
            shadowed=tuple(candidates[1:]),
            reason="source-priority" if len(candidates) > 1 else "only-candidate",
            snapshot_revision=self.snapshot_revision,
        )

    def search(self, query: str, *, limit: int = 20) -> tuple[SkillRecord, ...]:
        terms = tuple(term.casefold() for term in query.split() if term.strip())
        if not terms or limit <= 0:
            return ()

        def score(record: SkillRecord) -> tuple[int, int, str]:
            name = record.name.casefold()
            description = record.description.casefold()
            total = sum(5 for term in terms if term in name) + sum(
                1 for term in terms if term in description
            )
            return (total, record.source_priority, record.skill_id)

        ranked = [record for record in self._records if score(record)[0] > 0]
        ranked.sort(key=lambda record: (-score(record)[0], -record.source_priority, record.skill_id))
        return tuple(ranked[:limit])

    def read_text(
        self,
        skill_id: str,
        *,
        relative_path: str = "SKILL.md",
        expected_instruction_digest: str | None = None,
    ) -> tuple[str, str]:
        record = self.by_skill_id(skill_id)
        candidate = Path(relative_path)
        if candidate.is_absolute() or ".." in candidate.parts:
            raise SkillCatalogError("PATH_ESCAPE", relative_path)
        try:
            resolved = (record.skill_root / candidate).resolve(strict=True)
        except FileNotFoundError as exc:
            raise SkillCatalogError("RESOURCE_NOT_FOUND", relative_path) from exc
        if not _contained(resolved, record.skill_root):
            raise SkillCatalogError("PATH_ESCAPE", relative_path)
        if not resolved.is_file():
            raise SkillCatalogError("RESOURCE_NOT_FOUND", relative_path)
        data = resolved.read_bytes()
        digest = _sha256(data)
        if relative_path == "SKILL.md":
            expected = expected_instruction_digest or record.instruction_digest
            if digest != expected:
                raise SkillCatalogError("DIGEST_MISMATCH", skill_id)
        try:
            return data.decode("utf-8"), digest
        except UnicodeDecodeError as exc:
            raise SkillCatalogError("UNSUPPORTED_MEDIA_TYPE", relative_path) from exc
