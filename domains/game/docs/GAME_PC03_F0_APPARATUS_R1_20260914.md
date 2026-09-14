# PC03-F0 Loop Cartographer — Interactive Falsifier R1

Status: **CANDIDATE MECHANICALLY GREEN / INDEPENDENT EXACT-COMMIT REREVIEW PENDING / HUMAN CLAIMS UNOBSERVED / PRODUCT SELECTION FALSE / G0 FALSE**

Host Task: `task:game-pc03-f0-20260914`

Implementation path: original A01 occurrence plus controller recovery implementation after provider rate limiting; independent A02/A03/A04 reviewers remain read-only and their frozen contracts remain binding.

Base Game revision: `4fda7afedf36b9b915780c9317068609eca28025`

Runtime workspace: `ws-pc03f0-a01-r1`

## Carrier

The carrier is an interactive five-region out-and-return loop under `experiments/pc03-f0/web/`.

Player verbs remain exactly the PGP-A grammar: left/right plus jump. PC03 and PGP-A now consume the same extracted movement kernel at `experiments/pre-g0/web/pgp-a-kernel.js`:

- acceleration `0.55`;
- damping `0.82`;
- horizontal cap `5`;
- grounded jump impulse `-9.5`;
- gravity `0.48`;
- vertical cap `12`;
- avatar `24x32`.

The rejected pre-candidate rail implementation is not retained: there is no `railCarry`, boosted `-10.8` jump, forced `7.4` horizontal speed, or floor-speed clamp.

The compact loop is Hub → Fork → Gate A → Gate B → Far Turn → Gate B → Gate A → Fork revisit → Hub. The safe line and demanding line exist in the same World from the first frame; completion requires an in-run turn and return to the Hub rather than a terminal teleport/reset.

## Stable traversal rule

The stable rule is `late-edge-jump-v1`.

It is not a new movement ability. Under the unchanged PGP-A movement law, an ordinary grounded jump made sufficiently near a departure edge can preserve enough existing horizontal motion to clear a bounded gap. The same relation is mechanically useful at two physical gaps and in both outbound and return directions.

Knowledge is external to World authority. There is no inventory item, quest state, `knowledgeUnlocked`, `hasKey`, route-open flag, collision swap, platform spawn, or post-discovery timing-law change. The invariant serialized World/rule/control configuration is identical for uninformed and informed policy witnesses.

The initial UI gives only non-answer visual/structural cues. It does not state the exact causal takeoff rule or identify an optimal route.

## Deterministic mechanical witnesses

Current acceptance witness is from Runtime Job `job-01a0a0b7-8d93-74c2-a003-ca75dfc86aae`, a six-step candidate acceptance plan that completed successfully.

Observed deterministic outcomes:

| witness | route | outcome | frames | stable-rule uses | failures |
| --- | --- | --- | ---: | ---: | ---: |
| uninformed bounded baseline | safe | complete out-and-return loop | 733 | 0 | 0 |
| informed, timing-insensitive | fast | demanding attempt fails + immediate retry state | 130 | 0 | 1 |
| informed, timing-aware | fast | complete out-and-return loop | 565 | 4 | 0 |

The informed timing-aware path uses the same rule at:

1. Gate A outbound;
2. Gate B outbound;
3. Gate B return;
4. Gate A return.

This establishes only the bounded mechanical distinctions required by PC03-F0:

- an informed policy chooses a materially different later route than the uninformed baseline;
- knowing the demanding route is not sufficient when execution timing ignores the stable relation;
- timing-aware execution completes the demanding loop under the unchanged PGP-A movement law;
- the same stable relation matters at two distinct physical gaps and on the return path;
- the demanding loop is mechanically shorter than the legitimate safe loop (`565 < 733` frames);
- both policies run against the exact same serialized World/rule/control invariant;
- the demanding shortcut is physically available from pristine state; the successful witness completes on attempt 1 with no unlock/setup state;
- failure produces bounded immediate retry/reset behavior without changing the stable rule.

## Acceptance and regression evidence

Runtime Job `job-01a0a0b7-8d93-74c2-a003-ca75dfc86aae` completed all six steps with exit `0`:

1. PC03 browser e2e — PASS;
2. Pre-G0 / PGP-A browser regression — PASS after extracting the shared kernel;
3. TypeScript typecheck — PASS;
4. JavaScript web syntax sweep — PASS;
5. repository tests — PASS, **435/435**;
6. static contract gates — PASS.

Static gates exclude authoritative knowledge/progression names and the rejected rail-boost mechanics from the PC03 carrier. `node_modules` is workspace-only ignored dependency material and is not part of the candidate commit.

## Independent-review boundary

Mechanical acceptance by the implementation path is not independent adjudication. A02 Knowledge, A03 Embodied Control, and A04 Destroyer must rereview one exact candidate commit before main integration.

A valid independent rereview must continue to require:

- shared unchanged PGP-A movement law;
- no authoritative knowledge/progression gate;
- pristine physical fast-route availability;
- identical World/rule/control invariant across matched policies;
- genuine out-and-return loop/revisit topology;
- informed timing-insensitive failure versus timing-aware success;
- legitimate safe line;
- same rule useful at least twice;
- no answer-giving initial instruction;
- no reinterpretation of historical T05 negative evidence;
- no automated upgrade to Human or G0 claims.

## Scope boundary

```text
mechanismLibraryModified = false
runtimeAgentProfile       = none
Human mastery             = UNOBSERVED
Human flow                = UNOBSERVED
understood discovery      = UNOBSERVED
voluntary retry           = UNOBSERVED
enjoyment                  = UNOBSERVED
market claim               = UNOBSERVED
productSelected            = false
G0                         = false
```

This is a bounded whole-composition falsifier. Mechanical survival, even after independent rereview, only returns PC03 to the post-F0 composition comparison; it does not select PC03 as the product and does not repair or revive the failed historical T05 product thesis.
