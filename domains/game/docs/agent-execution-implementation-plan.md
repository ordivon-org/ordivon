# Game LEGO-Constrained Execution — Implementation Plan R1.1

> Agent workers: read [spec](agent-execution-contract-spec.md), root `AGENTS.md`, Game `AGENTS.md`, and existing G11 R2.1 before changing code. Use Superpowers' small red/green steps and verification-before-completion where applicable; this plan is not a new authority or runtime.

**Goal:** Make the actual G11 Room Encounter episode acceptance independently executable in a clean Game checkout, while retaining source-bound LEGO evidence and recording the future natural-Owner adoption seams.
**Architecture:** Extend the existing native `mise` entry using upstream Godot import. Reuse the existing G11 R2.1 declaration, Game real scene tests and GitHub native pipeline; do not add a schema, verifier executor, registry or mandatory Agent workflow.
**Tech stack:** Godot 4.7.2, Python 3, Rust/Bevy 0.20.1 as existing separate product, mise, GitHub Actions, Game G11 R2.1.
**Spec:** `domains/game/docs/agent-execution-contract-spec.md`.
**Frozen test seam:** `cd domains/game && mise run test:agent-episode`, in an isolated checkout without `examples/room-encounter/.godot`.

## Global constraints

- Use exact current Game source tree `7157e18d3bee2765205687380953dfabf72688a0` as the initial design basis; record any future diff.
- Retain Godot-native `PackedScene`/`EncounterRules`/Dialogue Manager and native action/observation semantics; do not simulate action execution in Python.
- Retain the 11-coordinate existing G11 `recursiveLegoR21` contract and its original authority split.
- No new global evaluator, workflow/verification database, native scene shim, Weak-Model experiment or ECC Stop Hook.
- Do not claim Player acceptance from headless checks; do not claim Git merged/installed when it is only a local branch.
- For claims requiring a clean import, remove ignored generated cache only inside a disposable isolated worktree. Never delete production or other agents' worktrees.

## Dependency graph

```text
A: native G11 red->green repair
  -> B: integrate native test contract and evidence in Game docs/CI
  -> C: Game source review and merge/CI confirmation
  -> D: optional consumer-specific cross-Owner Composition binding (later, only if needed)
```

### Task A — Fix native clean-workspace G11 execution (implement first)

**Files**: Modify `domains/game/mise.toml` at `[tasks."test:agent-episode"]`. Keep `examples/room-encounter/agent_episode_acceptance.py` unchanged unless an actual negative control establishes a flaw. No external library.

**Interface**
- Input: `mise run test:agent-episode` in fresh checkout.
- Effect: `godot --headless --path examples/room-encounter --editor --import` before test entry.
- Output: the *existing* Game native acceptance receipt, with nonzero exit on pre-import failure.

- [ ] A1. RED: in an isolated disposable worktree confirm `examples/room-encounter/.godot` absent, run `mise run test:agent-episode`. Expected: native parse/class errors or failure of receipt, not any artificially forced failure.
- [ ] A2. GREEN: keep a single upstream-native import in `[tasks."test:agent-episode"]` before `python3 examples/room-encounter/agent_episode_acceptance.py`; run as a `set -euo pipefail` multiline task.
- [ ] A3. Remove only this worktree's generated Godot cache; run `mise run test:agent-episode` again. Expected: `GAME_AGENT_EPISODE_PASS native_episodes=19` and exit 0.
- [ ] A4. Run `mise run test:encounter`, `mise run test:dialogue-native`, `mise run test:native-receipt-selftest`; compare with baseline and inspect actual logs. For original Rule claims, preserve UI/debug and invalid-action cases.

**Negative control**: the official import command's nonzero exit must abort the shell task; the Python acceptance must reject its own GDScript error output even if Godot exits 0. No mocked Godot PASS.

### Task B — Source-bound owner acceptance and spec handoff

**Files**: Add these two Game docs; modify `domains/game/docs/factory-pipeline.md` or `domains/game/AGENTS.md` only if needed to correct a directly consumed obsolete instruction. No new test runner.

**Interface**
- Input: G11 full R2.1 in existing Game planning JSON; existing Game `mise` checks and exact Git source.
- Output: scoped `G11-AC-001..005` acceptance reference usable by Game Agent/CI; non-claims stated explicitly.

- [ ] B1. Review changed native entry against `recursiveLegoR21.pre/post/inv/eff/prov`. Do not automatically mark all 11 properties mathematically proved.
- [ ] B2. State the clean-checkout entry in the real Game factory guide only if its consumers benefit; link this spec rather than duplicating it.
- [ ] B3. Run `pnpm check` and Game-native relevant suite. Preserve existing test counts and result forms.
- [ ] B4. Check `.github/workflows/game-factory.yml` `native-g11-contract` on pull requests: clean checkout, native Godot import and existing 19-episode acceptance; `actionlint .github/workflows/game-factory.yml` must pass. Preserve main-push preview packaging as a separate job. Record GitHub check state and exact SHA separately from local verification.

### Task C — Integration and actual completion claims

**Files**: only affected Game source, docs and tests.

- [ ] C1. Run `git diff --check`, inspect `git diff --stat`, and confirm no unrelated generated files or protected changes.
- [ ] C2. Run `mise run verify` from `domains/game` when this host has required toolchain; if native graphical dependencies block, record ENV_BLOCKED without claiming full Game PASS, and run the maximal relevant native subset.
- [ ] C3. Commit the reviewed Game change to isolated Git branch; if repository PR policy and GitHub credentials allow, submit a PR with exact source and native test output.
- [ ] C4. Claim only actual stages: branch committed, CI pending/passed, merged, released, or consumed. Never collapse them into a single SUCCESS.

