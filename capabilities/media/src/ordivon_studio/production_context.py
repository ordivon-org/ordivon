from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any


def _load_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"{path} must contain one JSON object")
    return value


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


def build_production_context(
    production_root: Path,
    *,
    source_repositories: dict[str, Path] | None = None,
) -> dict[str, Any]:
    root = production_root.resolve()
    production_path = root / "production.json"
    production = _load_object(production_path)

    production_id = production.get("id")
    sources = production.get("sources")
    if not isinstance(sources, dict) or not isinstance(sources.get("claims"), str):
        raise TypeError("Production must reference one claims source")
    claims_path = _relative_child(root, sources["claims"])
    claims_document = _load_object(claims_path)
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

    projected_outputs = []
    for output in outputs:
        if not isinstance(output, dict):
            raise TypeError("Production output entries must be objects")
        projected_outputs.append(
            {
                key: output[key]
                for key in ("id", "kind", "status", "profile", "blobDigest")
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
