from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest

MODULE_PATH = Path(__file__).resolve().parents[1] / "workstation/windows/runtime_provider.py"
SPEC = importlib.util.spec_from_file_location("windows_runtime_provider", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class RuntimeEnvironmentTests(unittest.TestCase):
    def test_merge_preserves_unrelated_and_replaces_managed_values_once(self) -> None:
        before = "A=1\nORDIVON_WINDOWS_LAUNCHER_PATH=/old.exe\nB=2\nORDIVON_WINDOWS_LAUNCHER_PATH=/duplicate.exe\n"
        desired = {
            "ORDIVON_WINDOWS_LAUNCHER_PATH": "/mnt/c/new.exe",
            "ORDIVON_WINDOWS_WSL_DISTRIBUTION": "archlinux",
        }
        after = MODULE.merge_runtime_environment(before, desired)
        self.assertIn("A=1\n", after)
        self.assertIn("B=2\n", after)
        self.assertEqual(after.count("ORDIVON_WINDOWS_LAUNCHER_PATH="), 1)
        self.assertEqual(after.count("ORDIVON_WINDOWS_WSL_DISTRIBUTION="), 1)
        self.assertIn("ORDIVON_WINDOWS_LAUNCHER_PATH=/mnt/c/new.exe", after)
        self.assertIn("ORDIVON_WINDOWS_WSL_DISTRIBUTION=archlinux", after)

    def test_versioned_launcher_path_binds_source_revision(self) -> None:
        provider = {
            "launcher_root": "/mnt/c/ProgramData/Ordivon/Runtime/WindowsJobLauncher",
            "source_revision": "a" * 40,
            "launcher_filename": "launcher.exe",
        }
        self.assertEqual(
            str(MODULE.launcher_path(provider)),
            "/mnt/c/ProgramData/Ordivon/Runtime/WindowsJobLauncher/"
            + "a" * 40
            + "/launcher.exe",
        )

    def test_provider_dropin_resets_base_hardening_and_adds_only_vsock(self) -> None:
        lines = MODULE.WINDOWS_PROVIDER_DROPIN.splitlines()
        self.assertEqual(lines[0], "[Service]")
        self.assertEqual(lines[1], "RestrictAddressFamilies=")
        self.assertEqual(
            set(lines[2].split("=", 1)[1].split()),
            {"AF_UNIX", "AF_INET", "AF_INET6", "AF_VSOCK"},
        )

    def test_context_validation_separates_limited_and_elevated(self) -> None:
        limited = {
            "tokenType": 1,
            "tokenUserSid": "S-1-5-21-1",
            "tokenIsElevated": False,
            "tokenIntegrityLevelRid": 8192,
            "administratorsGroupAttributes": 16,
            "environment": {"Path": "x"},
        }
        elevated = {
            "tokenType": 1,
            "tokenUserSid": "S-1-5-21-1",
            "tokenIsElevated": True,
            "tokenIntegrityLevelRid": 12288,
            "administratorsGroupAttributes": 15,
            "environment": {"Path": "x"},
        }
        self.assertFalse(MODULE.validate_context(limited, "limited")["tokenIsElevated"])
        self.assertTrue(MODULE.validate_context(elevated, "elevated")["tokenIsElevated"])
        with self.assertRaises(RuntimeError):
            MODULE.validate_context(elevated, "limited")
        with self.assertRaises(RuntimeError):
            MODULE.validate_context(limited, "elevated")


if __name__ == "__main__":
    unittest.main()