### Task D — Future *consumer-triggered* cross-Owner rollout (not an unconditional task)

**Files**: `packages/composition/src/ordivon_composition/schemas/cognitive-circuit-manifest-v1.schema.json`, `verification-obligation-set-v1.schema.json` are **reused unchanged** unless an evidenced obligation cannot be expressed. Natural Composition owner must own any later changes.

- [ ] D1. On the first real cross-owner Game factory change, bind an `objectiveRef`, selected capabilities and gate requirements to the existing Composition public API.
- [ ] D2. Derive obligations with `compile_verification_obligations` and bind existing native verifier at the task-local consumer; reject ungrounded success.
- [ ] D3. Use source-current Game/Runtime/CI evidence to discharge only matching obligations; preserve `domainAcceptanceEstablished=false` for Composition projections, allowing Game to establish its own domain acceptance.
- [ ] D4. Publish source-bound owner result only after impacted consumer tests; discard extra machinery not needed by consumer.

## Completion checks

Required for the implemented Slice A/B: `G11-AC-001..004` observed in the same disposable Game workspace. `G11-AC-005` requires an accurate integration status report. The broader idea that all Ordivon tasks now enforce independently compiled contracts is explicitly NOT claimed.

## R1.1 task extension — source-bound receipt trace refinement

Dependency: A/B/C above form the verified G11 import and CI seam. R1.1 builds only on that same natural Game consumer, without introducing G12, another runnable verifier or a universal output schema.

### Task E — Make the current native output reader test observable trace coherence

**Files:** Modify only Game's existing `examples/room-encounter/agent_episode_acceptance.py`. Preserve the native `agent_episode.gd` and `EncounterRules`. No workflow/runner changes.

**Input:** One actual successful `episode(actions, observation)` return with schema-v2 JSON, 0..64 native actions, player/debug mode. **Output:** positive verdict for coherent actual native receipt; assertion on inconsistent trace, rejected-state mutation, unknown debug fields leaking into player channel.

- [ ] E1. RED: add a focused negative mutation of a real native captured debug receipt, changing a valid observation's next `before` to an inconsistent value. The acceptance reader must reject it rather than passing. Also mutate an accepted state-changing action to `accepted=false`; rejection must be detected.
- [ ] E2. Define one small pure reader function `assert_native_trace_contract(receipt, actions, mode)` beside `episode`, no additional library/framework. Validate schema version, matching action sequence, before/after chain, final observation, debug rejected-state immutability, debug terminal phase, and public player field/step whitelist. Keep error receipts separate.
- [ ] E3. Run all previous native 19 episodes through that single function, including debug/player and invalid/empty/terminal cases. Execute negative mutations explicitly and confirm they are rejected, with original receipt unmodified.
- [ ] E4. Run `mise run test:agent-episode` after deleting only ignored workspace cache. Expected final Game native receipt and no branch-local changes outside affected files.
- [ ] E5. Run `mise run verify` and `actionlint .github/workflows/game-factory.yml`; bind result to exact commit, then push to the existing Game PR if it remains open. If the PR has merged, create a new source-current Game branch and PR instead of rewriting main.

**Proof scope:** bounded native Game receipt consistency, *not* algorithmic correctness of EncounterRules or universal noninterference. This is test-based code-to-observation refinement evidence with a real Godot producer; no fabricated model/proof stand-in.

### Task F — Source/Space peer review and integration

**Files:** This Spec/plan and exact touched Game source. **Effect authority:** GitHub PR checks/merge queue; Host Space is advisory only.

- [ ] F1. Read Host formal refinement topic and any peer challenge tied to message sequence 25746. Record actual replies as findings; retain UNKNOWN if no reply.
- [ ] F2. Check overlap against latest Game/Composition source and open PRs; avoid concurrent ownership of the same files.
- [ ] F3. Ensure external mathematics/CS sources support the scoped statements and the chosen testing seam, with no claim that a local test is a universal proof.
- [ ] F4. Review actual Git diff/source currentness, commit and push; identify PR check status. Do not call OPEN merged; do not call CI human gameplay.
- [ ] F5. Stop at Game consumer closure. Cross-owner Composition changes require their own real consumers and natural owner.

## Actual execution ledger (2026-11-09)

- Original R1 is MERGED on GitHub: PR #1969 merged 2026-11-09T15:32:15Z, exact head 02425d546d639e51cc5444604525b16463b3a102; native Godot RED/GREEN and full Game verification passed.
- E1 initial test-scaffolding failure: invoking the proposed missing reader raised NameError before implementation. This is **not** a semantic RED witness that the old reader accepted corrupted native receipts; that old-reader negative outcome was NOT_RUN. Subsequent E3 negative mutations demonstrated the new reader rejects inconsistent actual Godot receipts.
- E2/E3/E4 GREEN: existing Game reader now checks the actual native receipt state chain, rejected action immutability, terminal phase and player-only output; both tampered native receipts are rejected; 19 native Godot episodes PASS. No separate Game simulator.
- E5 local native owner verify EXIT0 (Z3/Godot/Bevy/R7), actionlint EXIT0. Independent follow-up GitHub PR status is recorded separately after publication.
- F1/F2 cross-agent: Host Capability & Verification formal-refinement message #25746 posted; independent peers identified overlapping global #1965/#1973 merged specs and #1977/#1978 open overlap. Do not add another cross-Owner source of authority; only Game G11 code changes.
- F4/F5 completion depends on the exact follow-up Git commit/PR and its check standing; source/Git/CI success is not installed or human-play acceptance.
