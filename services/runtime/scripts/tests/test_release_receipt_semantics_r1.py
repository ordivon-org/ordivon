"""Read-only receipt contract tests against the existing Runtime Release owner.

Uses unittest, which is the native Runtime owner CI discovery contract.
No pytest dependency, duplicate receipt implementation or deployment side effects.
"""

from __future__ import annotations

import itertools
import json
import runpy
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "ordivon-runtime-deploy"
sys.path.insert(0, str(SCRIPT.parent))
try:
    RECEIPT_READ = runpy.run_path(str(SCRIPT))["existing_structured_release_result"]
finally:
    sys.path.remove(str(SCRIPT.parent))


def request() -> dict[str, object]:
    return {
        "contract": "release-v1",
        "effectId": "e" * 64,
        "requestDigest": "runtime-release-v1:sha256:" + "a" * 64,
    }


def make_receipt(root: Path, *, terminal: bool = True) -> Path:
    receipt = root / ("effect-" + "e" * 64)
    receipt.mkdir()
    (receipt / "effect-request.json").write_text(json.dumps(request()), encoding="utf-8")
    if terminal:
        (receipt / "result.json").write_text(
            json.dumps({"releaseEffect": request(), "status": "deployed"}),
            encoding="utf-8",
        )
    return receipt


def receipt_bytes(root: Path) -> dict[str, bytes]:
    receipt = root / ("effect-" + "e" * 64)
    return {path.name: path.read_bytes() for path in receipt.iterdir() if path.is_file()}


class ReleaseReceiptSemanticsTests(unittest.TestCase):
    def setUp(self) -> None:
        self._temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self._temporary.cleanup)
        self.root = Path(self._temporary.name)

    def test_missing_receipt_is_not_claimed_successful(self) -> None:
        self.assertIsNone(RECEIPT_READ(self.root / "absent", request()))

    def test_exact_replay_preserves_historical_receipt_bytes(self) -> None:
        receipt = make_receipt(self.root)
        before = receipt_bytes(self.root)
        self.assertEqual(
            RECEIPT_READ(receipt, request()),
            {"releaseEffect": request(), "status": "deployed", "replayed": True},
        )
        self.assertEqual(receipt_bytes(self.root), before)

    def test_same_effect_id_with_changed_intent_rejected(self) -> None:
        receipt = make_receipt(self.root)
        changed = {**request(), "requestDigest": "runtime-release-v1:sha256:" + "b" * 64}
        with self.assertRaisesRegex(RuntimeError, "different release request"):
            RECEIPT_READ(receipt, changed)

    def test_intent_without_terminal_effect_requires_reconciliation(self) -> None:
        receipt = make_receipt(self.root, terminal=False)
        with self.assertRaisesRegex(RuntimeError, "reconcile it instead of repeating apply"):
            RECEIPT_READ(receipt, request())

    def test_terminal_effect_identity_mismatch_rejected(self) -> None:
        receipt = make_receipt(self.root)
        (receipt / "result.json").write_text(
            json.dumps({"releaseEffect": {**request(), "effectId": "f" * 64}}),
            encoding="utf-8",
        )
        with self.assertRaisesRegex(RuntimeError, "does not match its effect request"):
            RECEIPT_READ(receipt, request())

    def test_scalar_terminal_effect_rejected(self) -> None:
        receipt = make_receipt(self.root)
        (receipt / "result.json").write_text("null", encoding="utf-8")
        with self.assertRaisesRegex(RuntimeError, "terminal result is invalid"):
            RECEIPT_READ(receipt, request())

    def test_symlinked_receipt_directory_rejected(self) -> None:
        receipt = make_receipt(self.root)
        link = self.root / "receipt-link"
        link.symlink_to(receipt, target_is_directory=True)
        with self.assertRaisesRegex(RuntimeError, "not a safe directory"):
            RECEIPT_READ(link, request())

    def test_symlinked_receipt_files_rejected(self) -> None:
        for name in ("effect-request.json", "result.json"):
            with self.subTest(name=name):
                with tempfile.TemporaryDirectory() as td:
                    root = Path(td)
                    receipt = make_receipt(root)
                    target = root / name
                    target.write_bytes((receipt / name).read_bytes())
                    (receipt / name).unlink()
                    (receipt / name).symlink_to(target)
                    with self.assertRaises(RuntimeError):
                        RECEIPT_READ(receipt, request())

    def test_missing_effect_request_rejected(self) -> None:
        receipt = make_receipt(self.root)
        (receipt / "effect-request.json").unlink()
        with self.assertRaisesRegex(RuntimeError, "lacks its effect request"):
            RECEIPT_READ(receipt, request())

    def test_bounded_receipt_state_machine_all_48_combinations(self) -> None:
        """2 dirs x 3 request files x 2 intents x 4 terminal forms.

        Bounded owner-source check, not a claim of physical exactly-once.
        """
        variants = itertools.product(
            ("safe", "symlink"),
            ("valid", "missing", "symlink"),
            ("same", "changed"),
            ("matching", "missing", "different", "scalar"),
        )
        visited = 0
        accepted = 0
        for directory, req_file, intent, terminal in variants:
            with self.subTest(directory=directory, request=req_file, intent=intent, terminal=terminal):
                with tempfile.TemporaryDirectory() as td:
                    root = Path(td)
                    receipt = make_receipt(root)
                    request_file = receipt / "effect-request.json"
                    terminal_file = receipt / "result.json"
                    if req_file == "missing":
                        request_file.unlink()
                    elif req_file == "symlink":
                        target = root / "request-content.json"
                        target.write_bytes(request_file.read_bytes())
                        request_file.unlink()
                        request_file.symlink_to(target)
                    if terminal == "missing":
                        terminal_file.unlink()
                    elif terminal == "different":
                        terminal_file.write_text(
                            json.dumps({"releaseEffect": {**request(), "effectId": "f" * 64}}),
                            encoding="utf-8",
                        )
                    elif terminal == "scalar":
                        terminal_file.write_text("null", encoding="utf-8")
                    if directory == "symlink":
                        link = root / "receipt-link"
                        link.symlink_to(receipt, target_is_directory=True)
                        receipt = link
                    expected = request()
                    if intent == "changed":
                        expected["requestDigest"] = "runtime-release-v1:sha256:" + "b" * 64
                    before = receipt_bytes(root)
                    valid = (directory, req_file, intent, terminal) == (
                        "safe",
                        "valid",
                        "same",
                        "matching",
                    )
                    if valid:
                        self.assertIs(RECEIPT_READ(receipt, expected)["replayed"], True)
                        accepted += 1
                    else:
                        with self.assertRaises(RuntimeError):
                            RECEIPT_READ(receipt, expected)
                    self.assertEqual(receipt_bytes(root), before)
                    visited += 1
        self.assertEqual(visited, 48)
        self.assertEqual(accepted, 1)
