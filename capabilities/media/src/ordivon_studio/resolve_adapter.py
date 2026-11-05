from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import secrets
import shutil
from pathlib import Path
from typing import Any

from .assets import hash_file
from .resolve_contracts import (
    _DIGEST,
    _OPERATION_ID,
    ASSEMBLY_CONFORM_PROJECT_PREFIX,
    ASSEMBLY_CONFORM_TIMELINE_NAME,
    COMPATIBILITY_PRODUCT_NAME,
    validate_result,
)
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
    _build_assembly_source_parameters,
    _windows_child,
    _write_compatibility_otio,
    _write_resolve_assembly_otio,
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
COMPATIBILITY_PROJECT_PREFIX = "Ordivon Resolve 21 Compatibility "
COMPATIBILITY_VERSION = [21, 0, 3, 7, ""]
DEVELOPER_README_PATH = Path(
    "/mnt/c/ProgramData/Blackmagic Design/DaVinci Resolve/Support/Developer/Scripting/README.txt"
)
ASSEMBLY_CONFORM_OTIO_FILENAME = "assembly.v0.resolve-21.0.3.7.otio"


def _canonical_digest(value: object) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return f"sha256:{hashlib.sha256(payload).hexdigest()}"


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


def _new_operation_id(kind: str) -> str:
    timestamp = dt.datetime.now(dt.UTC).strftime("%Y%m%dt%H%M%Sz").lower()
    return f"resolve-{kind}-{timestamp}-{secrets.token_hex(4)}"


def _requested_at() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _validate_operation_id(operation_id: str) -> str:
    if not _OPERATION_ID.fullmatch(operation_id):
        raise ValueError("operationId has an invalid format")
    return operation_id


def build_probe_operation(operation_id: str | None = None) -> dict[str, Any]:
    operation_id = _validate_operation_id(operation_id or _new_operation_id("probe"))
    return {
        "schemaVersion": 1,
        "operationId": operation_id,
        "action": "probe",
        "requestedAt": _requested_at(),
    }


def build_smoke_operation(
    *,
    media_path: str,
    media_digest: str,
    operation_id: str | None = None,
    project_name: str | None = None,
) -> dict[str, Any]:
    operation_id = _validate_operation_id(operation_id or _new_operation_id("smoke"))
    if not _DIGEST.fullmatch(media_digest):
        raise ValueError("mediaDigest must be a sha256 digest")
    suffix = operation_id.removeprefix("resolve-smoke-")
    project_name = project_name or f"Ordivon Resolve Smoke {suffix}"
    if not project_name.startswith("Ordivon Resolve Smoke "):
        raise ValueError("smoke project name must use the reserved prefix")
    return {
        "schemaVersion": 1,
        "operationId": operation_id,
        "action": "create-smoke-project",
        "requestedAt": _requested_at(),
        "parameters": {
            "projectName": project_name,
            "timelineName": "Assembly",
            "binName": "01_SMOKE",
            "mediaPath": media_path,
            "mediaDigest": media_digest,
            "settings": {"frameRate": 30, "width": 1920, "height": 1080},
            "restorePreviousProject": True,
        },
    }


def build_compatibility_operation(
    *,
    media_path: str,
    media_digest: str,
    media_file_name: str,
    media_expected_frames: int,
    otio_path: str,
    otio_digest: str,
    source_clips_path: str,
    developer_package_digest: str,
    operation_id: str | None = None,
) -> dict[str, Any]:
    operation_id = _validate_operation_id(operation_id or _new_operation_id("compatibility"))
    if not _DIGEST.fullmatch(media_digest):
        raise ValueError("mediaDigest must be a sha256 digest")
    if not _DIGEST.fullmatch(otio_digest):
        raise ValueError("otioDigest must be a sha256 digest")
    if not _DIGEST.fullmatch(developer_package_digest):
        raise ValueError("developerPackageDigest must be a sha256 digest")
    if media_expected_frames < 60:
        raise ValueError("compatibility media must contain at least 60 frames")
    suffix = operation_id.removeprefix("resolve-compatibility-")
    return {
        "schemaVersion": 1,
        "operationId": operation_id,
        "action": "probe-compatibility",
        "requestedAt": _requested_at(),
        "parameters": {
            "projectName": COMPATIBILITY_PROJECT_PREFIX + suffix,
            "expectedProductName": COMPATIBILITY_PRODUCT_NAME,
            "expectedVersionString": COMPATIBILITY_VERSION_STRING,
            "expectedVersion": COMPATIBILITY_VERSION,
            "developerPackageDigest": developer_package_digest,
            "mediaPath": media_path,
            "mediaDigest": media_digest,
            "mediaFileName": media_file_name,
            "mediaExpectedFrames": media_expected_frames,
            "otioPath": otio_path,
            "otioDigest": otio_digest,
            "sourceClipsPath": source_clips_path,
            "settings": {"frameRate": 30, "width": 1920, "height": 1080},
            "restorePreviousProject": True,
            "cleanupProject": True,
        },
    }


def build_assembly_conform_operation(
    *,
    production_root: Path,
    media_root: Path,
    windows_media_root: str,
    resolve_otio_path: Path,
    windows_resolve_otio_path: str,
    developer_readme_path: Path = DEVELOPER_README_PATH,
    operation_id: str | None = None,
) -> dict[str, Any]:
    operation_id = _validate_operation_id(operation_id or _new_operation_id("assembly-conform"))
    parameters = _build_assembly_source_parameters(
        production_root=production_root,
        media_root=media_root,
        windows_media_root=windows_media_root,
    )
    suffix = operation_id.removeprefix("resolve-assembly-conform-")
    _write_resolve_assembly_otio(
        resolve_otio_path,
        production_id=parameters["productionId"],
        start_timecode=parameters["startTimecode"],
        segments=parameters["segments"],
    )
    parameters.update(
        {
            "projectName": ASSEMBLY_CONFORM_PROJECT_PREFIX + suffix,
            "timelineName": ASSEMBLY_CONFORM_TIMELINE_NAME,
            "expectedProductName": COMPATIBILITY_PRODUCT_NAME,
            "expectedVersionString": COMPATIBILITY_VERSION_STRING,
            "expectedVersion": COMPATIBILITY_VERSION,
            "developerPackageDigest": hash_file(developer_readme_path).digest,
            "resolveOtioPath": windows_resolve_otio_path,
            "resolveOtioDigest": hash_file(resolve_otio_path).digest,
            "cleanupProject": True,
        }
    )
    return {
        "schemaVersion": 1,
        "operationId": operation_id,
        "action": "probe-assembly-conform",
        "requestedAt": _requested_at(),
        "parameters": parameters,
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
    if errors:
        raise ValueError("; ".join(errors))
    return value
