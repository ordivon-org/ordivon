import unittest

import pandas as pd

from market_capital.cboe_market_structure import build_daily_market_structure


class CboeMarketStructureTests(unittest.TestCase):
    def test_aggregation_and_trf_share(self):
        raw = pd.DataFrame(
            [
                {"Day": "2026-01-02", "Market Participant": "NASDAQ (Q)", "Total Shares": 60.0, "Total Notional": 600.0, "Total Trade Count": 6},
                {"Day": "2026-01-02", "Market Participant": "FINRA / Nasdaq TRF (DQ)", "Total Shares": 40.0, "Total Notional": 400.0, "Total Trade Count": 4},
            ]
        )
        out = build_daily_market_structure(raw)
        self.assertEqual(len(out), 1)
        self.assertAlmostEqual(out.iloc[0]["total_shares"], 100.0)
        self.assertAlmostEqual(out.iloc[0]["trf_share"], 0.4)

    def test_duplicate_day_participant_fails(self):
        raw = pd.DataFrame(
            [
                {"Day": "2026-01-02", "Market Participant": "NASDAQ (Q)", "Total Shares": 10.0, "Total Notional": 100.0, "Total Trade Count": 1},
                {"Day": "2026-01-02", "Market Participant": "NASDAQ (Q)", "Total Shares": 10.0, "Total Notional": 100.0, "Total Trade Count": 1},
            ]
        )
        with self.assertRaises(ValueError):
            build_daily_market_structure(raw)


if __name__ == "__main__":
    unittest.main()
