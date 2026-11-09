# Game Factory: LEGO-Constrained Agent Execution — Spec R1.1

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
- **R2.1 contract admission:** a declared/admitted responsibility requires a typed eleven-coordinate contract. Existing G07–G11 carry eleven named coordinates, but textual cost/approximation/provenance fields are NOT machine-checked formal types or implementation proofs. Missing G01–G06 coordinates must not be invented.
- **Verification obligation:** bounded condition, source scope and evidence owned by the actual verifier. Existing Composition `verification-obligation-set-v1` is *non-authoritative* and does not execute checks.
- **Mechanical result:** Runtime Job/process/test exit and receipts, not product truth.
- **Domain acceptance:** current Game consumer-observed effect with the specified scope. Automated Game PASS is not player delight or Windows physical gameplay.
- **UNKNOWN:** genuinely missing evidence, not FAIL or success. A blocked graphical smoke is recorded as ENV_BLOCKED, never promoted from binary build success to graphical acceptance.

Responsibility split: Game specifies domain properties and its native test entry. Composition can deterministically project requirements. Runtime runs and records operations. Harness can orchestrate a chosen agent. GitHub native CI supplies independent checkout and check status. Artifact/Distribution publish binaries. Neither Composition nor Harness decides gameplay quality.

## 4. Effective R2.1 contract — G11 cold-start refinement

This is a **task-local proposed refinement with explicit proof duties against existing G11**, not new LEGO G12. Source carrier: `planning/lego-plan-r1.json` G11 `recursiveLegoR21`; actual implementation `examples/room-encounter/agent_episode_acceptance.py` and `mise.toml`.

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
2. **Slice B:** tie assertions and test evidence to the existing G11 R2.1 responsibility and native factory entry, updating only Game docs/tests that have real consumers; verify the independent `native-g11-contract` GitHub PR job in the existing `.github/workflows/game-factory.yml` on a clean checkout. The pre-existing push-to-main preview packaging remains distinct.
3. **Slice C:** when a concrete cross-owner producer/consumer needs it, project requirements via existing Composition obligation schema; no cross-owner implementation until the particular owner contract is accepted.
4. **Slice D:** real product deliveries and player evidence remain independent from mechanical Game test acceptance.

See `agent-execution-implementation-plan.md` for exact file paths, commands and acceptance.

## 8. Genuine stop condition

Ship the smallest native change that satisfies G11-AC-001 through AC-004 and report the actual merge/CI state of AC-005. Do not extend the project to method orchestration, baseline model comparison, speculative verification infrastructure or repeated skill studies.

## 9. Formal foundations R1.1 — adopted theories and their exact scope

This section refines the engineering meaning of the existing Game G11 responsibility; it creates **no additional LEGO, evaluator or global workflow**. The chosen implementation seam remains the real Godot episode entry, and the acceptance relation remains Game-owned. Explicitly avoid weak-model trials and nonconsumer toy verification.

### F1. Assume–guarantee contracts (Benveniste, Pacti, interface automata)

A behavioral component contract is represented by (A,G) over a typed external alphabet and environment. In a closed observation scope:

~~~text
  A : accepted environment histories / states
  G : guaranteed histories / states conditional on A

  component satisfies (A,G)
    iff all concrete observable behaviors under A satisfy G.
~~~

Pacti offers mature, algebraic assume–guarantee composition and incompatibility diagnostics; invoke it only for a real symbolic contract with representable variables, not as a compulsory Game dependency. For a producer P feeding consumer Q, do not compose on matching field names alone:

- P's outputs are semantically compatible with Q's inputs and protocol order.
- Under the composed environment, P's guarantee must establish Q's assumption.
- Composition preserves effect/authority and current source qualifications.
- If those premises are UNKNOWN, **composition is unproved**, not FALSE.

For behavioral substitution, the candidate should not strengthen required environmental assumptions or weaken guaranteed observations relative to the old contract under the selected refinement relation. Interface Automata (de Alfaro/Henzinger, FSE 2001) explicitly models temporal input assumptions and output guarantees. The fact that two JSON receipts share a schema does not make their protocols substitutable.

**Game G11 seam:** Godot owns scene import, signals, Rule admissions and final state; Python owns launch and inspection, not rules. The required ordering is import → instantiate real scene → accepted actions/Signals → one receipt → test verdict. If Godot import fails, script success must not be considered.

### F2. State transition systems and source-to-model refinement (Lamport / TLA+)

For one native episode define a *specification vocabulary* (not a parallel simulator):

~~~text
  T = (States, Start, Actions, Step, Observer)
  Step subset (States × Actions × States)
  Observer_player : States -> PlayerUI
  Observer_debug  : States -> RuleSnapshot
~~~

