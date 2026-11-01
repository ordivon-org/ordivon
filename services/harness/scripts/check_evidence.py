#!/usr/bin/env python3
"""Validate Harness evidence/file correspondence and revision/currentness bindings."""

from __future__ import annotations

import atexit
from functools import lru_cache
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
import tomllib

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "evidence"
_VERIFIED_IMPLEMENTATION_PATHS = (
    "src/",
    "pyproject.toml",
    "uv.lock",
    "scripts/harness_p0_scale_acceptance.py",
)
_SCOPED_VERIFIED_IMPLEMENTATION_PATHS = (
    "src/",
    "scripts/harness_p0_scale_acceptance.py",
)
_RUNTIME_DEPENDENCY_CLOSURE_KIND = "ordivon.harness-runtime-dependency-closure"
_RUNTIME_DEPENDENCY_INVALIDATOR = "@runtime-dependency-closure"
_SOURCE_HISTORY_BOUNDARY_INVALIDATOR = "@source-revision-outside-current-repository"
# Exact first monorepo introduction of the legacy Harness evidence files.
# This anchors RETENTION of archived bytes; it does not certify the original
# standalone repo, current implementation, or any live environment effect.
_HARNESS_HISTORICAL_IMPORT = "a548b7884bd8981548ff63e8976e484501ee0c52"
# Pinned native Git witness from the ORIGINAL independent Harness repository.
# The old source tree is not a monorepo ancestor; never fetch mutable HEAD as
# an authority substitute, and never use this historical proof as CURRENT.
_HARNESS_ORIGINAL_SOURCE_REPO = "https://github.com/ordivon-org/ordivon-harness.git"
_HARNESS_ORIGINAL_SOURCE_CUT = "62ebeb00728ea0b16bbf644734b8928438ff7cd1"
_INDEX_REVISION_HINT_FIELDS = (
    "implementationSourceRevision",
    "implementationRevision",
    "sourceRevision",
    "prebindingRevision",
    "repairCommit",
)


def _canonical_payload_digest(value: dict[str, object]) -> str:
    payload = dict(value)
    payload.pop("integrity", None)
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _path_matches_scope(path: str, scope: str) -> bool:
    if scope.endswith("/"):
        return path.startswith(scope)
    return path == scope


def _normalize_implementation_paths(value: object) -> tuple[str, ...] | None:
    if value is None:
        return None
    if not isinstance(value, list) or not value:
        raise ValueError("implementationPaths must be a non-empty array")
    normalized: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item or item.startswith("/"):
            raise ValueError("implementationPaths entries must be non-empty relative strings")
        parts = item.rstrip("/").split("/")
        if any(part in {"", ".", ".."} for part in parts):
            raise ValueError(f"invalid implementationPaths entry: {item}")
        if not any(
            _path_matches_scope(item.rstrip("/"), root.rstrip("/"))
            or _path_matches_scope(item, root)
            for root in _SCOPED_VERIFIED_IMPLEMENTATION_PATHS
        ):
            raise ValueError(
                f"implementationPaths entry is outside verified implementation roots: {item}"
            )
        normalized.append(item)
    if len(normalized) != len(set(normalized)):
        raise ValueError("implementationPaths entries must be unique")
    if not any(item.startswith("src/") for item in normalized):
        raise ValueError("scoped verified evidence must bind at least one src/ implementation path")
    return tuple(normalized)


def _validate_revision_token(revision: str) -> None:
    if (
        not isinstance(revision, str)
        or not revision
        or revision.startswith("-")
        or any(ch.isspace() for ch in revision)
    ):
        raise ValueError("revision must be a non-empty Git revision token")


def _git_repository_root() -> Path:
    return Path(
        subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=ROOT,
            text=True,
            encoding="utf-8",
        ).strip()
    )


def _git_owner_prefix() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "--show-prefix"],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
    ).strip()


