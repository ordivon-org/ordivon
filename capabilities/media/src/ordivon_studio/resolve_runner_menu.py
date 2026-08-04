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


ADAPTER_VERSION = "0.4.1"
CONFIG_NAME = "ordivon-runner.config.json"
OPERATION_NAME = "resolve-operation.json"
RESULT_NAME = "resolve-result.json"
_OPERATION_ID = re.compile(r"^[a-z0-9]+(?:[._-][a-z0-9]+)*$")
_DIGEST = re.compile(r"^sha256:[a-f0-9]{64}$")
_TIMECODE = re.compile(r"^[0-9]{2}:[0-9]{2}:[0-9]{2}:[0-9]{2}$")
_SMOKE_PROJECT_PREFIX = "Ordivon Resolve Smoke "
_COMPATIBILITY_PROJECT_PREFIX = "Ordivon Resolve 21 Compatibility "
_COMPATIBILITY_PRODUCT_NAME = "DaVinci Resolve"
_COMPATIBILITY_VERSION_STRING = "21.0.3.7"
_COMPATIBILITY_VERSION = [21, 0, 3, 7, ""]
_ASSEMBLY_PROJECT_NAME = "Ordivon Runtime Introduction"
_ASSEMBLY_TIMELINE_NAME = "Assembly v0"
_ASSEMBLY_BINS = {"01_PLACEHOLDERS", "02_MOTION"}


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


def _validate_settings(settings):
    if not isinstance(settings, dict) or set(settings) != {"frameRate", "width", "height"}:
        raise ValueError("settings must contain exactly frameRate, width, and height")
    frame_rate = settings.get("frameRate")
    width = settings.get("width")
    height = settings.get("height")
    if not isinstance(frame_rate, (int, float)) or frame_rate <= 0:
        raise ValueError("settings.frameRate must be positive")
    if not isinstance(width, int) or width <= 0 or not isinstance(height, int) or height <= 0:
        raise ValueError("settings width and height must be positive integers")
    return settings


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
    _validate_settings(parameters.get("settings"))
    restore = parameters.get("restorePreviousProject", True)
    if not isinstance(restore, bool):
        raise ValueError("restorePreviousProject must be boolean")
    return parameters


def _validate_compatibility_parameters(parameters):
    if not isinstance(parameters, dict):
        raise ValueError("probe-compatibility requires parameters")
    allowed = {
        "projectName",
        "expectedProductName",
        "expectedVersionString",
        "expectedVersion",
        "developerPackageDigest",
        "mediaPath",
        "mediaDigest",
        "mediaFileName",
        "mediaExpectedFrames",
        "otioPath",
        "otioDigest",
        "sourceClipsPath",
        "settings",
        "restorePreviousProject",
        "cleanupProject",
    }
    unknown = sorted(set(parameters) - allowed)
    if unknown:
        raise ValueError("unknown compatibility parameter fields: " + ", ".join(unknown))
    missing = sorted(allowed - set(parameters))
    if missing:
        raise ValueError("missing compatibility parameter fields: " + ", ".join(missing))
    _require_string(parameters.get("projectName"), "projectName", _COMPATIBILITY_PROJECT_PREFIX)
    if parameters.get("expectedProductName") != _COMPATIBILITY_PRODUCT_NAME:
        raise ValueError("compatibility expectedProductName is not supported")
    if parameters.get("expectedVersionString") != _COMPATIBILITY_VERSION_STRING:
        raise ValueError("compatibility expectedVersionString is not supported")
    if parameters.get("expectedVersion") != _COMPATIBILITY_VERSION:
        raise ValueError("compatibility expectedVersion is not supported")
    for label in ("developerPackageDigest", "mediaDigest", "otioDigest"):
        value = parameters.get(label)
        if not isinstance(value, str) or not _DIGEST.fullmatch(value):
            raise ValueError(label + " must be a sha256 digest")
    media_path = Path(_require_string(parameters.get("mediaPath"), "mediaPath"))
    otio_path = Path(_require_string(parameters.get("otioPath"), "otioPath"))
    source_clips_path = Path(_require_string(parameters.get("sourceClipsPath"), "sourceClipsPath"))
    if not media_path.is_absolute() or not otio_path.is_absolute() or not source_clips_path.is_absolute():
        raise ValueError("compatibility paths must be absolute")
    file_name = _require_string(parameters.get("mediaFileName"), "mediaFileName")
    if "/" in file_name or "\\" in file_name:
        raise ValueError("mediaFileName must be a base file name")
    expected_frames = parameters.get("mediaExpectedFrames")
    if not isinstance(expected_frames, int) or expected_frames < 60:
        raise ValueError("mediaExpectedFrames must be an integer of at least 60")
    settings = _validate_settings(parameters.get("settings"))
    if settings != {"frameRate": 30, "width": 1920, "height": 1080}:
        raise ValueError("probe-compatibility requires 1920x1080 at 30 fps")
    for label in ("restorePreviousProject", "cleanupProject"):
        if not isinstance(parameters.get(label), bool):
            raise ValueError(label + " must be boolean")
    return parameters


