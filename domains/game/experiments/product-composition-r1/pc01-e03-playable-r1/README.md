# PC01 + E03 R1 — Causal Lag Lab

Status: **MECHANICALLY GREEN / HUMAN CLAIMS UNOBSERVED / productSelected=false / G0=false**

This is the first bounded playable integration of the only survivor from Whole-Product Recomposition R1: `PC01+E03@R03-coupling`.

## What the carrier tests

The carrier makes the R03 coupling explicit rather than pretending it already existed in PC01:

```text
current ambiguous failure
+ optional bounded diagnostic
+ hidden cause persists for one command-lag step
+ next operating context is visible before commitment
+ architecture chosen now executes under that next context
```

The player sees the current signal and the next execution context, may inspect `process` or `route`, receives only `FAULT` or `OK`, then commits `SOURCE`, `PROCESS`, or `ROUTE`. The hidden cause is not revealed until delayed execution resolves.

Two fixed one-step transitions are exposed:

- `route-shift`: cycle 1 → cycle 2 with an existing `ROUTE` build;
- `source-rule`: cycle 2 → cycle 3 with no previous architecture.

The page does not disclose the mechanically optimal diagnostic or action mapping.

## Mechanical falsifiers

The acceptance keeps two independent attacks live:

1. **forecast ablation** — a policy optimized only for the current context is evaluated under the actual execution context and must be worse than the forecast-aware policy in both scenarios;
2. **cause-persistence ablation** — when the execution cause is made independent of the inspected current cause while keeping the same marginal distribution, diagnosis value must collapse and the best policy must choose no scan.

Current deterministic receipt:

- route-shift interactive trace: net `86`;
- source-rule interactive trace: net `94`;
- non-persistent stale-inspection trace: net `56`;
- both scenario witnesses pass.

## Run

Mechanical acceptance:

```bash
pnpm eval:pc01-e03:r1
```

Browser E2E:

```bash
pnpm e2e:pc01-e03:r1
```

Manual play from the repository root:

```bash
python -m http.server 8000
```

Then open:

```text
http://127.0.0.1:8000/experiments/product-composition-r1/pc01-e03-playable-r1/web/
```

## Evidence boundary

This carrier establishes only that the explicit R03 coupling can be expressed as a compact player-facing mechanical loop and that both forecastability and cause persistence matter to the bounded policy result.

It does **not** establish Human comprehension, enjoyment, planning value, voluntary replay, retention, market demand, product selection, or G0 admission.

```text
productSelected=false
G0=false
Human outcome=UNOBSERVED
Game Core changed=false
```
