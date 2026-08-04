from __future__ import annotations

import hashlib
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import opentimelineio as otio
import ordivon_studio.resolve_runner_menu as runner_menu
from ordivon_studio.resolve_adapter import (
    ASSEMBLY_PROJECT_NAME,
    ASSEMBLY_TIMELINE_NAME,
    CONFIG_FILENAME,
    OPERATION_FILENAME,
    RUNNER_FILENAME,
    build_assembly_operation,
    build_compatibility_operation,
    build_probe_operation,
    build_smoke_operation,
    install_runner,
    prepare_assembly,
    prepare_probe,
    prepare_smoke,
    validate_result,
)
from ordivon_studio.resolve_runner_menu import execute_operation, validate_operation


ASSEMBLY_LAYOUT = [
    ("hook-placeholder", "runtime-hook-placeholder", "00-hook-placeholder.mp4", 180, True, "01_PLACEHOLDERS"),
    ("runtime-flow", "runtime-flow-motion", "runtime-flow.mp4", 210, False, "02_MOTION"),
    (
        "source-patch-placeholder",
        "runtime-source-patch-placeholder",
        "02-source-patch-placeholder.mp4",
        330,
        True,
        "01_PLACEHOLDERS",
    ),
    (
        "exec-observe-placeholder",
        "runtime-exec-observe-placeholder",
        "03-exec-observe-placeholder.mp4",
        390,
        True,
        "01_PLACEHOLDERS",
    ),
    (
        "request-replay",
        "runtime-request-replay-motion",
        "runtime-request-replay.mp4",
        180,
        False,
        "02_MOTION",
    ),
    (
        "replay-terminal-placeholder",
        "runtime-replay-terminal-placeholder",
        "05-replay-terminal-placeholder.mp4",
        150,
        True,
        "01_PLACEHOLDERS",
    ),
    (
        "evidence-placeholder",
        "runtime-evidence-placeholder",
        "06-evidence-placeholder.mp4",
        330,
        True,
        "01_PLACEHOLDERS",
    ),
    (
        "exact-close",
        "runtime-exact-close-motion",
        "runtime-exact-close.mp4",
        180,
        False,
        "02_MOTION",
    ),
    ("diff-placeholder", "runtime-diff-placeholder", "08-diff-placeholder.mp4", 90, True, "01_PLACEHOLDERS"),
    (
        "boundary-placeholder",
        "runtime-boundary-placeholder",
        "09-boundary-placeholder.mp4",
        210,
        True,
        "01_PLACEHOLDERS",
    ),
    ("end-placeholder", "runtime-end-placeholder", "10-end-placeholder.mp4", 90, True, "01_PLACEHOLDERS"),
]
ASSEMBLY_DURATION_BY_FILE = {file_name: duration for _, _, file_name, duration, _, _ in ASSEMBLY_LAYOUT}


class FakeClip:
    def __init__(self, file_name: str) -> None:
        self.file_name = file_name
        self.duration = ASSEMBLY_DURATION_BY_FILE.get(file_name, 90)
        self.media_id = "media:" + file_name

    def GetName(self) -> str:
        return self.file_name

    def GetClipProperty(self) -> dict[str, str]:
        return {"File Name": self.file_name}

    def GetMediaId(self) -> str:
        return self.media_id

    def GetUniqueId(self) -> str:
        return "clip:" + self.file_name


class FakeTimelineItem:
    def __init__(
        self,
        clip: FakeClip,
        start: int,
        duration: int,
        *,
        source_start: int = 0,
        source_end: int | None = None,
    ) -> None:
        self.clip = clip
        self.start = start
        self.duration = duration
        self.source_start = source_start
        self.source_end = source_end if source_end is not None else source_start + duration - 1

    def GetName(self) -> str:
        return self.clip.GetName()

    def GetMediaPoolItem(self) -> FakeClip:
        return self.clip

    def GetStart(self, subframe_precision: bool = False) -> int:
        return self.start

    def GetDuration(self, subframe_precision: bool = False) -> int:
        return self.duration

    def GetEnd(self, subframe_precision: bool = False) -> int:
        return self.start + self.duration

    def GetSourceStartFrame(self) -> int:
        return self.source_start

    def GetSourceEndFrame(self) -> int:
        return self.source_end

    def GetUniqueId(self) -> str:
        return f"timeline-item:{self.clip.file_name}:{self.start}"