def _validate_assembly_parameters(parameters):
    if not isinstance(parameters, dict):
        raise ValueError("assemble-review requires parameters")
    allowed = {
        "productionId",
        "projectName",
        "timelineName",
        "startTimecode",
        "settings",
        "totalFrames",
        "sourceDigests",
        "segments",
        "restorePreviousProject",
    }
    unknown = sorted(set(parameters) - allowed)
    if unknown:
        raise ValueError("unknown assembly parameter fields: " + ", ".join(unknown))
    required = allowed - {"restorePreviousProject"}
    missing = sorted(required - set(parameters))
    if missing:
        raise ValueError("missing assembly parameter fields: " + ", ".join(missing))

    production_id = _require_string(parameters.get("productionId"), "productionId")
    if production_id != "runtime-introduction":
        raise ValueError("assemble-review is limited to runtime-introduction")
    if parameters.get("projectName") != _ASSEMBLY_PROJECT_NAME:
        raise ValueError("assemble-review projectName is not reserved")
    if parameters.get("timelineName") != _ASSEMBLY_TIMELINE_NAME:
        raise ValueError("assemble-review timelineName is not reserved")
    start_timecode = parameters.get("startTimecode")
    if not isinstance(start_timecode, str) or not _TIMECODE.fullmatch(start_timecode):
        raise ValueError("startTimecode has an invalid format")
    settings = _validate_settings(parameters.get("settings"))
    if settings != {"frameRate": 30, "width": 1920, "height": 1080}:
        raise ValueError("assemble-review requires 1920x1080 at 30 fps")
    if parameters.get("totalFrames") != 2340:
        raise ValueError("assemble-review requires exactly 2340 frames")

    source_digests = parameters.get("sourceDigests")
    if not isinstance(source_digests, dict) or set(source_digests) != {"production", "assets", "timeline"}:
        raise ValueError("sourceDigests must contain production, assets, and timeline")
    for value in source_digests.values():
        if not isinstance(value, str) or not _DIGEST.fullmatch(value):
            raise ValueError("sourceDigests contains an invalid digest")

    segments = parameters.get("segments")
    if not isinstance(segments, list) or len(segments) != 11:
        raise ValueError("assemble-review requires exactly 11 segments")
    cursor = 0
    seen_ids = set()
    for segment in segments:
        if not isinstance(segment, dict):
            raise ValueError("assembly segment must be an object")
        segment_allowed = {
            "id",
            "assetId",
            "fileName",
            "mediaPath",
            "mediaDigest",
            "binName",
            "startFrame",
            "durationFrames",
            "placeholder",
        }
        if set(segment) != segment_allowed:
            raise ValueError("assembly segment fields are invalid")
        segment_id = segment.get("id")
        asset_id = segment.get("assetId")
        if not isinstance(segment_id, str) or not _OPERATION_ID.fullmatch(segment_id):
            raise ValueError("assembly segment id has an invalid format")
        if segment_id in seen_ids:
            raise ValueError("assembly segment id is duplicated")
        seen_ids.add(segment_id)
        if not isinstance(asset_id, str) or not _OPERATION_ID.fullmatch(asset_id):
            raise ValueError("assembly assetId has an invalid format")
        file_name = _require_string(segment.get("fileName"), "assembly fileName")
        if "/" in file_name or "\\" in file_name:
            raise ValueError("assembly fileName must be a base file name")
        media_path = Path(_require_string(segment.get("mediaPath"), "assembly mediaPath"))
        if not media_path.is_absolute():
            raise ValueError("assembly mediaPath must be absolute")
        digest = segment.get("mediaDigest")
        if not isinstance(digest, str) or not _DIGEST.fullmatch(digest):
            raise ValueError("assembly mediaDigest is invalid")
        if segment.get("binName") not in _ASSEMBLY_BINS:
            raise ValueError("assembly segment uses an unsupported Bin")
        if segment.get("startFrame") != cursor:
            raise ValueError("assembly segments must be contiguous and ordered")
        duration = segment.get("durationFrames")
        if not isinstance(duration, int) or duration <= 0:
            raise ValueError("assembly durationFrames must be positive")
        if not isinstance(segment.get("placeholder"), bool):
            raise ValueError("assembly placeholder must be boolean")
        cursor += duration
    if cursor != parameters["totalFrames"]:
        raise ValueError("assembly segment durations do not match totalFrames")
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
    if action not in {"probe", "create-smoke-project", "probe-compatibility", "assemble-review"}:
        raise ValueError("unsupported Resolve action")
    requested_at = operation.get("requestedAt")
    if requested_at is not None and (not isinstance(requested_at, str) or not requested_at):
        raise ValueError("requestedAt must be a non-empty string when present")
    if action == "probe":
        if "parameters" in operation:
            raise ValueError("probe does not accept parameters")
    elif action == "create-smoke-project":
        _validate_smoke_parameters(operation.get("parameters"))
    elif action == "probe-compatibility":
        _validate_compatibility_parameters(operation.get("parameters"))
    else:
        _validate_assembly_parameters(operation.get("parameters"))
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


