# AI Red-Team Foundry R1 — Foundations

## 1. Threat-model dimensions

Every security claim must bind the attacker model. At minimum:

- knowledge: black-box / gray-box / white-box;
- access: text query / tool-output injection / model weights / monitor interface;
- budget: queries, tokens, wall time, compute, human iterations;
- adaptivity: static / transfer / defense-aware adaptive;
- state scope: one turn / conversation / run / cross-run memory;
- modality: text / image / audio / code / structured tool data;
- target: actor / classifier / monitor / judge / router / whole agent system;
- success object: text policy violation / secret disclosure / authority escalation / external effect.

A robustness number without these dimensions is not portable evidence.

## 2. Attacker moves second

The default Foundry threat model is defense-aware:

```text
Defender publishes D
      -> Attacker observes D
      -> Attacker searches specifically against D
      -> Defender measures adaptive robustness
```

Static benchmark resistance is retained as a regression signal, not treated as a proof of robustness.

## 3. Budgeted robustness

For attacker budget `B`, measure a curve rather than one number:

`ASR(B) = P(at least one invariant-violating candidate is found within budget B)`

R1's synthetic tail target is deterministic under a bound seed so the monotonicity of the discovery curve
can be tested without non-reproducible sampling.

## 4. Exploit != vulnerability != root cause

An exploit is one successful trajectory.
A vulnerability family is a class of trajectories that break the same contract.
A root cause is the owner-level mechanism whose correction should eliminate the family.

Example in this synthetic study:

```text
Exploit: untrusted tool record requests disclosure
    -> Vulnerability: tool data interpreted as privileged instruction
    -> Root cause: instruction/data provenance confusion
    -> Owner repair: separate trusted control flow from untrusted data flow
```

Blocking the exact exploit string is not a root-cause repair.

## 5. Minimum-correct-owner repair

For each failure:

1. identify the violated invariant;
2. identify the component that owns that invariant;
3. patch the smallest correct owner;
4. replay the original exploit;
5. mutate around the exploit family;
6. run an adaptive attacker that knows the patch;
7. run benign utility regressions;
8. bind the result into a regression receipt.

A broad retraining or new safety layer is not automatically preferred to a local architectural repair.

## 6. Model compromise != effect compromise

R1 treats a model/agent as a fallible cognitive provider. A successful content-level jailbreak should not,
by itself, imply external effect authority.

The long-run security goal is therefore not `P(jailbreak)=0`. It is to minimize expected system risk while
keeping blast radius bounded even when the model is manipulated.

## 7. Judge independence

The strongest judge is the world state, not another model's opinion. R1 judges synthetic outcomes using
exact state predicates (`canary_exfiltrated`, `authority_escalated`). Model judges may later be added only
as secondary evidence and must themselves enter the red-team surface.

## 8. Evidence tiers

- Tier A: standards/vendor primary documentation and peer-reviewed or directly inspectable research artifacts.
- Tier B: arXiv/research code with reproducible methods but weaker review guarantees.
- Tier C: GitHub issues, Reddit, Discord, blogs, and community experiments used for discovery/weak signals.

Community observations can create hypotheses; they cannot by themselves close a scientific finding.
