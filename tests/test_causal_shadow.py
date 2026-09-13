from datetime import date, datetime, timezone
import unittest

from market_capital.causal_shadow import evaluate_causal_shadow


class CausalShadowTests(unittest.TestCase):
    def setUp(self):
        self.boundary = datetime(2026, 9, 12, 14, 59, 29, tzinfo=timezone.utc)
        self.tz = "America/New_York"

    def test_same_or_prior_dates_do_not_create_causal_evidence(self):
        series = {s: {date(2026, 9, 11), date(2026, 9, 12)} for s in ("AAPL", "MSFT", "NVDA", "SPY")}
        result = evaluate_causal_shadow(decision_boundary=self.boundary, session_timezone=self.tz, series_dates=series)
        self.assertEqual(result["standing"], "WAITING_FOR_POST_DECISION_DATA")
        self.assertFalse(result["causalEvidenceAvailable"])

    def test_one_missing_required_series_fails_closed(self):
        series = {
            "AAPL": {date(2026, 9, 14)},
            "MSFT": {date(2026, 9, 14)},
            "NVDA": {date(2026, 9, 14)},
            "SPY": set(),
        }
        result = evaluate_causal_shadow(decision_boundary=self.boundary, session_timezone=self.tz, series_dates=series)
        self.assertEqual(result["standing"], "WAITING_FOR_POST_DECISION_DATA")

    def test_complete_post_decision_common_cut_is_admitted(self):
        series = {s: {date(2026, 9, 14), date(2026, 9, 15)} for s in ("AAPL", "MSFT", "NVDA", "SPY")}
        result = evaluate_causal_shadow(decision_boundary=self.boundary, session_timezone=self.tz, series_dates=series)
        self.assertEqual(result["standing"], "POST_DECISION_DATA_ADMITTED")
        self.assertTrue(result["causalEvidenceAvailable"])
        self.assertEqual(result["firstEligibleCommonSessionDate"], "2026-09-14")

    def test_common_cut_not_union(self):
        series = {
            "AAPL": {date(2026, 9, 14), date(2026, 9, 15)},
            "MSFT": {date(2026, 9, 15)},
            "NVDA": {date(2026, 9, 14), date(2026, 9, 15)},
            "SPY": {date(2026, 9, 15)},
        }
        result = evaluate_causal_shadow(decision_boundary=self.boundary, session_timezone=self.tz, series_dates=series)
        self.assertEqual(result["eligibleCommonSessionDates"], ["2026-09-15"])


if __name__ == "__main__":
    unittest.main()