def _ensure_folder(media_pool, root, name):
    folder = _find_folder(root, name)
    if folder is not None:
        return folder, "reused"
    return _require_object(_call(media_pool, "AddSubFolder", root, name), "AddSubFolder"), "created"


def _find_timeline(project, name):
    count = int(_call(project, "GetTimelineCount") or 0)
    for index in range(1, count + 1):
        timeline = _call(project, "GetTimelineByIndex", index)
        if timeline and _call(timeline, "GetName") == name:
            return timeline
    return None


def _clip_file_name(clip):
    properties = _call(clip, "GetClipProperty") or {}
    if isinstance(properties, dict):
        value = properties.get("File Name")
        if isinstance(value, str) and value:
            return value
    return _call(clip, "GetName")


def _media_id(clip):
    value = _call(clip, "GetMediaId")
    if not isinstance(value, str) or not value:
        raise RuntimeError("MediaPoolItem.GetMediaId returned no identity")
    return value


def _find_clip(folder, file_name):
    clips = _call(folder, "GetClipList") or []
    for clip in clips:
        if _clip_file_name(clip) == file_name:
            return clip
    return None


def _names(items):
    return [_call(item, "GetName") for item in (items or [])]


def _numeric_equal(actual, expected):
    try:
        return abs(float(actual) - float(expected)) < 0.0001
    except (TypeError, ValueError):
        return str(actual) == str(expected)


def _apply_project_settings(project, settings):
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


def _project_for_operation(project_manager, project_name):
    project_names = _call(project_manager, "GetProjectListInCurrentFolder") or []
    if project_name in project_names:
        return _require_object(_call(project_manager, "LoadProject", project_name), "LoadProject"), "reused"
    return _require_object(_call(project_manager, "CreateProject", project_name), "CreateProject"), "created"


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
        project, project_disposition = _project_for_operation(project_manager, project_name)
        _apply_project_settings(project, settings)

        media_pool = _require_object(_call(project, "GetMediaPool"), "GetMediaPool")
        root = _require_object(_call(media_pool, "GetRootFolder"), "GetRootFolder")
        target_folder, bin_disposition = _ensure_folder(media_pool, root, bin_name)
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


def _developer_readme_path():
    program_data = os.environ.get("PROGRAMDATA")
    if not program_data:
        raise RuntimeError("PROGRAMDATA is unavailable")
    return (
        Path(program_data)
        / "Blackmagic Design"
        / "DaVinci Resolve"
        / "Support"
        / "Developer"
        / "Scripting"
        / "README.txt"
    )


def _probe_value(target, method_name, *args):
    method = getattr(target, method_name, None) if target is not None else None
    if not callable(method):
        return {"available": False, "value": None}
    try:
        value = method(*args)
    except Exception as error:
        return {"available": True, "value": None, "error": type(error).__name__}
    if isinstance(value, (str, int, float, bool)) or value is None:
        safe_value = value
    elif isinstance(value, (list, tuple)):
        safe_value = [item for item in value if isinstance(item, (str, int, float, bool)) or item is None]
    else:
        safe_value = None
    return {"available": True, "value": safe_value, "truthy": bool(value)}


def _numeric_probe_value(probe):
    value = probe.get("value") if isinstance(probe, dict) else None
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    return None


def _probe_timeline_item(item, timeline_start):
    start_probe = _probe_value(item, "GetStart", False)
    end_probe = _probe_value(item, "GetEnd", False)
    duration_probe = _probe_value(item, "GetDuration", False)
    source_start_probe = _probe_value(item, "GetSourceStartFrame")
    source_end_probe = _probe_value(item, "GetSourceEndFrame")
    start = _numeric_probe_value(start_probe)
    end = _numeric_probe_value(end_probe)
    source_start = _numeric_probe_value(source_start_probe)
    source_end = _numeric_probe_value(source_end_probe)
    media_pool_item = None
    media_pool_item_probe = _probe_value(item, "GetMediaPoolItem")
    getter = getattr(item, "GetMediaPoolItem", None)
    if callable(getter):
        try:
            media_pool_item = getter()
        except Exception:
            media_pool_item = None
    identity = {
        "timelineItemName": _probe_value(item, "GetName"),
        "timelineItemUniqueId": _probe_value(item, "GetUniqueId"),
        "mediaPoolItemAvailable": bool(media_pool_item),
        "mediaPoolItemName": _probe_value(media_pool_item, "GetName"),
        "mediaPoolItemUniqueId": _probe_value(media_pool_item, "GetUniqueId"),
        "mediaId": _probe_value(media_pool_item, "GetMediaId"),
    }
    candidates = {
        "endMinusStart": end - start if start is not None and end is not None else None,
        "endMinusStartPlusOne": end - start + 1 if start is not None and end is not None else None,
        "sourceEndMinusStart": source_end - source_start
        if source_start is not None and source_end is not None
        else None,
        "sourceEndMinusStartPlusOne": source_end - source_start + 1
        if source_start is not None and source_end is not None
        else None,
    }
    return {
        "identity": identity,
        "timeline": {
            "getStart": start_probe,
            "getEnd": end_probe,
            "getDuration": duration_probe,
            "startOffset": start - timeline_start if start is not None and timeline_start is not None else None,
        },
        "source": {
            "getSourceStartFrame": source_start_probe,
            "getSourceEndFrame": source_end_probe,
        },
        "candidateFrameCounts": candidates,
        "mediaPoolItemProbe": media_pool_item_probe,
    }


