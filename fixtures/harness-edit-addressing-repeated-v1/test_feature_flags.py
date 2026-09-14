from __future__ import annotations

import unittest

from feature_flags import beta_enabled


class FeatureFlagTests(unittest.TestCase):
    def test_beta_is_enabled(self) -> None:
        self.assertTrue(beta_enabled())


if __name__ == "__main__":
    unittest.main()
