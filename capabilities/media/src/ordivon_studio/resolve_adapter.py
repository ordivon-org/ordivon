from __future__ import annotations

import json
import os
import shutil
from pathlib import Path
from typing import Any

from .assets import hash_file
from .resolve_contracts import COMPATIBILITY_PRODUCT_NAME, _canonical_digest, validate_result
from .resolve_discovery import (
    _media_frame_count,
    _resolved_paths,
    _wslpath,
    discover_production_media,
    discover_resolve_paths,
    discover_smoke_fixture,
)
from .resolve_editorial import (
    COMPATIBILITY_VERSION_STRING,
    _windows_child,
    _write_compatibility_otio,
)
from .resolve_operations import (
    DEVELOPER_README_PATH,
    build_assembly_conform_operation,
    build_compatibility_operation,
    build_probe_operation,
    build_smoke_operation,
)

# Editorial inspection/range validation belongs to the external OpenTimelineIO
# gate under processing/, using pinned otiotool.
# Resolve-private OTIO serialization and exact selected-asset binding live in
# resolve_editorial. This adapter retains operation preparation, discovery and
# result readback. Pure result checks are in resolve_contracts;
# neither layer replaces the external OTIO validation gate.

RUNNER_FILENAME = "Ordivon Studio Runner.py"
CONFIG_FILENAME = "ordivon-runner.config.json"
OPERATION_FILENAME = "resolve-operation.json"
RESULT_FILENAME = "resolve-result.json"
COMPATIBILITY_OTIO_FILENAME = "resolve-21.0.3.7-compatibility.otio"
ASSEMBLY_CONFORM_OTIO_FILENAME = "assembly.v0.resolve-21.0.3.7.otio"


def _atomic_write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f"{path.name}.tmp-{os.getpid()}")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def install_runner(
    *,
    scripts_directory: Path | None = None,
    control_directory: Path | None = None,
    windows_control_directory: str | None = None,
) -> dict[str, Any]:
    paths = _resolved_paths(
        scripts_directory=scripts_directory,
        control_directory=control_directory,
        windows_control_directory=windows_control_directory,
    )
    source = Path(__file__).resolve().with_name("resolve_runner_menu.py")
    if not source.is_file():
        raise FileNotFoundError(source)

    paths.scripts_directory.mkdir(parents=True, exist_ok=True)
    paths.control_directory.mkdir(parents=True, exist_ok=True)
    destination = paths.scripts_directory / RUNNER_FILENAME
    shutil.copyfile(source, destination)
    config = {
        "schemaVersion": 1,
        "controlDirectory": paths.windows_control_directory,
    }
    _atomic_write_json(paths.scripts_directory / CONFIG_FILENAME, config)
    return {
        "installed": True,
        "runner": str(destination),
        "config": str(paths.scripts_directory / CONFIG_FILENAME),
        "controlDirectory": str(paths.control_directory),
        "menu": "Workspace > Scripts > Utility > Ordivon > Ordivon Studio Runner",
    }
















def _prepare_operation(control: Path, operation: dict[str, Any]) -> dict[str, Any]:
    path = control / OPERATION_FILENAME
    _atomic_write_json(path, operation)
    stale_result = control / RESULT_FILENAME
    if stale_result.exists():
        stale_result.unlink()
    return {
        "prepared": True,
        "operation": operation,
        "operationDigest": _canonical_digest(operation),
        "operationPath": str(path),
    }


def prepare_probe(*, control_directory: Path | None = None, operation_id: str | None = None) -> dict[str, Any]:
    control = control_directory or discover_resolve_paths().control_directory
    return _prepare_operation(control, build_probe_operation(operation_id))


def prepare_smoke(
    *,
    control_directory: Path | None = None,
    media_path: Path | None = None,
    windows_media_path: str | None = None,
    operation_id: str | None = None,
) -> dict[str, Any]:
    control = control_directory or discover_resolve_paths().control_directory
    if media_path is None and windows_media_path is None:
        media_path, windows_media_path = discover_smoke_fixture()
    elif media_path is None:
        media_path = Path(_wslpath(windows_media_path, "-u"))  # type: ignore[arg-type]
    elif windows_media_path is None:
        windows_media_path = _wslpath(str(media_path), "-w")
    digest = hash_file(media_path).digest
    operation = build_smoke_operation(
        media_path=windows_media_path,
        media_digest=digest,
        operation_id=operation_id,
    )
    prepared = _prepare_operation(control, operation)
    prepared["media"] = {
        "path": str(media_path),
        "digest": digest,
        "sizeBytes": media_path.stat().st_size,
    }
    return prepared


