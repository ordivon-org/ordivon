# Ordivon Next

Ordivon Next is a greenfield rebuild focused on one outcome: turning mature human knowledge and existing capabilities into verified real-world results.

## One-sentence definition

**Ordivon turns real problems into verified outcomes by selecting and composing mature knowledge, methods, agents and tools instead of rebuilding them.**

The problem Ordivon solves is not generic execution. It is the higher-level problem of deciding what knowledge and capabilities a real problem requires, composing the right providers, carrying the work through, and establishing with evidence that the intended real-world outcome was actually achieved.

Its minimal problem-solving kernel is:

`KNOW -> DECIDE -> ACT -> VERIFY -> LEARN`

The fuller common loop below expands this kernel when problem definition and explicit planning are useful.

## Core loop

`KNOW -> DEFINE -> DECIDE -> PLAN -> ACT -> VERIFY -> LEARN`

Ordivon does not attempt to re-own mature disciplines, algorithms, tools, workflow engines, databases, network stacks, or domain science. It organizes and composes them.

## What this repository owns

- profiles and mappings that expose mature human knowledge and capabilities in a common usable form;
- domain life-cycle profiles;
- mappings from problem classes to mature methods, standards, algorithms, tools and validators;
- thin adapters to external execution systems;
- reusable, evidence-backed compositions;
- migration/disposition records for historical Ordivon components.

## What this repository does not own

- KM, DSS/OR, Systems Engineering, BPM, V&V as disciplines;
- domain science;
- external standards;
- generic algorithms;
- generic infrastructure;
- execution engines such as Temporal, n8n, Snakemake, CI systems, databases or container runtimes;
- tools such as Git, Blender, Godot, ffmpeg, R, Python, Lean, browsers, or external APIs.

## Structure

```text
ordivon-next/
├── docs/            # architecture, terminology, classification, migration rules
├── schemas/         # minimal common contracts; added only after cross-domain proof
├── knowledge/       # curated metadata/mappings to human knowledge, not copied world knowledge
├── domains/         # domain life-cycle profiles such as game/research/software
├── capabilities/    # external capability/provider records and task-local Capability Package inventories
├── compositions/    # reusable problem -> solution -> validation recipes
├── adapters/        # thin integration edges to mature external systems
├── verification/    # acceptance profiles and validator mappings
├── policies/        # responsibility/authority/risk rules
└── migrations/      # read-only mapping from historical Ordivon to the new model
```

## Rebuild rule

Historical Ordivon repositories are read-only inputs to migration analysis. Nothing is migrated merely because it existed before. A historical concept is retained only when it maps cleanly to the new model and still solves a real problem not already owned by a mature external capability.

The common core is capability-neutral. Mature disciplines, domains, standards, tools and execution systems are activated as a task-local working set and may change without changing Ordivon itself. There is no prescribed domain sequence or upgrade path.


## Standard-native enterprise environment

See `docs/STANDARD_NATIVE_ENTERPRISE_ENVIRONMENT_R2.md` for the current cross-domain operating contract for binding external authorities, applicability, stable trace identities, evidence, currentness, claim boundaries and domain-owned verdicts. It is an interoperability environment, not an Ordivon replacement for external standards.

## Enterprise operating model

See `docs/ENTERPRISE_OPERATING_MODEL_R1.md` and `compositions/enterprise-work-to-outcome-r1.md` for the demand-gated composition of mature quality/project/risk/audit guidance with ERPNext, Host v2, Flowable, Temporal, n8n, Runtime and domain-native V&V. Providers remain dormant unless a real responsibility justifies activation.

## Current common capability coverage

See `docs/CAPABILITY_PACKAGES_R1.md` for the current high-frequency Capability Package working map. It is a task-oriented coverage inventory, not a fixed architecture.
