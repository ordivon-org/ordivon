---
name: stpa
description: Apply STAMP/STPA-style system-theoretic safety or security analysis to a system when unacceptable losses can emerge from interactions, control actions, automation, software, humans, organizations, or authority relationships even if individual components work as designed. Use for safety-critical, security-sensitive, autonomous, multi-agent, or high-blast-radius systems. Do not reduce the analysis to a component failure checklist.
compatibility: Cross-platform. Produces system-level hazard/security analysis evidence.
metadata:
  source-authority: MIT STAMP/STPA / Leveson and Thomas
---

# STPA

Use this method when the critical question is not merely "which component fails?" but "which system interaction or control action can create loss?"

## Procedure

1. Define unacceptable losses in project-native terms.
2. Define system-level hazards: system states/conditions that, with a worst-case environment, can lead to a loss.
3. Build the relevant control structure:
   - controllers;
   - controlled processes;
   - control actions;
   - feedback/observations;
   - external influences.
4. Examine each important control action for unsafe forms:
   - action not provided when needed;
   - unsafe action provided;
   - action too early, too late, or in the wrong order;
   - action applied too long or stopped too soon.
5. Construct causal scenarios for the important unsafe control actions.
6. Derive candidate system constraints.
7. Map constraints back to project-native authority/interface boundaries.
8. Preserve uncertainty where evidence is missing.

## Security adaptation

For security-sensitive systems include:
- attacker-controlled inputs;
- compromised controllers/components;
- authority/delegation paths;
- misleading observations;
- unsafe but protocol-valid actions.

Do not assume "component behaved according to spec" implies the system is safe.

## Output

Produce:
- loss list;
- hazard list;
- control structure;
- unsafe control actions;
- causal scenarios;
- candidate safety/security constraints.

## Promotion law

A candidate constraint enters the architecture only after it is tied to a project-owned authority/interface and has an acceptance or verification strategy.

## Stop condition

Stop when the high-consequence losses relevant to the current design have constraints and testable scenarios, or when further analysis requires missing domain evidence.

Canonical local reference:
- knowledge/lessons/lego-theory-foundations-r1.md
