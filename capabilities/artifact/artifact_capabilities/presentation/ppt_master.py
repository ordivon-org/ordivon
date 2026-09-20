from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from artifact_core.contracts import file_fact, sha256_file
from artifact_core.profile_v1 import validate_profile_v1 as validate_profile

from .common import (
    DEFAULT_PRESENTATION_SEMANTIC_SVG_SOURCE_SCHEMA,
    PPT_MASTER_PROVIDER_LOCK,
    PresentationBuildHooks,
    _resolve_semantic_svg_source_path,
    _safe_project_relative_path,
    _semantic_svg_source_material_facts,
)


def _ppt_master_provider_facts() -> tuple[dict[str, Any], list[str]]:
    failures: list[str] = []
    try:
        lock = json.loads(PPT_MASTER_PROVIDER_LOCK.read_text(encoding="utf-8"))
    except Exception as error:
        return {"lock": {"path": str(PPT_MASTER_PROVIDER_LOCK)}}, [f"PPT Master provider lock could not be read: {error}"]
    configured_root = os.environ.get("ARTIFACT_PPT_MASTER_ROOT")
    root = Path(configured_root or "/opt/ordivon/external/ppt-master/current").resolve()
    python_path = Path(os.path.abspath(os.path.expanduser(os.environ.get("ARTIFACT_PPT_MASTER_PYTHON", str(root / ".venv-exp/bin/python")))))
    entrypoints = lock.get("entrypoints", {}) if isinstance(lock, dict) else {}
    quality_checker = root / str(entrypoints.get("qualityChecker", ""))
    exporter = root / str(entrypoints.get("exporter", ""))
    expected_commit = str((lock.get("source", {}) if isinstance(lock, dict) else {}).get("commit", ""))
    observed_commit: str | None = None
    tracked_worktree_clean = False
    if not root.is_dir():
        failures.append(f"PPT Master provider root is unavailable: {root}")
    else:
        proc = subprocess.run(
            ["/usr/bin/git", "-C", str(root), "rev-parse", "HEAD"],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=20,
        )
        if proc.returncode != 0:
            failures.append("PPT Master provider root is not a readable Git checkout")
        else:
            observed_commit = proc.stdout.strip()
            if observed_commit != expected_commit:
                failures.append(f"PPT Master provider commit mismatch: expected {expected_commit}, got {observed_commit}")
            status_proc = subprocess.run(
                ["/usr/bin/git", "-C", str(root), "status", "--porcelain", "--untracked-files=no"],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
                timeout=20,
            )
            if status_proc.returncode != 0:
                failures.append("PPT Master provider tracked-worktree status could not be established")
            elif status_proc.stdout.strip():
                failures.append("PPT Master provider tracked worktree differs from the pinned commit")
            else:
                tracked_worktree_clean = True
    for label, path in (("python", python_path), ("qualityChecker", quality_checker), ("exporter", exporter)):
        if not path.is_file():
            failures.append(f"PPT Master provider {label} is unavailable: {path}")
    provider_files = {}
    for label, path in (("python", python_path), ("qualityChecker", quality_checker), ("exporter", exporter)):
        if path.is_file():
            provider_files[label] = file_fact(path)
    provider = {
        "providerId": lock.get("providerId") if isinstance(lock, dict) else None,
        "root": str(root),
        "expectedCommit": expected_commit,
        "observedCommit": observed_commit,
        "python": str(python_path),
        "qualityChecker": str(quality_checker),
        "exporter": str(exporter),
        "files": provider_files,
        "trackedWorktreeClean": tracked_worktree_clean,
        "lock": file_fact(PPT_MASTER_PROVIDER_LOCK) if PPT_MASTER_PROVIDER_LOCK.is_file() else {"path": str(PPT_MASTER_PROVIDER_LOCK)},
    }
    return provider, failures


