# R19 — native bounded mechanic exploration

Host #33143 / #33199. Goal: find actual decision-quality counterexamples before
changing the product; preserve existing Classic and Trial, do not turn mechanical
search into a player rating or the independent frozen R7 study.
Thought: MDA, meaningful choice, search-based PCG, Pareto frontier, independent
falsification. References https://gpbib.pmacs.upenn.edu/gp-html/Togelius_2011_TCIAIG.html
and https://unity.com/blog/games/automate-your-playtesting-create-virtual-players-for-game-simulation .

Logic / Capability: configuration intervention -> Godot Resource duplicate;
transition oracle -> existing EncounterRules checkpoint/restore/attack/guard/advance;
state-space traversal -> bounded breadth-first graph; terminal comparison ->
nondominated (action count, remaining health); witness -> actual native replay;
decision -> report to designer, not automatic tuning/promotion. No second rules,
new dependency, study controller, general search engine, or required CI job.

I: Classic, Trial, isolated Trial guard_block=2; action horizon 48; state cap 100000.
O: completed bounded search, per-case win frontier and policy witnesses, or failure.
S: owned isolated Godot project, native Rule nodes, visited keys and parent pointers.
pre: exact source files, fresh rule initialization, bounded native turn <48+1.
post: expand each reachable key once in nondecreasing depth; retain shortest action
count at equivalent state; record all nondominated winning health/action pairs;
replay each frontier witness via fresh native reset.
inv: no invalid actions, rejected restore or silent truncation; no source config edit.
eff: temporary native process only; c: bounded state/depth/time; epsilon: mechanical
reachability, deterministic current rule scope, not player preference or exhaustive
all designs. prov: source file digests, native engine, horizon/cap, actual witnesses.
unfold: native checkpoint and BFS with parent pointers, Python validation.

State quotient: keep room, foes, enemy HP, player HP, stamina, phase, and turn mod 3
(keep exact turn for reference mode). Tuning fixed within each case. Only future
combat schedule reads turn mod 3; saturation unreachable from a fresh run under
this horizon. Earlier identical quotient dominates later paths for action-count
minimization. This is a source-specific reasoning obligation, not a general game
equivalence. Validate reduced vs exact traversal on the same bounded horizon;
replay frontier paths from fresh state; no extrapolation to future rule changes.

Counterfactual guard block=2 changes one parameter in a disposable Resource only.
Compare attack-first and forecast-aware policies on the same tuning, no labels
of human skill. Stop after reporting finite evidence; require independent design
review before changing player-facing tuning.

## Observed first experiment (2026-11-26)

Native receipt job-01a2154d-23ba-7753-95ac-bd4e96094768 exit0, exact
Rules SHA 8fa1e58d739161802ea1240042337a3f83a143a29c8c4cf8197e555ff9dffdb5.
48-action horizon. Exact vs reduced visited counts 362/362 Classic,
22067/2337 Trial, 22864/6360 Trial block2. Equal health/action Pareto
frontiers in all three cases, actual native replay; 2.154s combined
six searches plus policy/cycle observations (not a speedup measurement).
Classic frontier (10,8); Trial (28,8),(29,9); block2 (28,6),(29,7).
Attack-first Trial 28/6 vs forecast-aware 29/9; block2 28/1 vs 29/7.
Native three-guard sequence at full stamina preserves Trial HP48 and
tactical quotient, versus Classic14->11 and block2 48->46. It is not
the same exact state (turn increments), not automatically a design bug.
Preserve both configurations pending real player evidence; a tighter
policy survival margin can worsen accessibility. No R7 study changes.
Actual captured-receipt mutation checks reject seven selected corruptions.
Optional invocation: mise run experiment:mechanic-search. No change to
required verify or package; only execute when a design decision consumes it.
