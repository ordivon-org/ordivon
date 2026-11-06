# Tutorial: understand one Ordivon result in a real, read-only run

**Audience:** a person who has access to a checked-out Ordivon repository and
wants to see a working result. This is an offline developer demonstration, not
a public sign-up, paid product, or personal investment recommendation.

**You will:** run the existing Capital/Finance contribution-only projection,
see how an input becomes a reproducible output, and identify its limits. The
example uses invented asset labels and USD-cent amounts. It requires the
repository's pinned Capital toolchain; it requires **no broker credentials**.

## 1. Run the existing example

From the repository root:

```sh
cd domains/capital
scripts/run-strategic-contribution-brief < examples/strategic_contribution_r1.json
```

The runner prepares/uses its owner-native locked Python environment and
prints JSON. It does not transfer money or create a broker order.

## 2. Check the actual result

Look for these fields (observed against this example on 2026-11-06):

| Field | Expected value | Meaning |
| --- | --- | --- |
| `standing` | `READ_ONLY_PROJECTION` | A projection, not accepted investment advice |
| `contributionMinor` | `10000` | An illustrative USD $100 contribution |
| `protectedReserveMinor` | `30000` | Illustrative USD $300 retained reserve |
| `cashAfterMinor` | `40000` | Illustrative USD $400 cash after the projection |
| `executionAuthorized` | `false` | No trade or financial effect is authorized |

If the command fails, inspect the exact error and the owner's
[README](../../domains/capital/README.md). Do not silently assume that a
provider, installed tool or account is available.

## 3. Explore the source of truth

- The [input example](../../domains/capital/examples/strategic_contribution_r1.json)
  contains explicitly supplied weights and cash.
- The [Finance investment-first explanation](../../domains/capital/docs/FINANCE_INVESTMENT_FIRST_R1.md)
  describes what is calculated and what is not.
- The [Capital owner](../../domains/capital/README.md) leads to other
  read-only investment research, cash-flow-matched benchmarks and simulations.

**Next step:** choose your actual question and verify its owner via
[task navigation](tasks.md). A validated example does not establish that
Ordivon operates a production financial service or that historical returns
predict future performance.
