"""Self-contained DaVinci Resolve menu runner.

This module is copied into Resolve's user Scripts/Utility directory. It stays
standard-library-only and compatible with Resolve's embedded Python runtime.
Ordivon Studio prepares one bounded operation; the menu script executes it
inside Resolve and writes one structured result.
"""

import datetime
import hashlib
import json
import os
import re
from pathlib import Path


ADAPTER_VERSION = "0.2.0"
CONFIG_NAME = "ordivon-runner.config.json"
OPERATION_NAME = "resolve-operation.json"
RESULT_NAME = "resolve-result.json"
_OPERATION_ID = re.compile(r"^[a-z0-9]+(?:[._-][a-z0-9]+)*$")
_DIGEST = re.compile(r"^sha256:[a-f0-9]{64}$")
_SMOKE_PROJECT_PREFIX = "Ordivon Resolve Smoke "


def _utc_now():
    return datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def _canonical_digest(value):
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _hash_file(path, chunk_size=1024 * 1024):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(chunk_size)
            if not chunk:
                break
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


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


def _require_string(value, label, prefix=None):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(label + " must be a non-empty string")
    if prefix is not None and not value.startswith(prefix):
        raise ValueError(label + " must start with " + repr(prefix))
    return value


def _validate_smoke_parameters(parameters):
    if not isinstance(parameters, dict):
        raise ValueError("create-smoke-project requires parameters")
    allowed = {
        "projectName",
        "timelineName",
        "binName",
        "mediaPath",
        "mediaDigest",
        "settings",
        "restorePreviousProject",
    }
    unknown = sorted(set(parameters) - allowed)
    if unknown:
        raise ValueError("unknown smoke parameter fields: " + ", ".join(unknown))
    required = allowed - {"restorePreviousProject"}
    missing = sorted(required - set(parameters))
    if missing:
        raise ValueError("missing smoke parameter fields: " + ", ".join(missing))

    _require_string(parameters.get("projectName"), "projectName", _SMOKE_PROJECT_PREFIX)
    _require_string(parameters.get("timelineName"), "timelineName")
    _require_string(parameters.get("binName"), "binName")
    media_path = Path(_require_string(parameters.get("mediaPath"), "mediaPath"))
    if not media_path.is_absolute():
        raise ValueError("mediaPath must be absolute")
    media_digest = parameters.get("mediaDigest")
    if not isinstance(media_digest, str) or not _DIGEST.fullmatch(media_digest):
        raise ValueError("mediaDigest must be a sha256 digest")

    settings = parameters.get("settings")
    if not isinstance(settings, dict) or set(settings) != {"frameRate", "width", "height"}:
        raise ValueError("settings must contain exactly frameRate, width, and height")
    frame_rate = settings.get("frameRate")
    width = settings.get("width")
    height = settings.get("height")
    if not isinstance(frame_rate, (int, float)) or frame_rate <= 0:
        raise ValueError("settings.frameRate must be positive")
    if not isinstance(width, int) or width <= 0 or not isinstance(height, int) or height <= 0:
        raise ValueError("settings width and height must be positive integers")
    restore = parameters.get("restorePreviousProject", True)
    if not isinstance(restore, bool):
        raise ValueError("restorePreviousProject must be boolean")
    return parameters


def validate_operation(operation):
    if not isinstance(operation, dict):
        raise ValueError("operation must be an object")
    allowed = {"schemaVersion", "operationId", "action", "requestedAt", "parameters"}
    unknown = sorted(set(operation) - allowed)
    if unknown:
        raise ValueError("unknown operation fields: " + ", ".join(unknown))
    if operation.get("schemaVersion") != 1:
        raise ValueError("schemaVersion must be 1")
    operation_id = operation.get("operationId")
    if not isinstance(operation_id, str) or not _OPERATION_ID.fullmatch(operation_id):
        raise ValueError("operationId has an invalid format")
    action = operation.get("action")
    if action not in {"probe", "create-smoke-project"}:
        raise ValueError("unsupported Resolve action")
    requested_at = operation.get("requestedAt")
    if requested_at is not None and (not isinstance(requested_at, str) or not requested_at):
        raise ValueError("requestedAt must be a non-empty string when present")
    if action == "probe":
        if "parameters" in operation:
            raise ValueError("probe does not accept parameters")
    else:
        _validate_smoke_parameters(operation.get("parameters"))
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
    except Exception as error:
        warnings.append(method_name + " failed: " + type(error).__name__)
        return default


def _call(target, method_name, *args):
    if target is None:
        raise RuntimeError(method_name + " target is unavailable")
    method = getattr(target, method_name, None)
    if not callable(method):
        raise RuntimeError(method_name + " is unavailable")
    try:
        return method(*args)
    except Exception as error:
        raise RuntimeError(method_name + " failed: " + type(error).__name__) from error


