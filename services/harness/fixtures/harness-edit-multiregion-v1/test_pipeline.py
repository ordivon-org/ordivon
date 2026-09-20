from __future__ import annotations

import unittest

from pipeline import DEFAULT_TIMEOUT_SECONDS, retry_limit


class PipelineTests(unittest.TestCase):
    def test_timeout_and_retry_policy(self) -> None:
        self.assertEqual(DEFAULT_TIMEOUT_SECONDS, 30)
        self.assertEqual(retry_limit(), 3)


if __name__ == "__main__":
    unittest.main()
