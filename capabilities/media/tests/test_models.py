from __future__ import annotations

import unittest

from ordivon_studio.models import validate_repository


class ModelTests(unittest.TestCase):
    def test_repository_models_are_valid(self) -> None:
        self.assertEqual(validate_repository(), [])


if __name__ == "__main__":
    unittest.main()