class FakeTimeline:
    def __init__(self, name: str) -> None:
        self.name = name
        self.start_frame = 108000
        self.start_timecode = "01:00:00:00"
        self.video_items: list[FakeTimelineItem] = []
        self.audio_items: list[FakeTimelineItem] = []
        self.markers: dict[float, dict[str, object]] = {}

    def GetName(self) -> str:
        return self.name

    def GetUniqueId(self) -> str:
        return "timeline:" + self.name

    def GetStartFrame(self) -> int:
        return self.start_frame

    def GetEndFrame(self) -> int:
        items = self.video_items + self.audio_items
        return max((item.GetEnd() for item in items), default=self.start_frame)

    def SetStartTimecode(self, timecode: str) -> bool:
        hours, minutes, seconds, frames = (int(value) for value in timecode.split(":"))
        self.start_frame = ((hours * 60 + minutes) * 60 + seconds) * 30 + frames
        self.start_timecode = timecode
        return True

    def GetStartTimecode(self) -> str:
        return self.start_timecode

    def GetTrackCount(self, track_type: str) -> int:
        return 1 if track_type in {"video", "audio"} else 0

    def GetItemListInTrack(self, track_type: str, index: int) -> list[FakeTimelineItem]:
        if index != 1:
            return []
        return self.video_items if track_type == "video" else self.audio_items if track_type == "audio" else []

    def AddMarker(
        self,
        frame_id: int,
        color: str,
        name: str,
        note: str,
        duration: int,
        custom_data: str,
    ) -> bool:
        if float(frame_id) in self.markers:
            return False
        self.markers[float(frame_id)] = {
            "color": color,
            "name": name,
            "note": note,
            "duration": float(duration),
            "customData": custom_data,
        }
        return True

    def GetMarkers(self) -> dict[float, dict[str, object]]:
        return self.markers


class FakeFolder:
    def __init__(self, name: str) -> None:
        self.name = name
        self.subfolders: list[FakeFolder] = []
        self.clips: list[FakeClip] = []

    def GetName(self) -> str:
        return self.name

    def GetSubFolderList(self) -> list[FakeFolder]:
        return self.subfolders

    def GetClipList(self) -> list[FakeClip]:
        return self.clips


