# External LEGO Matrix

R1 follows DELETE-CUSTOM-BY-DEFAULT. These external systems are candidate providers, not code to copy.

| Provider | Mature ownership | Ordivon should consume | Ordivon should not recreate |
| --- | --- | --- | --- |
| NIST AI 100-2e2025 | AML terminology/taxonomy | threat-model vocabulary | a private competing AML taxonomy |
| OWASP GenAI LLM01 | prompt-injection risk framing | application threat catalog | another OWASP-like checklist |
| Microsoft PyRIT | red-team orchestration | attack/scorer/target adapter | generic attack workflow engine |
| NVIDIA garak | broad vulnerability scanning | probe/detector results | vulnerability scanner library |
| UK AISI Inspect AI | evaluation execution/logging | EvalLog artifacts, tasks, scorers, sandbox/model identity | generic LLM evaluation harness |
| UK AISI ControlArena | AI-control experiments | untrusted-policy/monitor/protocol experiments | custom control-research framework |
| Promptfoo | CI/application red teaming | application/agent scan artifacts and adaptive strategy results | CI red-team product clone |
| ClusterFuzzLite/Atheris | generic fuzzing | invariant-target execution for typed local contracts | custom byte/structure fuzz engine |
| HarmBench | attack/defense evaluation | standardized test-case evidence | benchmark pipeline clone |
| JailbreakBench | reproducible jailbreak benchmark | behavior/attack artifacts | leaderboard clone |
| StrongREJECT | jailbreak-success evaluation | evaluator comparison signal | custom subjective compliance score |
| EasyJailbreak | mutation/search decomposition | selector/mutator/constraint/evaluator adapter | mutation framework clone |
| AgentDojo | dynamic agent prompt-injection environment | agent-world experiments | fake productivity world from scratch |
| AgentThreatBench | memory/autonomy/exfil agentic evals | utility+security benchmark evidence through Inspect | bespoke OWASP agent benchmark |
| b3 / threat snapshots | agent-backbone vulnerability isolation | execution-state threat snapshots | full agent security benchmark clone |
| AgentHarm | post-jailbreak agent capability | capability-retention signal | custom harmful-agent benchmark |
| SHADE-Arena | sabotage + monitor evasion | main-task/side-task/stealth evaluation pattern | custom sabotage arena |
| Boundary Point Jailbreaking | black-box adaptive search | batch-level attacker/defender lessons | reimplementation of attack algorithm |
| CaMeL | control/data-flow defense architecture | architecture comparison / invariants | bespoke equivalent unless a gap is proven |
| OpenAI IH-Challenge / GPT-Red | instruction hierarchy + automated attackers | training/eval design lessons | vendor-specific training stack |
| Anthropic monitor research | monitor blind-spot methodology | monitor-as-target scenarios | assumption that monitor is trusted oracle |

## Normalized Ordivon boundary

External providers should eventually map into the following small ABI:

```text
ThreatModel
AttackSpec
AttackArtifactRef
TargetSpec
ObservationRef
JudgeSpec
Finding
RegressionReceipt
```

External framework-specific objects remain provider-owned and are referenced by immutable evidence rather
than flattened into one Ordivon mega-schema.

## Source ledger used for R1 design

Primary/current sources consulted on 2026-09-26:

- NIST AI 100-2e2025 — Adversarial Machine Learning taxonomy.
- OWASP GenAI LLM01:2025 Prompt Injection.
- Microsoft PyRIT current framework documentation and GitHub repository.
- NVIDIA `garak` current GitHub repository/documentation.
- HarmBench paper/repository.
- JailbreakBench paper/repository.
- AgentDojo paper/repository.
- CaMeL, *Defeating Prompt Injections by Design*.
- OpenAI, *Improving instruction hierarchy in frontier LLMs* (2026-03-10).
- OpenAI, *GPT-Red: Unlocking Self-Improvement for Robustness* (2026-07-15).
- Anthropic, *SLEIGHT-Bench: Finding Blind Spots in AI Monitors* (2026-05-19).
- Nasr et al., *The Attacker Moves Second* (2025).

The local study keeps claims at the level supported by these sources and does not import live attack
payloads from them.
