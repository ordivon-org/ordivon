import unittest

from ordivon_capital.market.portfolio import build_equal_weight_validation_portfolio


class PortfolioTests(unittest.TestCase):
    def test_equal_weight_respects_position_cap(self):
        ips = {
            "construction_method": "equal_weight_validation",
            "allow_short": False,
            "allowed_instruments": ["A", "B", "C"],
            "min_cash_weight": 0.0,
            "max_gross_exposure": 1.0,
            "max_position_weight": 0.30,
            "base_currency": "USD",
            "objective": "test",
        }
        reference = {
            "source": "GLEIF API",
            "retrieved_at": "2026-09-12T00:00:00+00:00",
            "entities": [
                {"symbol": "A", "lei": "A" * 20},
                {"symbol": "B", "lei": "B" * 20},
                {"symbol": "C", "lei": "C" * 20},
            ],
        }
        result = build_equal_weight_validation_portfolio(ips, reference)
        self.assertAlmostEqual(result["gross_exposure"], 0.90)
        self.assertAlmostEqual(result["cash_weight"], 0.10)
        self.assertTrue(all(p["target_weight"] == 0.30 for p in result["positions"]))

    def test_missing_reference_fails_closed(self):
        ips = {
            "construction_method": "equal_weight_validation",
            "allow_short": False,
            "allowed_instruments": ["A", "B"],
            "min_cash_weight": 0.0,
            "max_gross_exposure": 1.0,
            "max_position_weight": 0.60,
            "base_currency": "USD",
            "objective": "test",
        }
        reference = {
            "source": "GLEIF API",
            "retrieved_at": "2026-09-12T00:00:00+00:00",
            "entities": [{"symbol": "A", "lei": "A" * 20}],
        }
        with self.assertRaises(ValueError):
            build_equal_weight_validation_portfolio(ips, reference)


if __name__ == "__main__":
    unittest.main()
