# LEGO Regime-Shift Lens Prospective Validation R1

Date: 2026-09-18
Status: PRE-REGISTERED CANARY PLAN
Target lens: docs/LEGO_REGIME_SHIFT_DECISION_R1.md

## Goal

Test whether the new regime-shift lens adds decision-relevant information beyond the existing LEGO baseline without merely producing more vocabulary.

The lens passes only if it changes a test, observation plan, module boundary, or bounded decision before outcomes are known.

## Baseline

Baseline = existing LEGO Theory Layer R1 using project-native decomposition plus Systems Engineering / DSM / Feedback Control / STPA only as already applicable.

Treatment = baseline plus lego-regime-shift.

Do not retroactively edit the treatment questions after seeing the target outcome.

## Primary acceptance questions

For each domain:

1. Did the lens reveal a stock/flow divergence not explicit in baseline?
2. Did it identify a material buffer or delay that changes interpretation?
3. Did it identify a constraint migration that changes where work should be applied?
4. Did competing hypotheses prevent a premature single-story conclusion?
5. Did a falsifier/signpost become explicit?
6. Did the final action become more reversible, staged, or information-seeking?
7. Did any added concept fail to change a decision or test and therefore deserve deletion?

## Canary A — Agent Service

Question:
Is apparent improvement in agent capability still constrained mainly by model/tool capability, or has the dominant bottleneck migrated to coordination, trust boundaries, observation validity, recovery, or integration?

Pre-registered observations:
- current success/failure evidence by execution path;
- queue/backlog or deferred work where available;
- repeated failure classes;
- observation/authority boundary failures;
- time from failure detection to validated recovery;
- whether additional capability actually raises accepted end-to-end completion.

Competing hypotheses:
- H0: no material regime change; failures are ordinary implementation noise.
- H1: capability is still the dominant constraint.
- H2: bottleneck has migrated to orchestration/integration.
- H3: bottleneck has migrated to trust/observation boundaries.
- H4: resource limits dominate all of the above.

Decision test:
Would the lens move the next bounded slice away from adding raw capability toward a different constraint?

## Canary B — Research

Question:
As idea generation and agent execution become cheaper, has the bottleneck migrated from producing candidate analyses to evidence validity, independent verification, review bandwidth, or claim closure?

Pre-registered observations:
- ratio of generated candidate work to independently accepted work;
- rework caused by evidence or identity failures;
- human-review demand;
- unresolved claim-to-evidence dependencies;
- time spent generating versus validating;
- whether more agents increase accepted scientific throughput.

Competing hypotheses:
- H0: no migration; generation remains the main constraint.
- H1: evidence verification is now the main constraint.
- H2: human adjudication/review is the main constraint.
- H3: research-question quality/novelty remains the main constraint.
- H4: tooling/retrieval friction dominates.

Decision test:
Would the lens change resource allocation between generation, verification, review, and question selection?

## Canary C — Game

Question:
As mechanics/assets/combinations become easier to generate, has the bottleneck migrated from production to composition quality, playtesting, player feedback, evaluation, or selection?

Pre-registered observations:
- candidate mechanics/compositions generated;
- fraction reaching playable state;
- fraction surviving human/player canary;
- rework between generation and acceptance;
- evaluation latency;
- whether more generated variants improve accepted game quality.

Competing hypotheses:
- H0: production capacity remains the main constraint.
- H1: composition/integration is the bottleneck.
- H2: playtest/evaluation is the bottleneck.
- H3: player-feedback acquisition is the bottleneck.
- H4: selection criteria are unstable, causing Goodhart-like churn.

Decision test:
Would the lens cause us to stop increasing generation volume and instead improve evaluation or feedback?

## Cross-domain pass condition

PASS_FOR_R2 only if:
- at least two of three canaries expose a decision-relevant buffer/delay/constraint-migration fact not already explicit in baseline;
- at least one candidate concept is rejected or simplified, demonstrating anti-ontology pressure;
- no canary treats an early-warning signal as a forecast;
- every action recommendation is tied to a falsifier or signpost.

Otherwise:
- REVISE if useful but redundant/noisy;
- REJECT if it mainly produces post-hoc narratives.

## Non-claims

This plan does not claim that any listed hypothesis is currently true.
The canaries are prospective tests, not conclusions.


## Canary A result — Agent Service

Status: **PASS / DECISION-RELEVANT NEW INFORMATION**

Evidence:
- `knowledge/lessons/agent-service-regime-card-r1.md`
- `evidence/analysis/agent-service-regime-card-r1.json`

Observed incremental value beyond the frozen Wave-1 baseline:
- separated validated implementation stock from main-line/deployed capability flow;
- identified the live legacy Automation stack as a buffer masking the absence of deployed Agent Service;
- prevented stale 2026-09-13..16 ledger counts from being misused as current throughput;
- established a fresh current divergence: Browserless substrate healthy while provider admission is `CHALLENGE_GATED`;
- established that R14/current-main mergeability is currently clean, weakening "technical merge conflict" as the explanation for integration delay;
- changed the next bounded action from broad feature expansion to staged integration + E2E funnel measurement.

Competing-hypothesis outcome:
- H0 ordinary noise: weakened, not eliminated;
- H1 raw capability dominant: unknown and currently downstream of stronger observed gates;
- H2 orchestration/integration migration: supported candidate;
- H3 trust/observation migration: supported candidate;
- H4 resource limits dominant: not supported by this cut, not falsified.

Anti-ontology result:
- critical-transition statistics / critical-slowing-down / generic tipping-point thresholds were explicitly **not activated** because no justified continuous tipping-point model exists for this case.

Cross-domain standing:
- Canary A = PASS;
- Canary B Research = PENDING;
- Canary C Game = PENDING;
- R2 promotion remains blocked until the original cross-domain pass condition is satisfied.
