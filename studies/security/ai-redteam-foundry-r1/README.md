# AI Red-Team Foundry R1

Status: EXPERIMENTAL SECURITY STUDY / NOT PRODUCTION SECURITY AUTHORITY
Date: 2026-09-26

## Purpose

This study turns LLM/agent red teaming into a durable Ordivon experiment rather than a prompt collection.
It is intentionally safe-by-construction: the built-in laboratory uses synthetic canaries, fake tools, abstract
attack operations, and deterministic world-state judges. It does not contain real credentials, destructive
payloads, or instructions for attacking third-party systems.

The research question is:

> Given a target contract and a bounded attacker budget, can an adaptive attacker discover an invariant
> violation, can we cluster the exploit into a root-cause family, and can a minimum-owner repair survive an
> adaptive re-test without degrading unrelated utility?

## Current local truth at opening

This study was opened from Ordivon source revision:

`7161e14a4b62229e9315a971eaf451008e6bac69`

The current repository already contains two important security boundaries that this study must not duplicate:

- `platform/security/docs/AGENT-ADMISSION-V0.md` owns authorization/effect admission semantics and already
  states that prompt-injection-induced privilege escalation must not expand granted capability.
- `services/harness/docs/DATA_AND_PRIVACY.md` owns Harness content-retention/privacy semantics and already
  states that malicious content can influence model output but cannot expand `ToolGrant` by itself.

The Foundry therefore owns *experimental adversarial evaluation*, not production authorization, runtime
containment, Harness privacy, or external-effect truth.

## First-principles model

We separate five objects:

1. `Capability` — what the target can in principle do.
2. `Elicitation` — which inputs/trajectories cause a behavior to appear.
3. `Policy` — what behavior the aligned target is intended to select.
4. `Authority` — what effects the surrounding system may actually execute.
5. `Evidence` — what can be proven about the attack, target, judge, and resulting world state.

A jailbreak or prompt-injection finding is therefore not stored as "magic text". It is stored as:

`ThreatModel -> AttackSpec -> TargetSpec -> Observation -> Judge -> Finding -> RootCause -> Patch -> RegressionReceipt`

## R1 invariants

The synthetic worlds currently test seven architecture-level invariants:

- **I1 — Untrusted data cannot gain privileged instruction authority.**
- **I2 — Model/agent output cannot increase its own effect authority.**
- **I3 — A tool observation cannot directly become a privileged external effect.**
- **I4 — A protected canary cannot cross an unauthorized output channel.**
- **I5 — Persistence cannot silently promote untrusted memory into privileged future cognition.**
- **I6 — Connect-time tool trust cannot silently authorize runtime contract drift.**
- **I7 — A monitor verdict cannot replace independent evidence of world-state violations.**

The invariants are deliberately domain-neutral. They are designed to support property-based adversarial
search rather than signature matching against known jailbreak strings.

## R1 attack-family ontology

The research taxonomy tracks mechanism/root-cause families rather than community prompt names. R1 now has
safe synthetic representatives for the bold families and adapter slots for the rest:

1. semantic reframing
2. context learning / many-shot
3. **trajectory shaping / multi-turn accumulation**
4. token-space optimization
5. attacker-model semantic search
6. **sampling / rare-tail search**
7. **indirect prompt injection / provenance confusion**
8. multimodal boundary attacks
9. internal model manipulation
10. **monitor / judge evasion**
11. **persistent memory/context poisoning**
12. **tool trust / runtime tool poisoning**

The Foundry deliberately classifies by mechanism/root cause, not by community prompt names.

## R1 architecture

```text
ThreatModel
   |
AttackEngine -----> AttackCandidate(s)
   |                       |
   |                       v
   |                    Target
   |                       |
   |                  Observation
   |                       |
   +--------------------> Judge
                           |
                        Finding
                           |
                     RootCauseMap
                           |
                     RegressionSet
```

The built-in target is a deterministic mock. External engines such as PyRIT, garak, HarmBench,
JailbreakBench, StrongREJECT, AgentDojo, or future Ordivon model providers should connect through adapters
rather than being reimplemented here.

## Evidence rule

A finding is only a research finding if it binds at least:

- target identity/version;
- threat-model identity;
- attack algorithm/family;
- attacker budget;
- deterministic seed where relevant;
- complete synthetic trajectory digest;
- judge identity;
- invariant violated;
- final world-state digest;
- root-cause hypothesis.

`Observation != Evidence != RootCause != Production Authority`.

## Verification

Run the owner-local verification:

```bash
python3 -m unittest discover -s studies/security/ai-redteam-foundry-r1/tests -p 'test_*.py' -v
python3 studies/security/ai-redteam-foundry-r1/scripts/run_synthetic_campaign.py
```

The campaign script emits deterministic JSON only. It does not contact external models or networks.

## Search/fuzzing ownership

The small `AbstractInvariantFuzzer` in this study is a deterministic fixture generator for testing budget,
clustering, and evidence semantics. It is **not** an admitted fuzzing provider and must not grow into a custom
fuzz engine. `platform/security/docs/CLUSTERFUZZLITE-ADMISSION-R1.md` already establishes the external-first
rule for executable fuzzing: ClusterFuzzLite/Atheris owns generic fuzz mechanics; PyRIT, garak,
EasyJailbreak/HarmBench-class providers own LLM-specific attack search. The Foundry owns only the invariant
surface, adapter/evidence seam, and cross-provider comparison.

## Next frontier

R2 should not add more bespoke attack algorithms. It should complete provider adapters and replay fixtures for
mature external systems, then compare them under the existing Ordivon evidence waist. Live provider/model
execution comes only after exact target identity, budget accounting, and raw artifact retention are proven.
