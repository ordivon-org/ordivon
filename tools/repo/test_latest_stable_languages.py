"""Negative and positive contract tests for the latest-stable-by-default gate."""
from __future__ import annotations

import datetime as dt
import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

SOURCE = Path(__file__).with_name("check_latest_stable_languages.py")
SPEC = importlib.util.spec_from_file_location("language_gate", SOURCE)
assert SPEC and SPEC.loader
gate = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gate)

TARGETS = {
    k: {"version": v, "officialRelease": json.loads(
        Path(__file__).with_name("latest_stable_languages.json").read_text()
    )["targets"][k]["officialRelease"]}
    for k, v in (("python", "3.15.0"), ("rust", "1.99.0"), ("node", "26.12.0"), ("godot", "4.7.2"), ("typescript", "7.0.2"), ("opa", "1.21.2"), ("powershell", "7.6.7"), ("uv", "0.13.1"), ("uv-build", "0.13.1"), ("bash", "5.3.15"), ("sqlite", "3.54.0"), ("postgresql", "18.6"), ("osquery", "5.23.1"))
}


class LatestStableLanguageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / "tools/repo").mkdir(parents=True)
        self.baseline = {
            "schemaVersion": 1,
            "observedOn": "2026-10-15",
            "validForDays": 3,
            "targets": TARGETS,
            "exceptions": [],
        }
        subprocess.run(["git", "-C", str(self.root), "init", "-q"], check=True)

    def put(self, file: str, content: str) -> None:
        path = self.root / file
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        subprocess.run(["git", "-C", str(self.root), "add", file], check=True)

    def inspect(self, date: str = "2026-10-15") -> list[str]:
        self.put("tools/repo/latest_stable_languages.json", json.dumps(self.baseline))
        issues, _, _ = gate.check(self.root, today=dt.date.fromisoformat(date))
        return issues

    def test_exact_latest_stable_pins_are_accepted(self) -> None:
        self.put("x/mise.toml", '[tools]\npython="3.15.0"\nrust="1.99.0"\nnode="26.12.0"\n')
        self.put("x/.python-version", "3.15.0\n")
        self.put("x/rust-toolchain.toml", '[toolchain]\nchannel="1.99.0"\n')
        self.put("x/godot/mise.toml", '[tools]\ngodot="4.7.2-stable"\n')
        self.put("x/pyproject.toml", '[project]\nname="x"\nversion="0.1"\nrequires-python="==3.15.0"\n[tool.uv]\nrequired-version="==0.13.1"\n')
        self.put("x/package.json", '{"engines":{"node":"26.12.0"},"devDependencies":{"typescript":"7.0.2"}}')
        self.assertEqual(self.inspect(), [])

    def test_stale_uv_build_backend_is_rejected(self) -> None:
        self.put("project/pyproject.toml", '[project]\nname="x"\nversion="1"\n[build-system]\nrequires=["uv_build>=0.12.3,<0.13.0"]\nbuild-backend="uv_build"\n')
        self.assertTrue(any("uv-build=>=0.12.3,<0.13.0" in x for x in self.inspect()))

    def test_old_node_range_and_rust_pin_are_rejected(self) -> None:
        self.put("x/mise.toml", '[tools]\nrust="1.95.0"\n')
        self.put("x/package.json", '{"engines":{"node":">=26.9.0 <27"}}')
        issues = self.inspect()
        self.assertTrue(any("rust=1.95.0" in x for x in issues))
        self.assertTrue(any("node=>=26.9.0 <27" in x for x in issues))

    def test_provider_uv_version_pin_is_not_overlooked(self) -> None:
        self.put("windows/provider.toml", '[provider]\nuv_version="0.12.3"\n')
        self.assertTrue(any("windows/provider.toml#provider.uv_version" in x for x in self.inspect()))

    def test_independent_provider_python_config_pin_is_not_overlooked(self) -> None:
        self.put("windows/provider.toml", 'python_version="3.12.13"\n')
        self.assertTrue(any("windows/provider.toml#python_version" in x for x in self.inspect()))

    def test_untrusted_official_release_url_fails_closed(self) -> None:
        self.baseline["targets"]["rust"]["officialRelease"] = "https://evil.example/latest"
        self.assertTrue(any("rust: no trusted official release evidence" in x for x in self.inspect()))

    def test_stale_baseline_fails_closed(self) -> None:
        self.assertTrue(any("evidence is stale" in x for x in self.inspect("2026-10-20")))

    def test_unverified_exception_never_authorizes_old_version(self) -> None:
        self.put("x/.python-version", "3.12.13")
        self.baseline["exceptions"] = [{
            "path": "x/.python-version", "language": "python",
            "currentVersion": "3.12.13", "targetVersion": "3.15.0",
            "humanDecisionRef": "human-decision:claimed", "approvedBy": "some-human",
            "approvalPr": "https://github.com/ordivon-org/ordivon/pull/123",
            "approvedOn": "2026-10-15", "expiresOn": "2026-10-22",
            "reproduction": "python -m pytest", "failureEvidence": "job-xyz",
            "exitCriteria": "fix incompatibility"
        }]
        issues = self.inspect()
        self.assertTrue(any("UNAPPROVED EXCEPTION" in x for x in issues))
        self.assertTrue(any("3.12.13 is not latest" in x for x in issues))

    def test_shell_non_bash_shebang_is_rejected(self) -> None:
        self.put("tools/deploy.sh", "#!/bin/sh\nset -e\n")
        self.assertTrue(any("interpreter requires separate mapping" in x for x in self.inspect()))

    def test_extensionless_shell_with_syntax_error_is_rejected(self) -> None:
        self.put("scripts/run-transaction", "#!/usr/bin/env bash\nif (( 1 )); then\n")
        self.assertTrue(any("bash -n syntax failed" in x for x in self.inspect()))

        self.put("game/player.gd", "extends Node\n")
        self.assertTrue(any("GDScript code" in x for x in self.inspect()))


if __name__ == "__main__":
    unittest.main()