class FakeMediaPool:
    def __init__(self, project: FakeProject) -> None:
        self.project = project
        self.root = FakeFolder("Master")
        self.current_folder = self.root

    def GetRootFolder(self) -> FakeFolder:
        return self.root

    def AddSubFolder(self, parent: FakeFolder, name: str) -> FakeFolder:
        folder = FakeFolder(name)
        parent.subfolders.append(folder)
        return folder

    def SetCurrentFolder(self, folder: FakeFolder) -> bool:
        self.current_folder = folder
        return True

    def ImportMedia(self, paths: list[str]) -> list[FakeClip]:
        clips = [FakeClip(Path(path).name) for path in paths]
        self.current_folder.clips.extend(clips)
        return clips

    def CreateEmptyTimeline(self, name: str) -> FakeTimeline:
        timeline = FakeTimeline(name)
        self.project.timelines.append(timeline)
        self.project.current_timeline = timeline
        return timeline

    def AppendToTimeline(
        self, values: FakeClip | list[FakeClip | dict[str, object]]
    ) -> list[FakeTimelineItem]:
        timeline = self.project.current_timeline
        if timeline is None:
            return []
        normalized = [values] if isinstance(values, FakeClip) else values
        appended: list[FakeTimelineItem] = []
        for value in normalized:
            if isinstance(value, dict):
                clip = value["mediaPoolItem"]
                assert isinstance(clip, FakeClip)
                start = int(value["recordFrame"])
                if "startFrame" in value and "endFrame" in value:
                    source_start = int(value["startFrame"])
                    source_end = int(value["endFrame"])
                    duration = source_end - source_start
                else:
                    source_start = 0
                    source_end = clip.duration - 1
                    duration = clip.duration
                item = FakeTimelineItem(
                    clip,
                    start,
                    duration,
                    source_start=source_start,
                    source_end=source_end,
                )
                timeline.video_items.append(item)
                appended.append(item)
            else:
                start = timeline.GetEndFrame()
                video = FakeTimelineItem(value, start, 90)
                audio = FakeTimelineItem(value, start, 90)
                timeline.video_items.append(video)
                timeline.audio_items.append(audio)
                appended.extend([video, audio])
        return appended

    def ImportTimelineFromFile(self, path: str, options: dict[str, object]) -> FakeTimeline | None:
        clips = [clip for folder in self.root.subfolders for clip in folder.clips]
        if not clips:
            return None
        timeline = FakeTimeline(str(options["timelineName"]))
        timeline.video_items.append(
            FakeTimelineItem(clips[0], timeline.start_frame, 24, source_start=0, source_end=24)
        )
        timeline.video_items.append(
            FakeTimelineItem(clips[0], timeline.start_frame + 30, 30, source_start=24, source_end=54)
        )
        self.project.timelines.append(timeline)
        self.project.current_timeline = timeline
        return timeline


class FakeProject:
    def __init__(self, name: str, *, with_timeline: bool = False) -> None:
        self.name = name
        self.settings = {
            "timelineFrameRate": "24",
            "timelineResolutionWidth": "1920",
            "timelineResolutionHeight": "1080",
        }
        self.timelines: list[FakeTimeline] = []
        self.current_timeline: FakeTimeline | None = None
        self.media_pool = FakeMediaPool(self)
        if with_timeline:
            self.current_timeline = FakeTimeline("Assembly")
            self.timelines.append(self.current_timeline)

    def GetName(self) -> str:
        return self.name

    def GetTimelineCount(self) -> int:
        return len(self.timelines)

    def GetTimelineByIndex(self, index: int) -> FakeTimeline:
        return self.timelines[index - 1]

    def GetCurrentTimeline(self) -> FakeTimeline | None:
        return self.current_timeline

    def SetCurrentTimeline(self, timeline: FakeTimeline) -> bool:
        self.current_timeline = timeline
        return True

    def GetMediaPool(self) -> FakeMediaPool:
        return self.media_pool

    def GetSetting(self, key: str) -> str:
        return self.settings[key]

    def SetSetting(self, key: str, value: str) -> bool:
        self.settings[key] = value
        return True


class FakeProjectManager:
    def __init__(self) -> None:
        previous = FakeProject("Previous Project", with_timeline=True)
        self.projects: dict[str, FakeProject] = {previous.GetName(): previous}
        self.current = previous
        self.save_count = 0

    def GetCurrentDatabase(self) -> dict[str, str]:
        return {"DbType": "Disk", "DbName": "Local", "IpAddress": "private-value"}

    def GetCurrentProject(self) -> FakeProject:
        return self.current

    def SaveProject(self) -> bool:
        self.save_count += 1
        return True

    def GetProjectListInCurrentFolder(self) -> list[str]:
        return list(self.projects)

    def CreateProject(self, name: str) -> FakeProject | None:
        if name in self.projects:
            return None
        project = FakeProject(name)
        self.projects[name] = project
        self.current = project
        return project

    def LoadProject(self, name: str) -> FakeProject | None:
        project = self.projects.get(name)
        if project is not None:
            self.current = project
        return project

    def CloseProject(self, project: FakeProject) -> bool:
        return self.current is not project

    def DeleteProject(self, name: str) -> bool:
        if self.current.GetName() == name:
            return False
        return self.projects.pop(name, None) is not None


