from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest import mock

from scripts import browser_use_windows_cdp as W


class BrowserUseWindowsCdpTests(unittest.TestCase):
    def test_no_debug_listener_is_human_gate_not_auto_mutation(self):
        with (
            mock.patch.object(W, "_windows_probe", return_value={
                "probeStanding":"OBSERVED","chromeRunning":True,
                "chromeVersion":"154.0.8037.58","listeners":[]
            }),
        ):
            value=W.discover_windows_chrome_cdp()
        self.assertFalse(value["ready"])
        self.assertEqual(value["standing"], "HUMAN_REMOTE_DEBUGGING_REQUIRED")

    def test_chrome_owned_devtools_listener_becomes_ready(self):
        with (
            mock.patch.object(W, "_windows_probe", return_value={
                "probeStanding":"OBSERVED","chromeRunning":True,
                "chromeVersion":"154.0.8037.58",
                "listeners":[{"LocalPort": 34567, "OwningProcess": 1234}],
            }),
            mock.patch.object(W, "_devtools_version", return_value={
                "port":34567,"httpEndpoint":"http://127.0.0.1:34567",
                "browser":"Chrome/154.0.8037.58","protocolVersion":"1.3",
            }),
        ):
            value=W.discover_windows_chrome_cdp()
        self.assertTrue(value["ready"])
        self.assertEqual(value["standing"], "READY")
        self.assertEqual(value["cdpHttpEndpoint"], "http://127.0.0.1:34567")

    def test_systemd_owns_daemon_and_chrome_is_not_launched(self):
        with (
            mock.patch.object(W, "_daemon_ready", side_effect=[False, True]),
            mock.patch.object(W, "discover_windows_chrome_cdp", return_value={
                "ready":True,"standing":"READY",
                "cdpHttpEndpoint":"http://127.0.0.1:34567",
            }),
            mock.patch.object(W, "BROWSER_USE_PYTHON", W.Path("/usr/bin/python3")),
            mock.patch.object(W.subprocess, "run", return_value=SimpleNamespace(
                returncode=0, stdout="", stderr=""
            )) as run,
        ):
            value=W.ensure_daemon("task:windows-cdp")
        self.assertEqual(value["standing"], "STARTED")
        argv=run.call_args.args[0]
        self.assertEqual(argv[0], "/usr/bin/systemd-run")
        self.assertIn("--collect", argv)
        self.assertIn("--setenv", argv)
        self.assertTrue(any(x=="BU_CDP_URL=http://127.0.0.1:34567" for x in argv))
        self.assertFalse(any("chrome.exe" in x.lower() for x in argv))

    def test_close_stops_only_browser_use_owner_not_chrome(self):
        calls=[]
        def fake_run(argv, **kwargs):
            calls.append(list(argv))
            return SimpleNamespace(returncode=0,stdout="",stderr="")
        with mock.patch.object(W.subprocess,"run",side_effect=fake_run):
            value=W.close("task:windows-cdp")
        self.assertEqual(value["standing"],"CLOSED")
        self.assertFalse(value["chromeStopped"])
        self.assertFalse(any(any("chrome.exe" in x.lower() for x in argv) for argv in calls))


if __name__ == "__main__":
    unittest.main()
