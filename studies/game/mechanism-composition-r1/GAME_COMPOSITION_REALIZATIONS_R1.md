# Game Composition Realizations — R1

Status: **ACTIVE EXECUTION LEDGER**
Observed: 2026-09-14

This ledger separates **search decisions** from **physical experiment realization**. `GAME_COMPOSITION_SEARCH_R2.md` remains the search snapshot; this file records what has actually been built and validated.

## CS2-03 — Upstream-Random Buildcraft

```text
Search state        ADMIT_WAVE_A
Physical apparatus  READY
Structural precheck PASS
Human evidence      UNOBSERVED
```

Canonical apparatus:

```text
repo      /root/projects/ordivon-game
revision  7abb5856ad32a86a16c5555b54642022c5c64329
path      experiments/composition-r2/cs2-03-upstream-random-buildcraft
```

Structural gate:

- 625 encounter sequences / 81 complete build paths;
- 17 distinct optimal signatures;
- largest optimal signature share: 34.9%;
- largest first-pick share: 56.2%;
- adaptive-vs-best-universal uplift: 13.2%;
- optimal-vs-immediate-greedy mean uplift: 19.1%;
- >2% global-over-greedy advantage in 86.6% of encounter sequences.

The next admissible step is a Human C0 session. No Human-value claim is currently admitted.

Machine-readable authority: `game-composition-realizations-r1.json`.
