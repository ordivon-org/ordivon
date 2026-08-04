from __future__ import annotations

import hashlib
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import ordivon_studio.resolve_runner_menu as runner_menu
from ordivon_studio.resolve_adapter import (
    CONFIG_FILENAME,
    OPERATION_FILENAME,
    RUNNER_FILENAME,
    build_probe_operation,
    build_smoke_operation,
    install_runner,
    prepare_probe,
    prepare_smoke,
    validate_result,
)
from ordivon_studio.resolve_runner_menu import execute_operation, validate_operation


class FakeTimelineItem:
    def __init__(self, name: str) -> None:
        self.name = name

    def GetName(self) -> str:
        return self.name


class FakeTimeline:
    def __init__(self, name: str) -> None:
        self.name = name
        self.video_items: list[FakeTimelineItem] = []
        self.audio_items: list[FakeTimelineItem] = []

    def GetName(self) -> str:
        return self.name

    def GetItemListInTrack(self, track_type: str, index: int) -> list[FakeTimelineItem]:
        if index != 1:
            return []
        return self.video_items if track_type == "video" else self.audio_items if track_type == "audio" else []


class FakeClip:
    def __init__(self, file_name: str) -> None:
        self.file_name = file_name

    def GetName(self) -> str:
        return self.file_name

    def GetClipProperty(self) -> dict[str, str]:
        return {"File Name": self.file_name}


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

    def AppendToTimeline(self, clips: list[FakeClip]) -> list[FakeTimelineItem]:
        timeline = self.project.current_timeline
        if timeline is None:
            return []
        appended: list[FakeTimelineItem] = []
        for clip in clips:
            video = FakeTimelineItem(clip.GetName())
            audio = FakeTimelineItem(clip.GetName())
            timeline.video_items.append(video)
            timeline.audio_items.append(audio)
            appended.extend([video, audio])
        return appended


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
            control = Path(directory) / "control"
            control.mkdir()
            (control / "resolve-result.json").write_text("{}", encoding="utf-8")
            probe = prepare_probe(control_directory=control, operation_id="resolve-probe-test-004")
            self.assertTrue((control / OPERATION_FILENAME).is_file())
            self.assertFalse((control / "resolve-result.json").exists())
            self.assertEqual(probe["operation"]["operationId"], "resolve-probe-test-004")

            media = Path(directory) / "smoke.mp4"
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

    def test_result_validator_rejects_identity_drift_and_private_path(self) -> None:
        result = {
            "schemaVersion": 1,
            "adapter": "resolve",
            "adapterVersion": "0.2.0",
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
