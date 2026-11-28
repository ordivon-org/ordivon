# Game V6 R15 — test qualification and counterexample lifecycle

Host #32864, #2842 exact candidate90c60486a79d114e07ad7e10c11659ba9e63a1dc.
Current owner verify and PR native gate omit R11–R14 cheap consumer contracts.
Fix the recurring omission before growing the test inventory.

Thought LEGO: independent oracle, falsification, generated input/shrinking,
risk-based verification, no evidence promotion across effect boundaries.
Logic LEGO T01 property/oracle; T02 generation and shrink; T03 fixture identity;
T04 native state/transition; T05 composition; T06 artifact identity; T07 actual
render/input/audio; T08 mutation adequacy; T09 gate composition; T10 human study.
Capability LEGO: Hypothesis, existing unittest/Node, Z3, Godot native scene
runner, existing Xvfb/XTEST/FFmpeg, Mise and GitHub Actions. No second test
scheduler, no bespoke random generator, no second rules engine.

References: https://hypothesis.readthedocs.io/en/latest/stateful.html ;
https://hypothesis.readthedocs.io/en/latest/settings.html ;
https://stryker-mutator.io/docs/stryker-js/incremental/ ;
https://github.com/godot-gdunit-labs/gdUnit4 ;
https://docs.astral.sh/uv/guides/scripts/ .
GdUnit4 migration requires a demonstrated scene-runner gap; current native
state machine and traces retained. Stryker is TS-specific, not a Python/Godot
mutator. First use controlled source mutations for the actual Python seam.

I: source-bound archive fixtures and exact consumer code; O: test disposition
with reproducible shrinking and observed library version. S: private temp
fixtures, no network or actual product execution in cheap contracts.
pre: healthy original suite, generated valid archive, independently derived
expected relations. post: valid payload/permutation accepted; rehashed semantic
receipt corruption, malformed native inventory and substituted content rejected.
inv: no skip/xfail for missing capability; no production data mutation; a
passing test is not evidence of actual game output. eff: generated fixtures,
test-only environment, bounded runner. c: bounded examples, payload length,
no heavyweight Godot launches for fast property test. epsilon: scoped input
space, not exhaustive proof. prov: exact source, Hypothesis version, failures
and minimized examples. unfold: stdlib fixture builder + Hypothesis + existing
consumer. Use deterministic CI profile, database disabled for ephemeral run;
promote genuine minimized counterexamples into explicit regression examples.

Gate composition: test:consumer-contracts = archive/interaction/audio pure
contracts + generated archive properties. Called from owner verify and existing
PR native check. Keep real FFmpeg fixture task separate (effectful but cheap),
native blank and actual downloaded game checks on qualified display/template
runners. No new GitHub required job or READY expansion. Do not silently skip
the pure gate. Later qualify decoder/display tiers before broadening CI.

Actual mutation evidence: a disposable copy with SOURCE_TREE shape guard
removed passes all nine old archive cases, but Hypothesis rejects it with
field=SOURCE_TREE, value=0 (receipt value invalid_0, all hashes recomputed).
Promote this witness to @example. This is one killed non-equivalent mutant,
not an overall mutation score. No mutated source is published.


The first broader mutation trial (8 applicable deletions, one unmatched
patch excluded) found 7 generated kills and one survivor LINUX_SCOPE; all
eight escaped the old fixed cases. Finite field obligations must not compete
for a random example budget. Exhaust all 13 declared semantic fields for
each generated invalid value and preserve value 0 as an explicit example.
This is a finite-by-generated composition, not exhaustive value-space proof.

Final controlled matrix: 12 applied semantic guard deletions; original fixed
examples killed 1/12 and exhaustive-field generated suite killed 12/12,
baseline restored. The ENGINE version-string guard was exercised by the
generated property but not separately mutated in this matrix. Put fast
contracts before expensive Godot/SMT gates, not at the end.

## R16 — shrinkable native transition and observer trace

R15 #32938; T04/T05 native state and composition. Existing 486 traces
enumerate three actions at length five, not checkpoint/restart lifecycle or
signal trace semantics. Keep that finite oracle and SMT. Use Hypothesis
action-list generation/shrinking (https://hypothesis.readthedocs.io/en/latest/stateful.html)
and Godot signals (https://docs.godotengine.org/en/stable/classes/class_signal.html).
Generate whole bounded programs, replay each in one native Godot process
for both Classic and Trial; no persistent test RPC or duplicate rule engine.
Stage exact Rules/Tuning/config bytes in a private minimal test project,
not the exported product; no UI/audio/device claims. A test-only observer
returns per-step before/after states, acceptance and ordered signals.
Independent Python relations require rejection atomicity including no
signals, successful combat emits state then action once, reset/advance/
restore emit state only, checkpoint is observational, accepted restoration
equals the saved state, restart equals initial state, turn progression and
Trial forecast relation. Both modes on every generated program. Explicit
lifecycle examples, no database, bounded launch timeout; failures retain
the input list and Hypothesis shrinks it. A receipt has exact mode/step
inventory and strict native diagnostics, not mere exit zero.

I: exact Rules/Tuning/resources plus generated bounded action list.
O: independently verified per-step relations. S: fresh rules and checkpoint
per mode; pre: source byte staging and native process; post: expected
transition/signal relations; inv: no mutation of original source/production
slots, no second combat simulator; eff: private temp project and native
process; c: <=40 actions, 24 generated programs plus five explicit examples;
epsilon: actual native rules, not exported scene/UI/peripheral or universal
state coverage; prov: exact source revision, Hypothesis version, minimized
action sequence. Unfold with existing uv, native_process and Godot.
Only integrate into existing native gate after actual baseline and mutant
qualification; no new required job or dependency pin.

Actual baseline job-01a214f9-1892-70b9-a887-6774af010550 passed in 5.049s
test time, 5.786s wall, Hypothesis 6.170.17. Controlled native mutations in
disposable copies, job-01a214f9-c4d7-706f-a06a-36b612744fc9: rejected advance
emits state (old real 16,099 assertions/486 traces PASS, new shrunk
[advance] rejects), guard swaps state/action signals ([guard] rejects),
invalid restore emits state ([invalid_restore] rejects). All 3 killed.
Only first mutant was executed through the legacy suite; no global mutation
score. Preserve all three one-action witnesses as explicit examples.
Gate: existing test:encounter composes native-trace after original scene
and process restart suite; both owner verify and factory:validate:godot
(and the existing PR native check) already consume it. No additional
required CI job. Runtime cost is measured on native local runner; hosted
runner qualification remains pending. Test observer stays outside product
resource tree. No physical effect or export qualification inferred.

The first integrated generated run actually observed 29 programs / 58
mode-programs / 352 steps, but only four mode-phase pairs (Classic fighting,
cleared, lost; Trial fighting). This falsifies any all-phase claim based on
the random program budget. Exhaust the finite terminal-obligation axis
with four explicit native paths (Classic/Trial x won/lost), then checkpoint,
rejected combat/door operations, restart and restore. Require exact 8/8
mode-phase inventory across those paths. Increase only the probe's bounded
input length to 64 for long terminal witnesses; generated list budget stays
at 40. This is phase reachability, not all transitions/state coverage.
