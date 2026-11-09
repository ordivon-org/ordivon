# Episode R1 to Research consumer: evidence-access paired pilot

**Research-only; not a claim of agent memory learning or improved model ability.**

## Actual decision

Can an existing read-only Codex Agent make source-grounded factual and conservative
production-promotion decisions from the previously admitted Experimental Episode R1
data product? This product contains 10,007 historical EXPERIENCE projections
(10,000 Runtime R5C and 7 Harness), not a corpus with DEVELOPMENT/JUDGE labels
or a held-out agent task benchmark. The corpus manifest explicitly excludes
storing the full replay in Git, and the raw 10,007-row replay JSONL was not
located at the current source cut. Do not relabel analysis summaries as
searchable individual agent memories.

## Mature method

Use UK AISI Inspect AI's Dataset / Solver / Scorer separation, OpenAI
task-specific evaluation advice, and the existing local causal-intervention
Skill. Do not install another evaluation service for this ten-question fact
pilot. The solver is the existing Codex CLI, read-only and ephemeral.

Upstream:
https://inspect.aisi.org.uk/
https://developers.openai.com/api/docs/guides/evaluation-best-practices

The pilot derives ten fixed, source-bound factual/decision cases and exact
literal gold from the existing corpus manifest, SystemAnalysis receipt, and
ODPS product. The case gold is NEVER sent to Codex. Control receives no
evidence; treatment receives bounded fields from the exact same inputs.
Both conditions use identical questions and prompt skeleton. Codex runs in
independent empty temporary working directories with read-only sandbox.
Order is preregistered control / treatment / treatment / control.

Scoring distinguishes literal exact correctness, UNKNOWN abstention,
unsupported wrong assertions, and correct answers attributing the right
source ID. Monetary provider cost is unknown and elapsed seconds are not
a currency estimate. No trials claim causal generalization.

Native source/scoring checks, without provider calls:

    python3 -m unittest discover -s studies/experimental-episodes/experiments/evidence-consumer-pilot-r1 -p test_pilot.py -v

Actual solver calls, only from an explicitly qualified execution workspace:

    python3 studies/experimental-episodes/experiments/evidence-consumer-pilot-r1/pilot.py --output /tmp/episode-research-consumer-result.json --model

Provider failures are ERROR_NO_MODEL_SCORE, never silently synthetic or
wrong model answers. This tests **historical information accessibility for a
Research consumer**, not retrieval from a raw Episode memory store.

## Promotion limit

Even a perfect score establishes only that source evidence can answer these
specific historical questions. Neither a significant improvement in agent
coding success, causal uplift, a representative workload, nor a valid
DEVELOPMENT/JUDGE generalization claim follows. Retain HOLD until a real
agent task with actionable episode-level content, independent holdout, frozen
intervention, comparable compute budgets and an independent output oracle is
run.
