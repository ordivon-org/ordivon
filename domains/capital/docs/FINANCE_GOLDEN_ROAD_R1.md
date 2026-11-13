# Ordivon Finance Golden Road R1

**Scope: executable, non-live, bounded and falsifiable.** Current source of
truth: domains/capital. The seven existing domains own actual capabilities:
Markets, Research, Portfolio, Governance, Trading, Accounting and Risk.
There is no new OMS, second accounting ledger, broker mapping, or Agent owner.

## Economic objective and hard bounds

The Paper Investment Lab uses **USD $10,000 virtual starting cash**,
**USD $9,000 protected reserve** and a **maximum USD $1,000 simulated sleeve**.
One original Qlib-selected ETF is simulated for 5 or 20 holding sessions.
The experiment is NOT a real account, investment recommendation, historical
point-in-time market study, proven alpha or live authorization.

## End-to-end production-consumer graph

    Human: objective, reserve and allowed virtual capital
      -> Markets: capturedAt, availability, provenance, rights/PIT state
      -> Research: frozen study and actual Qlib OOS prediction snapshot
      -> Portfolio: existing strategic-contribution capital planner
      -> Governance: existing installed NON_LIVE execution policy
      -> Trading: original native Nautilus BacktestNode fills and order events
      -> Paper bridge: native-account-scoped event IDs, prices, fees, timestamps
      -> Accounting: EXISTING PG SERIALIZABLE Paper close per session
      -> Accounting independent read-latest committed receipt
      -> Risk / Portfolio performance, ONLY IF separate Markets snapshots
         and price/rights/time evidence are actually admitted
      -> Research: passive baseline, OOS independent falsification and report

A simulation mandate is only a caller-declared **Paper portfolio label** and
read-only Portfolio budget; it does NOT authenticate a customer or grant
live PortfolioIntent. Each distinct source / mandate has its own
run-specific r3sim_... PG account. The same portfolio label does **not**
create a canonical persistent multi-run portfolio aggregate.

## Golden commands

### 1. Start without any database or broker

From repo root:

    domains/capital/scripts/run-strategic-contribution-brief \
      < domains/capital/examples/strategic_contribution_r1.json

Require executionAuthorized=false, dataStanding=CALLER_SUPPLIED_UNATTESTED
and riskStanding=NOT_EVALUATED. Do not infer an executable order from a plan.

### 2. Check current Governance nonlive admission

From domains/capital:

    scripts/run-capability-python \
      -m ordivon_capital.governance.policy_decision \
      --repo . --config config/execution_policy.json --mode non-live

Require NON_LIVE_POLICY_ALLOWED, allowExternalWrite=false and
externalFinancialWritesAllowed=false. This comes from the repository's
installed configuration and external-write input, not user JSON.

### 3. Actually run the research and native model

The existing Qlib test producer must yield the exact:
  - native_study_result.json
  - qlib_test_predictions.csv

The existing qualification producer at
adoption/r3_native/tests/probe_native_buy_hold_exit.py must genuinely use
the pinned Qlib study with frozen historical Cboe/OpenBB capture and
NautilusTrader BacktestNode to yield:
  - native_holding_result.json (true original native fill claims)
  - paper_sessions.json (co-produced Paper daily account transitions)

The producer needs its existing ORDIVON_FINANCE_R3_* environment and
non-live optional toolchain. It is **a qualification probe, not a
production scheduler**, and test score interventions are never original
Qlib predictions. The prior 2025-10 market history was collected in
2026-11; it is NOT certified as historically knowable in 2025-10.

### 4. Declare a small Paper-only investment envelope

Keep a PRIVATE file called paper-mandate.json, replacing SPY with the
actually model-selected ETF when necessary. All money is in USD cents:

    {
      "schemaVersion": 1,
      "kind": "ordivon.finance.portfolio.paper-simulation-mandate",
      "portfolioRef": "paper-lab-r3",
      "lane": "NON_LIVE",
      "externalFinancialWritesAllowed": false,
      "maxHorizonSessions": 20,
      "allocationRequest": {
        "schemaVersion": 1,
        "kind": "ordivon.finance.portfolio.strategic-contribution-request",
        "currency": "USD",
        "cashMinor": 1000000,
        "protectedReserveMinor": 900000,
        "contributionMinor": 100000,
        "holdingsMinor": {"SPY": 0},
        "targetWeightsBps": {"SPY": 10000}
      }
    }

The contributionMinor=100000 value is a **read-only $1,000 simulation
allocation ceiling**; it does NOT deposit another $1,000 to PG.
The Portfolio component verifies allocation/exposure budgets and
reserves; the Governance component independently verifies NON_LIVE.
Wrong instrument, reserve, horizon, real-execution lane, buy beyond sleeve
or a non-Paper account label must be refused BEFORE the first PG write.

