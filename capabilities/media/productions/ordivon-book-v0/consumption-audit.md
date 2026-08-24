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


## G. Chapter 2 — representation / problem-solution consumption audit

### Source and model gate

Chapter 2 was added without changing Studio schemas or Agent APIs. The Book now has 12 source-bound Claims across three exact bindings: Atlas current synthesis, pre-Book Media Writing authority, and current Media/OMPC semantics.

Post-change mechanical results:

- `Studio production models are valid.`
- 17 targeted Model/Agent-surface tests passed.
- all 12 Claim source/evidence paths exist at their exact pinned revisions.
- Chapter 1 raw digest remains `sha256:c6835bcf306542801bdcd76cfb32492747d1fb2267f9f8c3164e30303cea1747`.
- Chapter 2 raw digest: `sha256:876c2eaec5e15b63aec11d2a3e815c151cc388294f676342225f76c80780d5b9`.
- deterministic current two-chapter `book.mdx` raw digest: `sha256:476313e2c8bf59d2f68f5cd25b6fa732c98b85d4b9a47976b13d5b8c48567902`.

### Adversarial fresh-Agent test

The Chapter-2 test intentionally asked a fresh Agent to adjudicate attractive but wrong collapses rather than merely summarize prose. It received only `chapter-02.mdx`; no Atlas, source map, Task chronology or Runtime/domain Tools were available.

Structured-result controls:

1. 30k total-token authority: one Provider attempt, one conclusion correction, then `budget_exhausted`; no semantic result admitted.
2. 65,536 total-token authority: three Provider attempts, two conclusion corrections, then `invalid_model_output`; no structured result admitted.

These are retained as Harness/Provider result-carrier evidence and do not count as semantic rejection of the chapter.

A first record-mode control reached `candidate_completed` but durably retained only a generic completion summary. The test was then corrected so the **entire audit had to be stored in the candidate-completed conclusion summary**, because transient Provider text is not the next consumer's durable result.

Accepted fresh-Agent episode:

- Harness Run: `harness-run:book-ch2-freeform-1787572314066`
- Harness implementation fence: local `ordivon-harness@d7935d47c27822859ee87dd5c6039947cd9f313c`
- Provider: `deepseek-v4-flash`
- stop: `candidate_completed`
- model calls: 1
- tool calls: 0
- total tokens: 5,824
- conclusion corrections: 0

The durable conclusion correctly adjudicated:

| Trap / scenario | Recovered decision |
| --- | --- |
| proposition truth preservation -> search geometry preservation | `FALSE` |
| more detail is always better | `FALSE` |
| one globally best representation for every observer/operation | `FALSE` |
| lossy -> insufficient | `FALSE` |
| every problem needs reframing | `FALSE` |
| terminal Result is universal future sufficient state | `FALSE` |
| same source may have different observer projections | `TRUE` |
| compact projection already sufficient for current bounded decision | `NO_CHANGE` |
| correct propositions but load-bearing search/generator route lost | selective search-geometry representation repair |
| correct source/currentness facts but wrong capability owner routing | selective owner-first routing repair |

The Agent also recovered Γ-relative sufficiency, the chapter's explicit non-claims, and stated that research chronology was unnecessary for the current model.

### Two-chapter composition boundary

`book.mdx` is a deterministic assembly of the two exact approved chapters plus a minimal title/contents preface. Two independent whole-book coherence attempts stopped at `invalid_model_output` before any admitted model call. This is Provider/Harness boundary evidence only.

Therefore:

```text
Chapter1 semantic output = APPROVED
Chapter2 semantic output = APPROVED
Two-chapter exact assembly = RENDERED
Independent whole-book comprehension = UNKNOWN
Parent Production = REVIEW
```

No whole-book semantic approval is inferred from chapter-local success.

### Acceptance consequence

Chapter 2 is admitted because its load-bearing falsifiers survived an independent durable-consumer test. The experiment does **not** admit a universal Representation Layer. Its direct engineering consequence is the opposite: representation repair should be selective and typed to the failed operation; a compact projection that already works should remain unchanged.
