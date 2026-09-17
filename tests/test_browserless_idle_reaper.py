import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import browserless_idle_reaper as reaper
from agent_automation_browserless import (
    BrowserlessAutomationConfig,
    BrowserlessAutomationService,
    BrowserlessCarrierBusy,
    _carrier_last_use_path,
)


def config(root: Path):
    return {
        "schemaVersion": 1,
        "stateRoot": str(root / "state"),
        "playwrightPython": "/usr/bin/python3",
        "browserlessSubmitScript": "/tmp/submit.py",
        "browserlessReconcileScript": "/tmp/reconcile.py",
        "browserlessTurnScript": "/tmp/turn.py",
        "browserlessPreflightScript": "/tmp/preflight.py",
        "browserlessHumanResumeScript": "/tmp/resume.py",
        "browserlessSessionTimeoutMs": 480000,
        "browserlessHumanHandoffMs": 60000,
        "waitStableSeconds": 150,
        "browserlessIdleTtlSeconds": 900,
        "browserlessWarmEndpointIds": ["carrier-11"],
        "browserSubstrate": {
            "schemaVersion": 1,
            "kind": "browserless",
            "endpoints": [
                {
                    "id": "carrier-11",
                    "websocketEndpoint": "ws://127.0.0.1:3011/chromium",
                    "httpEndpoint": "http://127.0.0.1:3011",
                    "tokenFile": str(root / "token"),
                    "networkNamespace": "n",
                    "userDataDir": "/data",
                    "headless": False,
                    "serviceUnit": "ordivon-browserless@11.service",
                },
                {
                    "id": "carrier-12",
                    "websocketEndpoint": "ws://127.0.0.1:3012/chromium",
                    "httpEndpoint": "http://127.0.0.1:3012",
                    "tokenFile": str(root / "token"),
                    "networkNamespace": "n",
                    "userDataDir": "/data",
                    "headless": False,
                    "serviceUnit": "ordivon-browserless@12.service",
                },
            ],
        },
    }


