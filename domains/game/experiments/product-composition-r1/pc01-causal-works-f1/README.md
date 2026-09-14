# PC01-F1 — Causal Works interactive carrier

PC01-F1 is the smallest player-facing Godot carrier for the PC01 composition that survived F0. It intentionally **reuses F0's current `design.json` at runtime** rather than creating a new mechanism definition.

The one-screen carrier exposes:

- the visible `SOURCE → PROCESS → ROUTE → OUTPUT` system;
- one authored architecture emphasis that persists between cycles;
- optional `process` or `route` diagnostics at the F0 diagnostic cost;
- an explicit `INSPECT → architecture revision → COMMIT & RUN` chronology so FAULT/OK can change the same-cycle choice while the realized cause stays hidden;
- pre-commit persistence consequence as `KEEP 0` or `SWITCH -8`;
- three cycles whose symptom/context and objective/rule framing change;
- a frozen aftermath view followed by explicit `NEXT CYCLE`, so the resolved causal chain is read before the next rule/objective appears;
- a readable three-cycle replay ledger.

Interactive runs sample the hidden cause from each cycle's exact F0 `causePrior`. `INSPECT` locks the chosen diagnostic, pays the diagnostic cost, and reveals only `FAULT` or `OK`; `OK` remains ambiguous between at least two causes. Architecture stays editable after inspection. `COMMIT & RUN` then resolves the selected architecture, persistence/switch cost, hidden cause, reward, and aftermath. The built architecture is carried causally into the next cycle. Mechanical acceptance forces known causes only inside the inspect/commit test path so the evidence is reproducible without changing interactive semantics.

## Run interactively

```bash
godot --path experiments/product-composition-r1/pc01-causal-works-f1/godot
```

## Deterministic acceptance

```bash
godot --headless --path experiments/product-composition-r1/pc01-causal-works-f1/godot -- --acceptance
```

Acceptance does not rely only on labels or stored F0 verdicts. It directly recomputes the F0 dynamic policy from current `causePrior`, reward matrices, diagnostic cost, and switch cost; asserts diagnosis uplift, no-scan `process → route → source` revaluation, and an exact persistence-vs-zero-switch policy change; verifies prior sampling can reach multiple causes per cycle; then exercises the live two-stage inspect/commit carrier, causal persistence, frozen aftermath gate, and replay fields.

## Boundary

`mechanismLibraryModified=false`. PC01-F1 is an implementation carrier only. Mechanical acceptance does **not** establish Human enjoyment, comprehension, satisfaction, retention, market demand, or G0 admission.
