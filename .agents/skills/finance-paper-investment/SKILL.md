---
name: finance-paper-investment
description: >-
  Use when an Ordivon Agent needs to operate existing Finance Investment Mode
  or Paper Lab, plan contribution-only allocation, compare passive benchmarks,
  replay ETF simulations, examine price-vintage drift, or prepare a paper-only
  PostgreSQL close receipt. Reuse existing natural Owners, not brokerage effects.
compatibility: Ordivon domains/capital; project mise/uv toolchain; native Runtime/Harness; no proprietary skill registry.
metadata:
  source-authority: Ordivon Finance Portfolio Markets and Accounting
---

# Finance Investment & Paper Lab — Agent Skill

This Skill is a **procedure and capability router**, not another portfolio engine, ledger, scheduler, provider client, or agent. Source remains `domains/capital`. For hypothesis freezing, holdout falsification and research candidate economics, switch to the already canonical `.agents/skills/finance-experiment-review/SKILL.md`; do not duplicate that workflow here. Human-facing operations are documented in `domains/capital/docs/FINANCE_HUMAN_GUIDE_R1.md`.

## Select the actual goal before invoking any tool

| Intention | Natural Owner | Native entrypoint | Actual standing |
|---|---|---|---|
| Allocate caller-defined new virtual contribution while protecting cash | Portfolio | `scripts/run-strategic-contribution-brief` | Stateless, no orders |
| Compare equal-cashflow strategy and passive benchmark | Portfolio | `python -m ordivon_capital.portfolio.passive_benchmark --input replay.json` under Capital toolchain | Read-only economic description |
| Replay a qualified historical source from a pinned snapshot | Portfolio | `scripts/run-paper-etf-replay-r1 --request request.json --source source.csv [--output private-receipt.json]` | Historical simulation only |
| Compare the economic effect of two source vintages | Portfolio | `scripts/run-paper-etf-vintage-compare-r1 --reference-request ... --reference-source ... --candidate-request ... --candidate-source ...` | Descriptive revision sensitivity |
| Admit an ETF EOD mark or historical source | Markets | `markets.etf_eod_snapshot`, `markets.historical_close_snapshot` | Source/time admission, not rights invented by Agent |
| Close a funded Paper session and read its receipt | Accounting | `scripts/run-capability-python -m ordivon_capital.accounting.postgres_paper_close --account NAME --input SESSION.json` | Mutates ONLY dedicated Paper PostgreSQL; no broker |
| Freeze a hypothesis, compare against passive benchmark and falsify | Research | Existing `finance-experiment-review` Skill and `scripts/run-finance-lego` | Evidence not authority |
| Evaluate exposure and effects | Risk / Governance / Trading | Actual bounded source contracts | No implicit cross-domain permission |

All command paths above are relative to `domains/capital` except the direct reference to the other canonical Skill. Before using one, check its exact option interface (`--help`) and latest source/contract version.


## How to route the source LEGO registry (CA01—CA10)

Do not invent a second LEGO namespace, general controller or another skill
registry. Consult the current canonical `planning/lego-plan-r1.json`.
The existing source units map to requested effects as follows:

- **Markets**: CA01 qualifies public observations; not private venue truth.
- **Risk**: CA02 measures dependence; CA03 projects positions/factor
  exposures. They are observations, not independent causal trade signals.
- **Portfolio**: CA04 evaluates named what-if composition with the Risk
  contract; CA09 computes contribution-only long-horizon allocation.
- **Governance**: CA05 applies the non-live effect admission. A passing
  source policy is not a broker execution permit.
- **Trading**: CA06 interprets ambiguous provider order standing; UNKNOWN
  remains UNKNOWN when external confirmation is missing.
- **Accounting**: CA07 owns durable reservation/journal semantics. Reuse its
  PostgreSQL paper close, never build a second NAV/ledger engine.
- **Research**: CA08 validates prospective evidence; CA10 freezes and reviews
  the experiment protocol. Continue using `finance-experiment-review`.

These are implemented **source-level** contracts only. The exact physical
Consumer, external-data authority, deploy readiness and permissions must be
checked separately at use time. Routes for modern ETF/paper modules remain
their respective Markets/Portfolio/Accounting implementations, not new
shadow LEGO registrations.

## Safe initial consumer (works without provider credentials)

From repository root:

```sh
domains/capital/scripts/run-strategic-contribution-brief \
  < domains/capital/examples/strategic_contribution_r1.json
```

Known fixture: `allocationsMinor.BOND_CORE=10000`,
`allocationsMinor.INDEX_CORE=0`, `cashAfterMinor=40000`, and
`executionAuthorized=false`. USD amounts are integer **minor units**
(cents); weights are basis points summing to 10000. Output retains
`dataStanding=CALLER_SUPPLIED_UNATTESTED` and
`riskStanding=NOT_EVALUATED`. Never report the example as source-qualified
investment advice.

## Paper replay admission

