#!/usr/bin/env python3
from pathlib import Path
import itertools
from unittest.mock import Mock
import unittest

from scripts.playwright_browserless_conversation_output import (
    observe_output,
    select_exact_turn_output,
    recommendation,
)

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

    def test_exact_turn_positive_and_nonmatching_or_duplicate_prompts(self):
        cases = [
            ([("user", "request A"), ("assistant", "answer A")], "CAPTURED", "answer A"),
            (
                [("user", "request B"), ("assistant", "answer B")],
                "EXPECTED_USER_TURN_NOT_VISIBLE",
                None,
            ),
            ([("assistant", "request A")], "EXPECTED_USER_TURN_NOT_VISIBLE", None),
            (
                [("user", "request A"), ("user", "request B"), ("assistant", "answer B")],
                "ASSISTANT_OUTPUT_NOT_VISIBLE",
                None,
            ),
            (
                [
                    ("user", "request A"),
                    ("assistant", "one"),
                    ("user", "request A"),
                    ("assistant", "two"),
                ],
                "EXPECTED_USER_TURN_AMBIGUOUS",
                None,
            ),
            (
                [("user", "request A"), ("assistant", "one"), ("assistant", "two")],
                "ASSISTANT_OUTPUT_AMBIGUOUS",
                None,
            ),
            (
                [
                    ("user", "request A"),
                    ("assistant", ""),
                    ("user", "request B"),
                    ("assistant", "answer B"),
                ],
                "ASSISTANT_OUTPUT_NOT_VISIBLE",
                None,
            ),
        ]
        for messages, expected_standing, expected_output in cases:
            with self.subTest(messages=messages):
                standing, _, output = select_exact_turn_output(messages, "request A")
                self.assertEqual((standing, output), (expected_standing, expected_output))

    def test_bounded_output_refinement(self):
        # Exhaustive finite oracle over ordered role/text traces. An output
        # is allowed iff there is a unique exact user and one nonempty adjacent
        # assistant before the next user; every other trace must withhold it.
        alphabet = [
            ("user", "request"),
            ("user", "other"),
            ("assistant", "A"),
            ("assistant", "B"),
            ("assistant", ""),
            ("tool", "result"),
        ]
        checked = 0
        for size in range(6):
            for trace in itertools.product(alphabet, repeat=size):
                checked += 1
                exact = [i for i, node in enumerate(trace) if node == ("user", "request")]
                expected = None
                if len(exact) == 1:
                    i = exact[0] + 1
                    end = next(
                        (j for j in range(i, len(trace)) if trace[j][0] == "user"), len(trace)
                    )
                    assistants = [text for role, text in trace[i:end] if role == "assistant"]
                    if i < end and trace[i][0] == "assistant" and len(assistants) == 1:
                        expected = assistants[0] or None
                standing, _, output = select_exact_turn_output(list(trace), "request")
                self.assertEqual(output, expected)
                self.assertEqual(standing == "CAPTURED", expected is not None)
        self.assertEqual(checked, 9331)

    def test_nonqualified_observations_do_not_release_assistant_bytes(self):
        resource = "https://chatgpt.com/c/12345678-1234-1234-1234-123456789abc"
        cases = [
            ("CAPTURED", False, None, resource),
            ("ASSISTANT_GENERATING", True, None, resource),
            ("CONVERSATION_FETCH_FAILED", False, "failure", resource),
            ("TARGET_RESOURCE_DRIFTED", False, None, "about:blank"),
        ]
        for expected, generating, fetch_error, after in cases:
            with self.subTest(expected=expected):
                page = Mock()
                page.url = after
                page.evaluate.return_value = {
                    "url": resource,
                    "messages": [
                        {"role": "user", "text": "request", "visible": True},
                        {"role": "assistant", "text": "answer", "visible": True},
                    ],
                    "generating": generating,
                    "fetchError": fetch_error,
                    "challenge": False,
                }
                result = observe_output(page, resource, "request", None)
                self.assertEqual(result["standing"], expected)
                self.assertEqual(result["assistantOutputRead"], expected == "CAPTURED")
                if expected != "CAPTURED":
                    for key in (
                        "assistantOutput",
                        "assistantOutputDigest",
                        "recommendation",
                        "captureMethod",
                    ):
                        self.assertIsNone(result[key])
                self.assertEqual(page.method_calls[0][0], "evaluate")
                self.assertEqual(len(page.method_calls), 1)

    def test_reader_uses_expected_dom_identity_without_selecting_old_same_prompt(self):
        resource = "https://chatgpt.com/c/12345678-1234-1234-1234-123456789abc"
        page = Mock()
        page.url = resource
        page.evaluate.return_value = {
            "url": resource,
            "messages": [
                {"role": "user", "text": "request", "visible": True, "messageId": "old-user"},
                {"role": "assistant", "text": "old result", "visible": True, "messageId": "old-answer"},
                {"role": "user", "text": "request", "visible": True, "messageId": "new-user"},
                {"role": "assistant", "text": "new result", "visible": True, "messageId": "new-answer"},
            ],
            "generating": False,
            "fetchError": None,
            "challenge": False,
        }
        unanchored = observe_output(page, resource, "request", None)
        self.assertIsNone(unanchored["assistantOutput"])
        anchored = observe_output(
            page, resource, "request", None, expected_dom_user_message_id="new-user",
        )
        self.assertEqual(anchored["assistantOutput"], "new result")
        self.assertEqual(anchored["evidenceScope"], "OBSERVED_DOM_MESSAGE_ID_MATCH")
        self.assertEqual(anchored["observedDomUserMessageId"], "new-user")

    def test_output_capture_only_classifies_terminal_recommendation(self):
        self.assertEqual(recommendation("review\nACCEPTABLE_TO_SUBMIT"), "ACCEPTABLE_TO_SUBMIT")
        self.assertIsNone(recommendation("ACCEPTABLE_TO_SUBMIT\nadditional discussion"))


if __name__ == "__main__":
    unittest.main()
