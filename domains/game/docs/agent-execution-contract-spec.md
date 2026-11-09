# Game Factory: LEGO-Constrained Agent Execution — Spec R1

Status: **implementation spec**, not a new execution authority. Scope: `domains/game/**`; dependent cross-Owner contracts are proposals until those Owners accept them.
SourceCut: `3b43977e682d8c7668f6371ffd998c7821e4312a`, Game tree `7157e18d3bee2765205687380953dfabf72688a0` (2026-11-09).
Natural owner: **Game**. Consumers: native Room Encounter episode runner, Game factory acceptance, packaged previews, ultimately real players.

## 1. Problem and desired result

The Game Factory already states that a real consumer, selected Godot/Bevy engine, actual composed action loop, native tests, source-bound package and consumer feedback govern work. Yet a fresh isolated Game checkout can invoke `mise run test:agent-episode` without first importing Godot Dialogue Manager resources. A previous audit observed GDScript class-resolution errors; manually importing then rerunning succeeded. That makes the native test contract dependent on unrecorded workspace history.

The larger failure mode is *semantic goal substitution*: an implementer can replace a consumer outcome with a planning artifact, framework, model-only PASS, test-count growth, or its own completion narrative. More prompts cannot establish independent domain truth.

**Outcome:** Game tasks bind product intent and G07–G11's existing R2.1 responsibilities to native, source-identified, independently observable consumer obligations. A model may change implementation, not redefine what evidence discharges the obligation. Reuse existing Owner tooling and packages; never create a second workflow/LEGO/verifier service.

## 2. Upstream methods adopted, not installed wholesale

| Source | Adopt exactly | Do not adopt mechanically |
| --- | --- | --- |
| Matt Pocock `to-spec`, `domain-modeling`, `implement-spec` | Synthesize existing intent and boundaries; spec separates requirements from implementation; tickets form a dependency graph; review against the original spec | A mandatory interview, new issue tracker, global glossary/ADR bureaucracy, or forced subagent fanout |
| ECC `intent-driven-development`, `contract-first` | AC identifiers with starting state/trigger/outcome/prohibited side effect/evidence; one canonical seam contract, real serialization test | ECC Stop hooks as Game success authority; mtime/regex proxy success; a second plugin/harness |
| Superpowers `writing-plans`, `test-driven-development`, `verification-before-completion` | Exact file/command/expected result, RED-GREEN-REFACTOR on behavior changes, fresh native verification before completion claims | A global mandatory workflow for every trivial fix, self-reported completion, CI bypass |
| Native providers | Godot `--headless --path ... --editor --import`, `mise` task composition; Game native tests/CI; Bevy/Cargo/Kani/Z3 with qualified scope | Alternative Godot importer or universal game renderer/simulator |

Authoritative references:
- https://github.com/mattpocock/skills/blob/main/skills/engineering/to-spec/SKILL.md
- https://github.com/mattpocock/skills/blob/main/skills/engineering/implement-spec/SKILL.md
- https://github.com/mattpocock/skills/blob/main/skills/engineering/domain-modeling/SKILL.md
- https://github.com/affaan-m/ECC
- https://github.com/obra/superpowers
- https://docs.godotengine.org/en/stable/tutorials/editor/command_line_tutorial.html

## 3. Domain vocabulary and authority

- **Product objective:** game behavior or player-visible artifact sought by the consumer. Only Game/product evidence can revise it.
- **LEGO:** goal-conditioned independently contractable responsibility, not a file/Skill/Tool/Agent.
- **R2.1 admitted contract:** typed `(I,O,S,pre,post,inv,eff,c,epsilon,prov,unfold)`; use the effective existing Game G07–G11 contracts. An empty/missing G01–G06 R2.1 coordinate is not magically filled by this spec.
- **Verification obligation:** bounded condition, source scope and evidence owned by the actual verifier. Existing Composition `verification-obligation-set-v1` is *non-authoritative* and does not execute checks.
- **Mechanical result:** Runtime Job/process/test exit and receipts, not product truth.
- **Domain acceptance:** current Game consumer-observed effect with the specified scope. Automated Game PASS is not player delight or Windows physical gameplay.
- **UNKNOWN:** genuinely missing evidence, not FAIL or success. A blocked graphical smoke is recorded as ENV_BLOCKED, never promoted from binary build success to graphical acceptance.

