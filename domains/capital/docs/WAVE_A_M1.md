# Wave A / M1 — Investment Loop

## Purpose

Validate the first clean-room vertical slice without legacy Market Capital code and without a trading runtime.

```text
CFA-informed IPS
  -> authoritative legal-entity reference data (GLEIF)
  -> Research E2E runtime / MLflow lineage
  -> deliberately boring validation portfolio construction
  -> deterministic target portfolio artifact
```

## Why equal weight

The first milestone tests architecture, provenance and constraint enforcement, not alpha. A simple public construction rule prevents strategy quality from being confused with system correctness.

## Acceptance

1. IPS validates against JSON Schema.
2. Each allowed symbol has one exact legal-name GLEIF record with registration status `ISSUED`.
3. Raw GLEIF responses are retained locally but not committed.
4. Normalized reference identities validate against schema.
5. Portfolio construction fails closed on missing authoritative identity.
6. Position cap, minimum cash and maximum gross exposure are enforced.
7. Target portfolio validates against schema.
8. Input/output SHA-256 digests are recorded.
9. The existing Research E2E Python environment executes the build.
10. MLflow records inputs, outputs, parameters and metrics.

No broker, order, LEAN, FIX session or external financial write occurs in M1.
