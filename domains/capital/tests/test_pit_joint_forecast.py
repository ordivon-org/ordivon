"""Contract tests: historical data may only use information already public."""
import hashlib
import json
import sys
import unittest
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(ROOT))

from ordivon_capital.research.pit_joint_forecast import (  # noqa: E402
    EmpiricalJointForecast,
    PointInTimeError,
    PriceVintage,
    empirical_joint_forecast,
    from_json_payload,
    make_one_step_optimizer_contract,
    point_in_time_prices,
    prequential_energy_evaluation,
    weighted_energy_score,
)


SHA = hashlib.sha256(b"research fixture, not exchange-attested").hexdigest()
STANDING = "SECONDARY_VENDOR_NOT_ATTESTED"


def rec(ticker, day, publication, close):
    return PriceVintage(
        asset=ticker,
        session=date.fromisoformat(day),
        published_at=datetime.fromisoformat(publication),
        adjusted_close=close,
        raw_source_sha256=SHA,
        source_standing=STANDING,
    )


class PITResearchContract(unittest.TestCase):
    def fixture(self):
        sessions = tuple(date.fromisoformat(x) for x in (
            "2026-07-31", "2026-08-31", "2026-09-30", "2026-10-30"
        ))
        records = []
        for a, values in (
            ("A", (100.0, 110.0, 99.0, 108.9)),
            ("B", (100.0, 90.0, 99.0, 89.1)),
        ):
            for day, price in zip(sessions, values, strict=True):
                records.append(rec(a, day.isoformat(), day.isoformat() + "T21:00:00+00:00", price))
        return sessions, records

    def test_revisions_only_known_after_publication(self):
        s, rows = self.fixture()
        revised = rec("A", "2026-08-31", "2026-11-06T11:30:00+00:00", 999.0)
        rows.append(revised)
        before = point_in_time_prices(rows, as_of=datetime(2026, 11, 4, 22, tzinfo=timezone.utc))
        after = point_in_time_prices(rows, as_of=datetime(2026, 11, 7, 22, tzinfo=timezone.utc))
        self.assertEqual(before[("A", s[1])].adjusted_close, 110)
        self.assertEqual(after[("A", s[1])].adjusted_close, 999)
        with self.assertRaisesRegex(PointInTimeError, "offset"):
            point_in_time_prices(rows, as_of=datetime(2026, 11, 4, 22))

    def test_future_observation_cannot_change_existing_forecast(self):
        sessions, rows = self.fixture()
        asof = datetime(2026, 11, 3, 22, tzinfo=timezone.utc)
        a = empirical_joint_forecast(
            records=rows, assets=("A", "B"), valuation_sessions=sessions,
            as_of=asof, valuation_session=sessions[2],
        )
        rows.extend([
            rec("A", "2026-09-30", "2026-11-05T08:00:00+00:00", 0.1),
            rec("B", "2026-10-30", "2026-11-10T08:00:00+00:00", 50000),
        ])
        b = empirical_joint_forecast(
            records=rows, assets=("A", "B"), valuation_sessions=sessions,
            as_of=asof, valuation_session=sessions[2],
        )
        self.assertEqual(a, b)
        self.assertEqual(a.training_return_count, 2)
        self.assertEqual(a.standing, "PAST_ONLY_EMPIRICAL_JOINT_BASELINE_NOT_CALIBRATED")

    def test_joint_market_co_crashes_not_product_of_marginal_probs(self):
        sessions, rows = self.fixture()
        fc = empirical_joint_forecast(
            records=rows, assets=("A", "B"), valuation_sessions=sessions,
            as_of=datetime(2026, 11, 4, 22, tzinfo=timezone.utc),
            valuation_session=sessions[-1],
        )
        self.assertEqual(fc.training_return_count, 3)
        self.assertEqual(len(fc.scenarios), 3)
        self.assertAlmostEqual(sum(s.probability for s in fc.scenarios), 1)
        self.assertAlmostEqual(fc.scenarios[0].probability, 1/3)
        self.assertEqual(fc.excluded_incomplete_intervals, 0)
        for s in fc.scenarios:
            self.assertEqual(len(s.gross_returns), 2)

    def test_missing_joint_session_not_forward_filled(self):
        sessions, rows = self.fixture()
        rows = [x for x in rows if not (x.asset == "B" and x.session == sessions[1])]
        fc = empirical_joint_forecast(
            records=rows, assets=("A", "B"), valuation_sessions=sessions,
            as_of=datetime(2026, 11, 4, 22, tzinfo=timezone.utc),
            valuation_session=sessions[-1],
        )
        self.assertEqual(fc.training_return_count, 1)
        self.assertEqual(fc.excluded_incomplete_intervals, 2)
        rows = [x for x in rows if not (x.asset == "B" and x.session == sessions[-1])]
        with self.assertRaisesRegex(PointInTimeError, "current valuation"):
            empirical_joint_forecast(
                records=rows, assets=("A", "B"), valuation_sessions=sessions,
                as_of=datetime(2026, 11, 4, 22, tzinfo=timezone.utc),
                valuation_session=sessions[-1],
            )

    def test_energy_score_is_proper_rule_not_threshold(self):
        sessions, rows = self.fixture()
        fc = empirical_joint_forecast(
            records=rows, assets=("A", "B"), valuation_sessions=sessions,
            as_of=datetime(2026, 11, 4, 22, tzinfo=timezone.utc),
            valuation_session=sessions[-1],
        )
        realized = (1.03, 0.98)
        actual = weighted_energy_score(forecasts=fc.scenarios, realized_gross=realized)
        self.assertGreaterEqual(actual, 0)
        with self.assertRaisesRegex(PointInTimeError, "probability mass"):
            weighted_energy_score(
                forecasts=(fc.scenarios[0],), realized_gross=realized
            )

    def test_exact_optimizer_json_contract_has_no_guessed_rates(self):
        sessions, rows = self.fixture()
        fc = empirical_joint_forecast(
            records=rows, assets=("A", "B"), valuation_sessions=sessions,
            as_of=datetime(2026, 11, 4, 22, tzinfo=timezone.utc),
            valuation_session=sessions[-1],
        )
        with self.assertRaisesRegex(TypeError, "scenario_maintenance"):
            make_one_step_optimizer_contract(
                fc, gamma=2, initial_margin=(.5, .5),
                turnover_cost=(0.001, 0.001), cash_gross=1.01,
                debt_gross=1.03,
            )
        contract = make_one_step_optimizer_contract(
            fc, gamma=2, initial_margin=(.5, .5),
            turnover_cost=(0.001, 0.001), cash_gross=1.01,
            debt_gross=1.03,
            scenario_maintenance=((.3, .3),) * len(fc.scenarios),
        )
        self.assertEqual(set(contract), {"gamma", "nodes"})
        self.assertEqual(contract["nodes"][0]["id"], "root")
        self.assertTrue(all(node["terminal"] for node in contract["nodes"][1:]))
        self.assertAlmostEqual(sum(node["conditional_probability"] for node in contract["nodes"][1:]), 1)
        self.assertEqual(contract["nodes"][0]["initial_margin"], [.5, .5])

    def test_prequential_forecast_freezes_decision_before_next_outcome(self):
        sessions, rows = self.fixture()
        decisions = {
            sessions[1]: datetime.fromisoformat("2026-08-31T22:00:00+00:00"),
            sessions[2]: datetime.fromisoformat("2026-09-30T22:00:00+00:00"),
        }
        scores = prequential_energy_evaluation(
            records=rows, assets=("A", "B"), valuation_sessions=sessions,
            decision_instants=decisions,
            evaluation_as_of=datetime.fromisoformat("2026-10-30T22:00:00+00:00"),
        )
        self.assertEqual(len(scores), 2)
        self.assertTrue(all(x["energy_score"] >= 0 for x in scores))
        self.assertEqual(scores[0]["training_n"], 1)
        self.assertEqual(scores[1]["training_n"], 2)
        later = rows + [rec("A", "2026-08-31", "2026-11-08T11:00:00+00:00", 1e9)]
        rescored = prequential_energy_evaluation(
            records=later, assets=("A", "B"), valuation_sessions=sessions,
            decision_instants=decisions,
            evaluation_as_of=datetime.fromisoformat("2026-10-30T22:00:00+00:00"),
        )
        self.assertEqual(scores, rescored)
        with self.assertRaisesRegex(PointInTimeError, "after decision"):
            prequential_energy_evaluation(
                records=rows, assets=("A", "B"), valuation_sessions=sessions,
                decision_instants=decisions,
                evaluation_as_of=datetime.fromisoformat("2026-08-31T20:00:00+00:00"),
            )

    def test_json_evidence_separate_from_optimizer_input(self):
        sessions, rows = self.fixture()
        payload = {
            "as_of": "2026-10-30T22:00:00+00:00",
            "valuation_session": sessions[-1].isoformat(),
            "assets": ["A", "B"],
            "valuation_sessions": [d.isoformat() for d in sessions],
            "prices": [
                {
                    "asset": r.asset, "session": r.session.isoformat(),
                    "published_at": r.published_at.isoformat(),
                    "adjusted_close": r.adjusted_close,
                    "raw_source_sha256": r.raw_source_sha256,
                    "source_standing": r.source_standing,
                }
                for r in rows
            ],
            "economic_contract": {
                "gamma": 3, "initial_margin": [.5, .5],
                "turnover_cost": [0, 0], "cash_gross": 1.0,
                "debt_gross": 1.03,
                "scenario_maintenance": [[.3, .3] for _ in range(3)],
            },
        }
        x = from_json_payload(payload)
        self.assertEqual(x["effects"], "NONE_NO_TRADE_NO_ACCOUNTING")
        self.assertEqual(set(x["optimizer_input"]), {"gamma", "nodes"})
        self.assertEqual(len(x["input_sha256"]), 64)
        self.assertNotIn("forecast_evidence", x["optimizer_input"])
        broken = dict(payload)
        broken["valuation_session"] = "2026-11-05"
        with self.assertRaises(PointInTimeError):
            from_json_payload(broken)


    def test_daily_intervals_rejected_in_monthly_optimization(self):
        sessions, rows = self.fixture()
        with self.assertRaisesRegex(PointInTimeError, "monthly"):
            empirical_joint_forecast(
                records=rows, assets=("A", "B"),
                valuation_sessions=(date(2026, 10, 29), date(2026, 10, 30)),
                as_of=datetime(2026, 10, 30, 22, tzinfo=timezone.utc),
                valuation_session=date(2026, 10, 30),
            )

    def test_exact_existing_multistage_validator_consumes_monthly_tree(self):
        from ordivon_capital.portfolio.multistage_policy import (
            InformationNode, MultistageProblem, _validate_tree,
        )
        sessions, rows = self.fixture()
        forecast = empirical_joint_forecast(
            records=rows, assets=("A", "B"), valuation_sessions=sessions,
            as_of=datetime(2026, 10, 30, 22, tzinfo=timezone.utc),
            valuation_session=sessions[-1],
        )
        data = make_one_step_optimizer_contract(
            forecast, gamma=2.0, initial_margin=(0.5, 0.5),
            turnover_cost=(0.001, 0.001),
            scenario_maintenance=((0.3, 0.3),) * len(forecast.scenarios),
            cash_gross=1.01, debt_gross=1.03,
        )
        validated = _validate_tree(MultistageProblem(
            gamma=data["gamma"],
            nodes=tuple(
                InformationNode(**{
                    key: tuple(value) if key in (
                        "risky_gross", "maintenance", "initial_margin", "turnover_cost"
                    ) else value
                    for key, value in node.items()
                })
                for node in data["nodes"]
            ),
        ))
        self.assertEqual(validated.months, 1)
        self.assertEqual(len(validated.leaves), len(forecast.scenarios))
if __name__ == "__main__":
    unittest.main()