An implementation refinement claim needs a stated abstraction map from real implementation transitions to this high-level vocabulary, a justified observer, and the needed stuttering/hidden-event treatment for asynchronous Godot Signals. Simply proving a model invariant does **not** prove the implementation respects the mapping.

Where an implementation can make unobservable editor/event-loop transitions, use an explicitly qualified weak/observable trace relation, not raw byte-for-byte trace inclusion:

~~~text
  Project_visible(Traces(ConcreteNative))
      subseteq Traces(AbstractGameContract)
  subject to an independently checked simulation/abstraction bridge.
~~~

This is a *candidate proof duty*. No universal inclusion, fairness, Windows real-input or player-satisfaction theorem is claimed here.

A bounded native trajectory can, however, expose a useful **local trace invariant** without reimplementing gameplay: the receipt must be a well-formed sequence of the actual native before/after observations. This is implemented in the existing Game acceptance reader in R1.1; it is a source/trace *test*, not a theorem.

### F3. Hoare triples, typestate and observable trace invariants

For a single Game test invocation, the Hoare-style obligation is:

~~~text
  { clean checkout AND pinned native Godot available }
      NativeImportThenEpisodeAcceptance
  { exit=0 => import succeeded AND native-episode-receipt validated
    import failure => exit!=0 AND no native episode PASS }
~~~

A bounded test proves this obligation only for executed conditions; no total program proof follows automatically. Within a *successful* schema-v2 episode receipt containing actions a[0..n-1], observations s[0..n]:

~~~text
  s[0] = receipt.initial
  step[i].before = s[i]
  step[i].after  = s[i+1]
  s[n] = receipt.final
  step[i].action = supplied_action[i]

  DebugRejected(i) => step[i].before == step[i].after
  DebugTerminal   <=> final.phase in {won, lost}
~~~

These are *observable consistency obligations* on the actual Godot receipt, not independently specified gameplay rules. They cannot prove that the game is entertaining, or that a malicious provider could not forge internally consistent receipts. Source-owned CI, real native execution and independent review remain distinct.

For the default player-observation channel, only native view fields (title, status, encounter, actions, hint, outcome, dialogue) may occur, and step keys must remain action/before/after only. Debug-only recognized/accepted/control_path must not flow to the player receipt. This is a **bounded output-shape property**; do not describe it as universal information-flow noninterference or a hyperproperty proof.

### F4. CEGAR and counterexample-directed repair

Clarke et al.'s Counterexample-Guided Abstraction Refinement gives the decision order for real discrepancies:

1. Record a concrete failing consumer trace and source version.
2. Decide whether the counterexample belongs to the concrete implementation, the environment, or only an abstraction.
3. Repair native implementation if concretely reproducible; refine the model/observer only when an abstract counterexample is spurious.
4. Repeat the exact affected native test and negative control.
5. Stop once the scoped real consumer contract holds.

Never hide a genuine Game failure by making the model more permissive, deleting a test, or reporting UNKNOWN as PASS. Never respond to a GPU launch failure by adding more disconnected RuleModel proofs.

### F5. Evidence grades, temporal currentness and trust boundaries

Evidence forms a nontrivial partial order, not one boolean:

~~~text
  DECLARED  != MODEL_CHECKED != SOURCE_REFINED
  SOURCE_TESTED != CI_VERIFIED != MERGED
  MERGED != INSTALLED != RENDERED != HUMAN_CONSUMED
~~~

A verifier result is meaningful only with matching claim, input, source revision, toolchain, execution environment and observer. A CI green status is proof of that CI's specified check on that SHA, not automatic human Game acceptance. If source, verifier or input changes, revalidate affected obligations; Git history is provenance, not current deployment proof.

Agent-generated code and agent-generated assertions can both drift. For consequential PRs reuse protected GitHub checks, exact SHA, original contract text and native consumer acceptance. A branch-controlled test is not by itself an adversarially independent oracle; do not claim strong unforgeability from workflow execution alone. Review/security policy remains under repository governance, not Game-owned code.

### F6. Role-specific use of Matt, ECC and Superpowers

**Thought LEGOs / advisory methods** (not effect-granting tools):
- Matt Pocock to-spec: convert already-aligned intent into domain-language behavior and a small number of high consumer test seams; prefer an existing Host Work/GitHub issue rather than creating another task authority.
- Matt to-tickets / implement-spec: model implementation as dependency-DAG tracer bullets with an executable frontier. Keep one Game delivery branch and use actual native CI; do not require multiple agents for narrow changes.
- ECC intent-driven-development / contract-first: each material acceptance criterion describes scenario, trigger, observable result, prohibited side effect and actual verifier; keep one canonical provider/consumer wire authority.
- Superpowers writing-plans / test-driven-development / verification-before-completion: exact file/path/command, watch a valid RED then GREEN, preserve negative controls, and make no completion statement without fresh result.
- Recursive LEGO R2.1: express the *retained independent responsibility* with all eleven typed coordinates; UNKNOWN is scoped, not fabricated. Only decompose when a real consumer can replace or validate the resulting component.
- Native engine/CI: owns real effects, builds, visible UI and independent execution receipts. Thinking methods cannot establish domain success.

