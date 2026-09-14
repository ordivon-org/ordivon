from __future__ import annotations

import sys
import unittest
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if importlib.util.find_spec("playwright") is None:
    raise unittest.SkipTest(
        "exact Playwright runtime is not installed in the Harness owner environment"
    )
sys.path.insert(0, str(ROOT / "scripts"))

from playwright_browserless_turn_once import _temporary_web_route, observe_post_send_route  # noqa: E402


class FakePage:
    def __init__(self, urls):
        self._urls = list(urls)
        self._index = 0
        self.waits = 0

    @property
    def url(self):
        return self._urls[self._index]

    def wait_for_timeout(self, _milliseconds):
        self.waits += 1
        if self._index + 1 < len(self._urls):
            self._index += 1


class BrowserlessPostSendRouteTests(unittest.TestCase):
    def test_only_exact_chatgpt_web_route_is_transient(self):
        self.assertTrue(_temporary_web_route("https://chatgpt.com/c/WEB:abc"))
        self.assertFalse(_temporary_web_route("https://chatgpt.com/c/abc"))
        self.assertFalse(_temporary_web_route("https://example.com/c/WEB:abc"))
        self.assertFalse(_temporary_web_route("https://chatgpt.com/"))

    def test_web_route_can_stabilize_back_to_exact_target(self):
        target = "https://chatgpt.com/c/stable-target"
        page = FakePage(["https://chatgpt.com/c/WEB:temp", target])
        result = observe_post_send_route(page, target, generation_started=True, timeout_ms=1000)
        self.assertTrue(result["postSendTemporaryWebRouteObserved"])
        self.assertEqual(result["pageUrlImmediatelyAfterSend"], "https://chatgpt.com/c/WEB:temp")
        self.assertEqual(result["observedResourceAfterSend"], target)
        self.assertTrue(result["targetStillBoundAfterSend"])
        self.assertEqual(page.waits, 1)

    def test_web_route_stabilizing_to_different_conversation_fails_closed(self):
        target = "https://chatgpt.com/c/stable-target"
        other = "https://chatgpt.com/c/other-target"
        page = FakePage(["https://chatgpt.com/c/WEB:temp", other])
        result = observe_post_send_route(page, target, generation_started=True, timeout_ms=1000)
        self.assertEqual(result["observedResourceAfterSend"], other)
        self.assertFalse(result["targetStillBoundAfterSend"])
        self.assertEqual(page.waits, 1)

    def test_non_web_unparsed_route_is_not_waited_into_success(self):
        target = "https://chatgpt.com/c/stable-target"
        page = FakePage(["https://chatgpt.com/", target])
        result = observe_post_send_route(page, target, generation_started=True, timeout_ms=1000)
        self.assertFalse(result["postSendTemporaryWebRouteObserved"])
        self.assertFalse(result["targetStillBoundAfterSend"])
        self.assertEqual(page.waits, 0)


if __name__ == "__main__":
    unittest.main()
