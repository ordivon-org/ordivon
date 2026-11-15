"""Contract tests: historical data may only use information already public."""

import hashlib
import sys
import unittest
from datetime import UTC, date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(ROOT))

from ordivon_capital.research.pit_joint_forecast import (  # noqa: E402
    PointInTimeError,
    PriceVintage,
    empirical_joint_forecast,
    from_json_payload,
    make_one_step_optimizer_contract,
    point_in_time_prices,
    prequential_energy_evaluation,
    weighted_energy_score,
    weighted_variogram_score,
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
        sessions = tuple(
            date.fromisoformat(x) for x in ("2026-07-31", "2026-08-31", "2026-09-30", "2026-10-30")
        )
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
        before = point_in_time_prices(rows, as_of=datetime(2026, 11, 4, 22, tzinfo=UTC))
        after = point_in_time_prices(rows, as_of=datetime(2026, 11, 7, 22, tzinfo=UTC))
        self.assertEqual(before[("A", s[1])].adjusted_close, 110)
        self.assertEqual(after[("A", s[1])].adjusted_close, 999)
        with self.assertRaisesRegex(PointInTimeError, "offset"):
            point_in_time_prices(rows, as_of=datetime(2026, 11, 4, 22))

    def test_future_observation_cannot_change_existing_forecast(self):
        sessions, rows = self.fixture()
        asof = datetime(2026, 11, 3, 22, tzinfo=UTC)
        a = empirical_joint_forecast(
            records=rows,
            assets=("A", "B"),
            valuation_sessions=sessions,
            as_of=asof,
            valuation_session=sessions[2],
        )
        rows.extend(
            [
                rec("A", "2026-09-30", "2026-11-05T08:00:00+00:00", 0.1),
                rec("B", "2026-10-30", "2026-11-10T08:00:00+00:00", 50000),
            ]
        )
        b = empirical_joint_forecast(
            records=rows,
            assets=("A", "B"),
            valuation_sessions=sessions,
            as_of=asof,
            valuation_session=sessions[2],
        )
        self.assertEqual(a, b)
        self.assertEqual(a.training_return_count, 2)
        self.assertEqual(a.standing, "PAST_ONLY_EMPIRICAL_JOINT_BASELINE_NOT_CALIBRATED")

    def test_joint_market_co_crashes_not_product_of_marginal_probs(self):
        sessions, rows = self.fixture()
        fc = empirical_joint_forecast(
            records=rows,
            assets=("A", "B"),
            valuation_sessions=sessions,
            as_of=datetime(2026, 11, 4, 22, tzinfo=UTC),
            valuation_session=sessions[-1],
        )
        self.assertEqual(fc.training_return_count, 3)
        self.assertEqual(len(fc.scenarios), 3)
        self.assertAlmostEqual(sum(s.probability for s in fc.scenarios), 1)
        self.assertAlmostEqual(fc.scenarios[0].probability, 1 / 3)
        self.assertEqual(fc.excluded_incomplete_intervals, 0)
        for s in fc.scenarios:
            self.assertEqual(len(s.gross_returns), 2)

    def test_missing_joint_session_not_forward_filled(self):
        sessions, rows = self.fixture()
        rows = [x for x in rows if not (x.asset == "B" and x.session == sessions[1])]
        fc = empirical_joint_forecast(
            records=rows,
            assets=("A", "B"),
            valuation_sessions=sessions,
            as_of=datetime(2026, 11, 4, 22, tzinfo=UTC),
            valuation_session=sessions[-1],
        )
        self.assertEqual(fc.training_return_count, 1)
        self.assertEqual(fc.excluded_incomplete_intervals, 2)
        rows = [x for x in rows if not (x.asset == "B" and x.session == sessions[-1])]
        with self.assertRaisesRegex(PointInTimeError, "current valuation"):
            empirical_joint_forecast(
                records=rows,
                assets=("A", "B"),
                valuation_sessions=sessions,
                as_of=datetime(2026, 11, 4, 22, tzinfo=UTC),
                valuation_session=sessions[-1],
            )

    def test_energy_score_is_proper_rule_not_threshold(self):
        sessions, rows = self.fixture()
        fc = empirical_joint_forecast(
            records=rows,
            assets=("A", "B"),
            valuation_sessions=sessions,
            as_of=datetime(2026, 11, 4, 22, tzinfo=UTC),
            valuation_session=sessions[-1],
        )
        realized = (1.03, 0.98)
        actual = weighted_energy_score(forecasts=fc.scenarios, realized_gross=realized)
        self.assertGreaterEqual(actual, 0)
        with self.assertRaisesRegex(PointInTimeError, "probability mass"):
            weighted_energy_score(forecasts=(fc.scenarios[0],), realized_gross=realized)

    def test_exact_optimizer_json_contract_has_no_guessed_rates(self):
        sessions, rows = self.fixture()
        fc = empirical_joint_forecast(
            records=rows,
            assets=("A", "B"),
            valuation_sessions=sessions,
            as_of=datetime(2026, 11, 4, 22, tzinfo=UTC),
            valuation_session=sessions[-1],
        )
        with self.assertRaisesRegex(TypeError, "scenario_maintenance"):
            make_one_step_optimizer_contract(
                fc,
                gamma=2,
                initial_margin=(0.5, 0.5),
                turnover_cost=(0.001, 0.001),
                cash_gross=1.01,
                debt_gross=1.03,
            )
        contract = make_one_step_optimizer_contract(
            fc,
            gamma=2,
            initial_margin=(0.5, 0.5),
            turnover_cost=(0.001, 0.001),
            cash_gross=1.01,
            debt_gross=1.03,
            scenario_maintenance=((0.3, 0.3),) * len(fc.scenarios),
        )
        self.assertEqual(set(contract), {"gamma", "nodes"})
        self.assertEqual(contract["nodes"][0]["id"], "root")
        self.assertTrue(all(node["terminal"] for node in contract["nodes"][1:]))
        self.assertAlmostEqual(
            sum(node["conditional_probability"] for node in contract["nodes"][1:]), 1
        )
        self.assertEqual(contract["nodes"][0]["initial_margin"], [0.5, 0.5])

    def test_prequential_forecast_freezes_decision_before_next_outcome(self):
        sessions, rows = self.fixture()
        decisions = {
            sessions[1]: datetime.fromisoformat("2026-08-31T22:00:00+00:00"),
            sessions[2]: datetime.fromisoformat("2026-09-30T22:00:00+00:00"),
        }
        scores = prequential_energy_evaluation(
            records=rows,
            assets=("A", "B"),
            valuation_sessions=sessions,
            decision_instants=decisions,
            evaluation_as_of=datetime.fromisoformat("2026-10-30T22:00:00+00:00"),
        )
        self.assertEqual(len(scores), 2)
        self.assertTrue(all(x["energy_score"] >= 0 for x in scores))
        self.assertEqual(scores[0]["training_n"], 1)
        self.assertEqual(scores[1]["training_n"], 2)
        later = rows + [rec("A", "2026-08-31", "2026-11-08T11:00:00+00:00", 1e9)]
        rescored = prequential_energy_evaluation(
            records=later,
            assets=("A", "B"),
            valuation_sessions=sessions,
            decision_instants=decisions,
            evaluation_as_of=datetime.fromisoformat("2026-10-30T22:00:00+00:00"),
        )
        self.assertEqual(scores, rescored)
        with self.assertRaisesRegex(PointInTimeError, "after decision"):
            prequential_energy_evaluation(
                records=rows,
                assets=("A", "B"),
                valuation_sessions=sessions,
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
                    "asset": r.asset,
                    "session": r.session.isoformat(),
                    "published_at": r.published_at.isoformat(),
                    "adjusted_close": r.adjusted_close,
                    "raw_source_sha256": r.raw_source_sha256,
                    "source_standing": r.source_standing,
                }
                for r in rows
            ],
            "economic_contract": {
                "gamma": 3,
                "initial_margin": [0.5, 0.5],
                "turnover_cost": [0, 0],
                "cash_gross": 1.0,
                "debt_gross": 1.03,
                "scenario_maintenance": [[0.3, 0.3] for _ in range(3)],
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
                records=rows,
                assets=("A", "B"),
                valuation_sessions=(date(2026, 10, 29), date(2026, 10, 30)),
                as_of=datetime(2026, 10, 30, 22, tzinfo=UTC),
                valuation_session=date(2026, 10, 30),
            )

    def test_exact_existing_multistage_validator_consumes_monthly_tree(self):
        from ordivon_capital.portfolio.multistage_policy import (
            InformationNode,
            MultistageProblem,
            _validate_tree,
        )

        sessions, rows = self.fixture()
        forecast = empirical_joint_forecast(
            records=rows,
            assets=("A", "B"),
            valuation_sessions=sessions,
            as_of=datetime(2026, 10, 30, 22, tzinfo=UTC),
            valuation_session=sessions[-1],
        )
        data = make_one_step_optimizer_contract(
            forecast,
            gamma=2.0,
            initial_margin=(0.5, 0.5),
            turnover_cost=(0.001, 0.001),
            scenario_maintenance=((0.3, 0.3),) * len(forecast.scenarios),
            cash_gross=1.01,
            debt_gross=1.03,
        )
        validated = _validate_tree(
            MultistageProblem(
                gamma=data["gamma"],
                nodes=tuple(
                    InformationNode(
                        **{
                            key: tuple(value)
                            if key
                            in ("risky_gross", "maintenance", "initial_margin", "turnover_cost")
                            else value
                            for key, value in node.items()
                        }
                    )
                    for node in data["nodes"]
                ),
            )
        )
        self.assertEqual(validated.months, 1)
        self.assertEqual(len(validated.leaves), len(forecast.scenarios))

    def test_lagged_knn_only_uses_complete_past_transitions(self):
        from datetime import UTC

        sessions = tuple(date(2026, m, 28) for m in range(1, 9))
        returns = (
            (0.70, 0.70),
            (1.40, 1.40),
            (0.71, 0.72),
            (1.50, 1.48),
            (0.69, 0.70),
            (1.60, 1.59),
            (1.30, 1.30),
        )
        prices = {"A": 100.0, "B": 100.0}
        rows = []
        for j, day in enumerate(sessions):
            if j:
                for asset, gross in zip(("A", "B"), returns[j - 1], strict=True):
                    prices[asset] *= gross
            for asset in ("A", "B"):
                rows.append(
                    rec(asset, day.isoformat(), day.isoformat() + "T21:00:00+00:00", prices[asset])
                )
        asof = datetime(2026, 8, 28, 22, tzinfo=UTC)
        kwargs = dict(
            records=rows,
            assets=("A", "B"),
            valuation_sessions=sessions,
            as_of=asof,
            valuation_session=sessions[-1],
        )
        unconditional = empirical_joint_forecast(**kwargs)
        conditional = empirical_joint_forecast(**kwargs, forecast_method="lagged_knn")
        self.assertEqual(conditional.conditioning["eligible_historical_transitions"], 6)
        self.assertEqual(conditional.conditioning["neighbor_count"], 3)
        self.assertEqual(conditional.conditioning["conditioning_session"], "2026-08-28")
        self.assertEqual(conditional.training_return_count, 7)
        self.assertNotEqual(conditional.scenarios, unconditional.scenarios)
        self.assertAlmostEqual(sum(x.probability for x in conditional.scenarios), 1.0)
        later = rows + [
            rec("A", "2026-07-28", "2026-09-01T10:00:00+00:00", 1e9),
            rec("B", "2026-08-28", "2026-09-01T10:00:00+00:00", 1e9),
        ]
        replay = empirical_joint_forecast(
            **{**kwargs, "records": later}, forecast_method="lagged_knn"
        )
        self.assertEqual(conditional.to_dict(), replay.to_dict())
        incomplete = [o for o in rows if not (o.asset == "B" and o.session == sessions[-1])]
        with self.assertRaisesRegex(PointInTimeError, "current valuation"):
            empirical_joint_forecast(
                **{**kwargs, "records": incomplete},
                forecast_method="lagged_knn",
            )

    def test_variogram_distinguishes_correlated_and_anticorrelated_ensemble(self):
        from ordivon_capital.research.pit_joint_forecast import JointScenario

        co_crash = (
            JointScenario(0.5, (0.8, 0.8), 1),
            JointScenario(0.5, (1.2, 1.2), 1),
        )
        disjoint = (
            JointScenario(0.5, (0.8, 1.2), 1),
            JointScenario(0.5, (1.2, 0.8), 1),
        )
        self.assertAlmostEqual(
            weighted_variogram_score(forecasts=co_crash, realized_gross=(0.8, 0.8)), 0
        )
        self.assertGreater(
            weighted_variogram_score(forecasts=disjoint, realized_gross=(0.8, 0.8)), 0.15
        )
        with self.assertRaises(PointInTimeError):
            weighted_variogram_score(forecasts=co_crash, realized_gross=(0.8,))

    def test_one_existing_json_entry_accepts_conditional_method(self):
        sessions, rows = self.fixture()
        payload = {
            "as_of": "2026-10-30T22:00:00+00:00",
            "valuation_session": sessions[-1].isoformat(),
            "assets": ["A", "B"],
            "valuation_sessions": [x.isoformat() for x in sessions],
            "prices": [
                dict(
                    asset=r.asset,
                    session=r.session.isoformat(),
                    published_at=r.published_at.isoformat(),
                    adjusted_close=r.adjusted_close,
                    raw_source_sha256=r.raw_source_sha256,
                    source_standing=r.source_standing,
                )
                for r in rows
            ],
            "economic_contract": {
                "gamma": 2,
                "initial_margin": [0.5, 0.5],
                "turnover_cost": [0.0, 0.0],
                "maintenance_by_asset": [0.3, 0.3],
                "cash_gross": 1.0,
                "debt_gross": 1.01,
            },
        }
        # Two eligible historical lag transitions: both are selected.
        result = from_json_payload({**payload, "forecast_method": "lagged_knn"})
        self.assertEqual(set(result["optimizer_input"]), {"gamma", "nodes"})
        self.assertEqual(result["forecast_evidence"]["conditioning"]["neighbor_count"], 2)
        # Refine to the exact existing numerical solver rather than only
        # testing the shape of its input JSON.
        from ordivon_capital.portfolio.multistage_policy import (
            InformationNode,
            MultistageProblem,
            solve_multistage,
        )

        nodes = tuple(
            InformationNode(
                **{
                    key: tuple(value)
                    if key in ("risky_gross", "maintenance", "initial_margin", "turnover_cost")
                    else value
                    for key, value in n.items()
                }
            )
            for n in result["optimizer_input"]["nodes"]
        )
        solution = solve_multistage(
            MultistageProblem(gamma=result["optimizer_input"]["gamma"], nodes=nodes)
        )
        self.assertEqual(solution.contributions_r_per_path, 1)
        self.assertLess(solution.equality_residual, 1e-7)
        self.assertLess(solution.inequality_residual, 1e-7)
        self.assertLess(solution.concavity_global_utility_gap_upper, 1e-5)
        self.assertEqual(
            from_json_payload(payload)["standing"],
            "HISTORICAL_POINT_IN_TIME_EMPIRICAL_RESEARCH_ONLY",
        )
        with self.assertRaisesRegex(PointInTimeError, "forecast_method"):
            from_json_payload({**payload, "forecast_method": "future_seer"})

    def test_historical_conditional_prequential_metric_is_frozen(self):
        sessions, records = self.fixture()
        next_month = date(2026, 11, 30)
        all_dates = (*sessions, next_month)
        extra = [
            rec("A", next_month.isoformat(), "2026-11-30T21:00:00+00:00", 118),
            rec("B", next_month.isoformat(), "2026-11-30T21:00:00+00:00", 91),
        ]
        at = datetime.fromisoformat("2026-10-30T22:00:00+00:00")
        evaluated_at = datetime.fromisoformat("2026-11-30T22:00:00+00:00")
        kwargs = dict(
            records=records + extra,
            assets=("A", "B"),
            valuation_sessions=all_dates,
            decision_instants={sessions[-1]: at},
            evaluation_as_of=evaluated_at,
            forecast_method="lagged_knn",
        )
        result = prequential_energy_evaluation(**kwargs)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["forecast_method"], "lagged_knn")
        self.assertGreaterEqual(result[0]["energy_score"], 0)
        self.assertGreaterEqual(result[0]["variogram_score"], 0)
        future_revision = rec("A", "2026-09-30", "2026-12-10T11:00:00+00:00", 1e9)
        same = prequential_energy_evaluation(
            **{**kwargs, "records": records + extra + [future_revision]}
        )
        self.assertEqual(result, same)


