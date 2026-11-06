# Finance — Investment-First Owner Convergence (R1)

Status: **SOURCE IMPLEMENTED, READ-ONLY CONSUMER VERIFIED**. Source owner:
`domains/capital` (temporary physical identity; no `domains/finance` alias or
duplicate package was introduced). No broker API, financial write, or production
deployment is enabled by this change.

## Strategic decisions

Finance is a coherent set of responsibilities, not seven independent agents or
a trading application that owns every market mechanism. Use Parnas information
hiding: each module owns one reason to change, and domain consumers use narrow
public contracts. Reuse the QuantConnect Algorithm Framework separation of
universe/data, insights/research, portfolio construction, independent risk
management, and execution; use NautilusTrader only where event-driven backtest
and execution semantics actually require that engine.

- **Markets**: observed facts, time/source quality and provider adapters; no alpha.
- **Research**: hypothesis, point-in-time evidence, backtest and falsification;
  no execution authority.
- **Portfolio**: user-mandated target allocation and descriptive counterfactuals;
  no authority to place orders.
- **Risk**: exposure, tail risk, liquidity and portfolio constraints; independent
  from portfolio optimization.
- **Governance**: immutable mandate/effect admission, explicit unknowns and audit.
- **Trading**: only qualified provider intent/effect and recovery/reconciliation;
  no default external financial effects.
- **Accounting**: source-of-truth-bound ledger and readback; PostgreSQL-first
  with explicit retirement qualification for legacy SQLite paths.

Existing module names remain unchanged because a mechanical monorepo source
relocation is a separate cross-owner consumer operation. Do not hide cross-owner
breakage behind an import alias. Any rename must follow a precise, separately
qualified consumer impact and entrypoint migration.

## Delivered: strategic contribution allocation LEGO

Natural owner: `portfolio/strategic_contribution.py`.

Inputs: strict schema-v1 caller-provided current holdings in USD cents,
cash, protected reserve, contribution budget and target weights in basis points.
Output: a deterministic *non-executable* contribution-only projection, with
current/projected holdings, protected cash, method and unverified-data standing.
No price lookup, prediction, broker order, short sale or leverage is introduced.

Invariants:

1. `sum(allocationsMinor) == contributionMinor`;
2. `projectedHoldingsMinor[i] >= currentHoldingsMinor[i]`;
3. `cashAfterMinor >= protectedReserveMinor`;
4. `sum(targetWeightsBps) == 10000`;
5. no `executionAuthorized` or inferred risk PASS, including zero-size plans.

The apportionment is integer Hamilton/largest-remainder on positive target
*deficits*, not a new mean-variance optimizer or a return forecast. It is
bounded by 128 instruments, uses exact integer cents, rejects invented assets,
non-integers and data beyond an int64 money boundary. The caller owns the
target weights; outcomes do not constitute security recommendations.

Real executable consumer:

```sh
cd domains/capital
scripts/run-strategic-contribution-brief < examples/strategic_contribution_r1.json
```

Existing runner `scripts/run-capability-python` supplies the locked owner
Python environment. Focused tests execute the actual subprocess and check
zero-output rejection on malformed JSON. The one-page source consumer and
`planning/lego-plan-r1.json` node CA09 provide progressive-disclosure
guidance for other agents without a new Skill registry.

## Source-level limitations

There is no observed provider-sourced holding valuation, pricing, tax-lot
accounting, fee model, instrument suitability or portfolio stress score. The
result is marked `CALLER_SUPPLIED_UNATTESTED` and `NOT_EVALUATED`; the
independent Risk/Governance route must qualify any future action. The function
cannot turn a desirable target weight into market permission.

## Subtractive maintenance

Historical, unreferenced Wave A/Wave B one-off acceptance narratives were retired where `git grep` found no
concrete source/consumer references. They remain available in Git history
without new archives or duplicate backup registries. Current interface
contracts, raw evidence, provider qualification, positive consumer tests,
source-root files and other Owner/Runtime workspaces are outside this deletion.

Deletion is not proof of zero dynamic Agent readership. A historical document
must be restored by exact Git revision if a concrete runtime consumer is
subsequently demonstrated.

## Next measurable engineering steps

- Add source-attested point-in-time and corporate-action-aware market data for
  long-horizon index studies; reuse native providers rather than a local data
  service.
- Compare user-target allocation with simple fixed-mix and cash benchmarks
  including fees, taxes and holdout sensitivity.
- Add independent portfolio budget and account ledger consumer to the current
  read-only projection. Then make simulated scenario decisions with an existing
  engine, and only afterward evaluate separate investment permissions.
- Retire legacy provider/protocol scaffolds after exact consumers are migrated,
  not by deleting current tests or turning UNKNOWN into FALSE.

## Mature precedent

- D. L. Parnas, *On the Criteria to Be Used in Decomposing Systems into
  Modules* (1972): https://doi.org/10.1145/361598.361623
- QuantConnect LEAN Algorithm Framework:
  https://www.quantconnect.com/docs/v2/writing-algorithms/algorithm-framework/overview
- NautilusTrader architecture: https://nautilustrader.io/docs/
- SEC market-access controls as an engineering precedent (not an assertion
  that this personal research package is a regulated broker):
  https://www.sec.gov/rules-regulations/staff-guidance/trading-markets-frequently-asked-questions/divisionsmarketregfaq-0

Acceptance owner: `mise run verify`. GitHub protection/CI is a distinct
release observation; no local suite substitutes for it.
