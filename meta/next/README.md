# Ordivon Next

Ordivon Next is a greenfield rebuild focused on one outcome: turning mature human knowledge and existing capabilities into verified real-world results.

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
├── capabilities/    # registry records for external capabilities and providers
├── compositions/    # reusable problem -> solution -> validation recipes
├── adapters/        # thin integration edges to mature external systems
├── verification/    # acceptance profiles and validator mappings
├── policies/        # responsibility/authority/risk rules
└── migrations/      # read-only mapping from historical Ordivon to the new model
```

## Rebuild rule

Historical Ordivon repositories are read-only inputs to migration analysis. Nothing is migrated merely because it existed before. A historical concept is retained only when it maps cleanly to the new model and still solves a real problem not already owned by a mature external capability.

The common core is adopted from mature, externally validated disciplines and standards rather than invented from Ordivon experiments. Domain slices such as Game, Research and Software/Engineering validate integration, tailoring and usability; they do not define whether the underlying mature disciplines are valid.