class PITNativeOptimizerConsumer(unittest.TestCase):
    """Real solver invocation with frozen, explicitly unattested price vintages."""

    def payload(self):
        calendar, rows = PITResearchContract().fixture()
        return {
            "as_of": "2026-10-30T22:00:00+00:00",
            "valuation_session": calendar[-1].isoformat(),
            "assets": ["A", "B"],
            "valuation_sessions": [d.isoformat() for d in calendar],
            "prices": [
                {
                    "asset": x.asset,
                    "session": x.session.isoformat(),
                    "published_at": x.published_at.isoformat(),
                    "adjusted_close": x.adjusted_close,
                    "raw_source_sha256": x.raw_source_sha256,
                    "source_standing": x.source_standing,
                }
                for x in rows
            ],
            "economic_contract": {
                "gamma": 2.0,
                "initial_margin": [0.5, 0.5],
                "turnover_cost": [0.0, 0.0],
                "cash_gross": 1.01,
                "debt_gross": 1.03,
                "maintenance_by_asset": [0.3, 0.3],
            },
        }

    def test_one_api_consumes_pit_joint_distribution_and_existing_solver(self):
        from ordivon_capital.research.pit_joint_forecast import solve_pit_payload

        payload = self.payload()
        out = solve_pit_payload(payload)
        self.assertEqual(
            out["allocation_standing"],
            "CONDITIONAL_UNCALIBRATED_ONE_STEP_RESEARCH",
        )
        self.assertEqual(out["effects"], "NONE_NO_TRADE_NO_ACCOUNTING")
        self.assertEqual(out["conditional_allocation"]["contributions_r_per_path"], 1)
        self.assertEqual(len(out["conditional_allocation"]["root_risky_r"]), 2)
        self.assertEqual(len(out["conditional_allocation"]["terminal_distribution"]), 3)
        self.assertLess(out["conditional_allocation"]["equality_residual"], 1e-7)
        self.assertLess(out["conditional_allocation"]["inequality_residual"], 1e-7)
        self.assertLess(out["conditional_allocation"]["concavity_global_utility_gap_upper"], 1e-5)
        # The original evidence-only API remains byte-for-byte semantically stable.
        evidence = from_json_payload(payload)
        self.assertEqual(out["optimizer_input"], evidence["optimizer_input"])
        self.assertEqual(out["forecast_evidence"], evidence["forecast_evidence"])
        self.assertNotIn("conditional_allocation", evidence)

    def test_future_released_revision_does_not_change_conditional_policy(self):
        from ordivon_capital.research.pit_joint_forecast import solve_pit_payload

        payload = self.payload()
        before = solve_pit_payload(payload)
        revised = {
            **payload["prices"][0],
            "published_at": "2026-11-10T12:00:00+00:00",
            "adjusted_close": 100000.0,
        }
        payload["prices"].append(revised)
        after = solve_pit_payload(payload)
        self.assertEqual(before["forecast_evidence"], after["forecast_evidence"])
        self.assertEqual(
            before["conditional_allocation"],
            after["conditional_allocation"],
        )
        self.assertNotEqual(before["input_sha256"], after["input_sha256"])

    def test_native_cli_solve_opt_in_and_original_cli_default(self):
        import json
        import os
        import subprocess
        import tempfile

        payload = self.payload()
        with tempfile.TemporaryDirectory() as temp:
            file = Path(temp) / "vintages.json"
            file.write_text(json.dumps(payload), encoding="utf-8")
            env = {**os.environ, "PYTHONPATH": str(ROOT)}
            command = [
                sys.executable,
                "-m",
                "ordivon_capital.research.pit_joint_forecast",
                "--input",
                str(file),
            ]
            old = subprocess.run(command, capture_output=True, text=True, check=True, env=env)
            full = subprocess.run(
                [*command, "--solve"], capture_output=True, text=True, check=True, env=env
            )
        old_json, new_json = json.loads(old.stdout), json.loads(full.stdout)
        self.assertNotIn("conditional_allocation", old_json)
        self.assertIn("conditional_allocation", new_json)
        self.assertEqual(old_json["input_sha256"], new_json["input_sha256"])
        self.assertEqual(new_json["effects"], "NONE_NO_TRADE_NO_ACCOUNTING")

    def test_missing_economic_owner_terms_never_create_an_optimal_policy(self):
        from ordivon_capital.research.pit_joint_forecast import solve_pit_payload

        payload = self.payload()
        payload["economic_contract"].pop("gamma")
        with self.assertRaises(PointInTimeError):
            solve_pit_payload(payload)


