"""Native Security-owner regression for schema-first Agent/Effect Admission."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
EVALUATOR = ROOT / "contracts" / "agent-admission-v1" / "evaluate.py"
FIXTURE = ROOT / "fixtures" / "agent-admission" / "v0-allow.json"


def evaluate(payload: dict[str, object]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(EVALUATOR)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        check=False,
        timeout=20,
    )


class AgentAdmissionSchemaBoundaryTests(unittest.TestCase):
    def test_valid_grant_keeps_existing_admission_behavior(self) -> None:
        payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
        result = evaluate(payload)
        self.assertEqual(result.returncode, 0, result.stderr)
        parsed = json.loads(result.stdout)
        self.assertEqual(parsed["agent"]["outcome"], "ALLOW")
        self.assertIs(parsed["effect"]["admitted"], True)

    def test_invalid_input_never_invokes_policy_seam(self) -> None:
        spec = importlib.util.spec_from_file_location("security_admission_evaluator", EVALUATOR)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        evaluator = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(evaluator)
        payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
        del payload["grant"]["remainingEffects"]
        with mock.patch.object(
            evaluator, "_opa", side_effect=AssertionError("policy invoked on invalid input")
        ) as forbidden_policy:
            with self.assertRaisesRegex(ValueError, "violates schema"):
                evaluator.evaluate(payload)
        forbidden_policy.assert_not_called()

    def test_invalid_grant_cannot_reach_effect_admission(self) -> None:
        original = json.loads(FIXTURE.read_text(encoding="utf-8"))
        cases = (
            ("missing_expiry", lambda x: x["grant"].pop("expiresAtEpochSeconds")),
            ("missing_budget", lambda x: x["grant"].pop("remainingEffects")),
            ("string_budget", lambda x: x["grant"].__setitem__("remainingEffects", "3")),
            ("boolean_budget", lambda x: x["grant"].__setitem__("remainingEffects", True)),
            ("extra_grant_field", lambda x: x["grant"].__setitem__("unknownAuthority", True)),
            ("wrong_schema_version", lambda x: x.__setitem__("schemaVersion", 2)),
        )
        for label, change in cases:
            with self.subTest(label=label):
                payload = json.loads(json.dumps(original))
                change(payload)
                result = evaluate(payload)
                self.assertNotEqual(result.returncode, 0, result.stdout)
                error = json.loads(result.stderr)
                self.assertEqual(error["kind"], "ordivon.security.agent-admission-error")
