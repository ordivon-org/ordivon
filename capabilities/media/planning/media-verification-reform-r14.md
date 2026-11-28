# Media R14 verification execution contract
Extends R11/R12/R13, Host #32823 and cross-owner #32815, #32805.
No separate verification service, test registry, or root CI writer.

## Thought / Logic / Capability
| Logic | Capability | Qualification |
|---|---|---|
| Contract & obligation | existing schemas, Lean, domain invariants | source vs effect vs acceptance |
| Input space | Hypothesis on unittest | generated and shrunk counterexamples |
| Independent oracle | set reachability, rational arithmetic, native tools | no implementation self-reference |
| Fixtures | temporary directories, disposable PostgreSQL | exclusive effects, cleanup |
| Native execution | FFmpeg, OTIO, ttconv, Runtime | no simulated provider pass |
| Discovery | existing unittest discovery, pnpm, mise | no static filename enumeration in full gate |
| Negative controls | targeted source mutants in isolated workspace | assertion kills, not environment failures |
| Evidence | native Runtime Job/Attempt/Artifact | exact source/tool/receipt, skip distinct |
| Consumer | owner verify/full and shared CI | qualify only actual selected coverage |

P0 property refinement of ProductionDependencyImpact.lean:
I bounded DAG of 1..10 nodes, match/missing/drift source byte states, permutation.
O actual public projection vs independent transitive ancestor closure.
S isolated materialized file fixtures, not production data.
pre exact declared edge carriers, supported schema.
post same semantic standing under manifest permutation, digest changes when
manifest bytes change, drift dominates unknown, unrelated branches unaffected.
inv no matching bytes grant cache/execution/publication, unknown propagates.
eff temporary files and read-only projection, no production effects.
c 120 generated examples plus explicit regressions; two orderings each.
epsilon bounded sampled property test, not proof of all DAGs or live effects.
prov Hypothesis 6.x native, exact frozen lock, controlled assertion-killed mutants.
unfold generate -> materialize -> observe -> independent oracle -> shrink/replay.
Original source restored after each mutation campaign; no mutant committed.
P0 integrate existing native discovery #2828 after base promotion.
P1 strict full verification rejects missing PG, skipped/expected failures,
zero discovered tests, while lightweight verify remains explicitly bounded.
P1 use branch coverage to find gaps, evaluate mutmut only after actual
risk/cost and interpreter compatibility; no arbitrary global coverage threshold.
P2 expand stateful tests on receipts/attempt lifecycle with real native fixtures,
not parallel pseudo provider or giant test framework.
Cross-owner root CI consumption requires actual provider availability and
independent Verification owner review. Full gate does not certify production.
References: https://hypothesis.readthedocs.io/en/latest/stateful.html
https://hypothesis.readthedocs.io/en/latest/_modules/hypothesis/_settings.html
https://coverage.readthedocs.io/en/latest/
https://mutmut.readthedocs.io/en/latest/
