# Ordivon Book v0 — consumption and acceptance audit

Status: `PILOT ACCEPTANCE EVIDENCE`

This audit separates semantic-text quality, Studio model compatibility, source-fence currentness, Agent discoverability, and independent Agent comprehension. It does not claim Human population-level comprehension.

## A. Existing substrate / no new platform

The Book is implemented as an ordinary Studio Writing Production. No Book repository, database, schema, daemon, MCP, or Agent-surface action was added.

Direct Studio model validation result:

`Studio production models are valid.`

Targeted regression result:

- `tests.test_models`
- `tests.test_agent_surface`
- 16 tests passed.

The ordinary Agent surface enumerated `ordivon-book-v0` through `studio_production_standing` and returned its 7 source-bound Claims through `studio_production_context` without any Book-specific code change.

## B. Exact source-fence audit

All seven claim source paths and their declared evidence paths were proven to exist at the pinned Git revisions.

Initial Atlas source audit exposed a real authority/currentness split:

- local Atlas `main = d8036cb...`
- remote-tracking `origin/main = 2eea93d...`
- relation: 8 local-only commits / 1 remote-only commit; neither side ancestor of the other.

The remote-only commit carried Human owner currentness repair; the local line carried newer PPD/first-look and Media-currentness work. An isolated merge candidate preserved both with zero conflicts.

Atlas convergence acceptance:

- merge revision: `c0ba3c7d22e217d3d38553542050aa0360a1e3f8`
- deterministic Atlas suite: 85 tests passed, 45 explicitly gated live/destructive tests skipped;
- push to `origin/main`: succeeded;
- canonical local `main` fast-forward: succeeded;
- final local `main == origin/main == c0ba3c7...`.

Book's Atlas binding was then moved to that converged source.

## C. Agent-surface currentness nuance

`studio_production_context` deliberately does not infer local filesystem repositories from a source binding name. Without an explicit caller mapping it reports cross-repository Git currentness as `unverified`; this is a fail-closed mechanical boundary, not evidence that the source is stale.

For this pilot the exact source-fence/currentness check was therefore performed separately through Runtime/Git and recorded above. Do not weaken `production_context` by auto-trusting a repository string as a local path merely to make the Book look green.

## D. Fresh-Agent bootstrap test

### Structured carrier negative control

The first independent DeepSeek Harness Run used a strict structured-result completion contract. Provider dispatch occurred, but no valid conclusion carrier was admitted; Harness stopped with `invalid_model_output`. This is retained as a carrier/protocol negative control, not a Book semantic failure.

### Free-form no-tool control

A second fresh Harness Run received only `story.mdx` plus the evaluation question. It received:

- no Atlas content;
- no Task chronology;
- no source map;
- no Runtime/domain Tools.

Observed execution:

- Harness Run: `harness-run:ordivon-book-v0-freeform-1787566006862`
- Provider: `deepseek-v4-flash`
- stop: `candidate_completed`
- model calls: 1
- tool calls: 0
- total tokens: 5,316
- prompt tokens: 3,922
- completion tokens: 1,394
- conclusion corrections: 0
- story canonical digest observed by Harness: `sha256:86d0ca97d10bafb0dc6c388b51a7977978301acce53269b6ce310a44c0205851`

The fresh Agent independently recovered:

1. the full open recursive Reality→Representation→Evidence→Standing→Authority/Decision→Effect→claim-relative Consequence→Revision model;
2. at least eight load-bearing anti-collapse distinctions, including `Reality != Representation`, `Evidence != Conclusion`, `Standing != Authority`, `Intent != Effect`, `HistoricalValidity != Currentness`, evaluator-independence distinctions, `Feedback != Learning != Gain`, and `NoNaturalContradiction != NoReachablePressure`;
3. the rule that Standing is not sufficient for Action without authority/objective/constraints;
4. claim-relative evaluator selection rather than Human/Agent universal terminality;
5. revision as semantic uptake that may validly produce `NO_CHANGE` and does not imply engineering mutation;
6. recursive changes to future ProblemSpace/ObservationInterface/Affordance/AuthorityEnvironment;
7. Book as a constrained integrated explanation rather than a semantic owner;
8. the explicit non-claims listed by the chapter.

The Agent answered `研究 chronology 是否需要: 不需要` for recovering the current model from the chapter.

This is one independent Agent episode, not a universal comprehension guarantee.

## E. Human evidence boundary

No independent Human reading experiment is fabricated here. The current artifact may be semantically approved as a source-fenced Writing output without claiming that its voice, pacing, trust, or comprehension effect generalizes to Humans.

The first real Human reading is therefore evidence about Human-specific experience, not an authority gate for the chapter's non-Human semantic source correctness.

## F. Acceptance decision

Approved semantic text:

- path: `productions/ordivon-book-v0/story.mdx`
- raw SHA-256 / Output `blobDigest`: `sha256:c6835bcf306542801bdcd76cfb32492747d1fb2267f9f8c3164e30303cea1747`
- output status: `approved`
- parent Production status: `review`

The parent remains `review` because no public publisher is selected and Human-specific reading effect remains unclaimed. No stronger Book machinery is earned by this pilot.