Responsibility split: Game specifies domain properties and its native test entry. Composition can deterministically project requirements. Runtime runs and records operations. Harness can orchestrate a chosen agent. GitHub native CI supplies independent checkout and check status. Artifact/Distribution publish binaries. Neither Composition nor Harness decides gameplay quality.

## 4. Effective R2.1 contract — G11 cold-start refinement

This is an **instance/refinement of existing G11**, not new LEGO G12. Source carrier: `planning/lego-plan-r1.json` G11 `recursiveLegoR21`; actual implementation `examples/room-encounter/agent_episode_acceptance.py` and `mise.toml`.

| Coordinate | Task-local realization |
| --- | --- |
| I | Immutable source tree, pinned Godot CLI, Room Encounter scenes/resources/addons; zero existing `.godot` cache; bounded 0–64 action sequence |
| O | Native schema-v2 episode receipts and Game test verdict; explicit nonzero/FAIL on import/script/parse failure |
| S | One native scene and its EncounterRules state per process; editor import cache is an *environmental prerequisite*, not hidden task history |
| pre | Godot executable and source available; importer may be run at test entry; native action limits remain unchanged |
| post | Running the documented `mise run test:agent-episode` from a clean checkout imports required resources then executes unchanged native episodes and checks receipt semantics |
| inv | EncounterRules owns combat; UI-only default vs debug opt-in preserved; no second simulator; no success inferred from plain exit=0 when script errors exist |
| eff | Godot editor import into ignored local cache, headless native scene effects, stdout/exit; no player-visible new gameplay effects |
| c | Additional bounded editor import on test invocation; actual wall-clock/resource cost is unmeasured |
| epsilon | Interactive hardware player experience and graphical rendering remain UNKNOWN; import+episode tests do not resolve those properties |
| prov | Game Git source cut, Godot pin in Game `mise.toml`, native test transcript, upstream Godot CLI docs |
| unfold | `mise.toml`, `agent_episode_acceptance.py`, `agent_episode.gd`, Dialogue Manager addon, Game native CI |

The actual external contract is one command, not a private preparatory ritual:
`cd domains/game && mise run test:agent-episode`.

### Contract refinement obligations

Let `C` be a fresh checkout with no Godot import cache, `I(C)` the native Godot import, `R(C)` the real episode runner, `E` a source-identifiable native test receipt.

- **G11-AC-001 (required):** Given `C`, invoking the documented native test performs the necessary upstream import and then produces the correct `GAME_AGENT_EPISODE_PASS` receipt. Verification: delete only ignored generated `.godot` within an isolated disposable Game workspace, then run the native entry.
- **G11-AC-002 (required):** If import cannot complete, the native test fails; no episode PASS may be emitted from stale resources. Verification: inspect strict nonzero exit propagation and independent CI run.
- **G11-AC-003 (required):** Default player observation does not expose debug state; invalid/illegal actions do not fabricate state changes; actual three-room terminal victory remains. Verification: existing 19 real native episodes, repeat and negative controls.
- **G11-AC-004 (required):** Existing native `factory:validate:godot` and Game's bounded quality checks continue to use the same one entry. Verification: native Game task and required CI.
- **G11-AC-005 (required):** Reporting distinguishes source modified, tests run, Git integrated and artifact consumed; the model cannot independently assign Game/domain completion. Verification: inspect actual command receipts and CI status.

