# Game Counterexample Synthesis R1

## Purpose

This document defines a thin **cross-Counterexample retrieval synthesis** over the source-grounded Design Counterexample Memory.

It answers a limited question:

> When a new composition or design hypothesis appears, which recurring historical failure structures are worth retrieving together so their assumptions and cheap discriminators can be attacked early?

It is **not a taxonomy, ontology, risk model, scorecard, anti-pattern catalog, development methodology, or design law**.

The machine source is `standards/game_counterexample_synthesis_r1.json`. Query it with:

```bash
pnpm knowledge:counterexample-themes -- --mechanism legacy-product-vision
pnpm knowledge:counterexample-themes -- --theme theme.authority-and-coordination-collision
pnpm knowledge:counterexample-themes -- --counterexample counterexample.thief.delayed-rewrite-can-be-as-risky-as-premature-rewrite
pnpm knowledge:counterexample-themes -- --q "local success"
```

## Retrieval semantics

R1 contains **8 deliberately overlapping, non-exhaustive themes**. A Counterexample may belong to several themes, and some valid Counterexamples belong to none.

Theme membership means only:

> These historical cases share enough structural resemblance that retrieving them together may expose a useful assumption, transfer boundary, or cheap discriminator.

Theme membership does **not** mean:

- the cases have the same cause;
- the same intervention should be used;
- one failure is more severe or more probable than another;
- the theme predicts failure;
- an unmatched case is unimportant;
- a matched novel design should be rejected.

A theme **cannot block or reject a novel combination, rank designs, mint recommendation authority, create Human evidence, or inherit evidence into a new composition**.

## R1 themes

| Theme | Retrieval question |
|---|---|
| Premature Commitment / Premise Drift | Did commitment arrive before the premise stabilized, or survive after the premise changed? |
| Authority / Coordination Collision | Are multiple actors or systems locally valid but colliding over a shared consequence or coordination boundary? |
| Local Success / Global Harm | Can a local win reverse over a larger product, time, population, loop, or planning horizon? |
| Legacy Coupling / Sunk Investment | Is current survival justified by present value, or by historical investment and compatibility surface? |
| Foundation / Context Mismatch | Does a competent borrowed or local foundation encode assumptions that do not fit the actual target interaction? |
| Hidden Operating / Integration Cost | What recurring staffing, integration, deployment, architecture, or population cost appears only after scaling/operation? |
| Proxy / Target Substitution | Is an easy-to-measure proxy silently replacing the actual product or behavior target? |
| Reopen / Reversibility / Rewrite | Is an old rejection, shipped state, near-complete state, or rewrite taboo being treated as more permanent than current evidence supports? |

These names are retrieval handles, not canonical categories. Future evidence may rename, split, merge, ignore, or delete them without changing the validity of the underlying Counterexamples.

## Why overlap is required

A single historical failure can expose several independent attack surfaces.

For example:

- Overwatch's long-lived PvE vision can be retrieved under **Premature Commitment / Premise Drift** and **Legacy Coupling / Sunk Investment**.
- Role Queue can appear under **Authority / Coordination Collision** and **Local Success / Global Harm** because it addressed one composition problem while exposing a population-flow bottleneck.
- Subnautica multiplayer can appear under **Foundation / Context Mismatch** and **Hidden Operating / Integration Cost** because a seemingly optional feature crossed architecture boundaries and carried schedule/implementation cost.

Forcing exactly one label would destroy useful retrieval context and turn a memory aid into a closed ontology.

## Retrieval path

```text
New mechanism / composition
        ↓
Mechanism Experience matches
        ↓
Counterexample matches
        ↓
Counterexample Theme matches
        ↓
retrieve several structurally related historical failures
        ↓
compare assumptions + contexts + transfer boundaries
        ↓
choose a cheap discriminator
        ↓
OPEN_EXPLORATION
```

The final disposition remains open unless some separate evidence/currentness/effect authority boundary applies. A synthesis match has no authority to change that disposition.

## Anti-collapse rules

1. **No exhaustiveness** — R1 intentionally leaves some Counterexamples unthemed.
2. **No exclusive membership** — overlap is expected and mechanically tested.
3. **No severity or probability score** — retrieval order is not design ranking.
4. **No inverse universalization** — repeated historical failure does not become a prohibition.
5. **No evidence inheritance** — member evidence does not prove the new composition will fail or succeed.
6. **No new domain authority** — source Counterexamples, Experiences and natural owners retain their existing evidence/authority boundaries.
7. **No framework promotion** — if the themes stop helping creative search, they may be renamed, recomposed or deleted without reopening Game semantic foundations.
