# Ordivon Verify — Public Wedge Audit Scope

## Purpose

Define the scope of the secret/private-reference audit for the Ordivon Verify
public wedge. The audit scans only future public-wedge candidate surfaces,
not the full private Ordivon repository.

## Candidate Public-Wedge Include Set

These paths are considered public-wedge candidates — they would be extracted
or published when Ordivon Verify goes public:

```
src/ordivon_verify/              # Package source
src/ordivon_verify/schemas/      # Prototype schemas
scripts/ordivon_verify.py        # Compatibility wrapper
scripts/smoke_ordivon_verify_private_install.py  # Install smoke
examples/ordivon-verify/         # Quickstart + GitHub Action examples
skills/ordivon-verify/           # Agent skill
docs/product/ordivon-verify-*    # Public-facing product docs
docs/runtime/ordivon-verify-*    # Runtime receipts (public-wedge relevant)
```

## Explicit Exclude Set

These are NOT in the audit scope — they belong to the private Ordivon Core:

```
adapters/          # Finance adapters (Alpaca, broker)
domains/           # Domain models
orchestrator/      # PFIOS workflow engine
capabilities/      # PFIOS capability layer
intelligence/      # PFIOS reasoning bridge
apps/              # Web/API applications
policies/          # Policy configs
docs/archive/      # Historical archives
docs/governance/   # DG Pack internals (not public wedge)
docs/architecture/ # Private Core architecture docs
docs/runtime/paper-trades/  # Finance dogfood internals
docs/runtime/alpaca-*       # Alpaca-specific docs
```

## Audit Categories

| # | Category | Blocking? |
|---|----------|-----------|
| 1 | Secret markers (API_KEY, TOKEN, PASSWORD) | Yes |
| 2 | Broker/trading leakage (Alpaca, broker, live trading) | Yes |
| 3 | Private path leakage (/root/projects, /mnt/, C:\) | Yes |
| 4 | Legacy identity (PFIOS, AegisOS, CAIOS as current truth) | Yes |
| 5 | Unsafe maturity claims (production-ready, public alpha as current) | Yes |
| 6 | License/release claims (activated, published as current) | Yes |

## Allowed Context Rules

A finding is reclassified from blocking to allowed_context when:

- It appears in a negative/boundary statement ("not a public release")
- It describes what something is NOT ("does not authorize execution")
- It's a checklist item to be verified ("[ ] secret audit clean")
- It's a proposal or recommendation ("should be published")
- It references private repo structure as design context ("Finance pack (Alpaca adapters)")
- It uses legacy identity only in explicit historical classification

## Blocking Rules

A finding is blocking when:

- An actual API key, token, or password appears in the wedge
- Broker/finance references appear as runtime behavior, not design description
- Private system paths appear as hardcoded values
- Legacy identity appears as current truth without historical classification
- Unsafe maturity claims appear as present-tense assertions
- License/release claims appear as activated facts

## Relationship to Private Core + Public Verify Wedge

The public wedge audit does NOT scan the full private Ordivon repo. That
would produce thousands of false positives from legitimate finance dogfood,
architecture docs, and phase history. The audit scope is deliberately narrow:
only surfaces intended for future public consumption.

A final pre-release audit on the extracted public repo is still required
before public alpha.

## Future Public Alpha Requirement

Before public alpha, the audit must be re-run on the actual extracted repo
(not just the candidate surfaces in the private repo). This confirms that
the extraction process itself didn't introduce new leakage.

---

*Created: 2026-05-01*
*Phase: PV-N6*
