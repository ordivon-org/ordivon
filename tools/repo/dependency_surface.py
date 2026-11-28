#!/usr/bin/env python3
"""Read-only source projection of Ordivon's dependency/toolchain surface.

This module deliberately does not claim installed, dynamic, or behavioral
consumer truth. It reuses native manifest/lock formats and Git as the source
authority instead of creating another dependency registry.
"""
from __future__ import annotations

import json
import subprocess
import tomllib
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
TRUTH_ROLE = "source-static-dependency-projection-not-installed-or-behavioral-proof"

MANIFEST_NAMES = (
    "pyproject.toml",
    "uv.lock",
    "Cargo.toml",
    "Cargo.lock",
    "package.json",
    "pnpm-lock.yaml",
    "flake.nix",
    "flake.lock",
    "mise.toml",
)


def tracked_files(root: Path = ROOT, revision: str | None = None) -> tuple[str, ...]:
    revision = revision or source_cut(root)
    output = subprocess.check_output(["git", "-C", str(root), "ls-tree", "-r", "--name-only", "-z", revision])
    return tuple(
        part.decode("utf-8", errors="surrogateescape")
        for part in output.split(b"\0")
        if part
    )


def source_cut(root: Path = ROOT) -> str:
    return subprocess.check_output(
        ["git", "-C", str(root), "rev-parse", "HEAD"], text=True
    ).strip()


def _read_toml(root: Path, path: str, revision: str | None = None) -> dict[str, Any]:
    if revision is None:
        return tomllib.loads((root / path).read_text(encoding="utf-8"))
    payload = subprocess.check_output(["git", "-C", str(root), "show", f"{revision}:{path}"])
    return tomllib.loads(payload.decode("utf-8"))


def manifest_counts(files: tuple[str, ...]) -> dict[str, int]:
    return {
        name: sum(Path(path).name == name for path in files)
        for name in MANIFEST_NAMES
    }


def _mise_uv_policies(root: Path, files: tuple[str, ...], revision: str | None = None) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for path in files:
        if Path(path).name != "mise.toml":
            continue
        data = _read_toml(root, path, revision)
        value = data.get("tools", {}).get("uv")
        if isinstance(value, str):
            rows.append({"path": path, "uv": value})
    return sorted(rows, key=lambda row: row["path"])


def _third_party_uv_packages(root: Path, path: str, revision: str | None = None) -> dict[str, dict[str, Any]]:
    data = _read_toml(root, path, revision)
    result: dict[str, dict[str, Any]] = {}
    for row in data.get("package", []):
        if not isinstance(row, dict):
            continue
        source = row.get("source")
        if not isinstance(source, dict) or "registry" not in source:
            continue
        name = row.get("name")
        if not isinstance(name, str):
            continue
        if name in result:
            raise ValueError(f"duplicate third-party uv package name unsupported: {name}")
        result[name] = row
    return result


def artifact_python_projection(root: Path = ROOT, revision: str | None = None) -> dict[str, Any]:
    owner = "capabilities/artifact"
    delivery = owner + "/artifact-delivery/python-uv"
    owner_project = _read_toml(root, owner + "/pyproject.toml", revision)
    delivery_project = _read_toml(root, delivery + "/pyproject.toml", revision)
    owner_deps = tuple(owner_project.get("project", {}).get("dependencies", ()))
    delivery_deps = tuple(delivery_project.get("project", {}).get("dependencies", ()))
    owner_packages = _third_party_uv_packages(root, owner + "/uv.lock", revision)
    delivery_packages = _third_party_uv_packages(root, delivery + "/uv.lock", revision)
    drift = {
        name: {"owner": owner_packages.get(name), "delivery": row}
        for name, row in delivery_packages.items()
        if owner_packages.get(name) != row
    }
    return {
        "directProductionDependenciesEqual": owner_deps == delivery_deps,
        "ownerDirectDependencies": list(owner_deps),
        "deliveryDirectDependencies": list(delivery_deps),
        "ownerThirdPartyPackageCount": len(owner_packages),
        "deliveryThirdPartyPackageCount": len(delivery_packages),
        "deliveryThirdPartySubsetOfOwner": not drift,
        "deliveryThirdPartyDrift": drift,
    }


def runtime_legacy_surface(root: Path = ROOT, revision: str | None = None) -> dict[str, Any]:
    core_path = "services/runtime/crates/ordivon-runtime-core/Cargo.toml"
    mcp_path = "services/runtime/crates/ordivon-runtime-mcp/Cargo.toml"
    core = _read_toml(root, core_path, revision)
    mcp = _read_toml(root, mcp_path, revision)
    core_features = core.get("features", {})
    mcp_features = mcp.get("features", {})
    default_core = tuple(core_features.get("default", ()))
    default_mcp = tuple(mcp_features.get("default", ()))
    transactional = tuple(core_features.get("transactional-runtime", ()))
    operator = tuple(core_features.get("operator-tools", ()))
    legacy = tuple(mcp_features.get("legacy-runtime", ()))
    return {
        "coreDefaultFeatures": list(default_core),
        "mcpDefaultFeatures": list(default_mcp),
        "transactionalRuntimeUsesRusqlite": "dep:rusqlite" in transactional,
        "operatorToolsReachTransactionalRuntime": "transactional-runtime" in operator,
        "legacyMcpReachTransactionalRuntime":
            "ordivon-runtime-core/transactional-runtime" in legacy,
        "postgresMcpFeaturePresent": "postgres-runtime" in mcp_features,
        "sourceRetirementEligible": False,
        "retirementEligibilityReason":
            "installed exclusive-writer/no-future-write/restart/consumer proof is external to source projection",
    }


def build_report(root: Path = ROOT) -> dict[str, Any]:
    revision = source_cut(root)
    files = tracked_files(root, revision)
    uv_rows = _mise_uv_policies(root, files, revision)
    return {
        "schemaVersion": 1,
        "kind": "ordivon-dependency-surface-r1",
        "truthRole": TRUTH_ROLE,
        "sourceCut": revision,
        "sourceMode": "committed-git-tree",
        "manifestCounts": manifest_counts(files),
        "toolPolicy": {
            "uv": uv_rows,
            "allDeclaredUvUseLatest": bool(uv_rows) and all(
                row["uv"] == "latest" for row in uv_rows
            ),
        },
        "runtimeLegacySurface": runtime_legacy_surface(root, revision),
        "artifactPythonProjection": artifact_python_projection(root, revision),
        "nonClaims": [
            "excludes uncommitted worktree and index changes",
            "does not prove installed package or binary identity",
            "does not prove dynamic imports, loader edges, subprocess selection or network dependencies",
            "does not prove behavioral consumer reachability or domain acceptance",
            "does not authorize deletion or production cutover",
        ],
    }


def main() -> int:
    print(json.dumps(build_report(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
