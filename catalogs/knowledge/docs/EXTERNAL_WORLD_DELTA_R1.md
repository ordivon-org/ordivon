# External World Claim–Evidence–Delta R1

## Scope and authority

This is an **owner-review source observation**, not an autonomous belief store, news
archive, scheduler, universal registry, fact-checker, or domain model. It complements
`catalogs/capabilities/docs/EXTERNAL_LEGO_EVOLUTION_R1.md`: externally observed
**events** can invalidate assumptions; external **software/method candidates** can
challenge implementations. They are distinct lanes with shared provenance and
consumer-verification obligations.

Natural owners decide substantive truth, domain hypotheses, model changes, and
production effects. The Catalog retains a dated, bounded reference only when a
real consumer or reproducibility obligation exists.

## Event-time semantics

- `eventAt`: when the underlying decision/event occurred, nullable if unknown.
- `reportedAt`: when the source publicly reported it (known for admitted packets).
- `dataAsOf`: the effective or observed period for the *current numeric claim*.
- `revisedAt`: optional corrected publication date; never inferred.
- `checkedAt`: source assessment date; **not** an event/publication date.
- `baseline.dataAsOf`: earlier observation/decision date. The baseline needs
  a separately traceable primary or equivalent source, not a yesterday fantasy.

R1 uses calendar-day precision deliberately: no fabricated hours/minutes. In-domain
owners may require a stronger timezone-aware precision before using intraday claims.

## Contract and operational path

A bounded original or official observation is recorded with its issuer, specific
support scope, historical baseline, exact typed value, status and proposed consumer
impact. `external_world_delta.py` checks shape, units, arithmetic and chronology
using Python stdlib `Decimal`, then emits a deterministic projection. This
program **does not fetch/verify source contents** and does not establish that
the source is correct. Evidence quality and counterevidence remain an independent
Research or domain-owner responsibility.

```sh
python3 catalogs/knowledge/scripts/external_world_delta.py \
  catalogs/knowledge/observations/boe-rate-20261105.json
python3 -m unittest discover -s catalogs/knowledge/tests -p 'test_*.py' -v
```

The sourced example is the Bank of England MPC policy-rate change:
official 17 Sep 2026 meeting summary (3.75%) → official 5 Nov 2026
publication concerning the meeting ending 4 Nov (4.00%). The resulting
numeric delta is **+0.25 percentage points / +25 basis points**. This is
a real historical-to-new public state observation, not evidence that a
specific Capital consumer, forecast, or portfolio was updated.

Only after a named domain owner supplies a concrete *existing* consumer reference,
an independently qualified evidence packet, a frozen baseline, and an accepted
change/verifier can the impact be recognized as a model revision. A new external
observation by itself is never a production release or permission grant.

## Intended next real consumers and non-claims

- External World / Capital: decide whether the new rate matters to a preexisting
  named macro assumption and perform a real source-bound consumer readback.
- Research: design competing causal hypotheses and negative-control studies when
  effect claims (rather than simple rate changes) are made.
- Composition: use existing Cognitive Circuit/Successor contracts for any eventual
  proposed model or capability successor; mechanical closure is not domain approval.
- GitHub Radar: keep the capability lane source/version-specific; a repository release
  may become an observation, but must not auto-install or promote a LEGO.

The catalog does not assert consumer acceptance, issuer authenticity from a URL,
independent verification, investment benefit, or autonomous live trading.