class PITPairedPrequentialConsumer(unittest.TestCase):
    def dataset(self):
        from ordivon_capital.research.pit_joint_forecast import PriceVintage

        sessions, records = PITResearchContract().fixture()
        outcome_day = date(2026, 11, 30)
        new = [
            PriceVintage(
                asset=name,
                session=outcome_day,
                published_at=datetime(2026, 11, 30, 21, tzinfo=UTC),
                adjusted_close=value,
                raw_source_sha256=SHA,
                source_standing=STANDING,
            )
            for name, value in (("A", 115.0), ("B", 91.0))
        ]
        return {
            "records": records + new,
            "assets": ("A", "B"),
            "valuation_sessions": (*sessions, outcome_day),
            "decision_instants": {sessions[-1]: datetime(2026, 10, 30, 22, tzinfo=UTC)},
            "evaluation_as_of": datetime(2026, 11, 30, 23, tzinfo=UTC),
        }

    def test_exact_matched_periods_no_invented_significance(self):
        from ordivon_capital.research.pit_joint_forecast import (
            compare_pit_prequential_forecasts,
        )

        kwargs = self.dataset()
        result = compare_pit_prequential_forecasts(**kwargs)
        a = prequential_energy_evaluation(**kwargs, forecast_method="empirical")
        b = prequential_energy_evaluation(**kwargs, forecast_method="lagged_knn")
        self.assertEqual(result["matchedEvaluationCount"], 1)
        self.assertEqual(
            result["standing"],
            "PAIRED_PREQUENTIAL_DESCRIPTIVE_NO_SIGNIFICANCE_OR_ALPHA",
        )
        self.assertEqual(result["effectStanding"], "READ_ONLY_NO_TRADE_NO_ACCOUNTING")
        self.assertAlmostEqual(
            result["meanCandidateMinusBaselineEnergy"],
            b[0]["energy_score"] - a[0]["energy_score"],
        )
        self.assertAlmostEqual(
            result["perEvaluation"][0]["candidate_minus_baseline_variogram"],
            b[0]["variogram_score"] - a[0]["variogram_score"],
        )
        self.assertEqual(
            result["perEvaluation"][0]["baseline_forecast_sha256"],
            a[0]["frozen_forecast_sha256"],
        )
        self.assertNotIn("pValue", result)
        self.assertNotIn("recommendedPortfolio", result)

    def test_later_historical_revision_cannot_rewrite_frozen_score(self):
        from ordivon_capital.research.pit_joint_forecast import (
            compare_pit_prequential_forecasts,
        )

        kwargs = self.dataset()
        before = compare_pit_prequential_forecasts(**kwargs)
        rows = list(kwargs["records"])
        rows.append(
            rec(
                "A",
                "2026-08-31",
                "2026-11-15T10:00:00+00:00",
                9000.0,
            )
        )
        after = compare_pit_prequential_forecasts(**{**kwargs, "records": rows})
        self.assertEqual(before, after)

    def test_unpublished_outcome_cannot_be_scored(self):
        from ordivon_capital.research.pit_joint_forecast import (
            compare_pit_prequential_forecasts,
        )

        kwargs = self.dataset()
        with self.assertRaisesRegex(PointInTimeError, "not yet published"):
            compare_pit_prequential_forecasts(
                **{
                    **kwargs,
                    "evaluation_as_of": datetime(2026, 11, 15, tzinfo=UTC),
                }
            )


