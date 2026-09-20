# Causal Lag R3 — Stateful Run

Status: **STATEFUL SESSION MECHANICALLY GREEN / EXPERIMENTAL CANDIDATE / HUMAN VALUE UNOBSERVED**

R3 closes the main session-continuity gap left by the one-step Causal Lag Lab and the R2 Memory Run.

## What changed

R1 and R2 established a strong micro loop:

```text
observe
→ optionally diagnose
→ read future context
→ commit architecture
→ delayed execution
→ reveal cause/consequence
→ update history
```

R3 makes that loop one continuous game session instead of a sequence of mechanically separate questions.

### Architecture persistence

The architecture actually committed by the player becomes the built architecture in the next round.

```text
round N commit PROCESS
→ round N+1 built architecture = PROCESS
```

Switch cost therefore depends on the player's own prior action.

### Latent cause continuity

The execution cause at the end of one round becomes the current hidden cause of the next.

```text
round N execution cause = ROUTE
→ round N+1 current cause = ROUTE
```

History now describes the same evolving system rather than unrelated samples.

### Chained operating contexts

The four-round contract follows one explicit context chain:

```text
cycle 1 → cycle 2
cycle 2 → cycle 3
cycle 3 → cycle 1
cycle 1 → cycle 2
```

### Session contract

The run target is a game-level R3 parameter:

```text
4 rounds
target total = 320
initial built architecture = ROUTE
```

PC01 reward tables remain unchanged.

Every scan and architecture switch reduces the same session total. A run ends:

- **SUCCESS** when the four-round total reaches the contract target;
- **FAILURE** as soon as even perfect remaining rounds cannot mathematically reach the target.

The current deterministic witnesses are:

- coherent route-aligned run: total `400` → **SUCCESS**;
- two early wrong SOURCE commitments against a persistent ROUTE cause: total `115`, maximum recoverable `315` → **FAILURE**;
- route scan + switch to PROCESS on a PROCESS cause: first-round net `86`, then next round is built on PROCESS and starts from that resolved cause.

## Browser flow

The browser now contains an explicit:

```text
START CONTRACT
→ ROUND 1
→ ROUND 2
→ ROUND 3
→ ROUND 4
→ CONTRACT SECURED / CONTRACT LOST
```

The page exposes current signal, next-context forecast, built architecture, run history, contract total, remaining target and maximum recoverable total.

Before resolution it still does not expose the hidden run regime or future execution cause.

## Run

Mechanical acceptance:

```bash
pnpm eval:causal-lag:r3
```

Browser E2E:

```bash
pnpm e2e:causal-lag:r3
```

Manual play from repository root:

```bash
python -m http.server 8000
```

Then open:

```text
http://127.0.0.1:8000/experiments/product-composition-r1/causal-lag-session-r3/web/
```

## Core-game standing after R3

R3 materially closes:

- micro-loop continuity;
- session-state continuity;
- architecture persistence;
- latent-cause persistence;
- cumulative decision cost;
- start/run/end flow;
- explicit success/failure.

It does **not** yet establish a complete full-game content architecture. The next development work should expand depth through composition rather than inventing another kernel:

- content grammar and scenario variation;
- pressure/difficulty dimensions;
- pacing across a longer run/campaign shape;
- stronger expression/feedback and final presentation;
- production-ready content authoring/validation.

Knowledge progression is already a valid progression carrier; XP, loot, crafting or character power are not required merely to make the core complete.

## Evidence boundary

```text
productSelected=false
G0=false
humanOutcomeEstablished=false
Game Core changed=false
```

R3 demonstrates stateful-session mechanics only. It does not establish Human enjoyment, comprehension, retention, market value or product selection.