### 5. Close a real simulation batch in a dedicated PostgreSQL

From domains/capital:

    export ORDIVON_CAPITAL_PAPER_PG_DSN='host=127.0.0.1 port=PAPER_PORT user=PAPER_ROLE dbname=ordivon_paper connect_timeout=4'
    scripts/run-capability-python -m ordivon_capital.accounting.paper_simulation_run \
      --study /private/research/native_study_result.json \
      --predictions /private/research/qlib_test_predictions.csv \
      --native /private/nonlive/native_holding_result.json \
      --sessions /private/nonlive/paper_sessions.json \
      --mandate /private/finance/paper-mandate.json

Do NOT commit connection secrets or private files. Database name is
required to be ordivon_paper; no real broker API is involved.
Require portfolioMandateStanding=SIMULATION_ONLY_PORTFOLIO_PLAN_BOUND,
simulationEvidence.nonlive_policy_standing=NON_LIVE_POLICY_ALLOWED,
protectedMinor=900000, brokerEffects=0,
realAccountMappingAuthorized=false, historicalPITQualified=false.

Legacy calls without --mandate still work as UNBOUND simulation replays,
but they do not fulfill this portfolio-scoped Golden Road.

### 6. Read the independently committed PG account head

    scripts/run-capability-python \
      -m ordivon_capital.accounting.postgres_paper_close \
      --account r3sim_FULL_KEY_FROM_PREVIOUS_OUTPUT --read-latest

Require COMMITTED_PAPER_HEAD and match account, mandate, simulation source
and valuation against the original response. The receipt still contains
caller-supplied marks, not independent market-price certification.

Every day is already an EXISTING serializable PG transaction, but the
multi-day batch is NOT atomic. To recover a committed prefix, rerun with
the exact same four artifacts AND same mandate; never silently replace
already-posted source or rewrite an existing Paper account.

### 7. Use independent Risk, benchmarks and Research only when qualified

Risk paper_close_risk and Portfolio paper_close_performance require separately
admitted Markets ETF EOD snapshots and rights/currentness, whereas these
native test closes carry CALLER_SUPPLIED_MARKS. Their stronger claims remain
BLOCKED for this raw experiment; never hand-author false market evidence.
The same-flow passive benchmark, fee/slippage/tax assumptions, OOS sample
size, actual Research precommitment and drawdown/tail risk are the next
independent scientific consumers. Positive simulated cash is NOT alpha.

The simulation account SIM-001 and derived r3sim_... accounts cannot
authorize trading.postgres_demo_intent, OKX, Binance, a live account or a
PortfolioIntent with external financial write effects.

## Engineering falsification and release acceptance

From domains/capital:

    mise run verify
    mise run verify:nonlive:nautilus
    mise run formal:paper

Verify the code on REAL isolated PostgreSQL18, not source-only fixtures:
H5/SPY 8 sessions and $10,005.17; H20/IWM 23 and $10,002.30; zero-entry H5
8 and $10,000; reserve $9,000 each. Assert wrong-ETF portfolio mandate,
changed reserve, false external write and wrong native fill price/fee/ID
are refused before PG; physically stop/restart and replay; interrupt after
four committed days then finish eight; independently read the PG latest
receipt and ensure it still reports non-PIT caller-supplied marks.

Measured 2026-11-13: the scoped run batch first wrote 55 original daily
closes across five virtual run accounts. Tests added extra fixture accounts;
a sixth deliberately interrupted scoped run was restored. The disposable
test cluster ended with 94 real rows in 14 virtual/testing accounts.
These are NOT real customers or production deployments. The existing Z3
Paper model is only an abstract mathematical proof; it is not a formal
proof of the whole Python and PG implementation.

Release code through GitHub Required CI, CodeQL and native Merge Queue,
then independently verify main's complete Capital Git tree. Keep peer
review standing UNKNOWN until an actual other participant checks that
exact source. Delete disposable test clusters and regenerable worktrees
only after Git/source/receipts are safely retained.

## Next-important work, in order

P0: Markets qualified PIT/rightful data -> Risk and Portfolio performance
real consumer acceptance, with no fabricated metadata.
P0: Independent adversarial review of current exact main SourceCut.
P1: Research net-of-fees, matched cash-flow passive benchmark and OOS
sample qualification; state UNKNOWN if no decisive increment.
P1: Persistent multi-run virtual portfolio aggregation ONLY when real
downstream consumers require it; current portfolioRef is not that owner.
P2: Scheduling via existing Harness/Runtime; never add a custom agent
worker or trading runner without a proven consumer and resource budget.
External broker finance writes remain NOT_ADMITTED.