def build_semantic_svg_presentation_source(
    source_path: Path,
    profile_path: Path,
    output_path: Path,
    source_schema_path: Path = DEFAULT_PRESENTATION_SEMANTIC_SVG_SOURCE_SCHEMA,
    *,
    hooks: PresentationBuildHooks,
) -> dict[str, Any]:
    source_result = hooks.validate_json_document(source_path, source_schema_path, "presentation-semantic-svg-source")
    profile_result = validate_profile(profile_path)
    source = source_result.get("document", {}) if isinstance(source_result, dict) else {}
    profile = profile_result.get("profile", {}) if isinstance(profile_result, dict) else {}
    failures: list[str] = []
    if source_result.get("status") != "PASS":
        failures.append("semantic SVG presentation source schema did not PASS")
    if profile_result.get("status") != "PASS":
        failures.append("delivery profile schema did not PASS")
    if isinstance(source, dict) and source.get("profileId") != profile.get("id"):
        failures.append("semantic SVG presentation source profileId does not match selected profile")
    source_materials, material_failures = _semantic_svg_source_material_facts(source_path, source if isinstance(source, dict) else {})
    failures.extend(material_failures)
    provider, provider_failures = _ppt_master_provider_facts()
    failures.extend(provider_failures)
    if failures:
        return {
            "status": "FAIL",
            "source": file_fact(source_path),
            "profile": file_fact(profile_path),
            "provider": provider,
            "sourceValidation": source_result,
            "materials": source_materials,
            "failures": failures,
        }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    quality_receipt: dict[str, Any] = {}
    export_receipt: dict[str, Any] = {}
    with tempfile.TemporaryDirectory(prefix="ordivon-artifact-ppt-master-parent-") as temp_dir:
        project = Path(temp_dir) / "ordivon-artifact-ppt-master-project"
        project.mkdir()
        svg_output = project / "svg_output"
        svg_output.mkdir(parents=True)
        (project / "validation").mkdir()
        (project / "exports").mkdir()
        for index, page in enumerate(source.get("pages", []), start=1):
            page_path = _resolve_semantic_svg_source_path(source_path, str(page["path"]))
            destination = svg_output / f"{index:03d}_{page_path.name}"
            shutil.copyfile(page_path, destination)
        for item in source.get("materials", []):
            material_path = _resolve_semantic_svg_source_path(source_path, str(item["path"]))
            relative = _safe_project_relative_path(str(item["projectRelativePath"]))
            destination = project.joinpath(*relative.parts)
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(material_path, destination)
        quality_cmd = [
            provider["python"],
            provider["qualityChecker"],
            str(project),
            "--quick-generate",
            "--canonical-authoring",
            "--stage",
            "final",
            "--json",
        ]
        quality_proc = subprocess.run(
            quality_cmd,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=120,
        )
        report_path = project / "validation/svg_quality_report.json"
        quality_receipt = {
            "returnCode": quality_proc.returncode,
            "stdoutTail": quality_proc.stdout[-6000:],
            "stderrTail": quality_proc.stderr[-4000:],
            "reportDigest": sha256_file(report_path) if report_path.is_file() else None,
        }
        if quality_proc.returncode != 0:
            failures.append("PPT Master semantic SVG quality gate did not PASS")
        if not failures:
            export_cmd = [
                provider["python"],
                provider["exporter"],
                str(project),
                "--quick-generate",
                "--primary-language",
                str(source["locale"]),
                "-t",
                "none",
                "-o",
                str(output_path),
            ]
            if bool(source.get("nativeChartsAndTables")):
                export_cmd.insert(-2, "--native-charts-and-tables")
            export_proc = subprocess.run(
                export_cmd,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
                timeout=180,
            )
            export_receipt = {
                "returnCode": export_proc.returncode,
                "stdoutTail": export_proc.stdout[-6000:],
                "stderrTail": export_proc.stderr[-4000:],
            }
            if export_proc.returncode != 0 or not output_path.is_file():
                failures.append("PPT Master semantic SVG export did not PASS")

    if failures or not output_path.is_file():
        return {
            "status": "FAIL",
            "source": file_fact(source_path),
            "profile": file_fact(profile_path),
            "provider": provider,
            "sourceValidation": source_result,
            "materials": source_materials,
            "quality": quality_receipt,
            "export": export_receipt,
            "failures": failures or ["primary PPTX output is absent"],
        }
    container_normalization = hooks.canonicalize_ppt_master(output_path)
    built = hooks.inspect_pptx(output_path, profile.get("semanticPolicy", {}).get("placeholderPatterns", []))
    semantic = hooks.verify_semantics(profile, built)
    if built.get("status") != "PASS":
        failures.append("PPT Master output failed package/relationship inspection")
    if semantic.get("status") != "PASS":
        failures.append("PPT Master output failed presentation semantic checks")
    return {
        "status": "PASS" if not failures else "FAIL",
        "source": file_fact(source_path),
        "profile": file_fact(profile_path),
        "artifact": file_fact(output_path),
        "presentationId": source.get("presentationId"),
        "builder": {
            "implementation": "ppt-master",
            "providerId": provider.get("providerId"),
            "commit": provider.get("observedCommit"),
        },
        "provider": provider,
        "materials": source_materials,
        "quality": quality_receipt,
        "export": export_receipt,
        "containerNormalization": container_normalization,
        "inspection": built,
        "semantic": semantic,
        "failures": failures,
        "boundary": "Builder PASS establishes digest-bound semantic SVG/material inputs, exact external PPT Master source identity, provider quality-gate success, and native PPTX package/semantic checks. Artifact Open XML SDK, Microsoft PowerPoint target, visual, accessibility and delivery gates remain independent.",
    }

