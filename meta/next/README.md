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
├── authorities/     # lightweight external-authority records, observations and generated discovery index
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

`authorities/` provides the lightweight discovery layer in front of that environment: version-aware authority identity records, append-only currentness observations and a disposable generated index. It helps find/load authorities cheaply; task-local profiles still decide applicability.

## Authority and policy composition

See `knowledge/lessons/authority-mature-substrate-decomposition-r1.md` for the current cross-disciplinary authority map. Ordivon does not claim a novel authority theory: institutional governance, evidence-to-decision, decision science, delegation, IAM/policy engines and adaptive/institutional learning remain externally owned mature substrates. `policies/` keeps only the thin task-local composition boundary and must not become a custom policy language, IAM system, generic Human gate or universal risk gate.

## Enterprise work routing

The optional `.agents/skills/enterprise-work/` Skill is a thin router from consequential work to current external authorities and natural providers. `docs/ENTERPRISE_OPERATING_MODEL_R1.md` remains the detailed provider/currentness and historical dogfood reference. There is no universal Ordivon enterprise-work lifecycle or mandatory provider composition.

## Current common capability coverage

See `docs/CAPABILITY_PACKAGES_R1.md` for the current high-frequency Capability Package working map. It is a task-oriented coverage inventory, not a fixed architecture.


## Repository validation

This repository is managed as a non-package Python project. The interpreter is pinned by `.python-version`, dependency groups are declared in `pyproject.toml`, and exact resolutions are recorded in `uv.lock`.

Core validation from a clean checkout:

```bash
uv run --locked python -m unittest discover -s tests -p 'test_*.py' -v
uv run --locked --group architecture lint-imports
uv run --locked --group quality ruff check agent_service scripts tests
uv run --locked --group authority python scripts/check_authority_catalog_r1.py
```

The default `test` group composes the runtime and deployment dependencies required by the complete unit and repository test suite. Architecture, quality, authority-catalog validation and heavier reasoning dependencies are separate groups and are installed only when their validation surface is invoked.

The read-only Agent Service canary uses the same lockfile. Its deployment environment is materialized without test/analysis groups:

```bash
uv sync --locked --no-default-groups --group deployment
```
