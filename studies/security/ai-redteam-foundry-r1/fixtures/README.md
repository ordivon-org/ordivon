# Provider replay fixtures

These are **synthetic, provider-shaped fixtures** used to test adapter semantics. They are not claimed to be
outputs from a live PyRIT or garak execution.

- `pyrit/scenario-results-attacks.synthetic.json` follows the field surface documented by current PyRIT
  `scenario-results <id> --view attacks --format json`: one row per attack containing id, technique,
  objective, outcome, turns, and score.
- `garak/report.synthetic.jsonl` follows the current report structure documented by garak and exercised by
  its own analysis code: a config record with target identity, attempt records, and eval records containing
  probe, detector, passed, and total_evaluated.
- `agentdojo/run.synthetic.json` follows the stable fields visible in AgentDojo run artifacts: suite/pipeline,
  user task, injection task, attack type, benchmark/package version, utility, and security. The boolean
  security field is intentionally retained verbatim rather than normalized into a universal attack-success
  bit.
- `inspect/eval-log.synthetic.json` follows documented Inspect `EvalLog`/`EvalSpec` identity plus sample score
  structure. It demonstrates a preferred common evaluation/logging substrate for AgentDojo, AgentHarm,
  AgentThreatBench, b3, CodeIPI, and other Inspect Evals without importing those benchmark implementations
  into Ordivon.

The adapter retains the exact fixture digest and only projects fields whose semantics are needed by the
Foundry. Provider-native artifacts remain the evidence source.

No live target, real jailbreak payload, credential, or external effect is present in these fixtures.
