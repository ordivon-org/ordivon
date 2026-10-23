from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "scripts/resource_workload_profile.py"
SPEC = importlib.util.spec_from_file_location("resource_workload_profile", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def receipt(*, cpu: int, memory: int, read: int, write: int, swap: int | None = None) -> dict[str, object]:
    memory_payload: dict[str, object] = {
        "peakBytes": memory,
        "events": {"low": 0, "high": 0, "max": 0, "oom": 0, "oomKill": 0},
    }
    if swap is not None:
        memory_payload["swapPeakBytes"] = swap
    return {
        "schemaVersion": 1,
        "taskId": "attempt-1",
        "jobId": "job-1",
        "attemptId": "attempt-1",
        "launchTokenDigest": "sha256:" + "0" * 64,
        "observedUnixMs": 1,
        "scope": "attempt_cgroup_including_runner",
        "provider": "linux_cgroup_v2",
        "cpu": {"usageUsec": cpu, "userUsec": cpu, "systemUsec": 0},
        "memory": memory_payload,
        "io": {
            "readBytes": read,
            "writeBytes": write,
            "readOps": 1,
            "writeOps": 1,
            "discardBytes": 0,
            "discardOps": 0,
        },
    }


def write_receipt(path: Path, payload: dict[str, object]) -> None:
    path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")


class ResourceWorkloadProfileTests(unittest.TestCase):
    def test_profile_reports_nearest_rank_percentiles_and_external_coverage(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            paths = []
            for index, value in enumerate([10, 20, 30, 40, 50], start=1):
                path = root / f"{index}.resource-receipt.json"
                write_receipt(path, receipt(cpu=value, memory=value * 100, read=value * 2, write=value * 3))
                paths.append(path)

            profile = MODULE.build_profile(paths, expected_attempts=10)

            self.assertEqual(profile["schemaVersion"], 1)
            self.assertEqual(profile["receiptCount"], 5)
            self.assertEqual(profile["coverage"]["expectedAttempts"], 10)
            self.assertEqual(profile["coverage"]["basis"], "caller_supplied_expected_attempts")
            self.assertEqual(profile["coverage"]["basisPoints"], 5000)
            self.assertEqual(profile["cpuUsageUsec"], {"p50": 30, "p95": 50, "p99": 50})
            self.assertEqual(profile["memoryPeakBytes"], {"p50": 3000, "p95": 5000, "p99": 5000})
            self.assertEqual(profile["ioTotalBytes"], {"p50": 150, "p95": 250, "p99": 250})

    def test_receipt_only_coverage_is_explicitly_not_terminal_attempt_coverage(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "resource-receipt.json"
            write_receipt(path, receipt(cpu=7, memory=11, read=13, write=17))

            profile = MODULE.build_profile([path], expected_attempts=None)

            self.assertEqual(profile["coverage"]["basis"], "receipt_files_only")
            self.assertIsNone(profile["coverage"]["expectedAttempts"])
            self.assertIsNone(profile["coverage"]["basisPoints"])

    def test_missing_optional_swap_is_reported_without_fabricating_zero(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            first = root / "a.resource-receipt.json"
            second = root / "b.resource-receipt.json"
            write_receipt(first, receipt(cpu=1, memory=2, read=3, write=4, swap=None))
            write_receipt(second, receipt(cpu=2, memory=3, read=4, write=5, swap=9))

            profile = MODULE.build_profile([first, second], expected_attempts=2)

            self.assertEqual(profile["swapPeakBytes"]["observedCount"], 1)
            self.assertEqual(profile["swapPeakBytes"]["missingCount"], 1)
            self.assertEqual(profile["swapPeakBytes"]["percentiles"], {"p50": 9, "p95": 9, "p99": 9})

    def test_directory_discovery_is_deterministic_and_ignores_unrelated_json(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            nested = root / "nested"
            nested.mkdir()
            write_receipt(nested / "b.resource-receipt.json", receipt(cpu=2, memory=2, read=2, write=2))
            write_receipt(root / "a.resource-receipt.json", receipt(cpu=1, memory=1, read=1, write=1))
            (root / "unrelated.json").write_text("{}", encoding="utf-8")

            discovered = MODULE.discover_receipts([root], max_files=10)

            self.assertEqual([path.name for path in discovered], ["a.resource-receipt.json", "b.resource-receipt.json"])

    def test_directory_discovery_fails_closed_when_bound_is_exceeded(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_receipt(root / "a.resource-receipt.json", receipt(cpu=1, memory=1, read=1, write=1))
            write_receipt(root / "b.resource-receipt.json", receipt(cpu=2, memory=2, read=2, write=2))

            with self.assertRaisesRegex(ValueError, "max-files"):
                MODULE.discover_receipts([root], max_files=1)

    def test_invalid_identity_contract_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "bad.resource-receipt.json"
            payload = receipt(cpu=1, memory=1, read=1, write=1)
            payload["provider"] = "invented"
            write_receipt(path, payload)

            with self.assertRaisesRegex(ValueError, "provider"):
                MODULE.build_profile([path], expected_attempts=1)

    def test_expected_attempts_cannot_be_below_receipt_count(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "resource-receipt.json"
            write_receipt(path, receipt(cpu=1, memory=1, read=1, write=1))

            with self.assertRaisesRegex(ValueError, "expected-attempts"):
                MODULE.build_profile([path], expected_attempts=0)


if __name__ == "__main__":
    unittest.main()
