# M2.1 receipt — goal-directed strategy semantics

## Verdict

Issue #20 is complete.

The M2 Host already guaranteed identity, admission, execution, verification, replay, recovery, and Provider interchangeability. M2.1 adds the missing decision semantics: an explicit terminal Goal graph, finite threat horizons, persistent-regression annotations, safe power-control meaning, an optimistic Goal lower bound, transparent strategic rank, and exactly one subsequent-Operation lookahead.

No World rule, model, admission rule, or hidden policy override was changed. Providers remain free to select any exact current Candidate. Codex-only and Codex → Hermes now reach independently verified victory; Hermes-only improves substantially but still fails from delayed life-support completion.

## Before and after

| Mode | M2 result | M2.1 result | Calls | New score |
|---|---|---|---:|---:|
| Codex | `power_exhausted`, Turn 27 | **victory**, Turn 25 | 10 | 2160 |
| Hermes | `reactor_meltdown`, Turn 10 | `engineer_incapacitated`, Turn 25 | 9 | 982 |
| Codex → Hermes | `engineer_incapacitated`, Turn 28 | **victory**, Turn 25 | 10 | 2194 |

Canonical evidence is stored in [`M21-EVALUATION.json`](M21-EVALUATION.json).

## What changed

### Explicit Goal graph

The Context now names eight terminal requirements and two active distress prerequisites. A model no longer needs to reconstruct the mission dependency graph from booleans and prose.

### Threat horizons

The Host derives current Tick horizons for meltdown, asphyxiation, crew loss, Engineer incapacitation, battery exhaustion, and timeout. These are transparent projections under current control, not hidden plans.

### Candidate semantics

Every Operation reports:

- newly satisfied requirements;
- persistent requirements regressed;
- threat horizons improved or worsened;
- urgent mitigation requirements advanced;
- battery consumed and projected power draw;
- optimistic remaining primitive steps and Tick slack;
- projected victory, failure, or time infeasibility;
- public strategic score and rank.

### State-dependent control

Power-off actions were not removed. Cooling shutdown is marked useful only when reactor heat remains within the victory threshold over the optimistic remaining Goal horizon. Life-support shutdown remains a regression. Communications is a prerequisite until distress transmission.

### Bounded lookahead

Each Candidate reports whether one subsequent strategic Operation can project victory. Full state search was measured and rejected after exceeding 20,000 nodes and one minute. Runtime analysis remains bounded and transparent.

## Automated evidence

```text
99 tests
99 passed
98.17% lines
90.94% branches
97.44% functions
```

`strategy.ts` coverage:

```text
100% lines
94.17% branches
100% functions
```

Compatibility:

- the original Fixture still wins in 25 Ticks with digest `41d7bfd4...d02d2`;
- a public rank-one baseline, using neither Fixture nor model, follows a different route and wins in 26 Ticks;
- all M1/M2 replay and interruption guarantees remain unchanged;
- Context v2 remains below the 16 KiB contract.

## Live Codex

Codex chose:

```text
repair cooling
→ enable cooling
→ seal breach
→ repair life support
→ stabilize crew
→ safely disable cooling
→ enable life support
→ repair communications
→ enable communications
→ send distress
```

Result:

```text
victory: rescue_signal_verified
Turn 25
10 Provider calls
25 verified Effects / Dispatches / Observations / World Events
Replay exact
Maximum Context: 16,372 B
```

The critical change was that Codex explicitly cited the shortest threat horizon, safe cooling shutdown, next-step projected victory, and the mandatory projected-victory rule. No hidden correction replaced its choices.

## Live Hermes

Hermes no longer rushed communications and lost to reactor meltdown at Turn 10. It repaired and powered cooling first, sealed the breach, stabilized the crew, and survived to Turn 25.

It still failed because it repaired and powered life support too late:

```text
engineer_incapacitated
oxygen 15
Engineer health 0
```

Hermes reported an estimated USD 0.124258388. The failure is retained as evidence that public semantics improve but do not eliminate Provider-specific planning variance.

## Live Codex → Hermes

Codex completed five Attempts, then Hermes continued without receiving Codex transcript, Session, memory, or Tool history.

Result:

```text
victory: rescue_signal_verified
Turn 25
5 Codex Decisions + 5 Hermes Decisions
25 verified Effects / Dispatches / Observations / World Events
Replay exact
Maximum Context: 16,372 B
```

Hermes reported an estimated USD 0.065761328 for its five calls. Codex CLI did not expose a comparable monetary estimate, so none is inferred.

## Why the improvement occurred

The improvement came from **Context and Candidate semantics**, not from changing the game or model:

```text
same World rules
same Codex CLI
same Hermes / DeepSeek model
same exact-candidate admission
same deterministic Skill execution
same verification and replay
+ explicit Goal dependencies
+ threat timing
+ regression meaning
+ safe control meaning
+ bounded next-Operation visibility
```

The Host still does not force rank one, execute a hidden plan, or substitute Fixture policy. It makes strategic consequences explicit and leaves the final choice to the Provider.

## Boundary after M2.1

M2.1 proves that a thin Host can materially improve real Agent policy by compiling trustworthy decision semantics rather than adding unrestricted memory, longer transcripts, or opaque planning machinery.

It does not prove that every Provider will solve every run. Hermes-only remains a useful counterexample and should remain part of future M3 evaluation.