Formal notation (scope-limited, not a claimed theorem):
```text
pre(C) := clean_checkout(C) ∧ Godot_4_7_2_available(C)
post(C) := imported(C) ∧ native_episode_result(C) = PASS
                ∧ receipt_has_real_Game_action_semantics(C)

Verified(G11-AC-001, C, E) :=
    native_owner_runner_on(C) = PASS ∧ evidence_binds_source(E,C)

For this task, "DONE" may be claimed only after every required AC is
discharged in its stated scope. Mechanically executed != domain accepted.
```
The stronger `DONE -> verified` safety statement holds only for a consumer that actually uses this evidence predicate; this document alone does not enforce a global scheduler invariant.

## 5. Product-level contract and composition boundaries

For each *consequential* Game product work unit, declare only the decision-relevant facts:

1. **Product/consumer:** target player action loop and platform; actual artifact expected.
2. **SourceCut:** exact Git revision, toolchain and external assets/licensing.
3. **Provider selection:** DELETE unconsumed custom work → REUSE mature native source → COMPOSE; custom glue only for a witnessed missing consumer contract.
4. **Existing LEGO responsibility:** G07 for Bevy product rules and ECS, G11 for Room action/observation, or the matching Game owner contract. Do not create a LEGO for each task/file.
5. **Obligations:** a minimal set of observable whole-composition properties, scoped negative cases, independent verifier owner, admitted evidence and OPEN/UNKNOWN conditions.
6. **Verdict:** real owner/native result and consumer evidence; no model-only PASS and no silent weakening of the goal.

For complex cross-owner tasks, reuse Composition's `cognitive-circuit-manifest-v1` and `verification-obligation-set-v1`. This spec does not add a second schema. They establish mechanically checkable bindings, **not** domain acceptance. For single native Game repair, direct native task/CI is the simpler higher-seam contract and suffices.

No global mandatory state machine is required: Host Work tracks actual work if needed; commits, tests and CI check runs are existing receipts.

## 6. Acceptance hierarchy and prohibited closure

```text
specified Game outcome
  -> source/consumer chosen
  -> real native Game implementation
  -> Game test or package check with exact source
  -> CI independent clean checkout, when merge/release scope requires it
  -> actual product delivery and player readback, when claimed
```

Do not infer rightward acceptance from leftward activity alone. Explicitly reject as completion:
- a spec/README/Skill replacement when the task is code repair;
- adding Kani/Z3 properties of a disconnected model to resolve real graphical launch failure;
- source-only or cargo test PASS advertised as physical platform play;
- skipping/rewriting away the assertion that witnesses the original defect;
- another general workflow/harness/cache/LEGO registry built for one native importer problem;
- treating a historical successful build as evidence of the current SourceCut.

## 7. Scope and execution sequence

**In:** Game-native G11 cold start, exact R2.1 refinement, one source-bound acceptance entry, planned cross-owner natural acceptance handoffs, terminal proof/evidence semantics, independent CI check on the actual change.

**Out:** Weak-model comparisons, prompts-only training, universal Ordivon validator, retrofitting all G01–G06 into invented R2.1 contract text, new game framework, forced prior approval for ordinary code edits, production-money effects, claims of human play evidence.

1. **Slice A:** reproduce missing import in clean Game checkout; fix native `mise` test entry via official Godot import; re-run native G11 and relevant pipeline tasks.
2. **Slice B:** tie assertions and test evidence to the existing G11 R2.1 responsibility and native factory entry, updating only Game docs/tests that have real consumers; preserve checks in CI.
3. **Slice C:** when a concrete cross-owner producer/consumer needs it, project requirements via existing Composition obligation schema; no cross-owner implementation until the particular owner contract is accepted.
4. **Slice D:** real product deliveries and player evidence remain independent from mechanical Game test acceptance.

See `agent-execution-implementation-plan.md` for exact file paths, commands and acceptance.

## 8. Genuine stop condition

Ship the smallest native change that satisfies G11-AC-001 through AC-004 and report the actual merge/CI state of AC-005. Do not extend the project to method orchestration, baseline model comparison, speculative verification infrastructure or repeated skill studies.
