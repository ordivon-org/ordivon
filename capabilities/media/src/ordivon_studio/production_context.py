from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any

from .assets import hash_file

_SHA256 = re.compile(r"^sha256:[0-9a-f]{64}$")


def _load_object(path: Path) -> dict[str, Any]:
    """Legacy object-only reader also consumed by the learning projection."""
    value, _ = _load_bound_object(path)
    return value


def _load_bound_object(path: Path) -> tuple[dict[str, Any], str]:
    """Bind parsed JSON to the SHA-256 digest of the *same* bytes read."""
    source_bytes = path.read_bytes()
    value = json.loads(source_bytes)
    if not isinstance(value, dict):
        raise TypeError(f"{path} must contain one JSON object")
    return value, "sha256:" + hashlib.sha256(source_bytes).hexdigest()


def _relative_child(root: Path, relative: str) -> Path:
    candidate = Path(relative)
    if candidate.is_absolute():
        raise ValueError(f"Production source path must be relative: {relative}")
    resolved_root = root.resolve()
    resolved = (root / candidate).resolve()
    if resolved != resolved_root and resolved_root not in resolved.parents:
        raise ValueError(f"Production source path escapes Production root: {relative}")
    return resolved


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        check=False,
        capture_output=True,
        text=True,
    )


def _source_binding_observation(
    binding: dict[str, Any],
    local_repository: Path | None,
) -> dict[str, Any]:
    binding_id = str(binding["id"])
    revision = str(binding["revision"])
    base: dict[str, Any] = {
        "bindingId": binding_id,
        "sourceRepository": binding["repository"],
        "boundRevision": revision,
        "localRepository": None if local_repository is None else str(local_repository),
        "revalidated": False,
        "relation": "unverified",
        "revisionPresent": None,
        "observedHeadRevision": None,
        "observedDirty": None,
        "semanticApplicability": "not-evaluated",
        "basis": "no-local-repository",
    }
    if local_repository is None:
        return base

    probe = _git(local_repository, "rev-parse", "--is-inside-work-tree")
    if probe.returncode != 0 or probe.stdout.strip() != "true":
        base["relation"] = "repository-unavailable"
        base["basis"] = "local-repository-is-not-readable-git-worktree"
        return base

    revision_probe = _git(local_repository, "cat-file", "-e", f"{revision}^{{commit}}")
    head_probe = _git(local_repository, "rev-parse", "HEAD")
    dirty_probe = _git(local_repository, "status", "--porcelain=v1")
    if head_probe.returncode != 0 or dirty_probe.returncode != 0:
        base["relation"] = "repository-unavailable"
        base["basis"] = "local-git-observation-failed"
        return base

    head = head_probe.stdout.strip()
    revision_present = revision_probe.returncode == 0
    base.update(
        {
            "revalidated": True,
            "revisionPresent": revision_present,
            "observedHeadRevision": head,
            "observedDirty": bool(dirty_probe.stdout),
            "basis": "local-git-exact-revision-observation",
        }
    )
    if not revision_present:
        base["relation"] = "bound-revision-missing"
    elif head == revision:
        base["relation"] = "head-matches-binding"
    else:
        base["relation"] = "head-differs-from-binding"
    return base



def _declared_source_files(sources: dict[str, Any]) -> set[str]:
    """Exact source-carrier allowlist from the Production's own descriptor."""
    paths: set[str] = set()
    for value in sources.values():
        if isinstance(value, str):
            paths.add(value)
        elif isinstance(value, list):
            paths.update(item for item in value if isinstance(item, str))
    return paths


def _output_blob_observation(
    root: Path,
    output: dict[str, Any],
    *,
    declared_source_files: set[str],
    selected_file: Path | None,
) -> dict[str, Any]:
    """One bounded, read-only byte comparison, not approval or publication.

    A sourceCarrier is an exact-byte source assertion; outputCarrier names
    one owner-declared local materialization of a transformed Output.
    Neither a local path nor an explicit consumer-selected file proves
    ongoing availability, domain acceptance, or publication.
    """
    expected = output.get("blobDigest")
    carrier = output.get("sourceCarrier")
    output_carrier = output.get("outputCarrier")
    row: dict[str, Any] = {
        "outputId": output.get("id"),
        "declaredStatus": output.get("status"),
        "expectedBlobDigest": expected,
        "sourceCarrier": carrier,
        "outputCarrier": output_carrier,
        "sourceSelection": None,
        "relation": "UNKNOWN_NO_SELECTED_BYTES",
        "observedBlob": None,
    }
    selected: Path | None = None
    if carrier is not None and output_carrier is not None:
        row["relation"] = "INVALID_MULTIPLE_CARRIERS"
        return row
    if carrier is not None:
        if not isinstance(carrier, str) or carrier not in declared_source_files:
            row["relation"] = "INVALID_UNDECLARED_SOURCE_CARRIER"
            return row
        try:
            selected = _relative_child(root, carrier)
        except ValueError:
            row["relation"] = "INVALID_ESCAPING_SOURCE_CARRIER"
            return row
        row["sourceSelection"] = "declared-exact-source-carrier"
    elif output_carrier is not None:
        if not isinstance(output_carrier, str) or not output_carrier or "\\" in output_carrier:
            row["relation"] = "INVALID_OUTPUT_CARRIER"
            return row
        try:
            selected = _relative_child(root, output_carrier)
        except ValueError:
            row["relation"] = "INVALID_ESCAPING_OUTPUT_CARRIER"
            return row
        row["sourceSelection"] = "declared-local-output-carrier"
    if selected_file is not None:
        row["sourceSelection"] = "explicit-consumer-file"
        selected = selected_file
    if selected is None:
        return row
    row["selectedPath"] = str(selected.resolve())
    if not isinstance(expected, str) or _SHA256.fullmatch(expected) is None:
        row["relation"] = "UNKNOWN_NO_VALID_DECLARED_DIGEST"
        return row
    try:
        blob = hash_file(selected)
    except (OSError, ValueError):
        row["relation"] = "UNKNOWN_SELECTED_FILE_UNAVAILABLE"
        return row
    row["observedBlob"] = blob.as_dict()
    row["relation"] = (
        "MATCHES_DECLARED_DIGEST"
        if blob.digest == expected
        else "DIFFERS_FROM_DECLARED_DIGEST"
    )
    return row


