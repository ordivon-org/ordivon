import unittest

from ordivon_capital.market.portfolio import build_research_gated_validation_portfolio


class ResearchGatedPortfolioTests(unittest.TestCase):
    def setUp(self):
        self.ips = {
            "construction_method": "equal_weight_validation",
            "allow_short": False,
            "allowed_instruments": ["A", "B"],
            "min_cash_weight": 0.0,
            "max_gross_exposure": 1.0,
            "max_position_weight": 0.60,
            "base_currency": "USD",
            "objective": "test",
        }
        self.reference = {
            "source": "GLEIF API",
            "retrieved_at": "2026-09-12T00:00:00+00:00",
            "entities": [
                {"symbol": "A", "lei": "A" * 20},
                {"symbol": "B", "lei": "B" * 20},
            ],
        }

    def test_research_evidence_is_required_for_every_symbol(self):
        research = {"source": "SEC Company Facts API", "features": [{"symbol": "A", "fiscal_year": 2026}]}
        with self.assertRaises(ValueError):
            build_research_gated_validation_portfolio(self.ips, self.reference, research)

    def test_duplicate_research_symbol_fails(self):
        research = {"source": "SEC Company Facts API", "features": [
            {"symbol": "A", "fiscal_year": 2026},
            {"symbol": "A", "fiscal_year": 2026},
            {"symbol": "B", "fiscal_year": 2026},
        ]}
        with self.assertRaises(ValueError):
            build_research_gated_validation_portfolio(self.ips, self.reference, research)

    def test_valid_research_artifact_gates_equal_weight_portfolio(self):
        research = {"source": "SEC Company Facts API", "features": [
            {"symbol": "A", "fiscal_year": 2025},
            {"symbol": "B", "fiscal_year": 2026},
        ]}
        out = build_research_gated_validation_portfolio(self.ips, self.reference, research)
        self.assertEqual(out["method"], "equal_weight_validation_research_gated")
        self.assertEqual(out["inputs"]["research_source"], "SEC Company Facts API")
        self.assertEqual(out["inputs"]["research_fiscal_years"], {"A": 2025, "B": 2026})
        self.assertTrue(all(p["target_weight"] == 0.5 for p in out["positions"]))


if __name__ == "__main__":
    unittest.main()
