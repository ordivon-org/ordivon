"""Exercise the Media consumer of the existing Workstation binding protocol."""
from __future__ import annotations

import hashlib
import json
import os
import shlex
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from ordivon_studio.equipment import compile_operation, discover_equipment, propose_operation

ROOT = Path(__file__).resolve().parents[1]
OWNER = ROOT.parents[1] / "platform/workstation/workstation/equipment_binding.py"
EQUIPMENT = "game-aseprite-e1"


def digest(path):
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


class EquipmentBindingAdmissionTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.executable = self.root / "fixture-tool"
        self.executable.write_text("#!/bin/sh\necho 'Fixture 1.0'\n")
        self.executable.chmod(0o700)
        self.binding = self.root / "equipment-binding"
        self.world = {"equipment": [{
            "id": "aseprite", "family": "sprite", "capabilities": ["sprite.runtime.export"],
            "discovery": [{"kind": "workstation-managed-binding", "platform": "linux",
                           "equipmentId": EQUIPMENT, "versionArgs": ["--version"]}],
        }]}
        self.parameters = {"source": "fixture.aseprite", "output": "fixture.png"}
        self.environment = patch.dict(os.environ, {"ORDIVON_EQUIPMENT_BINDING": str(self.binding)})
        self.environment.start()
        self.addCleanup(self.environment.stop)

    def fixture(self):
        return {
            "schemaVersion": 1, "kind": "ordivon.workstation-equipment-binding",
            "equipmentId": EQUIPMENT, "state": "AVAILABLE", "executionTarget": "local_linux",
            "provider": "workstation.v2.managed-external", "providerIdentity": {},
            "executable": str(self.executable), "executableDigest": digest(self.executable),
            "bindingDigest": "sha256:" + "a" * 64, "validUntilMs": None, "environment": {},
        }

    def write_fixture(self, value, status=0, *, raw=None):
        payload = json.dumps(value) if raw is None else raw
        self.binding.write_text("#!/usr/bin/env python3\nprint(" + repr(payload) + ")\nraise SystemExit(" + str(status) + ")\n")
        self.binding.chmod(0o700)

    def assert_unknown(self):
        row = discover_equipment(self.world)["equipment"][0]
        self.assertIsNone(row["present"])
        self.assertEqual(row["candidates"], [])
        proposal = propose_operation(self.world, "sprite.runtime.export", self.parameters)
        self.assertFalse(proposal["ready"])
        self.assertEqual(proposal["candidate"]["readiness"], "UNKNOWN")
        self.assertIsNone(proposal["plan"])
        with self.assertRaises(FileNotFoundError):
            compile_operation("aseprite", "sprite.runtime.export", self.parameters)

    def test_real_process_wrong_identity_and_representation_matrix(self):
        valid = self.fixture()
        for field, invalid in (
            ("equipmentId", "unrelated-equipment"), ("executableDigest", "sha256:" + "0" * 64),
            ("schemaVersion", True), ("executionTarget", "local_windows"), ("state", "UNKNOWN"),
            ("validUntilMs", 1), ("validUntilMs", True), ("bindingDigest", "not-a-digest"),
            ("providerIdentity", []), ("provider", ""), ("executable", "relative-tool"),
        ):
            with self.subTest(field=field, invalid=invalid):
                self.write_fixture({**valid, field: invalid})
                self.assert_unknown()
        self.write_fixture(valid, status=17)
        self.assert_unknown()
        self.write_fixture(valid, raw=json.dumps(valid).replace("{", '{"equipmentId":"other",', 1))
        self.assert_unknown()
        self.executable.chmod(0o600)
        self.write_fixture(valid)
        self.assert_unknown()

    def test_actual_owner_native_compatibility_and_failed_version(self):
        # Use the real Workstation CLI against a disposable synthetic catalog.
        catalog = self.root / "equipment.toml"
        def write_catalog():
            catalog.write_text(
                f'[managed_equipment.{EQUIPMENT}]\nexecutable = {json.dumps(str(self.executable))}\n'
                f'sha256 = "{digest(self.executable).removeprefix("sha256:")}"\n'
                'execution_target = "local_linux"\n'
            )
        write_catalog()
        command = shlex.join([sys.executable, str(OWNER), "--contract", str(catalog)])
        self.binding.write_text(f'#!/bin/sh\nexec {command} "$@"\n')
        self.binding.chmod(0o700)
        row = discover_equipment(self.world)["equipment"][0]
        self.assertTrue(row["present"])
        self.assertEqual(row["candidates"][0]["executableDigest"], digest(self.executable))
        self.assertEqual(row["candidates"][0]["version"], "Fixture 1.0")
        self.assertEqual(row["candidates"][0]["versionStanding"], "observed")
        self.assertEqual(compile_operation("aseprite", "sprite.runtime.export", self.parameters).executable,
                         str(self.executable))
        # The exact file can be present without a successful version observation.
        self.executable.write_text("#!/bin/sh\necho 'forged version 99'\nexit 17\n")
        write_catalog()
        row = discover_equipment(self.world)["equipment"][0]
        self.assertTrue(row["present"])
        self.assertIsNone(row["candidates"][0]["version"])
        self.assertEqual(row["candidates"][0]["versionStanding"], "unobserved")

    def test_returned_executable_digest_detects_post_binding_drift(self):
        self.write_fixture(self.fixture())
        self.executable.write_text("#!/bin/sh\necho 'changed bytes'\n")
        self.assert_unknown()
