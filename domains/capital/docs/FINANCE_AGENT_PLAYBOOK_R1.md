# Finance: source-bound guidance for Agents

Use this page for **discovering and using the existing Capital owners**, not
to establish a Finance super-Agent, broker, registry or hidden approval engine.
For task-specific prospective finance analysis, the canonical
[finance-experiment-review Skill](../../../.agents/skills/finance-experiment-review/SKILL.md)
has detailed method/CLI inputs. Read it only when an experiment requires it.

## 1. Orient to the actual source

The source identity is `domains/capital/src/ordivon_capital`. `Finance`
names a cross-owner investment program, *not* a second source tree. The
physical source packages and boundaries are:

| Natural responsibility | Source | Primary answer it owns |
| --- | --- | --- |
| Observable market facts | `markets/` | Source data, snapshots, public streaming and provenance |
| Hypothesis and evaluation | `research/` | Precommitment, holdout and model evidence |
| Portfolio planning and comparison | `portfolio/` | Fixed contribution, passive baseline, paper scenarios |
| Measurement of risk | `risk/` | Exposure, dependence, historical tail loss |
| Decision controls | `governance/` | Exact policy decision; no research bypass |
| Provider/broker effects | `trading/` | Provider reality, FIX, reconciliation, trade feasibility |
| Ledger and simulated account | `accounting/` | Exact durable account and paper settlement history |

Never infer package authority from a naming convention. Current machine-readable
source-owner mapping lives in `config/capital_domain_taxonomy.json`;
mechanics/ownership census is `config/external_owner_census.json`.
Bounded methods reuse provider APIs, existing LEAN/Nautilus/Qlib concepts,
rather than creating an Ordivon engine for each research question.

The source-bound dependencies are intentionally directional: Portfolio
consumes Markets and Governance where an actual calculation requires them;
Research consumes qualified Risk calculations; Risk delegates a bounded
policy decision to Governance. Diagnose coupling from *actual imports and
consumer contracts* (DSM) before moving a module. No physical directory
rename is authorized by a conceptual Finance taxonomy alone.

## 2. Start with two real, read-only consumers

From `domains/capital` in an isolated Runtime Workspace or checked-out
Git worktree:

```sh
scripts/run-strategic-contribution-brief < examples/strategic_contribution_r1.json
scripts/run-capability-python -m ordivon_capital.portfolio.passive_benchmark \
  --input examples/passive_benchmark_first_run_r1.json
```

For the supplied fixed example, the first response must keep
`executionAuthorized=false`, conserve the exact `contributionMinor=10000`
and preserve the `protectedReserveMinor=30000`. For the second, require
matched deposits, `contributedCapital=1200`, and `capitalAuthority=NONE`.
These are reproducible caller-data demonstrations, **not** proof of
historical market authenticity or investment skill.

## A small mathematical invariant, instead of redundant edge-case scaffolding

The current Portfolio contribution projection already implements Hamilton
(largest-remainder) integer-cent apportionment. For holdings `h[i]`,
nonnegative contribution `C`, exact target weights `w[i]` summing to
`B=10000` basis points, and target total `T=sum(h)+C`, define

```text
g[i] = max(0, T*w[i] - B*h[i])
D    = sum(g[i])
q[i] = floor(C*g[i] / D)
R    = C - sum(q[i])
```

`sum(T*w[i]-B*h[i])=B*C`, hence `D>=B*C` and `C>0` implies
`D>0`. Each fractional remainder is less than 1, so
`0<=R<number_of_instruments`. Allocating one additional cent to the
`R` largest fractional remainders proves `sum(allocation)=C` and
`allocation[i]>=0` without selling any holding. The admission
precondition `C<=cash-reserve` proves protected cash remains intact.
Source-bound integer limits and deterministic name tie-breaking are
separate implementation claims.

This is a **human-readable algebraic argument**, not a machine-checked
refinement proof or a claim that target-deficit weighting maximizes
investor utility. The existing
`tests/test_strategic_contribution.py` exercises the practical
conservation, no-sale, reserve and exact-cent consumer laws; do not
add dozens of trivial mutations merely to inflate test counts.

## 3. Select and assemble only needed LEGO

For an actual finance question, express:

- **Input**: human objective, investment horizon, capital/contribution facts,
  market source identity, cost model, as-of instant.