def prepare_compatibility(
    *,
    control_directory: Path | None = None,
    media_path: Path | None = None,
    windows_media_path: str | None = None,
    developer_readme_path: Path | None = None,
    operation_id: str | None = None,
) -> dict[str, Any]:
    control = control_directory or discover_resolve_paths().control_directory
    if media_path is None and windows_media_path is None:
        media_path, windows_media_path = discover_smoke_fixture()
    elif media_path is None:
        media_path = Path(_wslpath(windows_media_path, "-u"))  # type: ignore[arg-type]
    elif windows_media_path is None:
        windows_media_path = _wslpath(str(media_path), "-w")
    if media_path is None or windows_media_path is None:
        raise RuntimeError("compatibility media path resolution failed")
    media_frames = _media_frame_count(media_path)
    source_clips_path = windows_media_path.rsplit("\\", 1)[0]
    otio_path = media_path.parent / COMPATIBILITY_OTIO_FILENAME
    windows_otio_path = source_clips_path + "\\" + COMPATIBILITY_OTIO_FILENAME
    _write_compatibility_otio(
        otio_path,
        windows_media_path=windows_media_path,
        media_frames=media_frames,
    )
    developer_readme = developer_readme_path or DEVELOPER_README_PATH
    operation = build_compatibility_operation(
        media_path=windows_media_path,
        media_digest=hash_file(media_path).digest,
        media_file_name=media_path.name,
        media_expected_frames=media_frames,
        otio_path=windows_otio_path,
        otio_digest=hash_file(otio_path).digest,
        source_clips_path=source_clips_path,
        developer_package_digest=hash_file(developer_readme).digest,
        operation_id=operation_id,
    )
    prepared = _prepare_operation(control, operation)
    prepared["compatibility"] = {
        "expectedProductName": COMPATIBILITY_PRODUCT_NAME,
        "expectedVersionString": COMPATIBILITY_VERSION_STRING,
        "developerPackageDigest": operation["parameters"]["developerPackageDigest"],
        "mediaDigest": operation["parameters"]["mediaDigest"],
        "mediaExpectedFrames": media_frames,
        "otioDigest": operation["parameters"]["otioDigest"],
        "caseCount": 6,
        "cleanupProject": True,
    }
    return prepared


def prepare_assembly_conform(
    *,
    production_id: str = "runtime-introduction",
    production_root: Path | None = None,
    control_directory: Path | None = None,
    media_root: Path | None = None,
    windows_media_root: str | None = None,
    resolve_otio_root: Path | None = None,
    windows_resolve_otio_root: str | None = None,
    developer_readme_path: Path | None = None,
    operation_id: str | None = None,
) -> dict[str, Any]:
    repository_root = Path(__file__).resolve().parents[2]
    production_root = production_root or repository_root / "productions" / production_id
    control = control_directory or discover_resolve_paths().control_directory
    if media_root is None and windows_media_root is None:
        discovered = discover_production_media(production_id)
        media_root = discovered.directory
        windows_media_root = discovered.windows_directory
    elif media_root is None:
        media_root = Path(_wslpath(windows_media_root, "-u"))  # type: ignore[arg-type]
    elif windows_media_root is None:
        windows_media_root = _wslpath(str(media_root), "-w")
    if media_root is None or windows_media_root is None:
        raise RuntimeError("assembly conform media path resolution failed")

    if resolve_otio_root is None and windows_resolve_otio_root is None:
        resolve_otio_root = media_root.parent / "resolve"
        windows_resolve_otio_root = windows_media_root.rsplit("\\", 1)[0] + r"\resolve"
    elif resolve_otio_root is None:
        resolve_otio_root = Path(_wslpath(windows_resolve_otio_root, "-u"))  # type: ignore[arg-type]
    elif windows_resolve_otio_root is None:
        windows_resolve_otio_root = _wslpath(str(resolve_otio_root), "-w")
    if resolve_otio_root is None or windows_resolve_otio_root is None:
        raise RuntimeError("assembly conform OTIO path resolution failed")

    resolve_otio_path = resolve_otio_root / ASSEMBLY_CONFORM_OTIO_FILENAME
    windows_resolve_otio_path = _windows_child(windows_resolve_otio_root, ASSEMBLY_CONFORM_OTIO_FILENAME)
    operation = build_assembly_conform_operation(
        production_root=production_root,
        media_root=media_root,
        windows_media_root=windows_media_root,
        resolve_otio_path=resolve_otio_path,
        windows_resolve_otio_path=windows_resolve_otio_path,
        developer_readme_path=developer_readme_path or DEVELOPER_README_PATH,
        operation_id=operation_id,
    )
    prepared = _prepare_operation(control, operation)
    prepared["assemblyConform"] = {
        "productionId": production_id,
        "resolveProfile": "resolve-free-21.0.3.7-windows-internal-menu",
        "segmentCount": len(operation["parameters"]["segments"]),
        "totalFrames": operation["parameters"]["totalFrames"],
        "totalSeconds": operation["parameters"]["totalFrames"] / 30,
        "resolveOtioDigest": operation["parameters"]["resolveOtioDigest"],
        "cleanupProject": True,
    }
    return prepared


def read_result(
    *, control_directory: Path | None = None, expected_operation_id: str | None = None
) -> dict[str, Any]:
    control = control_directory or discover_resolve_paths().control_directory
    path = control / RESULT_FILENAME
    if not path.is_file():
        raise FileNotFoundError(path)
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError("Resolve result root must be an object")
    errors = validate_result(value, expected_operation_id=expected_operation_id)
    staged_path = control / OPERATION_FILENAME
    if value.get("status") == "succeeded" and staged_path.is_file():
        staged = json.loads(staged_path.read_text(encoding="utf-8-sig"))
        if not isinstance(staged, dict):
            raise ValueError("staged Resolve operation root must be an object")
        if value.get("operationId") != staged.get("operationId"):
            errors.append("result operationId does not match staged operation")
        if value.get("operationDigest") != _canonical_digest(staged):
            errors.append("result operationDigest does not match staged operation")
    if errors:
        raise ValueError("; ".join(errors))
    return value