**Do not install ECC stop hooks blindly:** its generic transcript regex / last-edited-learning-file criteria may reward the wrong work. Do not fork the Matt issue tracker, copy all Superpowers rules into the repository root, or add another Composition task schema.

### F7. Applicability and complete implementation DAG

| Stage | Existing carrier | Evidence / completion | Failure consequence |
| --- | --- | --- | --- |
| P0 source and consumer | Git, Game Agent, G11 effective R2.1 | SHA, playable/episode objective | STOP if no actual consumer |
| P1 specify the seam | This scoped Game spec + G11 contract | explicit observable obligations | retain UNKNOWN on missing assumptions |
| P2 native realization | Godot episode + Python reader + mise task | RED → GREEN against actual engine | repair/replace native interface |
| P3 trace refinement testing | Game acceptance reader, not standalone simulation | chain, rejection, terminal, player/public shape + negative mutations | fail on incoherent native receipt |
| P4 independent integration | GitHub PR native-g11-contract + root and CodeQL | exact SHA, successful required checks | no merged claim before mergedAt |
| P5 installed/product/human | Game Factory release, real binary, player evidence | actual qualified readback | do not promote CI to player truth |
| P6 cross-owner reuse | existing Composition obligations when needed | actual verifier-owned consumer witness | no custom generic runner or catalog |

No times, agent-count target, or completion-percent target is an acceptance property. Internal meta-rules cannot substitute for measured product behavior.

### F8. Primary literature and official implementations

- Pacti, Incer et al., ACM Transactions on Cyber-Physical Systems 2025, DOI 10.1145/3704736: https://doi.org/10.1145/3704736
- Pacti official assume-guarantee contract API and composition diagnostic: https://www.pacti.org/docs/getting_started/
- de Alfaro & Henzinger, Interface Automata, FSE 2001, DOI 10.1145/503209.503226: https://doi.org/10.1145/503209.503226
- Clarke, Grumberg, Jha, Lu & Veith, Counterexample-Guided Abstraction Refinement: https://web.stanford.edu/class/cs357/cegar.pdf
- Lamport, TLA+ refinement mappings: https://lamport.azurewebsites.net/tla/proving-safety.pdf
- Lamport et al., Specifying and Verifying Systems With TLA+: https://lamport.azurewebsites.net/pubs/spec-and-verifying.pdf
- Existing Ordivon method authority: ../../../.agents/skills/recursive-lego-calculus/SKILL.md (relative to this Game docs directory).
- Source Skills: https://github.com/mattpocock/skills ; https://github.com/affaan-m/ECC ; https://github.com/obra/superpowers

## 10. Space collaboration and exact social/effect separation

Host Space: space:ordivon-capability-task-forum-r1:20261101; topic:ordivon-capability-task-forum-r1:03-refinement:20261101. Message sequence 25746 (2026-11-09) requests peer challenge on G11 trace refinement, stuttering/fairness, CI independent witness, overlap and DELETE/REUSE. Peer replies are advisory evidence until source-bound, independently falsified and adopted by the natural Game owner; neither Space membership nor a message grants Git or production authority. Do not pretend there was a peer response if none has arrived.

## 11. R1.1 addition: actual native trace-contract refinement

**G11-AC-006 (required for new reader change):** For each successfully completed schema-v2 native episode invoked through the existing acceptance reader, check input/action cardinality, observation continuity, final state and (debug only) rejection stability and terminal projection; default player observations remain limited to the existing UI schema. No new gameplay interpreter.

**G11-AC-007 (required):** Build negative controls by mutating the *captured real Godot receipt*, not by inventing a second Game rule machine. The reader must reject a broken observation boundary and falsely rejected state-mutating action. Re-run the actual native episode tests after the mutation-only checks.

Completion for R1.1 includes an actual Git commit and independent PR check on the exact revision; the previously completed R1 import fix remains independently bounded. The result may still be OPEN in a merge queue and must be reported as such.

## R1.1 convergence and overlap decision

Source-read on 2026-11-09: global Agent execution specifications in PR #1965 and PR #1973 are merged. PR #1977 and #1978 still overlap that cross-Owner method/governance surface. This Game-local document is NOT another global Agent execution authority. Its only new program obligation is the G11 real-native trace consumer. Host Space formal-refinement topic message #25746 requests independent challenge; participant messages are advisory and do not replace Git, proofs or actual Game native acceptance.