def _probe_timeline(timeline):
    start_probe = _probe_value(timeline, "GetStartFrame")
    start = _numeric_probe_value(start_probe)
    track_count_probe = _probe_value(timeline, "GetTrackCount", "video")
    items = []
    item_getter = getattr(timeline, "GetItemListInTrack", None)
    if callable(item_getter):
        try:
            raw_items = item_getter("video", 1) or []
        except Exception:
            raw_items = []
        items = [_probe_timeline_item(item, start) for item in raw_items]
    return {
        "name": _probe_value(timeline, "GetName"),
        "uniqueId": _probe_value(timeline, "GetUniqueId"),
        "startFrame": start_probe,
        "endFrame": _probe_value(timeline, "GetEndFrame"),
        "startTimecode": _probe_value(timeline, "GetStartTimecode"),
        "videoTrackCount": track_count_probe,
        "videoItems": items,
        "videoItemCount": len(items),
    }


def _probe_returned_items(returned, timeline_start):
    if not isinstance(returned, (list, tuple)):
        return {"returnType": type(returned).__name__, "count": 0, "items": []}
    return {
        "returnType": type(returned).__name__,
        "count": len(returned),
        "items": [_probe_timeline_item(item, timeline_start) for item in returned],
    }


def _create_probe_timeline(project, media_pool, name):
    timeline = _require_object(_call(media_pool, "CreateEmptyTimeline", name), "CreateEmptyTimeline")
    _require_true(_call(project, "SetCurrentTimeline", timeline), "SetCurrentTimeline")
    _require_true(_call(timeline, "SetStartTimecode", "01:00:00:00"), "SetStartTimecode")
    return timeline


def _append_probe_case(project, media_pool, clip, case_id, timeline_name, mode, expected_frames):
    case = {
        "id": case_id,
        "kind": "append",
        "mode": mode,
        "expectedFrames": expected_frames,
        "status": "failed",
    }
    try:
        timeline = _create_probe_timeline(project, media_pool, timeline_name)
        timeline_start = int(round(float(_call(timeline, "GetStartFrame"))))
        if mode == "direct-object":
            request = {"overload": "AppendToTimeline(clip)"}
            returned = _call(media_pool, "AppendToTimeline", clip)
        elif mode == "direct-list":
            request = {"overload": "AppendToTimeline([clip])"}
            returned = _call(media_pool, "AppendToTimeline", [clip])
        elif mode == "positioned-full":
            record_offset = 30
            request = {
                "overload": "AppendToTimeline([{clipInfo}])",
                "recordOffset": record_offset,
                "sourceRangeSpecified": False,
                "mediaType": 1,
                "trackIndex": 1,
            }
            returned = _call(
                media_pool,
                "AppendToTimeline",
                [
                    {
                        "mediaPoolItem": clip,
                        "recordFrame": timeline_start + record_offset,
                        "mediaType": 1,
                        "trackIndex": 1,
                    }
                ],
            )
        elif mode == "subclip-0-23":
            record_offset = 12
            request = {
                "overload": "AppendToTimeline([{clipInfo}])",
                "recordOffset": record_offset,
                "startFrame": 0,
                "endFrame": 23,
                "officialExampleLabel": "first 24 frames",
                "mediaType": 1,
                "trackIndex": 1,
            }
            returned = _call(
                media_pool,
                "AppendToTimeline",
                [
                    {
                        "mediaPoolItem": clip,
                        "startFrame": 0,
                        "endFrame": 23,
                        "recordFrame": timeline_start + record_offset,
                        "mediaType": 1,
                        "trackIndex": 1,
                    }
                ],
            )
        else:
            raise ValueError("unknown append probe mode")
        case["request"] = request
        case["returned"] = _probe_returned_items(returned, timeline_start)
        case["trackScan"] = _probe_timeline(timeline)
        case["status"] = "completed"
    except Exception as error:
        case["error"] = {"type": type(error).__name__, "message": str(error)[:300]}
    return case


