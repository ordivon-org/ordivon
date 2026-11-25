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
