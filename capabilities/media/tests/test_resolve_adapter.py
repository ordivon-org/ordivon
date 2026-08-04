from __future__ import annotations

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
    install_runner,
    prepare_probe,
    validate_probe_result,
)
from ordivon_studio.resolve_runner_menu import execute_operation, validate_operation


class FakeTimeline:
    def GetName(self) -> str:
        return "Assembly"


class FakeMediaPool:
    pass


class FakeProject:
    def GetName(self) -> str:
        return "Runtime Introduction"

    def GetTimelineCount(self) -> int:
        return 1

    def GetCurrentTimeline(self) -> FakeTimeline:
        return FakeTimeline()

    def GetMediaPool(self) -> FakeMediaPool:
        return FakeMediaPool()

    def GetSetting(self, key: str) -> str:
        return {
            "timelineFrameRate": "30",
            "timelineResolutionWidth": "1920",
            "timelineResolutionHeight": "1080",
        }[key]


class FakeProjectManager:
    def GetCurrentDatabase(self) -> dict[str, str]:
        return {"DbType": "Disk", "DbName": "Local", "IpAddress": "private-value"}

    def GetCurrentProject(self) -> FakeProject:
        return FakeProject()


class FakeResolve:
    def GetProductName(self) -> str:
        return "DaVinci Resolve"

    def GetVersionString(self) -> str:
        return "21.0.3.7"

    def GetVersion(self) -> list[object]:
        return [21, 0, 3, 7, ""]

    def GetCurrentPage(self) -> str:
        return "edit"

    def GetProjectManager(self) -> FakeProjectManager:
        return FakeProjectManager()


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

    def test_prepare_probe_removes_stale_result(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            control = Path(directory)
            (control / "resolve-result.json").write_text("{}", encoding="utf-8")
            prepared = prepare_probe(control_directory=control, operation_id="resolve-probe-test-004")
            self.assertTrue((control / OPERATION_FILENAME).is_file())
            self.assertFalse((control / "resolve-result.json").exists())
            self.assertEqual(prepared["operation"]["operationId"], "resolve-probe-test-004")

    def test_result_validator_rejects_identity_drift_and_private_path(self) -> None:
        result = {
            "schemaVersion": 1,
            "adapter": "resolve",
            "adapterVersion": "0.1.0",
            "operationId": "resolve-probe-test-005",
            "operationDigest": "sha256:" + "a" * 64,
            "action": "probe",
            "status": "succeeded",
            "startedAt": "2026-08-04T00:00:00Z",
            "finishedAt": "2026-08-04T00:00:01Z",
            "probe": {"capabilities": {}, "note": r"C:\Users\private"},
        }
        errors = validate_probe_result(result, expected_operation_id="resolve-probe-other")
        self.assertTrue(any("does not match" in error for error in errors))
        self.assertTrue(any("private material" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
