"""Economic falsifiers for the existing multistage optimizer's terminal obligations.

All cashflow numbers are synthetic math witnesses, NOT risk preferences,
return estimates, financing policies, or recommendation thresholds.
"""
from __future__ import annotations

import json
import math
import os
import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from ordivon_capital.portfolio.algebraic_policy import AlgebraicPolicyError
from ordivon_capital.portfolio.multistage_policy import (
    InformationNode,
    MultistageProblem,
    solve_multistage,
)


def root() -> InformationNode:
    return InformationNode(
        id="root", parent=None, t=0, conditional_probability=1,
        initial_margin=(.5,), turnover_cost=(0,),
    )


def leaf(name: str, probability: float, gross: float) -> InformationNode:
    return InformationNode(
        id=name, parent="root", t=1,
        conditional_probability=probability, risky_gross=(gross,),
        cash_gross=1.02, debt_gross=1.04, maintenance=(.3,),
        terminal=True,
    )


class EconomicTerminalLiability(unittest.TestCase):
    def test_deterministic_disposable_wealth_is_exact_and_no_silent_rescue(self) -> None:
        nodes=(root(),leaf("end",1,.8))
        problem=MultistageProblem(
            gamma=1, nodes=nodes, terminal_liabilities_r={"end":.4}
        )
        solution=solve_multistage(problem)
        self.assertAlmostEqual(solution.root_cash_r,1,places=6)
        self.assertAlmostEqual(solution.root_debt_r,0,places=6)
        self.assertAlmostEqual(solution.expected_terminal_r,1.02,places=6)
        self.assertAlmostEqual(solution.expected_disposable_terminal_r,.62,places=6)
        self.assertAlmostEqual(solution.certainty_equivalent_disposable_r,.62,places=6)
        self.assertAlmostEqual(solution.certainty_equivalent_terminal_r,1.02,places=6)
        self.assertAlmostEqual(solution.terminal_distribution["end"]["obligationR"],.4)
        self.assertAlmostEqual(solution.terminal_distribution["end"]["disposableTerminalR"],.62)

    def test_optional_liability_contract_is_backward_compatible_and_cashflow_neutral(self) -> None:
        nodes=(root(),leaf("down",.4,.6),leaf("up",.6,1.7))
        a=solve_multistage(MultistageProblem(gamma=2,nodes=nodes))
        b=solve_multistage(
            MultistageProblem(gamma=2,nodes=nodes,terminal_liabilities_r={"down":0.0,"up":0.0})
        )
        self.assertAlmostEqual(a.expected_terminal_r,b.expected_terminal_r,places=6)
        self.assertAlmostEqual(a.certainty_equivalent_terminal_r,b.certainty_equivalent_terminal_r,places=6)
        self.assertAlmostEqual(a.expected_terminal_r,a.expected_disposable_terminal_r,places=6)
        c=solve_multistage(
            MultistageProblem(
                gamma=2,nodes=nodes,
                terminal_liabilities_r={"down":.3,"up":0.0},
            )
        )
        self.assertGreaterEqual(c.expected_terminal_r,c.expected_disposable_terminal_r)
        self.assertAlmostEqual(
            c.expected_terminal_r-c.expected_disposable_terminal_r,
            .4*.3,places=6,
        )
        self.assertGreaterEqual(c.inequality_residual,0)
        self.assertGreater(min(x["disposableTerminalR"] for x in c.terminal_distribution.values()),0)

    def test_liability_requires_complete_observable_terminal_contract(self) -> None:
        nodes=(root(),leaf("down",.4,.6),leaf("up",.6,1.7))
        for liabilities in (
            {"down":.1}, {"down":.1,"up":math.nan},
            {"down":.1,"up":-1.0}, {"down":False,"up":0},
            {"down":.1,"up":0,"invented_leaf":0},
        ):
            with self.subTest(liabilities=liabilities):
                with self.assertRaises(AlgebraicPolicyError):
                    solve_multistage(
                        MultistageProblem(
                            gamma=2,nodes=nodes,terminal_liabilities_r=liabilities
                        )
                    )

    def test_impossible_contract_is_infeasible_not_made_safe_by_magic_number(self) -> None:
        nodes=(root(),leaf("end",1,.8))
        with self.assertRaisesRegex(
            AlgebraicPolicyError, "no strictly positive post-liability consumption"
        ):
            solve_multistage(
                MultistageProblem(
                    gamma=1,nodes=nodes,terminal_liabilities_r={"end":100.0}
                )
            )

    def test_native_json_consumer_reports_obligation_separately_from_account_equity(self) -> None:
        payload={
            "gamma":1,
            "nodes":[
                {"id":"root","parent":None,"t":0,"conditional_probability":1,
                 "initial_margin":[.5],"turnover_cost":[0]},
                {"id":"end","parent":"root","t":1,"conditional_probability":1,
                 "risky_gross":[.8],"maintenance":[.3],
                 "cash_gross":1.02,"debt_gross":1.04,"terminal":True},
            ],
            "terminal_liabilities_r":{"end":.4},
        }
        env=os.environ.copy()
        src=str(Path(__file__).resolve().parents[1]/"src")
        env["PYTHONPATH"]=src+os.pathsep+env.get("PYTHONPATH","")
        result=subprocess.run(
            [sys.executable,"-m",
             "ordivon_capital.portfolio.multistage_policy","--input","-"],
            input=json.dumps(payload),encoding="utf-8",capture_output=True,
            env=env,check=True,
        )
        data=json.loads(result.stdout)
        self.assertEqual(data["effectStanding"],"READ_ONLY_NO_BROKER_NO_PAPER_LEDGER")
        self.assertEqual(data["inputStanding"],"CALLER_SUPPLIED_NOT_MARKET_ATTESTED")
        self.assertAlmostEqual(data["solution"]["expected_terminal_r"],1.02,places=6)
        self.assertAlmostEqual(data["solution"]["expected_disposable_terminal_r"],.62,places=6)


if __name__=="__main__":
    unittest.main()