def _require_object(value, label):
    if value is None or value is False:
        raise RuntimeError(label + " returned no object")
    return value


def _require_true(value, label):
    if value is not True:
        raise RuntimeError(label + " did not succeed")
    return True


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
            "timelineResolutionWidth": _safe_call(project, "GetSetting", warnings, None, "timelineResolutionWidth"),
            "timelineResolutionHeight": _safe_call(project, "GetSetting", warnings, None, "timelineResolutionHeight"),
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


def _find_folder(parent, name):
    folders = _call(parent, "GetSubFolderList") or []
    for folder in folders:
        if _call(folder, "GetName") == name:
            return folder
    return None


def _find_timeline(project, name):
    count = int(_call(project, "GetTimelineCount") or 0)
    for index in range(1, count + 1):
        timeline = _call(project, "GetTimelineByIndex", index)
        if timeline and _call(timeline, "GetName") == name:
            return timeline
    return None


def _find_clip(folder, file_name):
    clips = _call(folder, "GetClipList") or []
    for clip in clips:
        properties = _call(clip, "GetClipProperty") or {}
        candidate = properties.get("File Name") if isinstance(properties, dict) else None
        if candidate == file_name or _call(clip, "GetName") == file_name:
            return clip
    return None


def _names(items):
    return [_call(item, "GetName") for item in (items or [])]


def _numeric_equal(actual, expected):
    try:
        return abs(float(actual) - float(expected)) < 0.0001
    except (TypeError, ValueError):
        return str(actual) == str(expected)


def create_smoke_project(resolve_object, operation):
    parameters = operation["parameters"]
    project_name = parameters["projectName"]
    timeline_name = parameters["timelineName"]
    bin_name = parameters["binName"]
    media_path = Path(parameters["mediaPath"])
    media_digest = parameters["mediaDigest"]
    settings = parameters["settings"]
    restore_previous = parameters.get("restorePreviousProject", True)

    if not media_path.is_file():
        raise FileNotFoundError("smoke media file does not exist")
    actual_digest = _hash_file(media_path)
    if actual_digest != media_digest:
        raise ValueError("smoke media digest does not match")

    project_manager = _require_object(_call(resolve_object, "GetProjectManager"), "GetProjectManager")
    previous_project = _call(project_manager, "GetCurrentProject")
    previous_name = _call(previous_project, "GetName") if previous_project else None
    if previous_project:
        _require_true(_call(project_manager, "SaveProject"), "SaveProject(previous)")

    project = None
    result = None
    operation_error = None
    restored = not bool(previous_name and previous_name != project_name and restore_previous)
    try:
        project_names = _call(project_manager, "GetProjectListInCurrentFolder") or []
        if project_name in project_names:
            project = _require_object(_call(project_manager, "LoadProject", project_name), "LoadProject(smoke)")
            project_disposition = "reused"
        else:
            project = _require_object(_call(project_manager, "CreateProject", project_name), "CreateProject")
            project_disposition = "created"

        setting_pairs = {
            "timelineFrameRate": settings["frameRate"],
            "timelineResolutionWidth": settings["width"],
            "timelineResolutionHeight": settings["height"],
        }
        for key, value in setting_pairs.items():
            current = _call(project, "GetSetting", key)
            if not _numeric_equal(current, value):
                _require_true(_call(project, "SetSetting", key, str(value)), "SetSetting(" + key + ")")
            verified = _call(project, "GetSetting", key)
            if not _numeric_equal(verified, value):
                raise RuntimeError(key + " did not reach the requested value")

        media_pool = _require_object(_call(project, "GetMediaPool"), "GetMediaPool")
        root = _require_object(_call(media_pool, "GetRootFolder"), "GetRootFolder")
        target_folder = _find_folder(root, bin_name)
        if target_folder is None:
            target_folder = _require_object(_call(media_pool, "AddSubFolder", root, bin_name), "AddSubFolder")
            bin_disposition = "created"
        else:
            bin_disposition = "reused"
        _require_true(_call(media_pool, "SetCurrentFolder", target_folder), "SetCurrentFolder")

        file_name = media_path.name
        clip = _find_clip(target_folder, file_name)
        if clip is None:
            imported = _call(media_pool, "ImportMedia", [str(media_path)]) or []
            if len(imported) != 1:
                raise RuntimeError("ImportMedia did not return exactly one clip")
            clip = imported[0]
            media_disposition = "imported"
        else:
            media_disposition = "reused"

        timeline = _find_timeline(project, timeline_name)
        if timeline is None:
            timeline = _require_object(_call(media_pool, "CreateEmptyTimeline", timeline_name), "CreateEmptyTimeline")
            timeline_disposition = "created"
        else:
            timeline_disposition = "reused"
        _require_true(_call(project, "SetCurrentTimeline", timeline), "SetCurrentTimeline")

        video_items = _call(timeline, "GetItemListInTrack", "video", 1) or []
        audio_items = _call(timeline, "GetItemListInTrack", "audio", 1) or []
        if not video_items and not audio_items:
            appended = _call(media_pool, "AppendToTimeline", [clip]) or []
            if not appended:
                raise RuntimeError("AppendToTimeline returned no timeline items")
            timeline_media_disposition = "appended"
            video_items = _call(timeline, "GetItemListInTrack", "video", 1) or []
            audio_items = _call(timeline, "GetItemListInTrack", "audio", 1) or []
        else:
            expected_name = _call(clip, "GetName")
            existing_names = set(_names(video_items) + _names(audio_items))
            if expected_name not in existing_names:
                raise RuntimeError("existing smoke timeline contains unexpected media")
            timeline_media_disposition = "reused"

        _require_true(_call(project_manager, "SaveProject"), "SaveProject(smoke)")
        result = {
            "project": {
                "name": project_name,
                "disposition": project_disposition,
                "timelineCount": int(_call(project, "GetTimelineCount") or 0),
                "frameRate": _call(project, "GetSetting", "timelineFrameRate"),
                "width": _call(project, "GetSetting", "timelineResolutionWidth"),
                "height": _call(project, "GetSetting", "timelineResolutionHeight"),
            },
            "bin": {
                "name": bin_name,
                "disposition": bin_disposition,
                "clipCount": len(_call(target_folder, "GetClipList") or []),
            },
            "media": {
                "fileName": file_name,
                "digest": media_digest,
                "disposition": media_disposition,
                "clipName": _call(clip, "GetName"),
            },
            "timeline": {
                "name": timeline_name,
                "disposition": timeline_disposition,
                "mediaDisposition": timeline_media_disposition,
                "videoTrackItems": _names(video_items),
                "audioTrackItems": _names(audio_items),
            },
            "previousProject": previous_name,
        }
    except Exception as error:
        operation_error = error
    finally:
        if project:
            try:
                _call(project_manager, "SaveProject")
            except Exception:
                pass
        if previous_name and previous_name != project_name and restore_previous:
            try:
                restored = bool(_call(project_manager, "LoadProject", previous_name))
            except Exception:
                restored = False

    if operation_error is not None:
        if not restored:
            raise RuntimeError(type(operation_error).__name__ + "; previous project restoration failed") from operation_error
        raise operation_error
    if not restored:
        raise RuntimeError("previous project restoration failed")
    result["restoredPreviousProject"] = restored
    return result