def _otio_probe_case(project, media_pool, otio_path, case_id, timeline_name, options):
    case = {
        "id": case_id,
        "kind": "otio-import",
        "request": {
            "timelineName": timeline_name,
            "importSourceClips": options.get("importSourceClips"),
            "usesSourceClipsPath": "sourceClipsPath" in options,
            "usesSourceClipsFolders": "sourceClipsFolders" in options,
        },
        "status": "failed",
    }
    try:
        timeline = _require_object(
            _call(media_pool, "ImportTimelineFromFile", str(otio_path), options),
            "ImportTimelineFromFile",
        )
        _require_true(_call(project, "SetCurrentTimeline", timeline), "SetCurrentTimeline(imported)")
        case["timeline"] = _probe_timeline(timeline)
        case["status"] = "completed"
    except Exception as error:
        case["error"] = {"type": type(error).__name__, "message": str(error)[:300]}
    return case


def _safe_clip_properties(clip):
    properties = _call(clip, "GetClipProperty") or {}
    safe = {}
    if isinstance(properties, dict):
        for key in (
            "File Name",
            "Type",
            "Video Codec",
            "Audio Codec",
            "Resolution",
            "FPS",
            "Frame Rate",
            "Duration",
            "Start",
            "End",
            "Start TC",
            "End TC",
        ):
            value = properties.get(key)
            if isinstance(value, (str, int, float, bool)) or value is None:
                safe[key] = value
    return safe


