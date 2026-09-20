#!/usr/bin/env python3
"""Validate Harness evidence/file correspondence and revision/currentness bindings."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
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
                raise ValueError(
                    f"Git path escaped owner prefix: prefix={owner_base} path={path}"
                )
            path = path[len(owner_base):]
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


def _verified_revision_is_current(
    revision: str,
    implementation_paths: tuple[str, ...] | None = None,
    runtime_dependency_closure_digest: str | None = None,
) -> tuple[bool, list[str]]:
    ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", revision, "HEAD"],
        cwd=ROOT,
        check=False,
    )
    if ancestor.returncode != 0:
        return False, []
    invalidating = _invalidating_paths(revision, "HEAD", implementation_paths)
    if implementation_paths is None:
        if runtime_dependency_closure_digest is not None:
            raise ValueError("unscoped currentness cannot bind a scoped runtime dependency digest")
    else:
        if not _valid_sha256_digest(runtime_dependency_closure_digest):
            raise ValueError("scoped currentness requires a valid runtime dependency closure digest")
        historical = _runtime_dependency_closure_digest(revision)
        if historical != runtime_dependency_closure_digest:
            raise ValueError(
                "scoped runtime dependency digest differs from its implementation revision"
            )
        if _runtime_dependency_closure_digest("HEAD") != runtime_dependency_closure_digest:
            invalidating.append(_RUNTIME_DEPENDENCY_INVALIDATOR)
    return not invalidating, invalidating


def _validate_index_creation_lineage_binding(
    filename: str,
    revision: str,
) -> list[str]:
    """Validate external revision binding for one immutable evidence projection."""

    errors: list[str] = []
    path = EVIDENCE / filename
    relative_path = path.relative_to(ROOT).as_posix()
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
                except (OSError, subprocess.CalledProcessError, UnicodeDecodeError, ValueError, tomllib.TOMLDecodeError) as error:
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
            errors.extend(_validate_index_creation_lineage_binding(filename, revision))
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
            except (OSError, subprocess.CalledProcessError, UnicodeDecodeError, ValueError, tomllib.TOMLDecodeError) as error:
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