1. Freeze the source provider, rights, `availableAt`, exact source revision,
   SHA-256 and calendar sessions; do not equate a file digest with publisher
   authenticity. Historical copies edited after the tested dates cannot
   establish prospective outcomes.
2. With an explicit `--request` JSON and digest-matching `--source`, run
   `scripts/run-paper-etf-replay-r1`. The existing example
   `examples/paper_fixed_mix_etf_20261106.json` is a **request only**:
   no source CSV is bundled. If the source is missing, report BLOCKED /
   UNKNOWN rather than generating synthetic price facts.
3. Inspect `standing`, `capitalAuthority`, `sourceCommitClaimVerifiedExternally`,
   `providerPriceAuthenticityVerified`, `prospectiveHoldoutVerified`,
   `finalStrategyNAV`, `finalBenchmarkNAV`, `strategyMaxDrawdown`, and
   `dailySettlements`. Distinguish bounded mathematical replay from
   independently verified market performance.
4. A requested --output receipt is atomically published create-once. An identical replay is idempotent; different bytes at an occupied path fail without replacing the existing receipt. Use a distinct path for each source/policy version.
5. For a revised source vintage use the existing
   `scripts/run-paper-etf-vintage-compare-r1`, not a third price-replay
   implementation. The result indicates historical sensitivity, never
   prospective alpha.

## Formal Accounting evidence (load only when checking cash invariants)

Use `domains/capital/formal/paper_cash_settlement_r1.smt2` and the
owner-native `mise run formal:paper` task for three SMT-Presburger
invariants plus two deliberately satisfiable incorrect-model witnesses.
The natural specification and proof-level caveats are in
`domains/capital/formal/README.md`. Model proof != source refinement,
PostgreSQL persistence, deployment or capital authority. Do not create
a second ledger, copy Z3 into a private verifier or delete meaningful
database tests on model-only evidence.

## Stateful Paper Accounting admission

1. Check that the user/owner is asking for a **simulated** close and that
   `ORDIVON_CAPITAL_PAPER_PG_DSN` refers to the dedicated `ordivon_paper`
   database and a paper-only role. This writes virtual journal state, unlike
   the read-only portfolio CLI. No actual broker, bank or live exchange.
2. Bind one exchange session, prior close, funded cash, existing positions,
   fill identity, settlement dates, fees, and closing marks. The Markets
   qualified EOD path requires **both** `--market-snapshot` and
   `--market-binding` with empty inline marks; never mix unqualified inline
   prices and admitted snapshots.
3. Use only the existing Accounting entrypoint
   `scripts/run-capability-python -m ordivon_capital.accounting.postgres_paper_close
   --account NAME --input session.json` with the optional paired market
   arguments. It owns payable/receivable entries, atomic close, exact replay
   and PostgreSQL readback. The Skill never calculates a second NAV.
4. Output receipt identifiers, mode, snapshot lineage and whether a durable
   readback was actually witnessed. If source/receipts are missing, mark the
   unavailable field UNKNOWN and avoid publishing fictitious daily P&L.

## Decision and falsification rules

- **I**: goal, user investment assumptions, explicit capital units, current
  canonical source and qualified time/rights evidence.
- **O**: actual CLI result, receipt/digest, source availability, risk and
  authorization standing, absent/UNKNOWN facts and next natural consumer.
- **pre**: legitimate paper/no-effect purpose; exact source-qualified input
  for any claim beyond caller-supplied simulation.
- **post**: output honestly describes existing computation and never infers
  financial authority from a research/report status.
- **inv**: same cashflow base for benchmark, protected cash preserved,
  accounting owner alone owns NAV, no duplicate execution/ledger state.
- **eff**: read-only for Portfolio/Research, Paper-only DB for Accounting;
  never live broker order/transfer.
- **c**: source modules dictate bounded costs and limits; UNKNOWN without
  exact implementation evidence.
- **epsilon**: source vintage errors, fees/corporate actions and probabilistic
  uncertainty remain explicit; do not convert UNKNOWN to false.
- **prov**: module path, pinned source rev, dataset digest, actual session,
  observed result and real consumer evidence.
- **unfold**: Human goal → natural Owner → native call → validated receipt
  → independent research/risk interpretation.

The source of truth for composition is
`domains/capital/config/capital_domain_taxonomy.json`; for R2.1 identities,
`domains/capital/planning/lego-plan-r1.json`; for source/external Owner
census, `domains/capital/config/external_owner_census.json`. Execute
`mise run //domains/capital:verify` for acceptance. Treat repository Skill
packaging as discovery instructions only, **not** registration of a new
runtime, scheduler, financial provider, credential authority or live
investment mandate.

References: https://github.com/agentskills/agentskills/blob/main/docs/specification.mdx ;
https://www.quantconnect.com/docs/v2/writing-algorithms/algorithm-framework/overview ;
https://www.gipsstandards.org/standards/gips-standards-for-firms/gips-standards-handbook-for-firms/
