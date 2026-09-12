import unittest

from market_capital.sec_companyfacts import build_fundamental_feature, select_latest_annual_fact


def row(fy, end, val, accn, filed="2026-01-01", form="10-K", fp="FY"):
    return {"fy": fy, "end": end, "val": val, "accn": accn, "filed": filed, "form": form, "fp": fp}


class SecCompanyFactsTests(unittest.TestCase):
    def test_latest_annual_fact_ignores_comparatives_inside_latest_filing(self):
        facts = {
            "facts": {"us-gaap": {"X": {"units": {"USD": [
                row(2026, "2024-12-31", 10, "latest"),
                row(2026, "2025-12-31", 20, "latest"),
                row(2025, "2025-12-31", 999, "older"),
            ]}}}}
        }
        selected = select_latest_annual_fact(facts, "X")
        self.assertEqual(selected["val"], 20)
        self.assertEqual(selected["accn"], "latest")

    def test_feature_requires_same_annual_filing(self):
        facts = {
            "entityName": "TEST CORP",
            "facts": {"us-gaap": {
                "NetIncomeLoss": {"units": {"USD": [row(2026, "2025-12-31", 10, "A")] }},
                "Assets": {"units": {"USD": [row(2026, "2025-12-31", 100, "A")] }},
                "StockholdersEquity": {"units": {"USD": [row(2026, "2025-12-31", 50, "B")] }},
            }}
        }
        with self.assertRaises(ValueError):
            build_fundamental_feature("T", "0000000001", "TEST CORP", facts)

    def test_feature_calculation(self):
        facts = {
            "entityName": "TEST CORP",
            "facts": {"us-gaap": {
                "NetIncomeLoss": {"units": {"USD": [row(2026, "2025-12-31", 10, "A")] }},
                "Assets": {"units": {"USD": [row(2026, "2025-12-31", 100, "A")] }},
                "StockholdersEquity": {"units": {"USD": [row(2026, "2025-12-31", 50, "A")] }},
            }}
        }
        out = build_fundamental_feature("T", "0000000001", "TEST CORP", facts)
        self.assertAlmostEqual(out["roa_proxy"], 0.1)
        self.assertAlmostEqual(out["roe_proxy"], 0.2)
        self.assertAlmostEqual(out["equity_to_assets"], 0.5)


if __name__ == "__main__":
    unittest.main()