class FakeResolve:
    def __init__(self) -> None:
        self.project_manager = FakeProjectManager()

    def GetProductName(self) -> str:
        return "DaVinci Resolve"

    def GetVersionString(self) -> str:
        return "21.0.3.7"

    def GetVersion(self) -> list[object]:
        return [21, 0, 3, 7, ""]

    def GetCurrentPage(self) -> str:
        return "edit"

    def GetProjectManager(self) -> FakeProjectManager:
        return self.project_manager


def _write_assembly_sources(root: Path) -> tuple[Path, Path]:
    production_root = root / "runtime-introduction"
    media_root = root / "media"
    timeline_root = production_root / "timeline"
    production_root.mkdir(parents=True)
    media_root.mkdir(parents=True)
    timeline_root.mkdir(parents=True)

    assets: list[dict[str, object]] = []
    timeline = otio.schema.Timeline(
        name="Runtime Introduction · Assembly v0",
        global_start_time=otio.opentime.RationalTime(108000, 30),
    )
    timeline.metadata.update(
        {"ordivon": {"productionId": "runtime-introduction", "status": "assembly-v0", "totalFrames": 2340}}
    )
    track = otio.schema.Track(name="V1 · Assembly", kind=otio.schema.TrackKind.Video)

    for index, (segment_id, asset_id, file_name, duration, placeholder, bin_name) in enumerate(ASSEMBLY_LAYOUT):
        media = media_root / file_name
        media.write_bytes((f"media-{index}-" * 11).encode())
        digest = "sha256:" + hashlib.sha256(media.read_bytes()).hexdigest()
        assets.append(
            {
                "id": asset_id,
                "role": "test assembly media",
                "origin": "generated",
                "selectedBlob": {"digest": digest, "sizeBytes": media.stat().st_size, "mediaType": "video/mp4"},
                "technical": {"fileName": file_name, "durationFrames": duration},
                "rights": {"status": "owned"},
            }
        )
        available = otio.opentime.TimeRange(
            otio.opentime.RationalTime(0, 30),
            otio.opentime.RationalTime(duration, 30),
        )
        reference = otio.schema.ExternalReference(
            target_url="ordivon-asset://" + asset_id,
            available_range=available,
        )
        track.append(
            otio.schema.Clip(
                name=segment_id,
                media_reference=reference,
                source_range=available,
                metadata={
                    "ordivon": {
                        "assetId": asset_id,
                        "binName": bin_name,
                        "placeholder": placeholder,
                        "segmentId": segment_id,
                    }
                },
            )
        )
    timeline.tracks.append(track)
    otio.adapters.write_to_file(timeline, str(timeline_root / "assembly.v0.otio"), adapter_name="otio_json")

    (production_root / "production.json").write_text(
        json.dumps(
            {
                "schemaVersion": 1,
                "id": "runtime-introduction",
                "workingProfile": {
                    "frameRate": {"numerator": 30, "denominator": 1},
                    "canvas": {"width": 1920, "height": 1080},
                },
                "sources": {"otioSnapshots": ["timeline/assembly.v0.otio"]},
            }
        ),
        encoding="utf-8",
    )
    (production_root / "assets.json").write_text(
        json.dumps({"schemaVersion": 1, "productionId": "runtime-introduction", "assets": assets}),
        encoding="utf-8",
    )
    return production_root, media_root


def _build_test_assembly_operation(
    production_root: Path,
    media_root: Path,
    operation_id: str,
) -> dict[str, object]:
    operation = build_assembly_operation(
        production_root=production_root,
        media_root=media_root,
        windows_media_root=str(media_root),
        operation_id=operation_id,
    )
    parameters = operation["parameters"]
    assert isinstance(parameters, dict)
    segments = parameters["segments"]
    assert isinstance(segments, list)
    for segment in segments:
        assert isinstance(segment, dict)
        segment["mediaPath"] = str(media_root / str(segment["fileName"]))
    return operation


