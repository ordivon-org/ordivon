"""Contract tests for scoped Harness evidence Python compatibility currentness.

These cases use a synthetic Git object reader; they do not mutate repository history.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "check_evidence.py"
SPEC = importlib.util.spec_from_file_location("check_evidence_python_currentness", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
check_evidence = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(check_evidence)

BASE_PYTHON = ">=3.14.7,<3.15"
NEW_PYTHON = ">=3.15,<3.16"
SCOPE = ("src/ordivon_harness/adaptive_edit.py",)


def _project(requires_python: str) -> bytes:
    return f'[project]\nrequires-python = "{requires_python}"\n'.encode()


def _lock(requires_python: str) -> bytes:
    return (
        "version = 1\n"
        f'requires-python = "{requires_python}"\n'
        "[[package]]\n"
        'name = "ordivon-harness"\n'
        'version = "0.6.0"\n'
    ).encode()


class ScopedPythonCompatibilityCurrentnessTests(TestCase):
    def _currentness(self, project_head: str, lock_head: str) -> tuple[bool, list[str]]:
        files = {
            ("BASE", "pyproject.toml"): _project(BASE_PYTHON),
            ("BASE", "uv.lock"): _lock(BASE_PYTHON),
            ("HEAD", "pyproject.toml"): _project(project_head),
            ("HEAD", "uv.lock"): _lock(lock_head),
        }

        def git_read(revision: str, path: str) -> bytes:
            return files[(revision, path)]

        with (
            patch.object(check_evidence, "_git_file_bytes", side_effect=git_read),
            patch.object(check_evidence, "_git_scope_entries", return_value={}),
            patch.object(
                check_evidence.subprocess, "run", return_value=SimpleNamespace(returncode=0)
            ),
        ):
            initial = check_evidence._runtime_dependency_closure_digest("BASE")
            self.assertEqual(
                initial,
                check_evidence._runtime_dependency_closure_digest("HEAD"),
                "Control: legacy closure digest must not detect compatibility-only changes",
            )
            return check_evidence._verified_revision_is_current(
                "BASE", SCOPE, runtime_dependency_closure_digest=initial
            )

    def test_scoped_currentness_accepts_unchanged_python_compatibility(self) -> None:
        self.assertEqual(self._currentness(BASE_PYTHON, BASE_PYTHON), (True, []))

    def test_scoped_currentness_detects_pyproject_only_python_change(self) -> None:
        current, invalidating = self._currentness(NEW_PYTHON, BASE_PYTHON)
        self.assertFalse(current)
        self.assertEqual(invalidating, ["@runtime-dependency-closure"])

    def test_scoped_currentness_detects_uv_lock_only_python_change(self) -> None:
        current, invalidating = self._currentness(BASE_PYTHON, NEW_PYTHON)
        self.assertFalse(current)
        self.assertEqual(invalidating, ["@runtime-dependency-closure"])

    def test_scoped_currentness_detects_both_python_requirements_change(self) -> None:
        current, invalidating = self._currentness(NEW_PYTHON, NEW_PYTHON)
        self.assertFalse(current)
        self.assertEqual(invalidating, ["@runtime-dependency-closure"])

    def test_scoped_currentness_ignores_formatting_only_specifier_changes(self) -> None:
        self.assertEqual(
            self._currentness(" <3.15 , >=3.14.7 ", ">=3.14.7, <3.15"),
            (True, []),
        )

    def test_scoped_currentness_accepts_reordered_equivalent_constraints(self) -> None:
        self.assertEqual(
            self._currentness("<3.15,>=3.14.7", "<3.15,>=3.14.7"),
            (True, []),
        )

    def test_scoped_currentness_rejects_missing_python_requirement(self) -> None:
        with self.assertRaisesRegex(ValueError, "requires-python"):
            self._currentness("", BASE_PYTHON)
