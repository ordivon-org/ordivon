"""Self-contained DaVinci Resolve menu runner.

This module is copied into Resolve's user Scripts/Utility directory. It must
remain standard-library-only and compatible with the Python runtime embedded by
Resolve. Ordivon Studio prepares one bounded operation file; the menu script
executes it inside Resolve and writes one structured result.
"""

import datetime
import hashlib
import json
import os
import re
from pathlib import Path


ADAPTER_VERSION = "0.1.0"
CONFIG_NAME = "ordivon-runner.config.json"
OPERATION_NAME = "resolve-operation.json"
RESULT_NAME = "resolve-result.json"
_OPERATION_ID = re.compile(r"^[a-z0-9]+(?:[._-][a-z0-9]+)*$")


def _utc_now():
    return datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def _canonical_digest(value):
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _atomic_write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp-" + str(os.getpid()))
    with temporary.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(str(temporary), str(path))


def _load_json(path):
    with path.open("r", encoding="utf-8-sig") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError("JSON root must be an object")
    return value


def validate_operation(operation):
    if not isinstance(operation, dict):
        raise ValueError("operation must be an object")
    allowed = {"schemaVersion", "operationId", "action", "requestedAt"}
    unknown = sorted(set(operation) - allowed)
    if unknown:
        raise ValueError("unknown operation fields: " + ", ".join(unknown))
    if operation.get("schemaVersion") != 1:
        raise ValueError("schemaVersion must be 1")
    operation_id = operation.get("operationId")
    if not isinstance(operation_id, str) or not _OPERATION_ID.fullmatch(operation_id):
        raise ValueError("operationId has an invalid format")
    if operation.get("action") != "probe":
        raise ValueError("v0 supports only the probe action")
    requested_at = operation.get("requestedAt")
    if requested_at is not None and (not isinstance(requested_at, str) or not requested_at):
        raise ValueError("requestedAt must be a non-empty string when present")
    return operation


def _safe_call(target, method_name, warnings, default=None, *args):
    if target is None:
        return default
    method = getattr(target, method_name, None)
    if not callable(method):
        warnings.append(method_name + " is unavailable")
        return default
    try:
        return method(*args)
    except Exception as error:  # Resolve exposes native objects with varied exceptions.
        warnings.append(method_name + " failed: " + type(error).__name__)
        return default


def acquire_resolve():
    existing = globals().get("resolve")
    if existing:
        return existing, "injected-resolve"

    application = globals().get("app")
    getter = getattr(application, "GetResolve", None)
    if callable(getter):
        candidate = getter()
        if candidate:
            return candidate, "injected-app"

    fusion = globals().get("fusion")
    getter = getattr(fusion, "GetResolve", None)
    if callable(getter):
        candidate = getter()
        if candidate:
            return candidate, "injected-fusion"

    try:
        import DaVinciResolveScript as bmd
    except ImportError:
        try:
            import importlib.util

            program_data = os.environ.get("PROGRAMDATA")
            if not program_data:
                raise RuntimeError("PROGRAMDATA is unavailable")
            module_path = (
                Path(program_data)
                / "Blackmagic Design"
                / "DaVinci Resolve"
                / "Support"
                / "Developer"
                / "Scripting"
                / "Modules"
                / "DaVinciResolveScript.py"
            )
            specification = importlib.util.spec_from_file_location("DaVinciResolveScript", str(module_path))
            if specification is None or specification.loader is None:
                raise RuntimeError("cannot load DaVinciResolveScript specification")
            bmd = importlib.util.module_from_spec(specification)
            specification.loader.exec_module(bmd)
        except Exception:
            bmd = None
    try:
        candidate = bmd.scriptapp("Resolve") if bmd else None
        if candidate:
            return candidate, "scriptapp"
    except Exception:
        pass
    return None, "unavailable"


