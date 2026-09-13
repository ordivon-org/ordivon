# Classification

Before creating a repository, module, schema or E2E, classify the thing being discussed for the current problem boundary. Classification is contextual, not permanent: the same thing can play a different role when the Entity of Interest changes.

## Allowed top-level kinds

1. **Entity/System/Service of Interest** — the thing whose outcome matters.
2. **Domain Life-Cycle Profile** — complete domain-tailored life-cycle view of that entity.
3. **Life-Cycle Process** — a process applied during one or more stages.
4. **Cross-Cutting Discipline** — security, quality, safety, accessibility, etc.
5. **Enabling Capability/System/Service** — supports another life cycle.
6. **Method / Algorithm** — mature problem-solving mechanism.
7. **Tool / Capability Provider** — concrete implementation or service.
8. **Information Item / Artifact** — information consumed or produced by processes.
9. **Standard / Knowledge Source** — external normative or descriptive knowledge.
10. **Validator / Evidence Source** — produces evidence for acceptance.

## Decision test

Ask:

1. Is this the thing we ultimately want to create/change/operate/retire?
   - Yes: Entity of Interest / Domain Life-Cycle Profile.
2. Does it apply across many stages/domains as a concern?
   - Yes: Cross-Cutting Discipline.
3. Does it primarily help another entity achieve its life cycle?
   - Yes: Enabling Capability.
4. Is it a way to solve/compute/decide?
   - Yes: Method/Algorithm.
5. Is it a concrete implementation we can invoke or replace?
   - Yes: Tool/Provider.
6. Is it a requirement/specification/body of knowledge?
   - Yes: Standard/Knowledge Source.
7. Does it decide whether an outcome satisfies acceptance criteria?
   - Yes: Validator/Evidence Source.

Importance does not make something an E2E.

## Initial reclassification hypotheses for historical Ordivon

These are migration hypotheses, not final dispositions:

- Game -> Domain Life-Cycle Profile.
- Research -> Domain Life-Cycle Profile plus system-level knowledge-production role.
- Software/Engineer -> Domain Life-Cycle Profile heavily based on mature systems/software engineering.
- Market/Capital -> Domain Life-Cycle Profile where the economic/financial process is the Entity of Interest.
- Security -> primarily Cross-Cutting Discipline; may also have separate Security Service life cycles where explicitly the Entity of Interest.
- Network -> usually Enabling Capability; may become its own life-cycle profile when a network service itself is the Entity of Interest.
- Artifact -> usually Enabling Capability/Process family.
- Distribution -> usually Enabling Service/Process family.
- Runtime -> Execution Enabling Capability.
- Agent Birth -> Agent provisioning/orchestration Enabling Capability.
- Workstation -> Enabling System / operating substrate.
- Host -> retired historical mixed-responsibility container; no replacement entity. Residual mechanics belong to natural domain/external owners or disposable projections.
- Board -> retired authoritative concept; collaboration/work views belong to task-local mature systems, while any cross-owner overview is projection-only.
