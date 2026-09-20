# PC01 + E03 R2 — Causal Lag Lab · Memory Run

Status: **MECHANICALLY GREEN / HUMAN LEARNING UNOBSERVED / productSelected=false / G0=false**

R2 extends the mechanically green one-step Causal Lag Lab into a bounded four-round run.

## Core question

R1 proved that diagnosis has value when the hidden cause persists through the command lag. R2 asks a different question:

> Can past resolved cause transitions change what information is worth buying in a later otherwise-identical decision?

The run contains one hidden operating regime chosen at run start:

- STABLE: cause persistence 0.9;
- VOLATILE: cause persistence 0.2.

The player never sees those labels, probabilities, posterior beliefs, thresholds, expected values or an optimal policy.

The player sees only what the world legitimately revealed after earlier delayed resolutions:

```text
ROUND 1  PROCESS → PROCESS  PERSISTED
ROUND 2  ROUTE   → SOURCE   CHANGED
...
```

## Mechanical result

With an equal prior over the two hidden regimes:

- no history implies predictive persistence 0.55 and the route-shift oracle chooses **NO SCAN**;
- one observed `PROCESS → PROCESS` transition moves the mechanical oracle to predictive persistence about 0.6191 and flips the later route-shift policy to **ROUTE SCAN**;
- one observed `PROCESS → ROUTE` transition moves it to about 0.2778 and the later route-shift policy remains **NO SCAN**;
- a history-blind control stays at 0.55 for both histories and cannot distinguish them.

The compared later decision has the same current context, execution forecast and previous architecture. Only the resolved history differs.

Therefore R2 mechanically establishes:

```text
resolved history
→ updated hidden-process belief in the oracle
→ changed value of current information
→ changed later diagnostic policy
```

It does not establish that a Human player performs this update.

## Player-facing loop

```text
OBSERVE current signal
→ READ prior transition history
→ optionally SCAN
→ inspect next-context FORECAST
→ COMMIT architecture
→ wait one context shift
→ resolve and reveal source cause → execution cause
→ append that transition to SYSTEM MEMORY
→ next round
```

The browser never exposes the run-level regime or Bayesian oracle.

## Run

Mechanical acceptance:

```bash
pnpm eval:pc01-e03:r2
```

Browser E2E:

```bash
pnpm e2e:pc01-e03:r2
```

Manual play from repository root:

```bash
python -m http.server 8000
```

Then open:

```text
http://127.0.0.1:8000/experiments/product-composition-r1/pc01-e03-multiround-r2/web/
```

## Evidence boundary

R2 establishes history-sensitive mechanics only.

```text
productSelected=false
G0=false
humanOutcomeEstablished=false
humanLearningEstablished=false
Game Core changed=false
```

A future Human canary would still need to test separately whether a fresh player notices the transition history, forms a useful model, changes decisions because of it, and finds that process understandable or worthwhile.
