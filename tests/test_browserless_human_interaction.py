import subprocess
import unittest
from unittest import mock

import scripts.browserless_human_interaction as interaction


class BrowserlessHumanInteractionTests(unittest.TestCase):
    def test_http_ready_observes_host_loopback_from_host_network_namespace(self):
        completed = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="200", stderr=""
        )
        with mock.patch(
            "scripts.browserless_human_interaction.subprocess.run",
            return_value=completed,
        ) as run:
            self.assertTrue(interaction._http_ready(13, timeout=1.25))

        run.assert_called_once()
        command = run.call_args.args[0]
        self.assertEqual(
            command[:4],
            ["/usr/bin/nsenter", "--net=/proc/1/ns/net", "/usr/bin/curl", "--silent"],
        )
        self.assertIn("http://127.0.0.1:16013/vnc.html", command)
        self.assertIn("1.25", command)

    def test_http_ready_fails_closed_when_host_loopback_probe_fails(self):
        completed = subprocess.CompletedProcess(
            args=[], returncode=7, stdout="000", stderr="connect failed"
        )
        with mock.patch(
            "scripts.browserless_human_interaction.subprocess.run",
            return_value=completed,
        ):
            self.assertFalse(interaction._http_ready(11, timeout=0.5))


if __name__ == "__main__":
    unittest.main()
