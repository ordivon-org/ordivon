from __future__ import annotations

import unittest

from scripts.playwright_browserless_conversation_output import digest_obj as output_digest
from scripts.playwright_browserless_turn_once import digest_obj as turn_digest


class BrowserlessTurnReceiptJCSTests(unittest.TestCase):
    def test_receipt_digest_uses_rfc8785_number_and_utf16_rules(self) -> None:
        value = {"n": 1.0, "\ue000": "bmp", "😀": "astral"}
        expected = "sha256:b04125a719bf03b78db19463e385b03fe57082ee26dd8ab60ae4ee4622397a57"
        self.assertEqual(turn_digest(value), expected)
        self.assertEqual(output_digest(value), expected)


if __name__ == "__main__":
    unittest.main()
