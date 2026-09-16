from __future__ import annotations

import hashlib
import json
import mimetypes
import stat
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from .eligibility import observe_eligibility
from .model import (
    EligibilityState,
    SkillContext,
    SkillRecord,
    SkillSource,
    SourceHealth,
    SourceScanStatus,
    TrustState,
)
from .parser import SkillParseError, parse_skill_frontmatter
from .scanner import ScanState, scan_skill_package

ADMITTED_TRUST = {TrustState.TRUSTED, TrustState.APPROVED}
_SCOPE_RANK = {"project": 50, "workspace": 50, "user": 40, "vendor": 30, "plugin": 30, "managed": 10}
MAX_SKILL_MD_BYTES = 256 * 1024
MAX_RESOURCE_READ_BYTES = 1024 * 1024
MAX_PACKAGE_FILES = 512
MAX_PACKAGE_BYTES = 16 * 1024 * 1024
MAX_DIAGNOSTICS_PER_SOURCE = 32


class SkillCatalogError(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.detail = message


@dataclass(frozen=True, slots=True)
class SkillResolution:
    resolved: SkillRecord
    shadowed: tuple[SkillRecord, ...]
    reason: str
    snapshot_revision: str


@dataclass(frozen=True, slots=True)
class SkillView:
    records: tuple[SkillRecord, ...]
    snapshot_revision: str


@dataclass(frozen=True, slots=True)
class SkillReadResult:
    skill_id: str
    path: str
    media_type: str
    size: int
    digest: str
    instruction_digest: str
    package_revision: str
    content: str
    next_offset: int | None

    def value(self) -> dict:
        value = {
            "skillId": self.skill_id,
            "path": self.path,
            "mediaType": self.media_type,
            "size": self.size,
            "digest": self.digest,
            "instructionDigest": self.instruction_digest,
            "packageRevision": self.package_revision,
            "content": self.content,
        }
        if self.next_offset is not None:
            value["nextOffset"] = self.next_offset
        return value


def _sha256(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _contained(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _canonical_payload(records: Iterable[SkillRecord]) -> bytes:
    payload = [
        {
            "skillId": record.skill_id,
            "name": record.name,
            "description": record.description,
            "sourceId": record.source_id,
            "scope": record.scope,
            "sourceRelativeRoot": record.source_relative_root,
            "projectRoot": str(record.project_root) if record.project_root is not None else None,
            "instructionDigest": record.instruction_digest,
            "packageRevision": record.package_revision,
            "trust": record.trust_state.value,
            "eligibility": record.eligibility_state.value,
            "eligibilityReasons": list(record.eligibility_reasons),
            "scanState": record.scan_state,
            "implicitInvocation": record.implicit_invocation,
            "explicitInvocation": record.explicit_invocation,
        }
        for record in sorted(records, key=lambda item: item.skill_id)
    ]
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _prefix_denied(relative_root: str, prefixes: tuple[str, ...]) -> bool:
    rel = relative_root.strip("/")
    for prefix in prefixes:
        normalized = prefix.strip("/")
        if rel == normalized or rel.startswith(normalized + "/"):
            return True
    return False


def _infer_project_root(source: SkillSource, resolved_root: Path) -> Path | None:
    if source.scope not in {"project", "workspace"}:
        return None
    if source.project_root is not None:
        try:
            return source.project_root.resolve(strict=True)
        except FileNotFoundError:
            return source.project_root.resolve(strict=False)
    # Common Agent Skills project layout: <project>/.agents/skills
    if resolved_root.name == "skills" and resolved_root.parent.name in {".agents", ".codex", ".hermes"}:
        return resolved_root.parent.parent
    return resolved_root.parent


def _package_revision(root: Path) -> str:
    manifest: list[dict[str, object]] = []
    total_bytes = 0
    for candidate in sorted(root.rglob("*"), key=lambda p: p.as_posix()):
        relative = candidate.relative_to(root).as_posix()
        try:
            lst = candidate.lstat()
        except OSError as exc:
            raise SkillCatalogError("PACKAGE_CHANGED", f"cannot stat package entry: {relative}") from exc
        if stat.S_ISLNK(lst.st_mode):
            raise SkillCatalogError("PATH_ESCAPE", f"symlink package entry rejected: {relative}")
        if stat.S_ISDIR(lst.st_mode):
            continue
        if not stat.S_ISREG(lst.st_mode):
            raise SkillCatalogError("SKILL_INVALID", f"non-regular package entry rejected: {relative}")
        if len(manifest) >= MAX_PACKAGE_FILES:
            raise SkillCatalogError("PACKAGE_TOO_LARGE", f"package exceeds {MAX_PACKAGE_FILES} files")
        data = candidate.read_bytes()
        total_bytes += len(data)
        if total_bytes > MAX_PACKAGE_BYTES:
            raise SkillCatalogError("PACKAGE_TOO_LARGE", f"package exceeds {MAX_PACKAGE_BYTES} bytes")
        manifest.append(
            {
                "path": relative,
                "type": "file",
                "size": len(data),
                "executable": bool(lst.st_mode & 0o111),
                "sha256": _sha256(data),
            }
        )
    canonical = json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return _sha256(canonical)


def _context_applies(record: SkillRecord, context: SkillContext | None) -> bool:
    if record.scope not in {"project", "workspace"}:
        return True
    if record.project_root is None or context is None:
        return False
    workspace = context.normalized_workspace_path()
    if workspace is None:
        return False
    try:
        project_root = record.project_root.resolve(strict=False)
    except OSError:
        project_root = record.project_root.absolute()
    return _contained(workspace, project_root) or workspace == project_root

def _precedence_key(record: SkillRecord) -> tuple[int, int, str, str]:
    return (
        -_SCOPE_RANK.get(record.scope, 0),
        -record.source_priority,
        record.source_id,
        record.skill_id,
    )


def _effective_records(records: Iterable[SkillRecord]) -> tuple[SkillRecord, ...]:
    by_name: dict[str, list[SkillRecord]] = {}
    for record in records:
        by_name.setdefault(record.name, []).append(record)
    winners = [min(rows, key=_precedence_key) for rows in by_name.values()]
    return tuple(sorted(winners, key=lambda record: record.skill_id))



class SkillCatalog:
    """Federated raw inventory with context-specific effective projections."""

    def __init__(
        self,
        records: Iterable[SkillRecord],
        *,
        source_statuses: Iterable[SourceScanStatus] = (),
    ) -> None:
        inventory = tuple(sorted(records, key=lambda item: item.skill_id))
        seen: set[str] = set()
        for record in inventory:
            if record.skill_id in seen:
                raise SkillCatalogError("DUPLICATE_SKILL_ID", record.skill_id)
            seen.add(record.skill_id)
        self._inventory = inventory
        self._source_statuses = tuple(sorted(source_statuses, key=lambda item: item.source_id))
        self.catalog_revision = _sha256(_canonical_payload(inventory))

    @property
    def inventory(self) -> tuple[SkillRecord, ...]:
        return self._inventory

    @property
    def source_statuses(self) -> tuple[SourceScanStatus, ...]:
        return self._source_statuses

    @classmethod
    def scan(cls, sources: Iterable[SkillSource]) -> SkillCatalog:
        records: list[SkillRecord] = []
        statuses: list[SourceScanStatus] = []
        seen_source_ids: set[str] = set()
        for source in sources:
            if source.source_id in seen_source_ids:
                statuses.append(
                    SourceScanStatus(
                        source_id=source.source_id,
                        health=SourceHealth.DEGRADED,
                        discovered=0,
                        valid=0,
                        invalid=1,
                        quarantined=0,
                        admitted=0,
                        diagnostics=("duplicate configured sourceId; later source ignored",),
                    )
                )
                continue
            seen_source_ids.add(source.source_id)
            source_records, status = cls._scan_source(source)
            records.extend(source_records)
            statuses.append(status)
        return cls(records, source_statuses=statuses)

    @staticmethod
    def _scan_source(source: SkillSource) -> tuple[list[SkillRecord], SourceScanStatus]:
        if not source.enabled:
            return [], SourceScanStatus(
                source_id=source.source_id, health=SourceHealth.DISABLED, discovered=0, valid=0,
                invalid=0, quarantined=0, admitted=0
            )
        try:
            root = source.root.resolve(strict=True)
        except (FileNotFoundError, OSError):
            return [], SourceScanStatus(
                source_id=source.source_id,
                health=SourceHealth.UNAVAILABLE,
                discovered=0,
                valid=0,
                invalid=0,
                quarantined=0,
                admitted=0,
                diagnostics=(f"source root unavailable: {source.root}",),
            )
        if not root.is_dir():
            return [], SourceScanStatus(
                source_id=source.source_id,
                health=SourceHealth.UNAVAILABLE,
                discovered=0,
                valid=0,
                invalid=0,
                quarantined=0,
                admitted=0,
                diagnostics=(f"source root is not a directory: {source.root}",),
            )

        project_root = _infer_project_root(source, root)
        records: list[SkillRecord] = []
        diagnostics: list[str] = []
        local_ids: set[str] = set()
        discovered = valid = invalid = quarantined = 0
        try:
            candidates = sorted(root.rglob("SKILL.md"), key=lambda p: p.as_posix())
        except OSError as exc:
            return [], SourceScanStatus(
                source_id=source.source_id,
                health=SourceHealth.UNAVAILABLE,
                discovered=0,
                valid=0,
                invalid=0,
                quarantined=0,
                admitted=0,
                diagnostics=(f"source traversal failed: {type(exc).__name__}",),
            )

        for main_resource in candidates:
            discovered += 1
            relative_display = main_resource.relative_to(root).as_posix()
            try:
                lst = main_resource.lstat()
                if stat.S_ISLNK(lst.st_mode) or not stat.S_ISREG(lst.st_mode):
                    raise SkillCatalogError("SKILL_INVALID", "SKILL.md must be a regular non-symlink file")
                skill_root = main_resource.parent.resolve(strict=True)
                resolved_resource = main_resource.resolve(strict=True)
                if not _contained(skill_root, root) or not _contained(resolved_resource, skill_root):
                    raise SkillCatalogError("PATH_ESCAPE", "Skill root/resource escapes configured source")
                body = resolved_resource.read_bytes()
                if len(body) > MAX_SKILL_MD_BYTES:
                    raise SkillCatalogError("RESOURCE_TOO_LARGE", "SKILL.md exceeds hard size limit")
                decoded = body.decode("utf-8")
                parsed = parse_skill_frontmatter(
                    decoded,
                    validation_mode=source.validation_mode,
                    expected_directory_name=skill_root.name,
                )
                skill_id = f"{source.source_id}/{parsed.name}"
                if skill_id in local_ids:
                    raise SkillCatalogError("DUPLICATE_SKILL_ID", skill_id)
                package_revision = _package_revision(skill_root)
                source_relative_root = skill_root.relative_to(root).as_posix()
                local_ids.add(skill_id)
                implicit = not _prefix_denied(source_relative_root, source.implicit_deny_prefixes)
                explicit = not _prefix_denied(source_relative_root, source.explicit_deny_prefixes)
                eligibility = observe_eligibility(decoded, source.eligibility_adapter)
                scan = scan_skill_package(skill_root)
                if scan.state == ScanState.QUARANTINED:
                    quarantined += 1
                records.append(
                    SkillRecord(
                        skill_id=skill_id,
                        name=parsed.name,
                        description=parsed.description,
                        source_id=source.source_id,
                        scope=source.scope,
                        source_priority=source.priority,
                        source_relative_root=source_relative_root,
                        skill_root=skill_root,
                        main_resource=resolved_resource,
                        project_root=project_root,
                        instruction_digest=_sha256(body),
                        package_revision=package_revision,
                        trust_state=source.trust_state,
                        eligibility_state=eligibility.state,
                        eligibility_reasons=eligibility.reasons,
                        scan_state=scan.state.value,
                        scan_findings=scan.findings,
                        implicit_invocation=implicit,
                        explicit_invocation=explicit,
                        diagnostics=parsed.diagnostics,
                    )
                )
                valid += 1
            except (UnicodeDecodeError, SkillParseError, SkillCatalogError, OSError) as exc:
                invalid += 1
                if len(diagnostics) < MAX_DIAGNOSTICS_PER_SOURCE:
                    code = getattr(exc, "code", type(exc).__name__)
                    diagnostics.append(f"{relative_display}: {code}: {exc}")
                continue

        health = SourceHealth.READY if invalid == 0 else SourceHealth.DEGRADED
        admitted = sum(
            record.trust_state in ADMITTED_TRUST and record.scan_state != ScanState.QUARANTINED.value
            for record in records
        )
        return records, SourceScanStatus(
            source_id=source.source_id,
            health=health,
            discovered=discovered,
            valid=valid,
            invalid=invalid,
            quarantined=quarantined,
            admitted=admitted,
            diagnostics=tuple(diagnostics),
        )

    def view(
        self,
        *,
        context: SkillContext | None = None,
        invocation_mode: str = "implicit",
        include_ineligible: bool = False,
    ) -> SkillView:
        if invocation_mode not in {"implicit", "explicit"}:
            raise ValueError("invocation_mode must be implicit or explicit")
        records: list[SkillRecord] = []
        for record in self._inventory:
            if record.trust_state not in ADMITTED_TRUST:
                continue
            if record.scan_state == ScanState.QUARANTINED.value:
                continue
            if not _context_applies(record, context):
                continue
            if invocation_mode == "implicit" and not record.implicit_invocation:
                continue
            if invocation_mode == "explicit" and not record.explicit_invocation:
                continue
            if not include_ineligible and record.eligibility_state == EligibilityState.BLOCKED:
                continue
            records.append(record)
        context_payload = {
            "workspacePath": str(context.normalized_workspace_path()) if context and context.workspace_path else None,
            "workspaceId": context.workspace_id if context else None,
            "agentId": context.agent_id if context else None,
            "invocationMode": invocation_mode,
            "records": json.loads(_canonical_payload(records)),
        }
        snapshot = _sha256(json.dumps(context_payload, sort_keys=True, separators=(",", ":")).encode())
        return SkillView(tuple(records), snapshot)

    def effective(
        self,
        *,
        context: SkillContext | None = None,
        invocation_mode: str = "implicit",
    ) -> SkillView:
        raw = self.view(context=context, invocation_mode=invocation_mode)
        return SkillView(_effective_records(raw.records), raw.snapshot_revision)

    def by_skill_id(
        self,
        skill_id: str,
        *,
        context: SkillContext | None = None,
        invocation_mode: str = "explicit",
    ) -> SkillRecord:
        view = self.view(context=context, invocation_mode=invocation_mode)
        for record in view.records:
            if record.skill_id == skill_id:
                return record
        for record in self._inventory:
            if record.skill_id != skill_id:
                continue
            if record.scan_state == ScanState.QUARANTINED.value:
                raise SkillCatalogError("SKILL_QUARANTINED", skill_id)
            if record.eligibility_state == EligibilityState.BLOCKED:
                detail = "; ".join(record.eligibility_reasons) or skill_id
                raise SkillCatalogError("SKILL_INELIGIBLE", detail)
            raise SkillCatalogError("SKILL_NOT_VISIBLE", skill_id)
        raise SkillCatalogError("SKILL_NOT_FOUND", skill_id)

    def candidates(
        self,
        name: str,
        *,
        context: SkillContext | None = None,
        invocation_mode: str = "implicit",
    ) -> tuple[SkillRecord, ...]:
        view = self.view(context=context, invocation_mode=invocation_mode)
        return tuple(record for record in view.records if record.name == name)

    def resolve(
        self,
        ref: str,
        *,
        context: SkillContext | None = None,
        invocation_mode: str = "explicit",
        expected_snapshot_revision: str | None = None,
    ) -> SkillResolution:
        view = self.view(context=context, invocation_mode=invocation_mode)
        if expected_snapshot_revision is not None and view.snapshot_revision != expected_snapshot_revision:
            raise SkillCatalogError("SNAPSHOT_STALE", f"expected {expected_snapshot_revision}, current {view.snapshot_revision}")
        if "/" in ref:
            record = self.by_skill_id(ref, context=context, invocation_mode=invocation_mode)
            return SkillResolution(record, (), "explicit-skill-id", view.snapshot_revision)

        candidates = [record for record in view.records if record.name == ref]
        if not candidates:
            same_name = [record for record in self._inventory if record.name == ref]
            if any(
                record.trust_state in ADMITTED_TRUST
                and record.scan_state != ScanState.QUARANTINED.value
                and _context_applies(record, context)
                and record.eligibility_state == EligibilityState.BLOCKED
                for record in same_name
            ):
                reasons = sorted(
                    {
                        reason
                        for record in same_name
                        if record.eligibility_state == EligibilityState.BLOCKED
                        for reason in record.eligibility_reasons
                    }
                )
                raise SkillCatalogError("SKILL_INELIGIBLE", "; ".join(reasons) or ref)
            if any(
                record.trust_state in ADMITTED_TRUST
                and record.scan_state == ScanState.QUARANTINED.value
                and _context_applies(record, context)
                for record in same_name
            ):
                raise SkillCatalogError("SKILL_QUARANTINED", ref)
            if same_name:
                raise SkillCatalogError("SKILL_NOT_VISIBLE", ref)
            raise SkillCatalogError("SKILL_NOT_FOUND", ref)
        candidates.sort(key=_precedence_key)
        winner = candidates[0]
        return SkillResolution(
            winner,
            tuple(candidates[1:]),
            f"scope={winner.scope}; sourceOrder={winner.source_id}",
            view.snapshot_revision,
        )

    def search(
        self,
        query: str,
        *,
        context: SkillContext | None = None,
        limit: int = 20,
        invocation_mode: str = "implicit",
    ) -> tuple[SkillRecord, ...]:
        if not query.strip() or not (1 <= limit <= 100):
            return ()
        terms = tuple(dict.fromkeys(term.casefold() for term in query.split() if term.strip()))
        view = self.effective(context=context, invocation_mode=invocation_mode)

        def score(record: SkillRecord) -> tuple[int, int, str]:
            name = record.name.casefold()
            description = record.description.casefold()
            total = 0
            for term in terms:
                if term == name:
                    total += 100
                elif term in name:
                    total += 20
                if term in description:
                    total += 5
            return total, record.source_priority, record.skill_id

        ranked = [record for record in view.records if score(record)[0] > 0]
        ranked.sort(key=lambda record: (-score(record)[0], -record.source_priority, record.skill_id))
        return tuple(ranked[:limit])

    def read_text(
        self,
        skill_id: str,
        *,
        relative_path: str = "SKILL.md",
        context: SkillContext | None = None,
        expected_instruction_digest: str | None = None,
        expected_package_revision: str | None = None,
        expected_snapshot_revision: str | None = None,
        offset: int = 0,
        max_bytes: int = MAX_RESOURCE_READ_BYTES,
    ) -> SkillReadResult:
        if offset < 0 or not (1 <= max_bytes <= MAX_RESOURCE_READ_BYTES):
            raise ValueError("invalid read bounds")
        view = self.view(context=context, invocation_mode="explicit")
        if expected_snapshot_revision is not None and view.snapshot_revision != expected_snapshot_revision:
            raise SkillCatalogError("SNAPSHOT_STALE", f"expected {expected_snapshot_revision}, current {view.snapshot_revision}")
        record = self.by_skill_id(skill_id, context=context, invocation_mode="explicit")
        candidate = Path(relative_path)
        if "\x00" in relative_path or "\\" in relative_path or candidate.is_absolute() or ".." in candidate.parts:
            raise SkillCatalogError("PATH_ESCAPE", relative_path)
        try:
            resolved = (record.skill_root / candidate).resolve(strict=True)
        except FileNotFoundError as exc:
            raise SkillCatalogError("RESOURCE_NOT_FOUND", relative_path) from exc
        if not _contained(resolved, record.skill_root) or resolved.is_symlink() or not resolved.is_file():
            raise SkillCatalogError("PATH_ESCAPE", relative_path)

        current_instruction = record.main_resource.read_bytes()
        current_instruction_digest = _sha256(current_instruction)
        instruction_fence = expected_instruction_digest or record.instruction_digest
        if current_instruction_digest != instruction_fence:
            raise SkillCatalogError("DIGEST_MISMATCH", f"SKILL.md changed for {skill_id}")

        current_package_revision = _package_revision(record.skill_root)
        package_fence = expected_package_revision or record.package_revision
        if current_package_revision != package_fence:
            raise SkillCatalogError("PACKAGE_CHANGED", f"Skill package changed for {skill_id}")

        data = resolved.read_bytes()
        if len(data) > MAX_RESOURCE_READ_BYTES:
            raise SkillCatalogError("RESOURCE_TOO_LARGE", relative_path)
        chunk = data[offset : offset + max_bytes]
        try:
            content = chunk.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise SkillCatalogError("UNSUPPORTED_MEDIA_TYPE", relative_path) from exc
        media_type = mimetypes.guess_type(resolved.name)[0] or "text/plain"
        if resolved.suffix.lower() in {".md", ".markdown"}:
            media_type = "text/markdown"
        next_offset = offset + len(chunk) if offset + len(chunk) < len(data) else None
        return SkillReadResult(
            skill_id=skill_id,
            path=candidate.as_posix(),
            media_type=media_type,
            size=len(data),
            digest=_sha256(data),
            instruction_digest=current_instruction_digest,
            package_revision=current_package_revision,
            content=content,
            next_offset=next_offset,
        )
