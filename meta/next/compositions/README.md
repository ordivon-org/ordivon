# Compositions

A composition is a reusable, evidence-backed problem-solving recipe.

Conceptually:

```text
ProblemClass
  + applicability conditions
  + knowledge/methods
  + selected capabilities/providers
  + workflow/decision points
  + validators/acceptance criteria
  -> verified outcome
```

Compositions are expected to become one of Ordivon's primary long-lived assets. Prefer recording successful relationships and applicability evidence over adding bespoke infrastructure.

The former generic enterprise-work composition was retired after its routing knowledge moved into the thin `enterprise-work` Skill and external authority/provider records. Do not recreate a generic enterprise lifecycle as a reusable composition.

Current reasoning composition: `problem-to-plan-reasoning-waist-r1.md` binds mature graph validation, configuration/constraint solving, and planner-neutral plan generation without owning domain semantics or execution.