class PITAdjustedVintageFalsification(unittest.TestCase):
    """A retroactive split adjustment cannot fabricate the next-month gain."""

    def test_both_endpoints_share_evaluation_vintage_without_future_training(self):
        from dataclasses import replace

        from ordivon_capital.research.pit_joint_forecast import (
            compare_pit_prequential_forecasts,
        )

        kwargs = PITPairedPrequentialConsumer().dataset()
        initial = prequential_energy_evaluation(**kwargs)
        initial_pair = compare_pit_prequential_forecasts(**kwargs)

        # A 2-for-1 split backward-adjusts BOTH price endpoints. Dividing
        # 57.5 (post-split Nov) by the FROZEN pre-split October close 108.9
        # would fabricate a ~47% loss; true paired return is unchanged.
        revised = list(kwargs["records"])
        revision_digest = hashlib.sha256(b"as-of-evaluation split adjustment").hexdigest()
        revised.extend(
            (
                replace(
                    rec("A", "2026-10-30", "2026-11-10T11:00:00+00:00", 54.45),
                    raw_source_sha256=revision_digest,
                ),
                replace(
                    rec("A", "2026-11-30", "2026-11-30T22:00:00+00:00", 57.5),
                    raw_source_sha256=revision_digest,
                ),
            )
        )
        same_clock = {**kwargs, "records": revised}
        tested = prequential_energy_evaluation(**same_clock)
        score = tested[0]
        self.assertEqual(score["realized_price_basis"], "EVALUATION_AS_OF_BOTH_ENDPOINTS_ADJUSTED")
        self.assertEqual(score["frozen_forecast_sha256"], initial[0]["frozen_forecast_sha256"])
        self.assertAlmostEqual(score["realized_joint_gross"][0], 115.0 / 108.9, places=12)
        self.assertAlmostEqual(score["energy_score"], initial[0]["energy_score"], places=12)
        price_a = score["reference_revision_evidence"][0]
        self.assertEqual(price_a["asset"], "A")
        self.assertEqual(price_a["frozen_reference_close"], 108.9)
        self.assertEqual(price_a["evaluation_reference_close"], 54.45)
        self.assertEqual(price_a["evaluation_outcome_close"], 57.5)
        self.assertEqual(price_a["reference_revision_factor"], 0.5)
        self.assertTrue(price_a["reference_revised_since_decision"])
        self.assertEqual(price_a["evaluation_reference_source_sha256"], revision_digest)
        self.assertEqual(price_a["evaluation_outcome_source_sha256"], revision_digest)

        paired = compare_pit_prequential_forecasts(**same_clock)
        self.assertAlmostEqual(
            paired["meanCandidateMinusBaselineEnergy"],
            initial_pair["meanCandidateMinusBaselineEnergy"],
            places=12,
        )
        self.assertEqual(
            paired["perEvaluation"][0]["realized_price_basis"], score["realized_price_basis"]
        )
        self.assertEqual(
            paired["perEvaluation"][0]["reference_revision_evidence"],
            score["reference_revision_evidence"],
        )

        # No revision disclosed AFTER evaluation may rewrite the score, prices
        # or as-of source identities for that frozen historical experiment.
        future = revised + [
            rec("A", "2026-10-30", "2026-12-10T12:00:00+00:00", 1e9),
            rec("A", "2026-11-30", "2026-12-10T12:00:00+00:00", 1e-9),
        ]
        self.assertEqual(tested, prequential_energy_evaluation(**{**kwargs, "records": future}))

    def test_real_after_decision_price_correction_changes_only_outcome_score(self):
        kwargs = PITPairedPrequentialConsumer().dataset()
        old = prequential_energy_evaluation(**kwargs)
        corrected = list(kwargs["records"]) + [
            rec("A", "2026-10-30", "2026-11-15T10:00:00+00:00", 105.0)
        ]
        revised = prequential_energy_evaluation(**{**kwargs, "records": corrected})
        self.assertEqual(old[0]["frozen_forecast_sha256"], revised[0]["frozen_forecast_sha256"])
        self.assertAlmostEqual(revised[0]["realized_joint_gross"][0], 115 / 105)
        self.assertNotEqual(old[0]["energy_score"], revised[0]["energy_score"])
        self.assertTrue(
            revised[0]["reference_revision_evidence"][0]["reference_revised_since_decision"]
        )