def execute_operation(operation, resolve_object=None, acquisition=None):
    validate_operation(operation)
    if resolve_object is None:
        resolve_object, acquisition = acquire_resolve()
    if not resolve_object:
        raise RuntimeError("Resolve application object is unavailable in the menu-script context")
    if operation["action"] == "probe":
        return probe_resolve(resolve_object, acquisition or "provided")
    return create_smoke_project(resolve_object, operation)


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


def _matching_success(path, operation, operation_digest):
    if not path.is_file():
        return False
    try:
        result = _load_json(path)
    except Exception:
        return False
    return (
        result.get("operationId") == operation.get("operationId")
        and result.get("operationDigest") == operation_digest
        and result.get("status") == "succeeded"
    )


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
        operation_digest = _canonical_digest(operation)
        result_path = control / RESULT_NAME
        if _matching_success(result_path, operation, operation_digest):
            print("Ordivon Studio Runner: replayed existing success")
            print("Operation: " + operation["operationId"])
            return 0

        payload = execute_operation(operation)
        result = {
            "schemaVersion": 1,
            "adapter": "resolve",
            "adapterVersion": ADAPTER_VERSION,
            "operationId": operation["operationId"],
            "operationDigest": operation_digest,
            "action": operation["action"],
            "status": "succeeded",
            "startedAt": started_at,
            "finishedAt": _utc_now(),
        }
        if operation["action"] == "probe":
            result["probe"] = payload
        else:
            result["smoke"] = payload
    except Exception as error:
        result = {
            "schemaVersion": 1,
            "adapter": "resolve",
            "adapterVersion": ADAPTER_VERSION,
            "operationId": operation.get("operationId") if isinstance(operation, dict) else None,
            "operationDigest": _canonical_digest(operation) if isinstance(operation, dict) else None,
            "action": operation.get("action") if isinstance(operation, dict) else None,
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