class ResolveAdapterTests(unittest.TestCase):
    def test_probe_operation_is_minimal_and_valid(self) -> None:
        operation = build_probe_operation("resolve-probe-test-001")
        generated = build_probe_operation()
        self.assertEqual(validate_operation(operation), operation)
        self.assertEqual(validate_operation(generated), generated)
        self.assertEqual(operation["action"], "probe")
        self.assertEqual(set(operation), {"schemaVersion", "operationId", "action", "requestedAt"})

    def test_rejects_unknown_operation_fields(self) -> None:
        operation = build_probe_operation("resolve-probe-test-002")
        operation["project"] = "unexpected"
        with self.assertRaisesRegex(ValueError, "unknown operation fields"):
            validate_operation(operation)

    def test_probe_reads_state_without_private_database_address(self) -> None:
        operation = build_probe_operation("resolve-probe-test-003")
        probe = execute_operation(operation, FakeResolve(), "test-double")
        self.assertEqual(probe["productName"], "DaVinci Resolve")
        self.assertEqual(probe["project"]["currentTimeline"], "Assembly")
        self.assertTrue(probe["capabilities"]["mediaPool"])
        self.assertNotIn("IpAddress", probe["database"])
        self.assertNotIn("private-value", json.dumps(probe))

    def test_smoke_operation_is_idempotent_and_restores_previous_project(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            media = Path(directory) / "smoke.mp4"
            media.write_bytes(b"deterministic smoke media")
            digest = "sha256:" + hashlib.sha256(media.read_bytes()).hexdigest()
            operation = build_smoke_operation(
                operation_id="resolve-smoke-test-001",
                media_path=str(media),
                media_digest=digest,
            )
            validate_operation(operation)
            resolve = FakeResolve()

            first = execute_operation(operation, resolve, "test-double")
            second = execute_operation(operation, resolve, "test-double")

            self.assertEqual(first["project"]["disposition"], "created")
            self.assertEqual(first["media"]["disposition"], "imported")
            self.assertEqual(first["timeline"]["mediaDisposition"], "appended")
            self.assertEqual(second["project"]["disposition"], "reused")
            self.assertEqual(second["media"]["disposition"], "reused")
            self.assertEqual(second["timeline"]["mediaDisposition"], "reused")
            self.assertEqual(resolve.project_manager.current.GetName(), "Previous Project")
            self.assertTrue(first["restoredPreviousProject"])
            self.assertEqual(first["timeline"]["videoTrackItems"], ["smoke.mp4"])

    def test_smoke_rejects_digest_mismatch_before_project_creation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            media = Path(directory) / "smoke.mp4"
            media.write_bytes(b"content")
            operation = build_smoke_operation(
                operation_id="resolve-smoke-test-002",
                media_path=str(media),
                media_digest="sha256:" + "0" * 64,
            )
            resolve = FakeResolve()
            with self.assertRaisesRegex(ValueError, "digest does not match"):
                execute_operation(operation, resolve, "test-double")
            self.assertEqual(list(resolve.project_manager.projects), ["Previous Project"])

    def test_assembly_compiles_from_production_assets_and_otio(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            production_root, media_root = _write_assembly_sources(root)
            operation = build_assembly_operation(
                production_root=production_root,
                media_root=media_root,
                windows_media_root=str(media_root),
                operation_id="resolve-assembly-test-001",
            )
            validate_operation(operation)
            parameters = operation["parameters"]
            self.assertEqual(parameters["projectName"], ASSEMBLY_PROJECT_NAME)
            self.assertEqual(parameters["timelineName"], ASSEMBLY_TIMELINE_NAME)
            self.assertEqual(parameters["totalFrames"], 2340)
            self.assertEqual(len(parameters["segments"]), 11)
            self.assertEqual(sum(segment["placeholder"] for segment in parameters["segments"]), 8)
            self.assertEqual(parameters["segments"][-1]["startFrame"], 2250)

    def test_assembly_executes_exact_layout_then_reuses_it(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            production_root, media_root = _write_assembly_sources(root)
            operation = _build_test_assembly_operation(
                production_root,
                media_root,
                "resolve-assembly-test-002",
            )
            resolve = FakeResolve()

            first = execute_operation(operation, resolve, "test-double")
            second = execute_operation(operation, resolve, "test-double")

            self.assertEqual(first["project"]["disposition"], "created")
            self.assertEqual(first["timeline"]["videoItemCount"], 11)
            self.assertEqual(first["timeline"]["totalFrames"], 2340)
            self.assertEqual(first["timeline"]["markerCount"], 11)
            self.assertEqual(first["placeholderCount"], 8)
            self.assertTrue(all(segment["timelineDisposition"] == "appended" for segment in first["segments"]))
            self.assertTrue(all(segment["timelineDisposition"] == "reused" for segment in second["segments"]))
            self.assertTrue(all(asset["disposition"] == "reused" for asset in second["assets"]))
            self.assertEqual(resolve.project_manager.current.GetName(), "Previous Project")
            self.assertTrue(first["restoredPreviousProject"])

    def test_assembly_rejects_existing_layout_drift(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            production_root, media_root = _write_assembly_sources(root)
            operation = _build_test_assembly_operation(
                production_root,
                media_root,
                "resolve-assembly-test-003",
            )
            resolve = FakeResolve()
            execute_operation(operation, resolve, "test-double")
            assembly = resolve.project_manager.projects[ASSEMBLY_PROJECT_NAME]
            assert assembly.current_timeline is not None
            assembly.current_timeline.video_items[0].duration += 1

            with self.assertRaisesRegex(RuntimeError, "unexpected duration"):
                execute_operation(operation, resolve, "test-double")
            self.assertEqual(resolve.project_manager.current.GetName(), "Previous Project")

    def test_assembly_rejects_digest_mismatch_before_project_creation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            production_root, media_root = _write_assembly_sources(root)
            operation = _build_test_assembly_operation(
                production_root,
                media_root,
                "resolve-assembly-test-004",
            )
            operation["parameters"]["segments"][0]["mediaDigest"] = "sha256:" + "0" * 64
            resolve = FakeResolve()
            with self.assertRaisesRegex(ValueError, "digest does not match"):
                execute_operation(operation, resolve, "test-double")
            self.assertEqual(list(resolve.project_manager.projects), ["Previous Project"])

    def test_version_specific_compatibility_probe_runs_all_cases_and_cleans_up(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            media = root / "resolve-smoke-1080p30.mp4"
            otio_path = root / "resolve-21.0.3.7-compatibility.otio"
            developer_readme = root / "README.txt"
            media.write_bytes(b"compatibility-media")
            otio_path.write_bytes(b"compatibility-otio")
            developer_readme.write_bytes(b"resolve-21-developer-package")

            def digest(path: Path) -> str:
                return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()

            operation = build_compatibility_operation(
                media_path=str(media),
                media_digest=digest(media),
                media_file_name=media.name,
                media_expected_frames=90,
                otio_path=str(otio_path),
                otio_digest=digest(otio_path),
                source_clips_path=str(root),
                developer_package_digest=digest(developer_readme),
                operation_id="resolve-compatibility-test-001",
            )
            self.assertEqual(validate_operation(operation), operation)
            resolve = FakeResolve()
            with patch.object(runner_menu, "_developer_readme_path", return_value=developer_readme):
                result = execute_operation(operation, resolve, "test-double")

            self.assertEqual(result["resolve"]["versionString"], "21.0.3.7")
            self.assertEqual(result["resolve"]["edition"], "free")
            self.assertEqual(result["caseSummary"], {"total": 6, "completed": 6, "failed": 0})
            self.assertTrue(result["restoredPreviousProject"])
            self.assertTrue(result["cleanup"]["deleted"])
            self.assertEqual(list(resolve.project_manager.projects), ["Previous Project"])
            subclip = next(case for case in result["cases"] if case["id"] == "append-subclip-0-23")
            item = subclip["trackScan"]["videoItems"][0]
            self.assertEqual(item["timeline"]["getDuration"]["value"], 23)
            self.assertEqual(item["candidateFrameCounts"]["endMinusStartPlusOne"], 24)
            self.assertEqual(item["candidateFrameCounts"]["sourceEndMinusStartPlusOne"], 24)

    def test_menu_environment_without_dunder_file_uses_local_app_data(self) -> None:
        original = runner_menu.__dict__.pop("__file__", None)
        try:
            with patch.dict(os.environ, {"LOCALAPPDATA": r"C:\Users\Test\AppData\Local"}):
                expected = Path(r"C:\Users\Test\AppData\Local") / "OrdivonStudio" / "control"
                self.assertEqual(runner_menu.control_directory(), expected)
        finally:
            if original is not None:
                runner_menu.__dict__["__file__"] = original

    def test_installs_self_contained_runner_and_config(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            result = install_runner(
                scripts_directory=root / "scripts",
                control_directory=root / "control",
                windows_control_directory=r"C:\Local\OrdivonStudio\control",
            )
            runner = root / "scripts" / RUNNER_FILENAME
            config = root / "scripts" / CONFIG_FILENAME
            self.assertTrue(runner.is_file())
            self.assertTrue(config.is_file())
            self.assertIn("menu", result)
            config_value = json.loads(config.read_text(encoding="utf-8"))
            self.assertEqual(config_value["controlDirectory"], r"C:\Local\OrdivonStudio\control")

    def test_prepare_operations_remove_stale_result(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            control = root / "control"
            control.mkdir()
            (control / "resolve-result.json").write_text("{}", encoding="utf-8")
            probe = prepare_probe(control_directory=control, operation_id="resolve-probe-test-004")
            self.assertTrue((control / OPERATION_FILENAME).is_file())
            self.assertFalse((control / "resolve-result.json").exists())
            self.assertEqual(probe["operation"]["operationId"], "resolve-probe-test-004")

            media = root / "smoke.mp4"
            media.write_bytes(b"media")
            (control / "resolve-result.json").write_text("{}", encoding="utf-8")
            smoke = prepare_smoke(
                control_directory=control,
                media_path=media,
                windows_media_path=str(media),
                operation_id="resolve-smoke-test-003",
            )
            self.assertFalse((control / "resolve-result.json").exists())
            self.assertEqual(smoke["operation"]["action"], "create-smoke-project")

            production_root, media_root = _write_assembly_sources(root / "assembly")
            (control / "resolve-result.json").write_text("{}", encoding="utf-8")
            assembly = prepare_assembly(
                production_root=production_root,
                control_directory=control,
                media_root=media_root,
                windows_media_root=str(media_root),
                operation_id="resolve-assembly-test-005",
            )
            self.assertFalse((control / "resolve-result.json").exists())
            self.assertEqual(assembly["operation"]["action"], "assemble-review")
            self.assertEqual(assembly["assembly"]["totalSeconds"], 78)

    def test_result_validator_rejects_identity_drift_and_private_path(self) -> None:
        result = {
            "schemaVersion": 1,
            "adapter": "resolve",
            "adapterVersion": "0.3.0",
            "operationId": "resolve-probe-test-005",
            "operationDigest": "sha256:" + "a" * 64,
            "action": "probe",
            "status": "succeeded",
            "startedAt": "2026-08-04T00:00:00Z",
            "finishedAt": "2026-08-04T00:00:01Z",
            "probe": {"capabilities": {}, "note": r"C:\Users\private"},
        }
        errors = validate_result(result, expected_operation_id="resolve-probe-other")
        self.assertTrue(any("does not match" in error for error in errors))
        self.assertTrue(any("private material" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
