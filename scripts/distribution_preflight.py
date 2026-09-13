#!/usr/bin/env python
from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import tempfile
from typing import Any

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "contracts/distribution-preflight.schema.json"


class PreflightError(RuntimeError):
    pass


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return "sha256:" + h.hexdigest()


def canonical_digest(value: Any) -> str:
    data = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return "sha256:" + hashlib.sha256(data).hexdigest()


def load_profile(path: Path) -> dict[str, Any]:
    profile = json.loads(path.read_text())
    schema = json.loads(SCHEMA.read_text())
    errors = sorted(Draft202012Validator(schema).iter_errors(profile), key=lambda item: list(item.path))
    if errors:
        raise PreflightError("profile schema failure: " + "; ".join(error.message for error in errors))
    return profile


def snapshot_tree(root: Path) -> dict[str, Any]:
    if not root.is_dir():
        raise PreflightError(f"candidate directory is absent: {root}")
    files: list[dict[str, Any]] = []
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root).as_posix()
        if path.is_symlink():
            raise PreflightError(f"R1 rejects symlinks in release candidates: {rel}")
        if path.is_dir():
            continue
        if not path.is_file():
            raise PreflightError(f"unsupported filesystem object in candidate: {rel}")
        mode = stat.S_IMODE(path.stat().st_mode)
        files.append({
            "path": rel,
            "size": path.stat().st_size,
            "sha256": sha256_file(path),
            "executable": bool(mode & 0o111),
        })
    if not files:
        raise PreflightError(f"candidate directory is empty: {root}")
    return {"files": files, "treeDigest": canonical_digest(files)}


def matching_paths(snapshot: dict[str, Any], patterns: list[str]) -> list[str]:
    hits: set[str] = set()
    for item in snapshot["files"]:
        rel = item["path"]
        for pattern in patterns:
            if fnmatch.fnmatchcase(rel, pattern):
                hits.add(rel)
    return sorted(hits)


def run_tool(executable: Path, args: list[str], *, cwd: Path | None = None, timeout: int = 120) -> subprocess.CompletedProcess[str]:
    if not executable.is_file() or not os.access(executable, os.X_OK):
        raise PreflightError(f"required executable is unavailable: {executable}")
    result = subprocess.run(
        [str(executable), *args],
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=timeout,
        env={**os.environ, "LC_ALL": "C", "TZ": "UTC"},
    )
    return result


def tool_fact(executable: Path, version_args: list[str]) -> dict[str, Any]:
    result = run_tool(executable, version_args, timeout=30)
    if result.returncode != 0:
        raise PreflightError(f"cannot query tool version: {executable}: {result.stderr[-1000:]}")
    text = (result.stdout + result.stderr).strip().splitlines()
    return {
        "path": str(executable.resolve()),
        "sha256": sha256_file(executable.resolve()),
        "version": text[0] if text else "UNKNOWN",
    }


def validate_entrypoint(candidate: Path, profile: dict[str, Any], readelf: Path, ldd: Path) -> dict[str, Any]:
    entry = candidate / profile["entrypoint"]
    if not entry.is_file():
        raise PreflightError(f"entrypoint is absent: {profile['entrypoint']}")
    if not os.access(entry, os.X_OK):
        raise PreflightError(f"entrypoint is not executable: {profile['entrypoint']}")

    header = run_tool(readelf, ["-h", str(entry)], timeout=30)
    if header.returncode != 0:
        raise PreflightError(f"readelf rejected entrypoint: {header.stderr[-2000:]}")
    combined = header.stdout + header.stderr
    if "Class:" not in combined or "ELF64" not in combined or "X86-64" not in combined:
        raise PreflightError("entrypoint is not an ELF64 x86-64 executable")

    deps = run_tool(ldd, [str(entry)], timeout=30)
    dep_text = deps.stdout + deps.stderr
    if deps.returncode != 0:
        raise PreflightError(f"ldd failed for entrypoint: {dep_text[-2000:]}")
    if "not found" in dep_text:
        raise PreflightError(f"entrypoint has unresolved dynamic dependencies: {dep_text[-3000:]}")
    return {
        "path": profile["entrypoint"],
        "sha256": sha256_file(entry),
        "elf": "ELF64-x86_64",
        "dynamicDependencies": "RESOLVED",
        "lddOutput": dep_text.strip().splitlines(),
    }


