#!/usr/bin/env python3
from pathlib import Path
import ast
import unittest

ROOT = Path(__file__).resolve().parents[1]


class BrowserlessConversationOutputContractTests(unittest.TestCase):
    def test_turn_completion_requires_post_send_target_continuity(self):
        text = (ROOT / "scripts" / "playwright_browserless_turn_once.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("observe_post_send_route(", text)
        self.assertIn("POST_SEND_ROUTE_STABILIZE_MS = 15_000", text)
        self.assertIn("_temporary_web_route(current_url)", text)
        self.assertIn("hydration_deadline = time.monotonic() + 20.0", text)
        self.assertIn("conversation history did not hydrate before timeout", text)
        self.assertIn("conversation fetch failed before effect claim", text)
        self.assertIn("len(main_text_before_send) >= 32", text)
        self.assertIn('"targetStillBoundAfterSend": current_resource == target_resource', text)
        self.assertIn("composer_cleared and generation_started and target_still_bound", text)

    def test_output_capture_is_read_only_and_exact_turn_scoped(self):
        text = (ROOT / "scripts" / "playwright_browserless_conversation_output.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("expected-user-prompt-file", text)
        self.assertIn('role == "user" and text == expected_prompt', text)
        self.assertIn('"providerEffectAttempted": False', text)
        self.assertIn('"composerFilled": False', text)
        self.assertIn('"sendAttempted": False', text)
        self.assertIn("target_still_bound = observed_resource_after_wait == target_resource", text)
        self.assertIn('standing = "TARGET_RESOURCE_DRIFTED"', text)
        self.assertIn('standing = "CONVERSATION_FETCH_FAILED"', text)
        tree = ast.parse(text)
        call = next(
            node for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "body_anchored_output"
            and len(node.args) == 2
        )
        self.assertEqual([arg.id for arg in call.args if isinstance(arg, ast.Name)], ["body_text", "expected_prompt"])
        self.assertIn('"captureMethod": capture_method', text)
        self.assertNotIn("send.click(", text)
        self.assertNotIn("composer.fill(", text)

    def test_output_capture_only_classifies_terminal_recommendation(self):
        text = (ROOT / "scripts" / "playwright_browserless_conversation_output.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("stripped.endswith(label)", text)
        self.assertIn("return matches[0] if len(matches) == 1 else None", text)


if __name__ == "__main__":
    unittest.main()