class BrowserlessIdleReaperTests(unittest.TestCase):
    def service(self, root: Path):
        (root / "token").write_text("x" * 32)
        return BrowserlessAutomationService(BrowserlessAutomationConfig.from_dict(config(root)))

    def stale_stamp(self, service, endpoint_id, now=10_000.0):
        path = _carrier_last_use_path(service.config, endpoint_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch()
        os.utime(path, (now - 1000, now - 1000))
        return path

    def test_warm_floor_is_never_reaped(self):
        with tempfile.TemporaryDirectory() as d:
            svc = self.service(Path(d))
            with mock.patch.object(reaper, "_active", return_value=True), mock.patch.object(reaper, "_stop") as stop:
                value = reaper.reap_once(svc, now=10_000.0)
            self.assertEqual(value["carriers"][0]["standing"], "SKIP_WARM_FLOOR")
            stop.assert_not_called()

    def test_missing_stamp_starts_grace_instead_of_stopping(self):
        with tempfile.TemporaryDirectory() as d:
            svc = self.service(Path(d))
            with mock.patch.object(reaper, "_active", return_value=True), mock.patch.object(reaper, "_stop") as stop:
                value = reaper.reap_once(svc, now=10_000.0)
            row = next(r for r in value["carriers"] if r["endpointId"] == "carrier-12")
            self.assertEqual(row["standing"], "SKIP_GRACE_STARTED")
            stop.assert_not_called()

    def test_stale_carrier_with_session_is_kept(self):
        with tempfile.TemporaryDirectory() as d:
            svc = self.service(Path(d))
            self.stale_stamp(svc, "carrier-12")
            ep = next(e for e in svc.config.browserless_pool.endpoints if e.endpoint_id == "carrier-12")
            with mock.patch.object(reaper, "_active", return_value=True), mock.patch("browserless_substrate.BrowserlessEndpoint.sessions", return_value=[{"id": "s"}]), mock.patch.object(reaper, "_stop") as stop:
                value = reaper.reap_once(svc, now=10_000.0)
            row = next(r for r in value["carriers"] if r["endpointId"] == "carrier-12")
            self.assertEqual(row["standing"], "SKIP_ACTIVE_SESSION")
            stop.assert_not_called()

    def test_stale_idle_carrier_is_stopped(self):
        with tempfile.TemporaryDirectory() as d:
            svc = self.service(Path(d))
            self.stale_stamp(svc, "carrier-12")
            ep = next(e for e in svc.config.browserless_pool.endpoints if e.endpoint_id == "carrier-12")
            stopped = mock.Mock(returncode=0, stdout="", stderr="")
            def active(unit):
                return unit == "ordivon-browserless@12.service"
            with mock.patch.object(reaper, "_active", side_effect=active), mock.patch("browserless_substrate.BrowserlessEndpoint.sessions", return_value=[]), mock.patch.object(reaper, "_stop", return_value=stopped) as stop:
                value = reaper.reap_once(svc, now=10_000.0)
            row = next(r for r in value["carriers"] if r["endpointId"] == "carrier-12")
            self.assertEqual(row["standing"], "REAPED")
            stop.assert_called_once_with("ordivon-browserless@12.service")

    def test_recent_use_is_kept_without_session_probe(self):
        with tempfile.TemporaryDirectory() as d:
            svc = self.service(Path(d))
            path = _carrier_last_use_path(svc.config, "carrier-12")
            path.parent.mkdir(parents=True, exist_ok=True)
            path.touch()
            os.utime(path, (9_500.0, 9_500.0))
            with mock.patch.object(reaper, "_active", return_value=True), mock.patch(
                "browserless_substrate.BrowserlessEndpoint.sessions"
            ) as sessions, mock.patch.object(reaper, "_stop") as stop:
                value = reaper.reap_once(svc, now=10_000.0)
            row = next(r for r in value["carriers"] if r["endpointId"] == "carrier-12")
            self.assertEqual(row["standing"], "SKIP_RECENT_USE")
            sessions.assert_not_called()
            stop.assert_not_called()

    def test_human_transport_keeps_stale_idle_carrier(self):
        with tempfile.TemporaryDirectory() as d:
            svc = self.service(Path(d))
            self.stale_stamp(svc, "carrier-12")
            with mock.patch.object(reaper, "_active", return_value=True), mock.patch(
                "browserless_substrate.BrowserlessEndpoint.sessions", return_value=[]
            ), mock.patch.object(reaper, "_human_transport_active", return_value=True), mock.patch.object(
                reaper, "_stop"
            ) as stop:
                value = reaper.reap_once(svc, now=10_000.0)
            row = next(r for r in value["carriers"] if r["endpointId"] == "carrier-12")
            self.assertEqual(row["standing"], "SKIP_HUMAN_HANDOFF")
            stop.assert_not_called()

    def test_session_observation_failure_fails_safe(self):
        with tempfile.TemporaryDirectory() as d:
            svc = self.service(Path(d))
            self.stale_stamp(svc, "carrier-12")
            ep = next(e for e in svc.config.browserless_pool.endpoints if e.endpoint_id == "carrier-12")
            with mock.patch.object(reaper, "_active", return_value=True), mock.patch("browserless_substrate.BrowserlessEndpoint.sessions", side_effect=RuntimeError("x")), mock.patch.object(reaper, "_stop") as stop:
                value = reaper.reap_once(svc, now=10_000.0)
            row = next(r for r in value["carriers"] if r["endpointId"] == "carrier-12")
            self.assertEqual(row["standing"], "SKIP_SESSION_OBSERVATION_FAILED")
            stop.assert_not_called()

    def test_busy_carrier_is_kept(self):
        with tempfile.TemporaryDirectory() as d:
            svc = self.service(Path(d))
            self.stale_stamp(svc, "carrier-12")
            busy = mock.MagicMock()
            busy.__enter__.side_effect = BrowserlessCarrierBusy("busy")
            with mock.patch.object(reaper, "_active", return_value=True), mock.patch.object(reaper, "_carrier_lease", return_value=busy), mock.patch.object(reaper, "_stop") as stop:
                value = reaper.reap_once(svc, now=10_000.0)
            row = next(r for r in value["carriers"] if r["endpointId"] == "carrier-12")
            self.assertEqual(row["standing"], "SKIP_LEASE_BUSY")
            stop.assert_not_called()


if __name__ == "__main__":
    unittest.main()