def probe_compatibility(resolve_object, operation, acquisition):
    parameters = operation["parameters"]
    media_path = Path(parameters["mediaPath"])
    otio_path = Path(parameters["otioPath"])
    if not media_path.is_file():
        raise FileNotFoundError("compatibility media file does not exist")
    if _hash_file(media_path) != parameters["mediaDigest"]:
        raise ValueError("compatibility media digest does not match")
    if not otio_path.is_file():
        raise FileNotFoundError("compatibility OTIO file does not exist")
    if _hash_file(otio_path) != parameters["otioDigest"]:
        raise ValueError("compatibility OTIO digest does not match")
    developer_readme = _developer_readme_path()
    if not developer_readme.is_file():
        raise FileNotFoundError("Resolve Developer Package README is unavailable")
    if _hash_file(developer_readme) != parameters["developerPackageDigest"]:
        raise ValueError("Resolve Developer Package digest does not match")

    product_name = _call(resolve_object, "GetProductName")
    version_string = _call(resolve_object, "GetVersionString")
    version = _call(resolve_object, "GetVersion")
    if product_name != parameters["expectedProductName"]:
        raise RuntimeError("Resolve product name differs from the version profile")
    if version_string != parameters["expectedVersionString"]:
        raise RuntimeError("Resolve version string differs from the version profile")
    if list(version or []) != parameters["expectedVersion"]:
        raise RuntimeError("Resolve version fields differ from the version profile")

    project_manager = _require_object(_call(resolve_object, "GetProjectManager"), "GetProjectManager")
    previous_project = _call(project_manager, "GetCurrentProject")
    previous_name = _call(previous_project, "GetName") if previous_project else None
    if previous_project:
        _require_true(_call(project_manager, "SaveProject"), "SaveProject(previous)")

    project_name = parameters["projectName"]
    if project_name in (_call(project_manager, "GetProjectListInCurrentFolder") or []):
        raise RuntimeError("compatibility project name already exists")

    project = None
    restored = previous_name is None
    cleanup_attempted = False
    cleanup_deleted = False
    result = None
    operation_error = None
    try:
        project = _require_object(_call(project_manager, "CreateProject", project_name), "CreateProject")
        _apply_project_settings(project, parameters["settings"])
        media_pool = _require_object(_call(project, "GetMediaPool"), "GetMediaPool")
        root = _require_object(_call(media_pool, "GetRootFolder"), "GetRootFolder")
        folder, _ = _ensure_folder(media_pool, root, "01_PROBE_MEDIA")
        _require_true(_call(media_pool, "SetCurrentFolder", folder), "SetCurrentFolder")
        imported = _call(media_pool, "ImportMedia", [str(media_path)]) or []
        if len(imported) != 1:
            raise RuntimeError("compatibility ImportMedia did not return exactly one clip")
        clip = imported[0]

        cases = [
            _append_probe_case(
                project,
                media_pool,
                clip,
                "append-direct-object",
                "01 Append Direct Object",
                "direct-object",
                parameters["mediaExpectedFrames"],
            ),
            _append_probe_case(
                project,
                media_pool,
                clip,
                "append-direct-list",
                "02 Append Direct List",
                "direct-list",
                parameters["mediaExpectedFrames"],
            ),
            _append_probe_case(
                project,
                media_pool,
                clip,
                "append-positioned-full",
                "03 Append Positioned Full",
                "positioned-full",
                parameters["mediaExpectedFrames"],
            ),
            _append_probe_case(
                project,
                media_pool,
                clip,
                "append-subclip-0-23",
                "04 Append Subclip 0-23",
                "subclip-0-23",
                24,
            ),
            _otio_probe_case(
                project,
                media_pool,
                otio_path,
                "otio-existing-media",
                "05 OTIO Existing Media",
                {
                    "timelineName": "05 OTIO Existing Media",
                    "importSourceClips": False,
                    "sourceClipsFolders": [folder],
                },
            ),
            _otio_probe_case(
                project,
                media_pool,
                otio_path,
                "otio-import-source-path",
                "06 OTIO Import Source Path",
                {
                    "timelineName": "06 OTIO Import Source Path",
                    "importSourceClips": True,
                    "sourceClipsPath": parameters["sourceClipsPath"],
                },
            ),
        ]
        _require_true(_call(project_manager, "SaveProject"), "SaveProject(compatibility)")
        completed = sum(1 for case in cases if case.get("status") == "completed")
        result = {
            "profileSchemaVersion": 1,
            "resolve": {
                "productName": product_name,
                "edition": "free" if product_name == "DaVinci Resolve" else "studio",
                "versionString": version_string,
                "version": list(version or []),
                "platform": "windows",
                "executionMode": "internal-menu",
                "acquisition": acquisition,
            },
            "developerPackage": {
                "digest": parameters["developerPackageDigest"],
            },
            "fixture": {
                "fileName": parameters["mediaFileName"],
                "digest": parameters["mediaDigest"],
                "expectedFrames": parameters["mediaExpectedFrames"],
                "mediaId": _probe_value(clip, "GetMediaId"),
                "uniqueId": _probe_value(clip, "GetUniqueId"),
                "clipProperties": _safe_clip_properties(clip),
                "otioDigest": parameters["otioDigest"],
            },
            "project": {
                "name": project_name,
                "frameRate": _call(project, "GetSetting", "timelineFrameRate"),
                "width": _call(project, "GetSetting", "timelineResolutionWidth"),
                "height": _call(project, "GetSetting", "timelineResolutionHeight"),
            },
            "cases": cases,
            "caseSummary": {
                "total": len(cases),
                "completed": completed,
                "failed": len(cases) - completed,
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
        if previous_name and parameters.get("restorePreviousProject", True):
            try:
                restored = bool(_call(project_manager, "LoadProject", previous_name))
            except Exception:
                restored = False
        elif project and parameters.get("cleanupProject", True):
            try:
                restored = bool(_call(project_manager, "CloseProject", project))
            except Exception:
                restored = False
        if project and parameters.get("cleanupProject", True) and restored:
            cleanup_attempted = True
            try:
                cleanup_deleted = bool(_call(project_manager, "DeleteProject", project_name))
            except Exception:
                cleanup_deleted = False

    if operation_error is not None:
        if not restored:
            raise RuntimeError(type(operation_error).__name__ + "; previous project restoration failed") from operation_error
        raise operation_error
    if not restored:
        raise RuntimeError("previous project restoration failed")
    result["restoredPreviousProject"] = restored
    result["cleanup"] = {
        "requested": parameters.get("cleanupProject", True),
        "attempted": cleanup_attempted,
        "deleted": cleanup_deleted,
    }
    return result


def _timeline_item_snapshot(item, timeline_start):
    media_pool_item = _require_object(_call(item, "GetMediaPoolItem"), "TimelineItem.GetMediaPoolItem")
    start = int(round(float(_call(item, "GetStart", False))))
    reported_duration = int(round(float(_call(item, "GetDuration", False))))
    end = int(round(float(_call(item, "GetEnd", False))))
    span = end - start
    if reported_duration <= 0 or span <= 0:
        raise RuntimeError("TimelineItem returned a non-positive duration")
    if span != reported_duration:
        raise RuntimeError("TimelineItem duration differs from its exclusive timeline span")
    return {
        "item": item,
        "mediaId": _media_id(media_pool_item),
        "fileName": _clip_file_name(media_pool_item),
        "startAbsolute": start,
        "startFrame": start - timeline_start,
        "reportedDurationFrames": reported_duration,
        "durationFrames": span,
        "endAbsolute": end,
        "endFrame": start - timeline_start + span,
    }


def _video_item_snapshots(timeline):
    timeline_start = int(round(float(_call(timeline, "GetStartFrame"))))
    items = _call(timeline, "GetItemListInTrack", "video", 1) or []
    return timeline_start, [_timeline_item_snapshot(item, timeline_start) for item in items]


def _find_item_at(snapshots, start_frame):
    matches = [snapshot for snapshot in snapshots if snapshot["startFrame"] == start_frame]
    if len(matches) > 1:
        raise RuntimeError("multiple video items occupy one assembly start frame")
    return matches[0] if matches else None


def _overlaps(snapshot, start_frame, duration_frames):
    end_frame = start_frame + duration_frames
    return snapshot["startFrame"] < end_frame and start_frame < snapshot["endFrame"]


def _ensure_timeline_marker(timeline, segment, operation_id):
    custom_data = "ordivon:" + operation_id + ":" + segment["id"]
    markers = _call(timeline, "GetMarkers") or {}
    for marker in markers.values():
        if isinstance(marker, dict) and marker.get("customData") == custom_data:
            return "reused"
    color = "Yellow" if segment["placeholder"] else "Blue"
    name = ("PLACEHOLDER · " if segment["placeholder"] else "MOTION · ") + segment["id"]
    note = "Replace before picture lock" if segment["placeholder"] else "Selected programmatic motion"
    _require_true(
        _call(
            timeline,
            "AddMarker",
            segment["startFrame"],
            color,
            name,
            note,
            segment["durationFrames"],
            custom_data,
        ),
        "Timeline.AddMarker",
    )
    return "created"


def assemble_review(resolve_object, operation):
    parameters = operation["parameters"]
    project_name = parameters["projectName"]
    timeline_name = parameters["timelineName"]
    settings = parameters["settings"]
    segments = parameters["segments"]
    restore_previous = parameters.get("restorePreviousProject", True)

    # Validate every byte identity before touching Resolve state.
    for segment in segments:
        media_path = Path(segment["mediaPath"])
        if not media_path.is_file():
            raise FileNotFoundError("assembly media file does not exist: " + segment["fileName"])
        if _hash_file(media_path) != segment["mediaDigest"]:
            raise ValueError("assembly media digest does not match: " + segment["fileName"])

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
        project, project_disposition = _project_for_operation(project_manager, project_name)
        _apply_project_settings(project, settings)
        media_pool = _require_object(_call(project, "GetMediaPool"), "GetMediaPool")
        root = _require_object(_call(media_pool, "GetRootFolder"), "GetRootFolder")

        folders = {}
        bin_results = []
        for bin_name in sorted(_ASSEMBLY_BINS):
            folder, disposition = _ensure_folder(media_pool, root, bin_name)
            folders[bin_name] = folder
            bin_results.append({"name": bin_name, "disposition": disposition})

        clips = {}
        asset_results = []
        for segment in segments:
            asset_id = segment["assetId"]
            if asset_id in clips:
                continue
            folder = folders[segment["binName"]]
            _require_true(_call(media_pool, "SetCurrentFolder", folder), "SetCurrentFolder")
            clip = _find_clip(folder, segment["fileName"])
            if clip is None:
                imported = _call(media_pool, "ImportMedia", [segment["mediaPath"]]) or []
                if len(imported) != 1:
                    raise RuntimeError("ImportMedia did not return exactly one clip: " + segment["fileName"])
                clip = imported[0]
                disposition = "imported"
            else:
                disposition = "reused"
            if _clip_file_name(clip) != segment["fileName"]:
                raise RuntimeError("imported media identity differs: " + segment["fileName"])
            clips[asset_id] = clip
            asset_results.append(
                {
                    "assetId": asset_id,
                    "fileName": segment["fileName"],
                    "binName": segment["binName"],
                    "digest": segment["mediaDigest"],
                    "disposition": disposition,
                }
            )

        _require_true(_call(media_pool, "SetCurrentFolder", root), "SetCurrentFolder(root)")
        timeline = _find_timeline(project, timeline_name)
        if timeline is None:
            timeline = _require_object(_call(media_pool, "CreateEmptyTimeline", timeline_name), "CreateEmptyTimeline")
            timeline_disposition = "created"
        else:
            timeline_disposition = "reused"
        _require_true(_call(project, "SetCurrentTimeline", timeline), "SetCurrentTimeline")

        timeline_start, existing = _video_item_snapshots(timeline)
        if not existing:
            _require_true(_call(timeline, "SetStartTimecode", parameters["startTimecode"]), "SetStartTimecode")
            timeline_start, existing = _video_item_snapshots(timeline)
        elif _call(timeline, "GetStartTimecode") != parameters["startTimecode"]:
            raise RuntimeError("existing Assembly v0 uses an unexpected start timecode")

        segment_results = []
        for segment in segments:
            timeline_start, snapshots = _video_item_snapshots(timeline)
            existing_item = _find_item_at(snapshots, segment["startFrame"])
            expected_media_id = _media_id(clips[segment["assetId"]])
            if existing_item is not None:
                if existing_item["mediaId"] != expected_media_id:
                    raise RuntimeError(
                        "existing Assembly v0 contains unexpected media at "
                        + str(segment["startFrame"])
                        + ": actual="
                        + existing_item["fileName"]
                        + ", expected="
                        + segment["fileName"]
                    )
                if existing_item["durationFrames"] != segment["durationFrames"]:
                    raise RuntimeError(
                        "existing Assembly v0 contains an unexpected duration at "
                        + str(segment["startFrame"])
                        + ": actual="
                        + str(existing_item["durationFrames"])
                        + ", expected="
                        + str(segment["durationFrames"])
                    )
                timeline_item_disposition = "reused"
                verified = existing_item
            else:
                for snapshot in snapshots:
                    if _overlaps(snapshot, segment["startFrame"], segment["durationFrames"]):
                        raise RuntimeError("existing Assembly v0 overlaps the requested segment: " + segment["id"])
                record_frame = timeline_start + segment["startFrame"]
                clip_info = {
                    "mediaPoolItem": clips[segment["assetId"]],
                    "mediaType": 1,
                    "trackIndex": 1,
                    "recordFrame": record_frame,
                }
                appended = _call(media_pool, "AppendToTimeline", [clip_info]) or []
                if not appended:
                    raise RuntimeError("AppendToTimeline returned no item: " + segment["id"])
                timeline_start, refreshed = _video_item_snapshots(timeline)
                verified = _find_item_at(refreshed, segment["startFrame"])
                if verified is None:
                    raise RuntimeError("appended Assembly item could not be recovered: " + segment["id"])
                if verified["mediaId"] != expected_media_id or verified["durationFrames"] != segment["durationFrames"]:
                    raise RuntimeError(
                        "appended Assembly item failed verification: "
                        + segment["id"]
                        + "; actualMedia="
                        + verified["fileName"]
                        + "; actualDuration="
                        + str(verified["durationFrames"])
                        + "; expectedDuration="
                        + str(segment["durationFrames"])
                    )
                timeline_item_disposition = "appended"

            marker_disposition = _ensure_timeline_marker(timeline, segment, operation["operationId"])
            segment_results.append(
                {
                    "id": segment["id"],
                    "assetId": segment["assetId"],
                    "fileName": segment["fileName"],
                    "placeholder": segment["placeholder"],
                    "requestedStartFrame": segment["startFrame"],
                    "actualStartFrame": verified["startFrame"],
                    "requestedDurationFrames": segment["durationFrames"],
                    "actualDurationFrames": verified["durationFrames"],
                    "actualEndFrame": verified["endFrame"],
                    "timelineDisposition": timeline_item_disposition,
                    "markerDisposition": marker_disposition,
                }
            )

        timeline_start, final_items = _video_item_snapshots(timeline)
        expected_layout = sorted(
            (
                segment["startFrame"],
                segment["durationFrames"],
                _media_id(clips[segment["assetId"]]),
            )
            for segment in segments
        )
        actual_layout = sorted((item["startFrame"], item["durationFrames"], item["mediaId"]) for item in final_items)
        if actual_layout != expected_layout:
            raise RuntimeError("Assembly v0 final layout differs from the compiled editorial snapshot")
        verified_total_frames = max(item["endFrame"] for item in final_items) if final_items else 0
        if verified_total_frames != parameters["totalFrames"]:
            raise RuntimeError("Assembly v0 verified duration differs from totalFrames")

        _require_true(_call(project_manager, "SaveProject"), "SaveProject(assembly)")
        result = {
            "productionId": parameters["productionId"],
            "sourceDigests": parameters["sourceDigests"],
            "project": {
                "name": project_name,
                "disposition": project_disposition,
                "frameRate": _call(project, "GetSetting", "timelineFrameRate"),
                "width": _call(project, "GetSetting", "timelineResolutionWidth"),
                "height": _call(project, "GetSetting", "timelineResolutionHeight"),
            },
            "bins": bin_results,
            "assets": asset_results,
            "timeline": {
                "name": timeline_name,
                "disposition": timeline_disposition,
                "startTimecode": _call(timeline, "GetStartTimecode"),
                "startFrame": timeline_start,
                "endFrame": int(round(float(_call(timeline, "GetEndFrame")))),
                "totalFrames": verified_total_frames,
                "videoTrackCount": int(_call(timeline, "GetTrackCount", "video") or 0),
                "videoItemCount": len(final_items),
                "markerCount": len(_call(timeline, "GetMarkers") or {}),
            },
            "segments": segment_results,
            "placeholderCount": sum(1 for segment in segments if segment["placeholder"]),
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
    if operation["action"] == "create-smoke-project":
        return create_smoke_project(resolve_object, operation)
    if operation["action"] == "probe-compatibility":
        return probe_compatibility(resolve_object, operation, acquisition or "provided")
    return assemble_review(resolve_object, operation)


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
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        replacements.append(local_app_data)
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
        elif operation["action"] == "create-smoke-project":
            result["smoke"] = payload
        elif operation["action"] == "probe-compatibility":
            result["compatibility"] = payload
        else:
            result["assembly"] = payload
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