def render_steam_vdf(profile: dict[str, Any], output: Path) -> dict[str, Any]:
    output.mkdir(parents=True, exist_ok=True)
    steam = profile["steam"]
    app = output / "app_build.template.vdf"
    depot = output / "depot_build.template.vdf"

    exclusions = "\n".join(f'    "FileExclusion" "{value}"' for value in steam["exclusions"])
    app_text = f'''"AppBuild"
{{
    "AppID" "{steam['appIdToken']}"
    "Desc" "{steam['description']}"
    "Preview" "1"
    "ContentRoot" "../content"
    "BuildOutput" "../build-output"
    "Depots"
    {{
        "{steam['depotIdToken']}" "depot_build.template.vdf"
    }}
}}
'''
    depot_text = f'''"DepotBuild"
{{
    "DepotID" "{steam['depotIdToken']}"
    "FileMapping"
    {{
        "LocalPath" "{steam['mapping']['localPath']}"
        "DepotPath" "{steam['mapping']['depotPath']}"
        "Recursive" "1"
    }}
{exclusions}
}}
'''
    app.write_text(app_text)
    depot.write_text(depot_text)
    return {
        "standing": "STATIC_TEMPLATE_ONLY",
        "appBuild": {"path": app.name, "sha256": sha256_file(app)},
        "depotBuild": {"path": depot.name, "sha256": sha256_file(depot)},
        "appId": "PLACEHOLDER_NOT_PROVISIONED",
        "depotId": "PLACEHOLDER_NOT_PROVISIONED",
        "realSteamPipePreview": "NOT_PERFORMED",
    }


def sync_tree(rclone: Path, source: Path, destination: Path) -> dict[str, Any]:
    destination.mkdir(parents=True, exist_ok=True)
    result = run_tool(rclone, ["sync", str(source), str(destination), "--checksum", "--metadata"], timeout=120)
    if result.returncode != 0:
        raise PreflightError(f"rclone sync failed: {result.stdout[-2000:]}\n{result.stderr[-2000:]}")
    return {"exitCode": result.returncode}


def assert_same_tree(expected: dict[str, Any], actual: dict[str, Any], label: str) -> None:
    if actual["treeDigest"] != expected["treeDigest"]:
        raise PreflightError(f"{label} tree does not exactly match candidate: {expected['treeDigest']} != {actual['treeDigest']}")


def launch(installed: Path, profile: dict[str, Any]) -> dict[str, Any]:
    entry = installed / profile["entrypoint"]
    result = subprocess.run(
        [str(entry), *profile["launch"]["args"]],
        cwd=installed,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=120,
        env={**os.environ, "LC_ALL": "C", "TZ": "UTC"},
    )
    combined = result.stdout + result.stderr
    if result.returncode != 0:
        raise PreflightError(f"installed entrypoint failed: {combined[-4000:]}")
    marker = profile["launch"]["successMarker"]
    if marker not in combined:
        raise PreflightError(f"installed entrypoint did not emit required marker: {marker}")
    return {"exitCode": result.returncode, "successMarker": marker, "observed": True}


