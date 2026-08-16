---
schema_version: 1
id: game.g-series.selection
title: Ordivon Game G5 Selection
type: decision
profile: product
lifecycle: active
source_role: canonical
visibility: public
owners:
  - ordivon-game
audience:
  - designer
  - builder
  - agent
  - producer
updated: 2026-08-16
summary: First G5 select/kill decision from the post-dogfood Concept Lab. Casefile advances as the G6 candidate because its deduction loop survives blind play; Last Light is deferred; Echo Hunt is rejected as an Agent-cognition direction; Station Zero remains a reference baseline.
evidence_status: verified
readiness: READY
applies_to:
  - ordivon-game
related:
  - game.g-series.reset
  - game.g-series.product-search
---
# Ordivon Game G5 Selection

## Evidence boundary

This selection uses:

- direct browser inspection of every Concept Lab treatment;
- deterministic autonomy-vs-cheap-baseline E2E;
- two rounds of fresh-agent blind play using `deepseek-v4-flash` with only player-visible state and currently legal actions;
- post-session fresh-agent understanding/confusion/replay self-report;
- deletion pressure and expected production burden.

It does **not** establish human fun, attachment, retention, market demand, willingness to pay, or commercial viability.

The fresh-agent evidence is deliberately weaker than human play evidence. Its job is to find structural/comprehension failures before more expensive production.

## Falsifier defects discovered before selection

The first blind-play round was not treated as product evidence until three prototype defects were corrected:

1. Casefile contained one trace-label/clue mismatch and evidence that was too close to a direct answer.
2. Last Light described relationship recovery more clearly than its food/progress cost, so the player repeatedly chose a misleadingly safe-looking action.
3. Echo Hunt allowed out-of-bounds directions into the legal browser action surface and originally allowed information-gathering `Listen` to become an immediate unavoidable death.

These defects were fixed locally and the relevant treatments were rerun. The corrections are evidence that a cheap prototype should absorb design falsification before architecture.

## Result

### SELECT — Casefile / Social Detective

Casefile advances as the only current **G6 candidate**.

Why:

- its player problem is naturally phrased without implementation nouns: investigate, decide what evidence matters, decide whom to trust, and commit an accusation before time expires;
- fresh blind play reached a correct accusation in both autonomy and fixed-testimony treatments;
- the player reported a coherent mental model of limited investigation, testimony, traces and accusation;
- current replay self-report was `0.6` in both treatments, higher than the other current concepts;
- uncertainty was experienced as tension/ambiguity rather than pure inability to operate the interface;
- the world-truth / observation / belief / testimony / accusation separation maps cleanly onto Ordivon's durable authority discipline while remaining invisible as engineering machinery to the player;
- one incident is cheap enough to author and falsify without a universal engine or high-fidelity production pipeline.

### Agent-cognition decision inside Casefile

Casefile's **game form** is selected. Expensive/live model cognition is **not** selected.

The blind matched treatment did not show a material player-value advantage for current motive-sensitive autonomy over the fixed testimony baseline: both treatments solved the same case and both reported `0.6` replay desire. Therefore G6 begins with a deterministic, inspectable witness policy over bounded knowledge/motive/memory.

Reopen model cognition only if a later player-facing failure demonstrates that cheaper policy cannot create the needed adaptive social behavior.

This is a critical G-Series result:

```text
select the game
!= select the expensive Agent implementation
```

### DEFER — Last Light / Persistent Companion

The fantasy remains valuable, but the current treatment does not isolate companion value. Fresh blind play repeatedly optimized the visibly safe relationship-recovery action until supplies collapsed. After cost legibility was improved, the same behavior persisted and the dominant learning was resource management rather than trust/attachment.

Current evidence therefore cannot tell whether companion autonomy creates attachment or merely friction.

Reopen after Casefile only if we can build a small treatment where a rational route necessarily creates a meaningful dependency/trust conflict without requiring production-quality writing, voice, animation or a campaign.

### REJECT AS AGENT-COGNITION DIRECTION — Echo Hunt / Adaptive Predator

Echo Hunt remains a plausible ordinary game form, but current evidence rejects it as a reason to invest in richer Agent cognition.

After fixing illegal boundary actions and the unfair Listen/death interaction, matched fresh blind play still produced effectively identical autonomy/baseline trajectories:

- both used Listen twice;
- both moved east then south;
- both were intercepted after four actions;
- both reported replay desire `0.4`;
- both described similar frustration/curiosity and the same information problem.

A deterministic adaptive policy is already the appropriate mechanism class until player evidence proves otherwise. No model-powered predator work is admitted.

### RETAIN AS REFERENCE — Station Zero

Station Zero remains the strongest reference implementation for delegated command, bounded cognition, deterministic consequence, persistence/recovery and replay. It is not selected for G6 and receives no new content-production authority from this decision.

## G6 admission

Casefile may now receive a bounded true-playable implementation with these constraints:

- server-authoritative hidden incident truth;
- player-visible observations and testimony never expose hidden truth directly;
- deterministic witness policy first;
- exact legal action surface generated by current case state;
- limited investigation time;
- explicit accusation commitment and terminal reconstruction;
- at least three bounded incidents or equivalent basic variation;
- short-session refresh/recovery;
- independent browser play without developer controls;
- no generic Game engine, NPC platform, dialogue framework or Agent provider layer.

## G6 exit remains unearned

Implementation success does not close G6. The candidate must still demonstrate that an independent player can understand and complete the intended loop without developer intervention and that gameplay findings dominate engineering failures.

Fresh-agent play may provide an early independent-comprehension probe. Human-specific fun, social interpretation, suspense and replay desire remain `UNKNOWN` until appropriate human play evidence exists.

## G7 / G8

Not admitted.

Do not start vertical-slice art/audio production or content scaling merely because Casefile wins this prototype comparison.
