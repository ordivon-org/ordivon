# Finance: a first run for people

Ordivon Finance is an **investment research and portfolio-decision program**
implemented using the existing [Capital owner](../README.md). It is not a
brokerage account, an autonomous fund manager, or an independent finance
platform. You can use current read-only components to investigate an
investment decision; the platform does not establish that the investment
will outperform or that a public web trading application is available.

## What can I actually do?

| Your question | Existing capability | Proven scope |
| --- | --- | --- |
| How might a new contribution follow my target allocation without selling? | Portfolio: strategic contribution | Deterministic cents, existing holdings, protected cash |
| Did a strategy beat doing nothing but owning a passive benchmark with the **same contributions**? | Portfolio: passive benchmark | Caller-supplied returns, fees and cash flows; no market-data attestation |
| How did an ETF-style virtual allocation behave in a given price history? | Markets + Portfolio: paper replay | Retrospective simulation, admitted CSV bytes, no real orders |
| Would revised historical prices change that conclusion? | Portfolio: vintage comparison | Compare separately byte-bound prices; not true point-in-time attestation |
| Is a claimed alpha supported by prospective evidence? | Research: freeze and review | Holdout identity, source arithmetic, independent verification standing |
| Are exposures and historical tail losses concerning? | Risk | Descriptive measures; no automatic capital approval |

You do **not** need to understand Runtime, MCP, Agent Skills or LEGO notation
to perform the following exercise.

## First example: a no-sale contribution

Use a local source checkout with the owner-native Python toolchain. From
the repository root:

```sh
cd domains/capital
scripts/run-strategic-contribution-brief < examples/strategic_contribution_r1.json
```

The supplied input is **not your portfolio**. It has $500 of illustrative
cash, a $300 protected reserve and a $100 proposed contribution. The output
contains `cashAfterMinor=40000` ($400), `protectedReserveMinor=30000`
($300), `allocationsMinor.BOND_CORE=10000` ($100), and
`executionAuthorized=false`. The two fictitious labels `INDEX_CORE`
and `BOND_CORE` are not tradeable instrument identifiers.

The result is an answer to **"what does this fixed rule allocate?"**,
not "should I buy this asset?" and does not issue any order.

## Second example: same contributions, two return paths

From `domains/capital`:

```sh
scripts/run-capability-python -m ordivon_capital.portfolio.passive_benchmark \
  --input examples/passive_benchmark_first_run_r1.json
```

The example supplies exactly two hypothetical periods, starts both paths
with $1,000, contributes $100 **at the start of each period**, and
specifies different returns and expenses. The output must report
`periodCount=2`, `contributedCapital=1200`,
`cashFlowConvention=MATCHED_DEPOSIT_AT_PERIOD_START`,
and `capitalAuthority=NONE`. Compare the two terminal wealth fields;
their difference cannot be attributed to unequal contributions.

All supplied returns are invented. This is **not** a backtest with verified
market data, expected return forecast, or GIPS-compliant performance report.

## Choose the next real task

For historical market data, use
[the ETF source and paper-simulation contract](PAPER_ETF_EOD_SNAPSHOT_R1.md)
and [the portfolio paper guide](FINANCE_PAPER_INVESTMENT_R1.md);
the data provider owns price authenticity. For research hypotheses, use
[the prospective research boundary](FINANCE_R2_RESEARCH_BOUNDARY.md).
For human-facing risk scenarios, see
[the existing risk observatory](PORTFOLIO_RISK_MONITORING_R1.md).

**Example: an Anthropic valuation hypothesis.** Finance can preserve explicit
valuation inputs, scenario assumptions and research evidence using existing
components, but it does not yet expose a qualified Anthropic valuation-data
pipeline or a one-click IPO price estimator. Treat an analyst-created
valuation table as a hypothesis, not a market-clearing quote. Do not claim
this missing workflow is delivered until data source, model and real consumer
are independently accepted.

If a command fails, first check the exact source revision, installed
Capital toolchain and the observed exception. An owner-native test result is
not proof of a deployed customer product.

## Terms and boundary

- **Capital**: the larger ownership umbrella; **Finance**: its investment
  research and decision program, not a second package or registry.
- **Investment**: caller-supplied portfolio intent, contributions and
  measured outcomes; **Research**: proposed strategies, frozen experiments
  and independent evidence.
- **Paper**: hypothetical or explicitly simulated investment and accounting;
  never a live account merely because values look realistic.
- **Risk** and **Governance** retain their own contracts; investment evidence
  cannot directly authorize broker actions.

The mature reference lens is the investment-management process and performance
presentation discipline (CFA Institute / GIPS). GIPS does not permit mixing
theoretical performance into a verified actual track record; this project does
not claim GIPS firm compliance:
https://www.cfainstitute.org/insights/professional-learning/refresher-readings/2026/overview-of-the-global-investment-performance-standards .