def probe_resolve(resolve_object, acquisition):
    warnings = []
    product_name = _safe_call(resolve_object, "GetProductName", warnings)
    version_string = _safe_call(resolve_object, "GetVersionString", warnings)
    version = _safe_call(resolve_object, "GetVersion", warnings, [])
    current_page = _safe_call(resolve_object, "GetCurrentPage", warnings)
    project_manager = _safe_call(resolve_object, "GetProjectManager", warnings)

    database = _safe_call(project_manager, "GetCurrentDatabase", warnings, {})
    safe_database = {}
    if isinstance(database, dict):
        for key in ("DbType", "DbName"):
            value = database.get(key)
            if isinstance(value, (str, int, float, bool)) or value is None:
                safe_database[key] = value

    project = _safe_call(project_manager, "GetCurrentProject", warnings)
    project_result = None
    media_pool_available = False
    if project:
        timeline = _safe_call(project, "GetCurrentTimeline", warnings)
        timeline_name = _safe_call(timeline, "GetName", warnings) if timeline else None
        media_pool_available = bool(_safe_call(project, "GetMediaPool", warnings))
        project_result = {
            "name": _safe_call(project, "GetName", warnings),
            "timelineCount": _safe_call(project, "GetTimelineCount", warnings, 0),
            "currentTimeline": timeline_name,
            "timelineFrameRate": _safe_call(project, "GetSetting", warnings, None, "timelineFrameRate"),
            "timelineResolutionWidth": _safe_call(
                project, "GetSetting", warnings, None, "timelineResolutionWidth"
            ),
            "timelineResolutionHeight": _safe_call(
                project, "GetSetting", warnings, None, "timelineResolutionHeight"
            ),
        }

    return {
        "acquisition": acquisition,
        "productName": product_name,
        "versionString": version_string,
        "version": version if isinstance(version, (list, tuple)) else [],
        "currentPage": current_page,
        "database": safe_database,
        "project": project_result,
        "capabilities": {
            "resolveObject": bool(resolve_object),
            "projectManager": bool(project_manager),
            "currentProject": bool(project),
            "mediaPool": media_pool_available,
        },
        "warnings": warnings,
    }


def execute_operation(operation, resolve_object=None, acquisition=None):
    validate_operation(operation)
    if resolve_object is None:
        resolve_object, acquisition = acquire_resolve()
    if not resolve_object:
        raise RuntimeError("Resolve application object is unavailable in the menu-script context")
    return probe_resolve(resolve_object, acquisition or "provided")


def _default_control_directory():
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        return Path(local_app_data) / "OrdivonStudio" / "control"
    return Path.home() / "AppData" / "Local" / "OrdivonStudio" / "control"


def _script_path():
    value = globals().get("__file__")
    if isinstance(value, str) and value:
        return Path(value).resolve()
    return None


def control_directory():
    script_path = _script_path()
    if script_path is None:
        return _default_control_directory()
    config_path = script_path.with_name(CONFIG_NAME)
    if not config_path.is_file():
        return _default_control_directory()
    config = _load_json(config_path)
    if config.get("schemaVersion") != 1:
        raise ValueError("runner config schemaVersion must be 1")
    configured = config.get("controlDirectory")
    if not isinstance(configured, str) or not configured.strip():
        raise ValueError("runner config controlDirectory must be a non-empty string")
    return Path(configured)


def _safe_error_message(error, control):
    message = str(error) or type(error).__name__
    replacements = [str(control), str(Path.home())]
    script_path = _script_path()
    if script_path is not None:
        replacements.append(str(script_path))
    for value in replacements:
        if value:
            message = message.replace(value, "<local>")
    return message[:500]


def main():
    started_at = _utc_now()
    operation = None
    control = _default_control_directory()
    try:
        control = control_directory()
        operation_path = control / OPERATION_NAME
        if not operation_path.is_file():
            raise FileNotFoundError("no pending resolve-operation.json")
        operation = validate_operation(_load_json(operation_path))
        payload = execute_operation(operation)
        result = {
            "schemaVersion": 1,
            "adapter": "resolve",
            "adapterVersion": ADAPTER_VERSION,
            "operationId": operation["operationId"],
            "operationDigest": _canonical_digest(operation),
            "action": operation["action"],
            "status": "succeeded",
            "startedAt": started_at,
            "finishedAt": _utc_now(),
            "probe": payload,
        }
    except Exception as error:
        result = {
            "schemaVersion": 1,
            "adapter": "resolve",
            "adapterVersion": ADAPTER_VERSION,
            "operationId": operation.get("operationId") if isinstance(operation, dict) else None,
            "operationDigest": _canonical_digest(operation) if isinstance(operation, dict) else None,
            "action": operation.get("action") if isinstance(operation, dict) else "probe",
            "status": "failed",
            "startedAt": started_at,
            "finishedAt": _utc_now(),
            "error": {
                "type": type(error).__name__,
                "message": _safe_error_message(error, control),
            },
        }

    try:
        _atomic_write_json(control / RESULT_NAME, result)
        print("Ordivon Studio Runner: " + result["status"])
        if result.get("operationId"):
            print("Operation: " + result["operationId"])
    except Exception as write_error:
        print("Ordivon Studio Runner could not write its result: " + type(write_error).__name__)
        return 2
    return 0 if result["status"] == "succeeded" else 1


if __name__ == "__main__":
    main()