def _git_owner_path_at_revision(
    revision: str,
    relative_path: str,
    *,
    required: bool,
) -> str | None:
    _validate_revision_token(revision)
    normalized = relative_path.rstrip("/")
    if (
        not normalized
        or normalized.startswith("/")
        or any(part in {"", ".", ".."} for part in normalized.split("/"))
    ):
        raise ValueError(f"invalid owner-relative Git path: {relative_path}")
    prefix = _git_owner_prefix()
    candidates = ([f"{prefix}{normalized}"] if prefix else []) + [normalized]
    repository_root = _git_repository_root()
    for candidate in dict.fromkeys(candidates):
        exists = subprocess.run(
            ["git", "cat-file", "-e", f"{revision}:{candidate}"],
            cwd=repository_root,
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        if exists.returncode == 0:
            return candidate
    if required:
        raise ValueError(
            f"owner-relative Git path is absent at revision: revision={revision} path={relative_path}"
        )
    return None


def _git_file_bytes(revision: str, relative_path: str) -> bytes:
    repository_root = _git_repository_root()
    resolved = _git_owner_path_at_revision(revision, relative_path, required=True)
    assert resolved is not None
    return subprocess.check_output(
        ["git", "show", f"{revision}:{resolved}"],
        cwd=repository_root,
    )


def _git_scope_entries(revision: str, scope: str) -> dict[str, str]:
    repository_root = _git_repository_root()
    resolved = _git_owner_path_at_revision(revision, scope, required=False)
    if resolved is None:
        return {}
    prefix = _git_owner_prefix()
    owner_base = prefix if prefix and resolved.startswith(prefix) else ""
    output = subprocess.check_output(
        ["git", "ls-tree", "-r", revision, "--", resolved],
        cwd=repository_root,
        text=True,
        encoding="utf-8",
    )
    entries: dict[str, str] = {}
    for line in output.splitlines():
        metadata, path = line.split("\t", 1)
        if owner_base:
            if not path.startswith(owner_base):
                raise ValueError(f"Git path escaped owner prefix: prefix={owner_base} path={path}")
            path = path[len(owner_base) :]
        entries[path] = metadata
    return entries


def _git_creation_revisions(relative_path: str) -> list[str]:
    repository_root = _git_repository_root()
    prefix = _git_owner_prefix()
    candidates = [relative_path]
    if prefix:
        candidates.append(f"{prefix}{relative_path}")
    for candidate in candidates:
        revisions = subprocess.check_output(
            [
                "git",
                "log",
                "--full-history",
                "HEAD",
                "--diff-filter=A",
                "--format=%H",
                "--",
                candidate,
            ],
            cwd=repository_root,
            text=True,
            encoding="utf-8",
        ).splitlines()
        if revisions:
            return revisions
    return []


def _runtime_dependency_closure_projection(revision: str) -> dict[str, object]:
    lock = tomllib.loads(_git_file_bytes(revision, "uv.lock").decode("utf-8"))
    packages = [item for item in lock.get("package", []) if isinstance(item, dict)]
    by_name: dict[str, dict[str, object]] = {}
    for package in packages:
        name = str(package.get("name") or "").lower()
        if not name:
            raise ValueError("uv.lock contains a package without a name")
        if name in by_name:
            raise ValueError(f"uv.lock contains ambiguous duplicate package name: {name}")
        by_name[name] = package

    root = by_name.get("ordivon-harness")
    if root is None:
        raise ValueError("uv.lock omits the Harness root package")

    def normalized_dependency_rows(value: object) -> list[dict[str, object]]:
        if not isinstance(value, list):
            return []
        rows = [dict(item) for item in value if isinstance(item, dict)]
        return sorted(
            rows,
            key=lambda item: json.dumps(
                item, ensure_ascii=False, sort_keys=True, separators=(",", ":")
            ),
        )

    root_dependencies = normalized_dependency_rows(root.get("dependencies"))
    pending = [
        str(item.get("name") or "").lower()
        for item in root_dependencies
        if isinstance(item.get("name"), str)
    ]
    reachable: set[str] = set()
    while pending:
        name = pending.pop()
        if not name or name in reachable:
            continue
        package = by_name.get(name)
        if package is None:
            raise ValueError(f"runtime dependency is absent from uv.lock: {name}")
        reachable.add(name)
        pending.extend(
            str(item.get("name") or "").lower()
            for item in normalized_dependency_rows(package.get("dependencies"))
            if isinstance(item.get("name"), str)
        )

    metadata = root.get("metadata")
    root_requirements = normalized_dependency_rows(
        metadata.get("requires-dist") if isinstance(metadata, dict) else None
    )
    closure_packages: list[dict[str, object]] = []
    for name in sorted(reachable):
        package = by_name[name]
        closure_packages.append(
            {
                "name": name,
                "version": str(package.get("version") or ""),
                "source": dict(package.get("source") or {}),
                "dependencies": normalized_dependency_rows(package.get("dependencies")),
            }
        )
    return {
        "schemaVersion": 1,
        "kind": _RUNTIME_DEPENDENCY_CLOSURE_KIND,
        "rootPackage": "ordivon-harness",
        "rootDependencies": root_dependencies,
        "rootRequirements": root_requirements,
        "packages": closure_packages,
    }


def _runtime_python_compatibility_projection(
    revision: str,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Track Python requirements without changing historical dependency digests.

    Existing evidence receipts pin the prior digest algorithm and its bytes.
    The independent compatibility check catches otherwise invisible drift.
    """
    project = tomllib.loads(_git_file_bytes(revision, "pyproject.toml").decode("utf-8"))
    lock = tomllib.loads(_git_file_bytes(revision, "uv.lock").decode("utf-8"))
    metadata = project.get("project")
    project_requirement = metadata.get("requires-python") if isinstance(metadata, dict) else None
    normalized: list[tuple[str, ...]] = []
    for source, requirement in (
        ("pyproject.toml", project_requirement),
        ("uv.lock", lock.get("requires-python")),
    ):
        if not isinstance(requirement, str) or not requirement.strip():
            raise ValueError(f"{source} omits requires-python")
        specifiers = tuple(sorted("".join(part.split()) for part in requirement.split(",")))
        if any(not part for part in specifiers):
            raise ValueError(f"{source} has an invalid requires-python specifier")
        normalized.append(specifiers)
    return normalized[0], normalized[1]


def _runtime_dependency_closure_digest(revision: str) -> str:
    encoded = json.dumps(
        _runtime_dependency_closure_projection(revision),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _valid_sha256_digest(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 71
        and value.startswith("sha256:")
        and all(ch in "0123456789abcdef" for ch in value[7:])
    )


def _invalidating_paths(
    revision_from: str,
    revision_to: str,
    implementation_paths: tuple[str, ...] | None = None,
) -> list[str]:
    scopes = implementation_paths or _VERIFIED_IMPLEMENTATION_PATHS
    changed: set[str] = set()
    for scope in scopes:
        before = _git_scope_entries(revision_from, scope)
        after = _git_scope_entries(revision_to, scope)
        for path in before.keys() | after.keys():
            if before.get(path) != after.get(path):
                changed.add(path)
    return sorted(changed)


def _is_original_harness_source_revision(revision: str) -> bool:
    """Detect old source-root identity independent of Git history depth.

    In complete CI Git history an old standalone source revision can be an
    ancestor of monorepo HEAD, yet its source-root namespace is different.
    """
    if len(revision) != 40 or any(c not in "0123456789abcdef" for c in revision):
        return False
    old_tree = subprocess.run(
        ["git", "--no-replace-objects", "cat-file", "-e", f"{revision}:src/ordivon_harness"],
        cwd=ROOT,
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    imported_tree = subprocess.run(
        [
            "git",
            "--no-replace-objects",
            "cat-file",
            "-e",
            f"{revision}:services/harness/src/ordivon_harness",
        ],
        cwd=ROOT,
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return old_tree.returncode == 0 and imported_tree.returncode != 0


def _verified_revision_is_current(
    revision: str,
    implementation_paths: tuple[str, ...] | None = None,
    runtime_dependency_closure_digest: str | None = None,
) -> tuple[bool, list[str]]:
    if _is_original_harness_source_revision(revision):
        # Original source namespace is not current after monorepo import,
        # even if complete Git history makes this commit an ancestor.
        return False, [_SOURCE_HISTORY_BOUNDARY_INVALIDATOR]
    ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", revision, "HEAD"],
        cwd=ROOT,
        check=False,
    )
    if ancestor.returncode != 0:
        # Missing/unqualified history never proves current implementation.
        return False, [_SOURCE_HISTORY_BOUNDARY_INVALIDATOR]
    invalidating = _invalidating_paths(revision, "HEAD", implementation_paths)
    if implementation_paths is None:
        if runtime_dependency_closure_digest is not None:
            raise ValueError("unscoped currentness cannot bind a scoped runtime dependency digest")
    else:
        if not _valid_sha256_digest(runtime_dependency_closure_digest):
            raise ValueError(
                "scoped currentness requires a valid runtime dependency closure digest"
            )
        historical = _runtime_dependency_closure_digest(revision)
        if historical != runtime_dependency_closure_digest:
            raise ValueError(
                "scoped runtime dependency digest differs from its implementation revision"
            )
        if _runtime_dependency_closure_digest(
            "HEAD"
        ) != runtime_dependency_closure_digest or _runtime_python_compatibility_projection(
            revision
        ) != _runtime_python_compatibility_projection("HEAD"):
            invalidating.append(_RUNTIME_DEPENDENCY_INVALIDATOR)
    return not invalidating, invalidating


def _original_source_git_environment() -> dict[str, str]:
    """Keep an independent source repository free of caller Git-graph overrides."""
    disallowed = {
        "GIT_SHALLOW_FILE",
        "GIT_NO_LAZY_FETCH",
        "GIT_DIR",
        "GIT_WORK_TREE",
        "GIT_COMMON_DIR",
        "GIT_OBJECT_DIRECTORY",
        "GIT_ALTERNATE_OBJECT_DIRECTORIES",
        "GIT_INDEX_FILE",
        "GIT_GRAFT_FILE",
        "GIT_REPLACE_REF_BASE",
    }
    return {
        key: value
        for key, value in os.environ.items()
        if key not in disallowed and not key.startswith("GIT_CONFIG_")
    }


def _local_pinned_original_source_graph(directory: Path) -> bool:
    """Build an isolated, complete original Git DAG from pinned local objects.

    This does NOT turn a monorepo ancestry check into a source proof. Git
    transfers exactly the hardcoded original *commit object* (including its
    immutable parents and trees) into a new bare object database. Neither
    current HEAD, a tree-prefix rewrite, alternate objects, nor local Git
    grafts/replace refs are admitted as the original-source identity.
    """
    environment = _original_source_git_environment()
    environment["GIT_NO_LAZY_FETCH"] = "1"
    try:
        source = subprocess.check_output(
            ["git", "--no-replace-objects", "rev-parse", "--show-toplevel"],
            cwd=ROOT,
            env=environment,
            text=True,
            timeout=12,
        ).strip()
        subprocess.run(
            [
                "git",
                "--no-replace-objects",
                "cat-file",
                "-e",
                f"{_HARNESS_ORIGINAL_SOURCE_CUT}^{{tree}}",
            ],
            cwd=source,
            env=environment,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            timeout=12,
        )
        # An unrelated monorepo commit has a valid Git hash too; it cannot
        # masquerade as the old standalone Harness source root.
        subprocess.run(
            [
                "git",
                "--no-replace-objects",
                "cat-file",
                "-e",
                f"{_HARNESS_ORIGINAL_SOURCE_CUT}:src/ordivon_harness",
            ],
            cwd=source,
            env=environment,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            timeout=12,
        )
        imported = subprocess.run(
            [
                "git",
                "--no-replace-objects",
                "cat-file",
                "-e",
                f"{_HARNESS_ORIGINAL_SOURCE_CUT}:services/harness/src/ordivon_harness",
            ],
            cwd=source,
            env=environment,
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            timeout=12,
        )
        if imported.returncode == 0:
            raise ValueError("pinned original source is a monorepo-root object")
        subprocess.run(
            ["git", "init", "--bare", "-q", str(directory)],
            env=environment,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            timeout=12,
        )
        subprocess.run(
            [
                "git",
                "-c",
                "protocol.file.allow=always",
                "fetch",
                "--no-tags",
                "--quiet",
                source,
                _HARNESS_ORIGINAL_SOURCE_CUT,
            ],
            cwd=directory,
            env=environment,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            timeout=70,
        )
        subprocess.run(
            ["git", "update-ref", "refs/heads/pinned-original", _HARNESS_ORIGINAL_SOURCE_CUT],
            cwd=directory,
            env=environment,
            check=True,
            stdout=subprocess.DEVNULL,
            timeout=12,
        )
        subprocess.run(
            ["git", "symbolic-ref", "HEAD", "refs/heads/pinned-original"],
            cwd=directory,
            env=environment,
            check=True,
            stdout=subprocess.DEVNULL,
            timeout=12,
        )
        # A bare transfer never borrows objects from mutable monorepo packs
        # after this point, and forbids lazy reads from any remote.
        if (directory / "objects/info/alternates").exists():
            raise ValueError("original-source graph inherited mutable alternate objects")
        # The fast path is acceptable ONLY for a fully materialized,
        # independently self-contained Git graph, not a promisor/shallow
        # cache whose missing objects would be fetched after qualification.
        subprocess.run(
            [
                "git",
                "--no-replace-objects",
                "fsck",
                "--full",
                "--no-reflogs",
                "--no-dangling",
                "--strict",
            ],
            cwd=directory,
            env=environment,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            timeout=65,
        )
        # Native git fsck accepts declared shallow graph boundaries; those
        # are not a full history/ancestor qualification. Require no shallow
        # marker on the isolated original object DB after native fsck.
        shallow = subprocess.check_output(
            ["git", "--no-replace-objects", "rev-parse", "--is-shallow-repository"],
            cwd=directory,
            env=environment,
            text=True,
            timeout=12,
        ).strip()
        if shallow != "false":
            raise ValueError("pinned original Git DAG has an unqualified shallow boundary")
        return True
    except OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired, ValueError:
        # A missing/incomplete local *original* graph is not permission to
        # substitute a monorepo commit. Retain remote pinned-source fallback.
        return False


@lru_cache(maxsize=1)
def _historical_source_checkout() -> Path:
    """Read-only native Git snapshot. Missing original source is NOT a PASS."""
    directory = Path(tempfile.mkdtemp(prefix="ordivon-harness-historical-git-"))
    try:
        if not _local_pinned_original_source_graph(directory):
            # An unavailable immutable local original-DAG object graph must
            # not produce false acceptance. Fall back to the existing remote
            # original-source origin and *same* exact commit identity.
            shutil.rmtree(directory)
            subprocess.run(
                [
                    "git",
                    "-c",
                    "protocol.version=2",
                    "clone",
                    "--filter=blob:none",
                    "--single-branch",
                    "--no-checkout",
                    _HARNESS_ORIGINAL_SOURCE_REPO,
                    str(directory),
                ],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                timeout=110,
            )
        observed = subprocess.check_output(
            ["git", "--no-replace-objects", "rev-parse", "HEAD"],
            cwd=directory,
            text=True,
            timeout=15,
        ).strip()
        if observed != _HARNESS_ORIGINAL_SOURCE_CUT:
            raise ValueError(
                "original Harness source HEAD does not match pinned source cut: "
                f"observed={observed} expected={_HARNESS_ORIGINAL_SOURCE_CUT}"
            )
    except OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired, ValueError:
        shutil.rmtree(directory, ignore_errors=True)
        raise
    atexit.register(shutil.rmtree, directory, ignore_errors=True)
    return directory


def _validate_original_historical_source(filename: str, revision: str, current: bytes) -> list[str]:
    """Validate old-source provenance separately from imported-byte retention."""
    errors: list[str] = []
    try:
        repository = _historical_source_checkout()
        environment = _original_source_git_environment()
        path = f"evidence/{filename}"
        creations = subprocess.check_output(
            [
                "git",
                "--no-replace-objects",
                "log",
                "--full-history",
                "--diff-filter=A",
                "--format=%H",
                _HARNESS_ORIGINAL_SOURCE_CUT,
                "--",
                path,
            ],
            cwd=repository,
            env=environment,
            text=True,
            timeout=22,
        ).splitlines()
        if len(creations) != 1:
            return [
                f"original independent Harness source must have exactly one evidence "
                f"creation for {filename}: found={creations}"
            ]
        predecessor = subprocess.run(
            ["git", "--no-replace-objects", "merge-base", "--is-ancestor", revision, creations[0]],
            cwd=repository,
            env=environment,
            check=False,
            timeout=20,
        )
        if predecessor.returncode != 0:
            errors.append(
                f"historical implementation revision is not an original-repository "
                f"ancestor of evidence creation for {filename}: revision={revision} "
                f"creation={creations[0]}"
            )
        source = subprocess.check_output(
            ["git", "--no-replace-objects", "show", f"{_HARNESS_ORIGINAL_SOURCE_CUT}:{path}"],
            cwd=repository,
            env=environment,
            timeout=28,
        )
        if source != current:
            errors.append(f"original independent Harness source evidence bytes differ: {filename}")
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired, ValueError) as error:
        errors.append(
            f"cannot qualify pinned original independent Harness source for {filename}: {error}"
        )
    return errors


def _validate_index_creation_lineage_binding(
    filename: str,
    revision: str,
    *,
    historical: bool = False,
) -> list[str]:
    """Verify archive origin or same-repository current provenance.

    Historical old-root evidence requires exact imported bytes and the pinned
    original-repository source/creation chain. No cross-root ancestor shortcut
    is used, so shallow and complete history must yield identical standing.
    """
    errors: list[str] = []
    path = EVIDENCE / filename
    relative_path = path.relative_to(ROOT).as_posix()
    old_source_root = _is_original_harness_source_revision(revision)
    if old_source_root:
        if not historical or _git_owner_prefix() != "services/harness/":
            return [
                f"original Harness Git source cannot certify current/verified evidence for {filename}"
            ]
        try:
            imported_bytes = _git_file_bytes(_HARNESS_HISTORICAL_IMPORT, relative_path)
            current_bytes = path.read_bytes()
        except (subprocess.CalledProcessError, OSError, ValueError) as error:
            return [f"cannot verify pinned Harness monorepo import bytes for {filename}: {error}"]
        if imported_bytes != current_bytes:
            return [
                f"index-bound evidence bytes changed after pinned import for {filename}: "
                f"import={_HARNESS_HISTORICAL_IMPORT}"
            ]
        return _validate_original_historical_source(filename, revision, current_bytes)

    try:
        creation_revisions = _git_creation_revisions(relative_path)
    except (subprocess.CalledProcessError, ValueError) as error:
        return [f"cannot inspect evidence creation lineage for {filename}: {error}"]
    if len(creation_revisions) != 1:
        return [
            f"index-bound evidence must have exactly one creation commit for {filename}: "
            f"found={creation_revisions}"
        ]
    creation_revision = creation_revisions[0]
    ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", revision, creation_revision],
        cwd=ROOT,
        check=False,
    )
    if ancestor.returncode != 0:
        errors.append(
            f"index-bound revision is not an ancestor of evidence creation for {filename}: "
            f"revision={revision} creation={creation_revision}"
        )
        return errors
    invalidating = _invalidating_paths(revision, creation_revision)
    if invalidating:
        errors.append(
            f"implementation changed before index-bound evidence creation for {filename}: "
            f"invalidating={invalidating}"
        )
    try:
        created_bytes = _git_file_bytes(creation_revision, relative_path)
        current_bytes = path.read_bytes()
    except (subprocess.CalledProcessError, OSError) as error:
        errors.append(f"cannot verify immutable evidence bytes for {filename}: {error}")
    else:
        if created_bytes != current_bytes:
            errors.append(
                f"index-bound evidence bytes changed after creation for {filename}: "
                f"creation={creation_revision}"
            )
    return errors


def _recognized_revision_hints(receipt: dict[str, object]) -> dict[str, str]:
    return {
        field: value
        for field in _INDEX_REVISION_HINT_FIELDS
        if isinstance((value := receipt.get(field)), str) and len(value) == 40
    }


def _validate_embedded_revision_binding(
    filename: str,
    receipt: dict[str, object],
    revision: str,
) -> list[str]:
    observed = (
        receipt.get("implementationSourceRevision")
        or receipt.get("implementationRevision")
        or receipt.get("sourceRevision")
    )
    if observed == revision:
        return []
    return [f"revision mismatch for {filename}: index={revision} receipt={observed}"]


def main() -> int:
    errors: list[str] = []
    index_path = EVIDENCE / "index.json"
    try:
        index = json.loads(index_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        print(f"evidence: cannot read index: {error}", file=sys.stderr)
        return 1
    if index.get("kind") != "ordivon.harness-evidence-index":
        errors.append("index kind is invalid")
    entries = index.get("entries")
    if not isinstance(entries, list):
        errors.append("index entries are missing")
        entries = []
    claim_ids: set[str] = set()
    files: set[str] = set()
    for entry in entries:
        if not isinstance(entry, dict):
            errors.append("one evidence entry is not an object")
            continue
        claim_id = entry.get("claimId")
        filename = entry.get("file")
        revision = entry.get("implementationRevision")
        status = entry.get("status")
        revision_binding = entry.get("revisionBinding", "embedded")
        runtime_dependency_digest = entry.get("runtimeDependencyClosureDigest")
        try:
            implementation_paths = _normalize_implementation_paths(entry.get("implementationPaths"))
        except ValueError as error:
            errors.append(f"invalid implementationPaths for {claim_id}: {error}")
            implementation_paths = None
        if not isinstance(claim_id, str) or not claim_id:
            errors.append("one evidence entry has no claimId")
            continue
        if claim_id in claim_ids:
            errors.append(f"duplicate claimId: {claim_id}")
        claim_ids.add(claim_id)
        if not isinstance(filename, str) or filename in files:
            errors.append(f"invalid or duplicate evidence file for {claim_id}")
            continue
        files.add(filename)
        if status not in {"historical", "verified"}:
            errors.append(f"unsupported evidence status for {claim_id}: {status}")
        if revision_binding not in {"embedded", "index-creation-lineage"}:
            errors.append(f"unsupported revision binding for {claim_id}: {revision_binding}")
        if not isinstance(revision, str) or len(revision) != 40:
            errors.append(f"invalid implementation revision: {claim_id}")
            continue
        if implementation_paths is None:
            if runtime_dependency_digest is not None:
                errors.append(
                    f"unscoped evidence must not carry runtimeDependencyClosureDigest: {claim_id}"
                )
        else:
            if not _valid_sha256_digest(runtime_dependency_digest):
                errors.append(
                    f"scoped evidence requires valid runtimeDependencyClosureDigest: {claim_id}"
                )
            else:
                try:
                    historical_dependency_digest = _runtime_dependency_closure_digest(revision)
                except (
                    OSError,
                    subprocess.CalledProcessError,
                    UnicodeDecodeError,
                    ValueError,
                    tomllib.TOMLDecodeError,
                ) as error:
                    errors.append(
                        f"cannot resolve historical runtime dependency closure for {claim_id}: {error}"
                    )
                else:
                    if historical_dependency_digest != runtime_dependency_digest:
                        errors.append(
                            "runtime dependency closure digest differs from implementation "
                            f"revision for {claim_id}"
                        )
        path = EVIDENCE / filename
        if not path.is_file():
            errors.append(f"missing evidence file: {filename}")
            continue
        try:
            receipt = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            errors.append(f"invalid JSON {filename}: {error}")
            continue
        if revision_binding == "embedded":
            errors.extend(_validate_embedded_revision_binding(filename, receipt, revision))
        elif revision_binding == "index-creation-lineage":
            errors.extend(
                _validate_index_creation_lineage_binding(
                    filename, revision, historical=(status == "historical")
                )
            )
            for field, observed in _recognized_revision_hints(receipt).items():
                if field in {"prebindingRevision", "repairCommit"} and observed != revision:
                    errors.append(
                        f"index-bound revision hint differs for {filename}: "
                        f"field={field} index={revision} evidence={observed}"
                    )
                if (
                    field
                    in {
                        "implementationSourceRevision",
                        "implementationRevision",
                        "sourceRevision",
                    }
                    and observed != revision
                ):
                    errors.append(
                        f"index-bound embedded implementation revision differs for {filename}: "
                        f"field={field} index={revision} evidence={observed}"
                    )
        integrity = receipt.get("integrity")
        if integrity is not None and not isinstance(integrity, dict):
            errors.append(f"invalid integrity object: {filename}")
        if isinstance(integrity, dict) and receipt.get("kind") in {
            "ordivon.harness-p0-scale-acceptance",
            "ordivon.harness-c3-agent-first-api-acceptance",
            "ordivon.harness-h3-independent-product-acceptance",
            "ordivon.harness-h4-stress-acceptance",
        }:
            if integrity.get("payloadDigest") != _canonical_payload_digest(receipt):
                errors.append(f"integrity mismatch: {filename}")
        if receipt.get("kind") == "ordivon.harness-c3-agent-first-api-acceptance":
            checks = receipt.get("checks")
            expected_changed = {
                "CHANGELOG.md",
                "README.md",
                "docs/COMPATIBILITY.md",
                "docs/QUICKSTART.md",
                "pyproject.toml",
                "scripts/check_docs.py",
                "scripts/check_wheel.py",
                "src/ordivon_harness/api.py",
                "src/ordivon_harness/host_api.py",
                "tests/test_public_api.py",
            }
            if set(receipt.get("changedPaths", [])) != expected_changed:
                errors.append("C3 API receipt changed-path set differs")
            if not isinstance(checks, dict):
                errors.append("C3 API receipt checks are missing")
            else:
                for required_check in (
                    "fullRegressionPassed",
                    "documentationContractPassed",
                    "dependencyContractPassed",
                    "recommendedApiHostFreeInBaseWheel",
                    "hostCompatibilityFacadePassedWithHostExtra",
                    "deterministicDemoPassed",
                    "wheelSmokePassed",
                ):
                    if checks.get(required_check) is not True:
                        errors.append(f"C3 API receipt failed check: {required_check}")
                for forbidden_change in (
                    "productionCutoverActivated",
                    "dualWriteActivated",
                    "legacyWriterRemoved",
                    "durableRunStateModulesChanged",
                ):
                    if checks.get(forbidden_change) is not False:
                        errors.append(f"C3 API receipt changed forbidden state: {forbidden_change}")
                if checks.get("cliCommandsVerified") != 19:
                    errors.append("C3 API receipt CLI command count differs")
        if status == "verified":
            try:
                current, invalidating = _verified_revision_is_current(
                    revision,
                    implementation_paths,
                    runtime_dependency_closure_digest=(
                        runtime_dependency_digest
                        if isinstance(runtime_dependency_digest, str)
                        else None
                    ),
                )
            except (
                OSError,
                subprocess.CalledProcessError,
                UnicodeDecodeError,
                ValueError,
                tomllib.TOMLDecodeError,
            ) as error:
                errors.append(f"cannot evaluate verified currentness for {claim_id}: {error}")
                continue
            if not current:
                errors.append(
                    f"verified receipt is stale for {claim_id}: invalidating={invalidating}"
                )

    receipt_files = {path.name for path in EVIDENCE.glob("*.json") if path.name != "index.json"}
    if files != receipt_files:
        errors.append(
            "evidence index/file set differs: "
            f"missing={sorted(receipt_files - files)} extra={sorted(files - receipt_files)}"
        )
    if errors:
        for error in errors:
            print(f"evidence: {error}", file=sys.stderr)
        return 1
    historical = sum(entry.get("status") == "historical" for entry in entries)
    verified = sum(entry.get("status") == "verified" for entry in entries)
    print(f"evidence contract: valid historical_receipts={historical} verified_receipts={verified}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
