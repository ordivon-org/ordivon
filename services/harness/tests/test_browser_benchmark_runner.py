from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import browser_benchmark_contract as B  # noqa: E402
import browser_benchmark_runner as X  # noqa: E402
import browser_capability_router as R  # noqa: E402


def ready() -> dict:
    return {"ready": True, "standing": "READY"}


class BrowserBenchmarkRunnerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.policy = R.load_policy()
        self.suite = B.load_suite(policy=self.policy)

    def test_blocked_exact_route_emits_no_runtime_proposal(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            result = X.prepare_case(
                "generic-navigate-click-jev",
                "run:block:1",
                state_root=Path(d),
                policy=self.policy,
                suite=self.suite,
                readiness_overrides={
                    "jev-fast-windows-v1": {
                        "ready": False,
                        "standing": "CREDENTIAL_MISSING",
                        "missingEnvironment": ["TYPESAFE_API_KEY"],
                    },
                    "browser-use-browserless-v1": ready(),
                },
            )
        self.assertEqual(result["standing"], "PREEXEC_BLOCKED")
        self.assertIsNone(result["executionProposal"])
        self.assertFalse(result["effectsExecuted"])
        self.assertEqual(result["preflightReceipt"]["routeId"], "jev-fast-windows-v1")

    def test_browser_use_ready_builds_local_linux_proposal(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            result = X.prepare_case(
                "generic-navigate-click-browser-use",
                "run:bu:1",
                state_root=Path(d),
                policy=self.policy,
                suite=self.suite,
                readiness_overrides={"browser-use-browserless-v1": ready()},
            )
            proposal = result["executionProposal"]
            self.assertEqual(result["standing"], "READY_FOR_RUNTIME")
            self.assertEqual(proposal["executionTarget"], "local_linux")
            self.assertEqual(proposal["runId"], "run:bu:1")
            self.assertTrue(proposal["routeRunRequestDigest"].startswith("sha256:"))
            self.assertEqual(proposal["executable"], "/usr/bin/python3")
            self.assertEqual(proposal["requiredSecretEnvironment"], [])
            self.assertIn("browser_benchmark_route_adapter.py", proposal["args"][0])
            request_file = Path(proposal["args"][-1])
            self.assertTrue(request_file.is_file())
            self.assertEqual(proposal["requestFileDigest"], X._sha256_file(request_file))

    def test_jev_ready_builds_windows_native_unc_proposal_without_secret_values(self) -> None:
        status = {
            "healthy": True,
            "python": {
                "path": "/mnt/c/Users/test/AppData/Local/Ordivon/External/python/python.exe"
            },
            "chrome": {
                "path": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                "profileWindows": r"C:\Users\test\AppData\Local\Ordivon\Chrome-CDP\jev",
                "cdpPort": 9338,
            },
        }
        with tempfile.TemporaryDirectory() as d:
            result = X.prepare_case(
                "generic-navigate-click-jev",
                "run:jev:proposal",
                state_root=Path(d),
                policy=self.policy,
                suite=self.suite,
                readiness_overrides={"jev-fast-windows-v1": ready()},
                jev_status_fn=lambda: status,
                windows_path_fn=lambda p: "\\wsl.localhost\archlinux" + str(p).replace("/", "\\"),
            )
        proposal = result["executionProposal"]
        self.assertEqual(proposal["executionTarget"], "windows_native")
        self.assertEqual(proposal["runId"], "run:jev:proposal")
        self.assertTrue(proposal["routeRunRequestDigest"].startswith("sha256:"))
        self.assertEqual(proposal["windowsAuthority"], "limited")
        self.assertEqual(
            proposal["requiredSecretEnvironment"],
            ["TYPESAFE_API_KEY"],
        )
        self.assertNotIn("TYPESAFE_API_KEY", proposal["env"])
        self.assertEqual(proposal["env"]["PYTHONUTF8"], "1")
        self.assertTrue(proposal["args"][0].startswith("\\wsl.localhost\archlinux"))
        self.assertTrue(proposal["args"][-1].startswith("\\wsl.localhost\archlinux"))

    def test_proposal_digest_binds_execution_target_and_exact_files(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            result = X.prepare_case(
                "generic-navigate-click-browser-use",
                "run:stable:1",
                state_root=Path(d),
                policy=self.policy,
                suite=self.suite,
                readiness_overrides={"browser-use-browserless-v1": ready()},
            )
        proposal = dict(result["executionProposal"])
        digest = proposal.pop("proposalDigest")
        self.assertEqual(digest, R.canonical_digest(proposal))


if __name__ == "__main__":
    unittest.main()
