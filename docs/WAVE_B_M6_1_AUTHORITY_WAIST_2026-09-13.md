# Market Capital Clean-Room — Wave B / M6.1 Authority Waist Integration

## Standing

**PASS_BOUND_NON_LIVE_AUTHORITY_WAIST**.

Market Capital's trading runners now cross an explicit fail-closed preflight bound to the external `ordivon-market-capital-v2` semantic-waist provider. The application does not copy or reimplement the provider's core authority semantics.

## Exact provider binding

- provider repo: `/root/projects/ordivon-market-capital-v2`
- revision: `fd0a15db0152a1c35b4820b72e047df9db7a9e63`
- semantic implementation SHA-256: `0c50f9b397cdbde89f1770221eac76c50f94b85f2a4f012855baaf2f6423b4e6`
- semantic-freeze contract SHA-256: `d74d9796c63c811bf2cd7f7bcefb4dd7d2ad95ee4d387f5bbc727109b3775032`
- production-authorization contract SHA-256: `715a04de50ea6dd369375b84dff8f2cb2ba77f48ec1c3b8d447ef49d8c017c67`
- external-boundary contract SHA-256: `fa4cf810edc7a3a1554b2ff94a2e90acafd150e8386beda1558206a80404d89e`

Any provider revision or bound-file digest drift causes the preflight to fail closed.

## Current production authority

The provider remains:

- `ProductionAuthorization = BLOCK_NOT_GRANTED`
- `externalFinancialWriteAllowed = false`
- Market Capital `externalFinancialWriteAdmission = NOT_ADMITTED`
- independent live grant mechanism = `NOT_IMPLEMENTED`

A semantic `GRANTED` flag alone is intentionally insufficient to open a money-moving path. The application requires a separately admitted live grant mechanism before external-write mode can pass.

## Execution-path consequence

Wave B M1, M2, M3 and M4 now execute the authority-waist non-live preflight before starting LEAN. M6 retains the exact preflight result in its run evidence. Future paper/live runners must use the same boundary rather than bypassing it with direct strategy-to-broker calls.

This milestone does not open a FIX network session, broker session, credential path, venue write, or any other external financial effect.
