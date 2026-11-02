---
name: systems-engineering
description: "Apply systems-engineering and systems-thinking framing to an already evidenced complex project: define the system of interest, environment, boundaries, interfaces, lifecycle, stakeholder outcomes, and whole-system properties before or while decomposing it into project-native elements. Use when scope is ambiguous, the project is a system-of-systems, local optimizations may conflict, or interfaces dominate behavior. Do not use as a generic project-management checklist."
compatibility: Cross-platform. Produces analysis evidence; it does not alter project truth by itself.
metadata:
  source-authority: ISO/IEC/IEEE 42010:2022 architecture descriptions / INCOSE systems engineering
---

# Systems Engineering

Use this method to frame the system before forcing a decomposition.

## Procedure

1. Name the system of interest in one sentence.
2. State the desired whole-system outcome separately from component outputs.
3. Identify the environment and external actors/systems.
4. Draw the system boundary and list every important boundary crossing.
5. Type interfaces by what crosses them: data, control, effect, identity, policy, observation, evidence, material/energy, or domain-native type.
6. Identify lifecycle phases that materially change ownership or interfaces.
7. Separate project-owned responsibilities from external authorities and assumptions.
8. Check for local optimization: ask whether improving one component can degrade the whole.
9. Only then propose or review project-native elements.
10. Record unresolved boundary/interface questions as uncertainty, not invented facts.

## Output

Produce a compact:
- system-of-interest statement;
- context/boundary map;
- interface inventory;
- lifecycle-sensitive concerns;
- whole-system properties;
- boundary ambiguities.

## Promotion law

Update the project project plan only when the analysis establishes an architecture-relevant boundary, responsibility, interface, or do-not-own fact.

## Non-claims

A clean boundary diagram does not prove correctness, completeness, feasibility, safety, or implementation standing.

## Stop condition

Stop when the system boundary, external authorities, major interfaces and whole-system outcome are clear enough that further framing will not change the next architecture decision.

Canonical local reference:
- catalogs/knowledge/lessons/lego-theory-foundations-r1.md