def build_production_context(
    production_root: Path,
    *,
    source_repositories: dict[str, Path] | None = None,
    output_files: dict[str, Path] | None = None,
) -> dict[str, Any]:
    root = production_root.resolve()
    production_path = root / "production.json"
    production, production_manifest_digest = _load_bound_object(production_path)

    production_id = production.get("id")
    sources = production.get("sources")
    if not isinstance(sources, dict) or not isinstance(sources.get("claims"), str):
        raise TypeError("Production must reference one claims source")
    claims_path = _relative_child(root, sources["claims"])
    claims_document, claims_manifest_digest = _load_bound_object(claims_path)
    if claims_document.get("productionId") != production_id:
        raise ValueError("Claim set productionId does not match Production id")

    source_bindings = production.get("sourceBindings")
    if not isinstance(source_bindings, list):
        raise TypeError("Production sourceBindings must be an array")
    outputs = production.get("outputs")
    if not isinstance(outputs, list):
        raise TypeError("Production outputs must be an array")
    claims = claims_document.get("claims")
    if not isinstance(claims, list):
        raise TypeError("Claim set claims must be an array")

    repositories = source_repositories or {}
    known_binding_ids = {
        str(binding.get("id"))
        for binding in source_bindings
        if isinstance(binding, dict)
    }
    unknown_repositories = sorted(set(repositories) - known_binding_ids)
    if unknown_repositories:
        raise ValueError(
            "source repository mapping names unknown binding(s): " + ", ".join(unknown_repositories)
        )

    observations = []
    for raw_binding in source_bindings:
        if not isinstance(raw_binding, dict):
            raise TypeError("Production sourceBindings entries must be objects")
        binding_id = str(raw_binding.get("id"))
        observations.append(
            _source_binding_observation(raw_binding, repositories.get(binding_id))
        )

    projected_claims = []
    for claim in claims:
        if not isinstance(claim, dict):
            raise TypeError("Claim entries must be objects")
        projected_claims.append(
            {
                "id": claim.get("id"),
                "source": claim.get("source"),
                "meaning": claim.get("meaning"),
                "evidence": claim.get("evidence"),
            }
        )

    selected_output_files = output_files or {}
    output_ids = [output.get("id") for output in outputs if isinstance(output, dict)]
    if len(output_ids) != len(set(output_ids)):
        raise ValueError("Production outputs contain duplicate ids")
    unknown_output_ids = sorted(set(selected_output_files) - set(output_ids))
    if unknown_output_ids:
        raise ValueError(
            "output-file mapping names unknown output(s): " + ", ".join(unknown_output_ids)
        )
    source_file_names = _declared_source_files(sources)
    output_observations = [
        _output_blob_observation(
            root,
            output,
            declared_source_files=source_file_names,
            selected_file=selected_output_files.get(output["id"]),
        )
        for output in outputs
    ]

    projected_outputs = []
    for output in outputs:
        if not isinstance(output, dict):
            raise TypeError("Production output entries must be objects")
        projected_outputs.append(
            {
                key: output[key]
                for key in ("id", "kind", "status", "profile", "blobDigest", "outputCarrier")
                if key in output
            }
        )

    return {
        "schemaVersion": 1,
        "kind": "ordivon.studio.production-context",
        "truthRole": "derived-read-only-projection",
        "production": {
            key: production[key]
            for key in ("id", "title", "status", "intent", "audiences")
            if key in production
        },
        "sourceBindings": source_bindings,
        "claims": {
            "count": len(projected_claims),
            "items": projected_claims,
        },
        "outputs": projected_outputs,
        "inputManifestIdentity": {
            "productionManifestSha256": production_manifest_digest,
            "claimsManifestSha256": claims_manifest_digest,
            "truthRole": "exact-parsed-input-bytes-not-source-currentness",
        },
        "outputByteIdentity": {
            "truthRole": "point-in-time-local-byte-comparison-only",
            "semanticApplicability": "not-evaluated",
            "editorialApproval": "source-declared-only",
            "publicationAuthorization": "not-evaluated",
            "rule": (
                "Digest equality establishes only observed byte identity at inspection. "
                "Missing bindings are UNKNOWN, not FALSE. Declared outputCarrier paths "
                "are local materializations, not durable Artifact ownership. Neither Output "
                "status, file equality, nor historical receipts authorize publication."
            ),
            "observations": output_observations,
        },
        "sourceBindingCurrentness": {
            "truthRole": "mechanical-git-relation-only",
            "allBindingsRevalidated": bool(observations)
            and all(item["revalidated"] for item in observations),
            "semanticApplicability": "not-evaluated",
            "rule": (
                "A changed repository HEAD does not make a revision-bound Claim stale by itself. "
                "This projection reports Git relation only; semantic applicability remains Agent/domain work."
            ),
            "observations": observations,
        },
        "escapeHatch": {
            "productionManifest": str(production_path),
            "claimsManifest": str(claims_path),
        },
    }
