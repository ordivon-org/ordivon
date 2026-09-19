import unittest

from ordivon_capital.market.gleif_reference import select_exact_issued


class GleifSelectionTests(unittest.TestCase):
    def test_exact_issued_match(self):
        records = [
            {
                "id": "X" * 20,
                "attributes": {
                    "entity": {"legalName": {"name": "Apple Inc."}},
                    "registration": {"status": "ISSUED"},
                },
            },
            {
                "id": "Y" * 20,
                "attributes": {
                    "entity": {"legalName": {"name": "Apple Ford, Inc."}},
                    "registration": {"status": "ISSUED"},
                },
            },
        ]
        record = select_exact_issued(records, "Apple Inc.")
        self.assertEqual(record["id"], "X" * 20)

    def test_lapsed_exact_match_rejected(self):
        records = [
            {
                "id": "X" * 20,
                "attributes": {
                    "entity": {"legalName": {"name": "Apple Inc."}},
                    "registration": {"status": "LAPSED"},
                },
            }
        ]
        with self.assertRaises(ValueError):
            select_exact_issued(records, "Apple Inc.")


if __name__ == "__main__":
    unittest.main()
