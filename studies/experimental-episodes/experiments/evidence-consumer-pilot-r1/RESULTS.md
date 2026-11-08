# 2026-11-08 – An actual Agent consumes the existing Episode R1 analytical product

**Standing: ACCEPTED_BOUNDED_RESEARCH_FACTUAL_CONSUMPTION; agent task-learning uplift NOT_IDENTIFIED.**

## Real deliverable

A Research agent was asked to determine whether Ordivon Experimental Episode
R1 can currently justify memory-based autonomous agent promotion and to
answer ten source-specific factual/decision questions. The real source-bounded
decision is **HOLD**, not automatic production promotion.

The experiment used the existing source-authoritative product (10,007
historical EXPERIENCE Episode projections) and the installed authenticated
Codex CLI (model reported as gpt-6.1-sol). Four **real model calls** used
independent ephemeral read-only working directories and the identical
preregistered question/scoring contract. This is not a simulated LLM.

## Preregistered results

Method, target answers, source SHA-256 commitments, assignment and grader were
frozen at commit 1182a0b48c3daec5f7d98a5060aaaec2d31ab6cc BEFORE any
experimental agent call. The preregistration contract SHA-256 is
2d909f129233671179626ec83aa1aa9343e9c06237dd98a6a19aeff2545071ec.
The order is control / evidence / evidence / control. Scores were independently
recomputed from saved raw agent answers against the original source-bound gold.

| Run | Exact condition | Correct of 10 | Proper UNKNOWN | Unsupported | Correct + source attribution | Elapsed wall seconds |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | Control: NO source content | 1 | 9 | 0 | 0 | 15.690 |
| 2 | Treatment: exact product evidence | 10 | 0 | 0 | 10 | 13.836 |
| 3 | Treatment: exact product evidence | 10 | 0 | 0 | 10 | 13.007 |
| 4 | Control: NO source content | 1 | 9 | 0 | 0 | 12.339 |
| **Total A** | No evidence | **2 / 20** | **18** | **0** | **0** | not meaningful at n=2 |
| **Total B** | Evidence | **20 / 20** | **0** | **0** | **20** | not meaningful at n=2 |

The correct control answer is the conservative HOLD policy, which the prompt
specified independent of the source. The other nine factual answers were
correctly withheld rather than guessed without evidence. Evidence-treated
answers covered the corpus size, Runtime outcomes, Harness Runtime link
coverage, provider-cost coverage, explicit missing development/judge evidence,
missing intervention identification, unassigned retention and the same HOLD
decision.

**Observed uplift is answerability on these specifically chosen factual
questions, not improved task-solving intelligence.** The questions were
selected from the exact evidence fields given in the treatment. This is a
positive data-to-Research-consumer smoke test by design; it is not a test of
generalization, learned skills or autonomous code changes. No inferential
confidence interval, provider monetary cost, or production-wide benefit is
claimed. Even assigning a dollar ROI to the elapsed seconds would be
unjustified.

## Business decision derived from accepted source

1. **Accept** the analytical Episode R1 product as a useful evidence source
   for factual Research support when cited by exact manifest, analysis and
   ODPS source digests.
2. **Do not promote** an autonomous self-improving Agent based on these
   historical records: DEVELOPMENT=0, JUDGE=0, no frozen intervention contract,
   and no explicit assignment. The recorded causal and generalization
   standings remain NOT_IDENTIFIED.
3. **Do not infer** money, failure causes or domain success from Runtime
   mechanical artifact/event bytes and terminal execution states alone.
   Provider-cost signal coverage is 2 of 7 Harness Episodes.
4. **Do not authorize GC** from this result: the product's retention schedule
   is UNASSIGNED and automated deletion is not authorized by product metadata.
5. **Next meaningful evaluation:** obtain genuinely actionable task-level
   experiences with authority from their original Runtime/Harness producers;
   freeze a separate held-out coding or research task population and a concrete
   task outcome oracle; then compare the SAME Agent WITH and WITHOUT those
   episode-level experiences. Use UK AISI Inspect AI and its existing Codex/SWE
   agent bridge rather than building a new permanent Ordivon evaluator.
   If old task-level replay sources cannot be genuinely recovered, do not
   fabricate them; either construct new prospective opt-in episodes or stop.

## Data and source identity

- Corpus Manifest SHA-256:
  67c917eacd59fb7ae48877cde4d893093477c9c730a454824251291aad012b1b.
- SystemAnalysis R1 SHA-256:
  e5e2c6bd8801c266dc6e94f80ca30fbaf62ef9240b7dce816f73634259d1d57d.
- ODPS R1 source SHA-256:
  6691c6168c7d0fa1d031ab2d1bbce69a15dd755878d4c2dac8cf9f01d13ef04a.
- Raw per-arm JSON answers, explicit UNKNOWN abstentions, exact source
  attribution, scorer results, source digests, model version hints and
  request wall times: result-20261108.json.
- Native reproducibility: Python standard-library unittest with 7/7
  acceptance checks; real Codex CLI, without a new evaluation service.

Scope is intentionally narrow: the actual full replay JSONL was not found
in the current live source cut. The original product manifest says it is not
stored in Git. These findings should never be presented as retrieval from all
10,007 raw memories or as an identified causal gain in Agent ability.