- **Desired output**: a falsifiable research statement or comparable
  investment/cost/risk report (not vague "profitable AI").
- **SourceCut**: code revision, dataset bytes and *available-at* evidence.
- **Owner**: the current authority for each source, computation, decision
  and external effect.
- **Consumer proof**: exact CLI/Job and output, realistic negative hypothesis,
  Owner verification and a domain-specific independent check.
- **Remaining UNKNOWN**: provider truth, publication chronology, selection
  bias, multiple trials, survivorship, or actual suitability when unproven.

If declaring/admitting an R2.1 LEGO, use the existing
[recursive-lego-calculus Skill](../../../.agents/skills/recursive-lego-calculus/SKILL.md)
with its complete `(I,O,S,pre,post,inv,eff,c,epsilon,prov,unfold)`
contract. Do not relabel every file, CLI or Agent as its own LEGO. The
default rule is **DELETE unused custom machinery → REUSE qualified mature
owners → COMPOSE narrow seams → CREATE only after a real substitution
failure**.

## 4. Research/portfolio/risk are separate

A normal research request may combine these existing, independently qualified
steps when materially required:

```text
provider observation + availability provenance (Markets)
    -> frozen hypothesis / trial family (Research)
    -> held-out sample + independent arithmetic replay (Research)
    -> matching deposits and passive opportunity cost (Portfolio)
    -> descriptive exposure / tail-risk review (Risk)
    -> human-facing conclusion with explicit UNKNOWN
```

Do not invent a universal orchestrator to implement this picture. Use the
existing `scripts/run-finance-lego` operations
`fingerprint-policy`, `freeze-experiment`,
`assess-holdout` and `review-candidate` only for their declared inputs.
A source hash verifies bytes; it does not verify that a vendor published
them at the claimed historical instant. The
[retrospective paper comparison](FINANCE_PAPER_INVESTMENT_R1.md) checks
sensitivity to source revisions, **not** true point-in-time vintage truth.

If real equity trades or broker access are requested, do not interpret
Runtime admin access or a Research result as capital authorization. The
natural provider, Governance and Accounting contracts define their own
actions. This is an ownership fact, not a request for another mandatory
authorization framework.

## 5. Verification, handoff and retirement

Run `mise tasks ls` from the owner, use the focused native consumer tests
for changed code, and for a consequential implementation run
`mise run verify` from `domains/capital`.
Separate mechanical PASS from provider authenticity, scientific validity
and real user acceptance. Use existing GitHub PR/required CI/merge queue;
do not build a competing release pipeline.

Before retiring files, trace incoming imports, CLI usage, templates,
test/executable contracts, deployment files and persisted-state consumers.
Prefer deleting unused legacy reports/fixtures with no current consumer;
keep SQLite source import/replay paths while real PostgreSQL migration tests
still depend on them. Do not delete another Agent's live Workspace or
active Job. Git history is sufficient for unconsumed historical prose, not
a reason to ship duplicate runbooks indefinitely.

## Mature external responsibilities to reuse

- [QuantConnect LEAN Algorithm Framework](https://www.quantconnect.com/docs/v2/writing-algorithms/algorithm-framework/overview):
  Universe/Alpha/Portfolio/Risk/Execution are separable model roles;
  do not build a second local engine merely to copy those classes.
- [NautilusTrader architecture](https://nautilustrader.io/docs/nightly/concepts/architecture/):
  event-driven Ports/Adapters and source/reconciliation concepts are
  candidate mechanics, not automatically admitted installed providers.
- [Microsoft Qlib documentation](https://github.com/microsoft/qlib/blob/main/docs/index.rst):
  training/dataset/model/evaluation and experiment recording are reference
  mechanics; instantiate them only for a real ML research consumer.
- [CFA GIPS](https://www.cfainstitute.org/insights/professional-learning/refresher-readings/2026/overview-of-the-global-investment-performance-standards):
  historical hypothetical returns must not be presented as verified
  actual client results.
- [Diátaxis](https://diataxis.fr/):
  separate this Agent how-to from the
  [human learning tutorial](FINANCE_HUMAN_QUICKSTART_R1.md),
  native API reference and explanatory architecture.

The absence of real provider currentness, historic holdout attestation,
generalized alpha or production investor onboarding is a real gap, not a
reason to create parallel data platforms.