class MarketCapturedVintageAdmission(unittest.TestCase):
    """Real Markets CSV digest contract -> PIT decisions; no retroactive origin."""

    @staticmethod
    def csv(close_a="108.9", missing_b=False):
        prices = [
            ("2026-07-31", "100", "100"),
            ("2026-08-31", "110", "90"),
            ("2026-09-30", "99", "99"),
            ("2026-10-30", close_a, "" if missing_b else "89.1"),
        ]
        text = "Date,A,B\\n" + "".join(
            ",".join(row) + "\\n" for row in prices
        )
        # Intentional literal newline encoding for CSV reader.
        return text.replace("\\n", "\n").encode("utf-8")

    @staticmethod
    def admitted(raw, **override):
        from ordivon_capital.research.pit_joint_forecast import (
            market_capture_to_pit_vintages,
        )

        fields = {
            "raw_csv": raw,
            "expected_sha256": hashlib.sha256(raw).hexdigest(),
            "assets": ("A", "B"),
            "first_session": date(2026, 7, 31),
            "last_session": date(2026, 10, 30),
            "captured_at": datetime(2026, 11, 7, 12, tzinfo=UTC),
            "last_session_close_at": datetime(2026, 10, 30, 20, tzinfo=UTC),
        }
        fields.update(override)
        return market_capture_to_pit_vintages(**fields)

    def test_five_year_archive_is_not_five_years_of_point_in_time_access(self):
        rows = self.admitted(self.csv())
        self.assertEqual(len(rows), 8)
        self.assertEqual({x.source_standing for x in rows}, {
            "SECONDARY_VENDOR_NOT_ATTESTED",
        })
        self.assertEqual({x.published_at for x in rows}, {
            datetime(2026, 11, 7, 12, tzinfo=UTC),
        })
        # Dates in a later imported archive do not make the archive
        # historically available for an earlier investment decision.
        self.assertFalse(
            point_in_time_prices(rows, as_of=datetime(2026, 10, 30, 23, tzinfo=UTC))
        )
        sessions = [
            date.fromisoformat(x)
            for x in ("2026-07-31", "2026-08-31", "2026-09-30", "2026-10-30")
        ]
        with self.assertRaisesRegex(PointInTimeError, "current valuation missing"):
            empirical_joint_forecast(
                records=rows, assets=("A", "B"),
                valuation_sessions=sessions,
                as_of=datetime(2026, 10, 30, 23, tzinfo=UTC),
                valuation_session=sessions[-1],
            )
        forecast = empirical_joint_forecast(
            records=rows, assets=("A", "B"),
            valuation_sessions=sessions,
            as_of=datetime(2026, 11, 7, 13, tzinfo=UTC),
            valuation_session=sessions[-1],
        )
        self.assertEqual(forecast.training_return_count, 3)
        self.assertEqual(forecast.source_digests, (
            hashlib.sha256(self.csv()).hexdigest(),
        ))

    def test_later_updated_csv_cannot_rewrite_earlier_information(self):
        old = self.admitted(self.csv())
        replacement = self.admitted(
            self.csv(close_a="999"),
            captured_at=datetime(2026, 11, 8, 12, tzinfo=UTC),
        )
        earlier = point_in_time_prices(
            (*old, *replacement),
            as_of=datetime(2026, 11, 7, 13, tzinfo=UTC),
        )
        later = point_in_time_prices(
            (*old, *replacement),
            as_of=datetime(2026, 11, 9, tzinfo=UTC),
        )
        key = ("A", date(2026, 10, 30))
        self.assertAlmostEqual(earlier[key].adjusted_close, 108.9)
        self.assertAlmostEqual(later[key].adjusted_close, 999)

    def test_digest_missing_quotes_and_impossible_capture_are_rejected(self):
        raw = self.csv()
        with self.assertRaisesRegex(PointInTimeError, "Markets source admission"):
            self.admitted(raw, expected_sha256="0" * 64)
        with self.assertRaisesRegex(PointInTimeError, "Markets source admission"):
            self.admitted(self.csv(missing_b=True))
        with self.assertRaisesRegex(PointInTimeError, "before its market close"):
            self.admitted(
                raw, captured_at=datetime(2026, 10, 30, 19, tzinfo=UTC)
            )
        with self.assertRaisesRegex(PointInTimeError, "must match"):
            self.admitted(
                raw,
                last_session_close_at=datetime(2026, 10, 29, 20, tzinfo=UTC),
            )
        with self.assertRaisesRegex(PointInTimeError, "UTC offset"):
            self.admitted(raw, captured_at=datetime(2026, 11, 7, 12))


if __name__ == "__main__":
    unittest.main()
