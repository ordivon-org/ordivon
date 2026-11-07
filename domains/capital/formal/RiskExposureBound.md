# Risk exposure — kernel theorem, implementation gap and native consumer

**Canonical owner:** `domains/capital/src/ordivon_capital/risk/portfolio_risk.py::build_exposure_ledger` (CA03).
This is a mathematical property of positions, not a new risk calculator or a source of financial authority.

## Contract and assurance levels

1. **Specification:** for any finite list of exact integer signed notionals `p`, define
   `net(p) = sum(p)` and `gross(p) = sum(abs(p_i))`. Requirements:
   `abs(net(p)) <= gross(p)`; both measures compose across disjoint lists by
   addition of their contributions. Empty lists are allowed.
2. **Lean model / proof:** `RiskExposureBound.lean`, pinned Lean 4 in
   `tools/formal/mise.toml`, kernel-checks the three named theorems for
   **all finite lists**, not a fixed enumeration. No `sorry`, custom axioms,
   stochastic approximations or undocumented solver status. Check using:
   `mise run //domains/capital:verify:formal:risk-exposure`.
3. **Implementation refinement:** **UNKNOWN**. Production uses Python
   `Decimal` inputs and lossless string presentation, while the theorem uses
   mathematical `Int` and `Nat`. No machine-checked correspondence from
   `build_exposure_ledger` to the Lean definitions has been supplied.
   `equity > 0`, input uniqueness, precision, margins and factors are not
   consequences of this theorem.
4. **Real consumer witness:** from `domains/capital`, run
   `mise run verify` for the existing real `test_portfolio_risk.py`
   consumer, including the mixed long/short factor-exposure fixture.
   That fixture observes `gross=200`, `net=100` for +150 and -50 and
   `grossToEquity=2` for equity 100. Three source-level counterexample
   regressions preserve a `1e-10` notional after cancellation against
   `±1e20` and format a finite `1e22` notional without a spurious
   `Decimal.InvalidOperation`; the third checks a 38-digit factor product
   that ambient Decimal precision previously truncated. They do **not** prove the entire Python
   implementation. Caller-supplied exposures cannot attest brokerage holdings.
5. **Native acceptance gate:** `mise run //domains/capital:verify` invokes
   the same pinned Risk theorem before the existing Ruff/Pytest consumer suite.
   A passing source test alone does not bypass the kernel-check obligation.
6. **External effects:** None. This stateless projection may not authorize
   an order, a capital transfer, a risk budget or a live broker effect.

## Human

Interpret the output as exposure, not investment recommendation. A fully hedged
net position can still have large gross exposure; overlapping factor loadings
must never be summed as independent portfolio risk. To validate a source change,
run the pinned theorem plus the native Risk suite and review the exact source
revision. The mathematical bound permits no claim about positive prospective
returns, market provenance or venue reconciliation.

## Agent — R2.1 evidence template

- `I`: exact portfolio notionals, type/scale and source standing.
- `O`: actual exposure ledger and command receipts; no broker write.
- `pre`: finite input list, mathematical integer abstraction for the theorem,
  separately validated production decimal inputs.
- `post`: `abs(net) <= gross`; list concatenation preserves decomposed
  gross/net arithmetic **in the model**.
- `inv`: pure arithmetic; no cross-owner state mutation; UNKNOWN stays UNKNOWN.
- `eff`: read-only computation, no external financial effects.
- `prov`: Git revision, model SHA256, Lean version, kernel diagnostics,
  native Risk test result and caller-data authenticity standing.
- `unfold`: Risk math specification → Lean theorem → source inspection →
  actual Python consumer → separately qualified market/account data.

Only mark `modelProof=PROVED` when the exact tool run passes; keep
`implementationRefinement=UNKNOWN` and `realConsumer=OBSERVED` independent.
If source arithmetic changes, re-evaluate the correspondence even if the
unchanged Lean model still compiles.

**Test subtraction:** retain the real-source exposure fixture and external
provider tests until implementation refinement/consumer equivalence is
established. The abstract algebra does not license deleting those tests.