def run_preflight(
    *,
    profile_path: Path,
    candidate_a: Path,
    candidate_b: Path,
    work_root: Path,
    vdf_dir: Path,
    rclone: Path,
    readelf: Path,
    ldd: Path,
    candidate_a_ref: str,
    candidate_b_ref: str,
) -> dict[str, Any]:
    profile = load_profile(profile_path)
    snap_a = snapshot_tree(candidate_a)
    snap_b = snapshot_tree(candidate_b)

    leakage_a = matching_paths(snap_a, profile["policy"]["forbiddenPaths"])
    leakage_b = matching_paths(snap_b, profile["policy"]["forbiddenPaths"])
    if leakage_a or leakage_b:
        raise PreflightError(f"forbidden release paths detected: A={leakage_a} B={leakage_b}")

    excluded_a = matching_paths(snap_a, profile["steam"]["exclusions"])
    excluded_b = matching_paths(snap_b, profile["steam"]["exclusions"])
    if excluded_a or excluded_b:
        raise PreflightError(f"candidate contains files that Steam mapping would exclude: A={excluded_a} B={excluded_b}")

    entry_a = validate_entrypoint(candidate_a, profile, readelf, ldd)
    entry_b = validate_entrypoint(candidate_b, profile, readelf, ldd)
    vdf = render_steam_vdf(profile, vdf_dir)

    if work_root.exists():
        shutil.rmtree(work_root)
    install = work_root / "install"

    sync_tree(rclone, candidate_a, install)
    clean_a = snapshot_tree(install)
    assert_same_tree(snap_a, clean_a, "clean install A")
    launch_a = launch(install, profile)

    sync_tree(rclone, candidate_b, install)
    updated = snapshot_tree(install)
    assert_same_tree(snap_b, updated, "update A->B")
    launch_b = launch(install, profile)

    sync_tree(rclone, candidate_a, install)
    rolled_back = snapshot_tree(install)
    assert_same_tree(snap_a, rolled_back, "rollback B->A")
    rollback_launch = launch(install, profile)

    shutil.rmtree(install)
    sync_tree(rclone, candidate_b, install)
    reinstalled = snapshot_tree(install)
    assert_same_tree(snap_b, reinstalled, "clean reinstall B")
    reinstall_launch = launch(install, profile)

    return {
        "schemaVersion": 1,
        "kind": "ordivon.distribution.local-preflight-receipt",
        "status": "PASS",
        "standing": "LOCAL_DISTRIBUTION_PREFLIGHT_PASS_REAL_PLATFORM_DEFERRED",
        "profile": {"path": str(profile_path.relative_to(ROOT)) if profile_path.is_relative_to(ROOT) else profile_path.name, "sha256": sha256_file(profile_path)},
        "target": profile["target"],
        "candidates": {
            "A": {"sourceRef": candidate_a_ref, **snap_a},
            "B": {"sourceRef": candidate_b_ref, **snap_b},
        },
        "admission": {
            "forbiddenPathLeakage": "PASS",
            "steamExclusionCollision": "PASS",
            "entrypointA": entry_a,
            "entrypointB": entry_b,
        },
        "steam": vdf,
        "lifecycle": {
            "cleanInstallA": {"status": "PASS", "treeDigest": clean_a["treeDigest"], "launch": launch_a},
            "updateAToB": {"status": "PASS", "treeDigest": updated["treeDigest"], "launch": launch_b, "staleFileDetection": "PASS_BY_EXACT_TREE_EQUALITY"},
            "rollbackBToA": {"status": "PASS", "treeDigest": rolled_back["treeDigest"], "launch": rollback_launch, "staleFileDetection": "PASS_BY_EXACT_TREE_EQUALITY"},
            "uninstallReinstallB": {"status": "PASS", "treeDigest": reinstalled["treeDigest"], "launch": reinstall_launch},
        },
        "tools": {
            "rclone": tool_fact(rclone, ["version"]),
            "readelf": tool_fact(readelf, ["--version"]),
            "ldd": tool_fact(ldd, ["--version"]),
        },
        "upstreamArtifactReleaseEvidence": {
            "standing": "NOT_BOUND_BY_THIS_PREFLIGHT",
            "owner": "Artifact",
            "note": "Distribution does not mint SBOM, SLSA/in-toto provenance, Sigstore trust, vulnerability, secret, or releaseReady claims.",
        },
        "claimsNotMinted": [
            "STEAM_BACKEND_ACCEPTANCE",
            "STEAMPIPE_PREVIEW_PASS",
            "STEAM_APP_ID",
            "STEAM_DEPOT_MANIFEST",
            "STEAM_BUILD_ID",
            "STEAM_CDN_INSTALL",
            "PUBLIC_RELEASE",
            "ARTIFACT_RELEASE_READY",
            "SBOM",
            "SLSA_PROVENANCE",
            "SIGNATURE_TRUST",
            "PLAYER_VALUE",
            "COMMERCIAL_READINESS"
        ],
        "boundary": "PASS proves exact local directory admission, ELF/runtime dependency sanity, provider-compatible Steam VDF template rendering, rclone-backed clean install, update, rollback, stale-file elimination, reinstall, and installed launch. It does not contact Steam or replace Artifact-owned software release evidence.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", type=Path, required=True)
    parser.add_argument("--candidate-a", type=Path, required=True)
    parser.add_argument("--candidate-b", type=Path, required=True)
    parser.add_argument("--candidate-a-ref", default="candidate:A")
    parser.add_argument("--candidate-b-ref", default="candidate:B")
    parser.add_argument("--work-root", type=Path)
    parser.add_argument("--vdf-dir", type=Path)
    parser.add_argument("--receipt", type=Path)
    parser.add_argument("--rclone", type=Path, default=Path("/usr/bin/rclone"))
    parser.add_argument("--readelf", type=Path, default=Path("/usr/bin/readelf"))
    parser.add_argument("--ldd", type=Path, default=Path("/usr/bin/ldd"))
    args = parser.parse_args()

    temporary: tempfile.TemporaryDirectory[str] | None = None
    try:
        if args.work_root is None or args.vdf_dir is None:
            temporary = tempfile.TemporaryDirectory(prefix="ordivon-distribution-preflight-")
            base = Path(temporary.name)
            work_root = args.work_root or (base / "lifecycle")
            vdf_dir = args.vdf_dir or (base / "steam")
        else:
            work_root = args.work_root
            vdf_dir = args.vdf_dir
        receipt = run_preflight(
            profile_path=args.profile.resolve(),
            candidate_a=args.candidate_a.resolve(),
            candidate_b=args.candidate_b.resolve(),
            work_root=work_root.resolve(),
            vdf_dir=vdf_dir.resolve(),
            rclone=args.rclone.resolve(),
            readelf=args.readelf.resolve(),
            ldd=args.ldd.resolve(),
            candidate_a_ref=args.candidate_a_ref,
            candidate_b_ref=args.candidate_b_ref,
        )
        text = json.dumps(receipt, indent=2, ensure_ascii=False) + "\n"
        if args.receipt:
            args.receipt.parent.mkdir(parents=True, exist_ok=True)
            args.receipt.write_text(text)
        print(text, end="")
        return 0
    except Exception as error:
        print(json.dumps({"status": "FAIL", "error": str(error)}, ensure_ascii=False))
        return 1
    finally:
        if temporary is not None:
            temporary.cleanup()


if __name__ == "__main__":
    raise SystemExit(main())
