from __future__ import annotations
import ast
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import playwright_browserless_chatgpt_submit as submit  # noqa: E402


class Clock:
    def __init__(self):
        self.now = 0.0

    def monotonic(self):
        return self.now


class Page:
    def __init__(self, clock):
        self.clock = clock

    def wait_for_timeout(self, ms):
        self.clock.now += ms / 1000.0


class RehydratingComposer:
    def __init__(self, clock):
        self.clock = clock
        self.fills = 0

    def inner_text(self):
        if self.fills == 0:
            return "persisted draft"
        if self.fills == 1 and self.clock.now >= 0.1:
            return "rehydrated draft"
        return ""

    def fill(self, value):
        assert value == ""
        self.fills += 1


class StuckComposer:
    def __init__(self):
        self.fills = 0

    def inner_text(self):
        return "persistent draft"

    def fill(self, value):
        self.fills += 1


class StopLocator:
    def __init__(self, page):
        self.page = page

    @property
    def first(self):
        return self

    def count(self):
        return 1

    def is_visible(self):
        return self.page.clock.now < self.page.generating_until


class RoutePage(Page):
    def __init__(self, clock, *, canonical_at=None, generating_until=0.0):
        super().__init__(clock)
        self.canonical_at = canonical_at
        self.generating_until = generating_until

    @property
    def url(self):
        if self.canonical_at is not None and self.clock.now >= self.canonical_at:
            return "https://chatgpt.com/c/6aa25f00-0000-83ea-9000-000000000001"
        return "https://chatgpt.com/c/WEB:test-provisional"

    def locator(self, selector):
        self.last_selector = selector
        return StopLocator(self)


class CleanSurfaceTests(unittest.TestCase):
    def test_playwright_is_runtime_equipment_not_module_import_dependency(self):
        text = (ROOT / "scripts/playwright_browserless_chatgpt_submit.py").read_text()
        tree = ast.parse(text)
        top_level = [node for node in tree.body if isinstance(node, (ast.Import, ast.ImportFrom))]
        self.assertFalse(
            any(
                isinstance(node, ast.ImportFrom) and node.module == "playwright.sync_api"
                for node in top_level
            )
        )
        main = next(
            node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "main"
        )
        self.assertTrue(
            any(
                isinstance(node, ast.ImportFrom) and node.module == "playwright.sync_api"
                for node in ast.walk(main)
            )
        )

    def test_stabilizer_absorbs_one_async_draft_rehydration_before_send(self):
        clock = Clock()
        page = Page(clock)
        composer = RehydratingComposer(clock)
        with mock.patch.object(submit.time, "monotonic", side_effect=clock.monotonic):
            self.assertTrue(
                submit.stabilize_empty_composer(page, composer, timeout_ms=1200, quiet_ms=300)
            )
        self.assertEqual(composer.fills, 2)

    def test_stabilizer_fails_closed_when_composer_never_becomes_empty(self):
        clock = Clock()
        page = Page(clock)
        composer = StuckComposer()
        with mock.patch.object(submit.time, "monotonic", side_effect=clock.monotonic):
            self.assertFalse(
                submit.stabilize_empty_composer(page, composer, timeout_ms=500, quiet_ms=200)
            )
        self.assertGreater(composer.fills, 1)

    def test_canonical_wait_can_outlive_old_sixty_second_window_while_generation_is_active(self):
        clock = Clock()
        page = RoutePage(clock, canonical_at=70.0, generating_until=90.0)
        with mock.patch.object(submit.time, "monotonic", side_effect=clock.monotonic):
            resource = submit.wait_for_canonical_after_send(
                page, generation_started=True, hard_timeout_seconds=150, settle_seconds=8
            )
        self.assertEqual(resource, "https://chatgpt.com/c/6aa25f00-0000-83ea-9000-000000000001")
        self.assertGreaterEqual(clock.now, 70.0)
        self.assertLess(clock.now, 71.0)

    def test_canonical_wait_releases_capacity_soon_after_generation_finishes(self):
        clock = Clock()
        page = RoutePage(clock, canonical_at=None, generating_until=3.0)
        with mock.patch.object(submit.time, "monotonic", side_effect=clock.monotonic):
            self.assertIsNone(
                submit.wait_for_canonical_after_send(
                    page, generation_started=True, hard_timeout_seconds=150, settle_seconds=2
                )
            )
        self.assertGreaterEqual(clock.now, 5.0)
        self.assertLess(clock.now, 6.0)

    def test_fresh_birth_normalizes_to_root_before_provider_gate_and_send(self):
        text = (ROOT / "scripts/playwright_browserless_chatgpt_submit.py").read_text()
        navigate = text.index("page.goto(NEW_CHAT_URL")
        gate = text.index("blocker = human_blocker(page)", navigate)
        stabilize = text.index("if not stabilize_empty_composer(page, composer):", gate)
        fill_prompt = text.index("composer.fill(prompt)", stabilize)
        click = text.index("send.click()", fill_prompt)
        self.assertLess(navigate, gate)
        self.assertLess(gate, stabilize)
        self.assertLess(stabilize, fill_prompt)
        self.assertLess(fill_prompt, click)
        self.assertIn('providerEffectAttempted": False', text)
        self.assertIn('a.human_handoff_mode == "live-url"', text)
        reconnect = text.index('cdp.send("Browserless.reconnect"')
        live_only = text.rindex('a.human_handoff_mode == "live-url"', 0, reconnect)
        self.assertLess(live_only, reconnect)


if __name__ == "__main__":
    unittest.main()
