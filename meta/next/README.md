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
- repository-specific semantic/integration code only where a mature external owner does not already own the responsibility;
- task-local policy, evidence and provider bindings needed to prove real outcomes;
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
├── .agents/skills/  # standard Agent Skills procedures
├── authorities/     # external-authority records, observations and rebuildable discovery index
├── capabilities/    # capability/provider routing knowledge and task-local inventories
├── domains/         # domain-native life-cycle profiles
├── policies/        # native OPA/Rego policy artifacts where declarative policy is justified
├── plugins/         # Agent Plugins standard packaging artifacts
├── tests/           # behavior, integration, architecture and historical-integrity regression tests
├── scripts/         # current commands/validators only; historical reproducers do not live here
├── schemas/         # minimal cross-domain contracts after demonstrated reuse
├── experiments/     # bounded experiments and experiment-owned artifacts
├── evidence/        # point-in-time observations/receipts; never runtime configuration
├── planning/        # active/prospective work and explicitly disposable migration ratchets
├── migrations/      # retirement, cutover and historical disposition records
├── knowledge/       # reusable knowledge/provenance dependencies, not a construction diary
└── docs/            # maintained explanatory/reference documentation
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

This repository is managed as a non-package Python project. Standard PEP 621 metadata pins `requires-python ==3.14.7` and owns the runtime dependencies; `.python-version` selects the same interpreter, task-local validation dependencies live in dependency groups, and exact resolutions are recorded in `uv.lock`. The virtual-project metadata version `0.0.0` is not a release/versioning authority and the repository is not built or published as a Python package.

Core validation from a clean checkout:

```bash
uv run --locked python -m pytest
uv run --locked --group quality ruff check scripts tests
uv run --locked --group quality ruff format --check scripts tests
uv run --locked --group authority python scripts/check_authority_catalog_r1.py
uv run --locked --group authority python scripts/check_standard_native_enterprise_r2.py
uv run --locked --group reasoning python scripts/check_reasoning_waist_r1.py
```

PEP 621 project dependencies are the runtime/deployment dependency authority. The default `test` group adds only test-time dependencies. Lint/format quality, authority-catalog validation, security auditing, coverage analysis and heavier reasoning dependencies are separate groups and are installed only when their validation surface is invoked.

Security uses external tools directly rather than a repository-specific scanner. Bandit covers source heuristics, PyPA `pip-audit` checks known Python dependency vulnerabilities, and Gitleaks scans both repository history and the current tree for credential material. Gitleaks is a system-level external tool rather than a Python project dependency, so it is not mirrored into `uv.lock`. Reviewed false positives live only as exact fingerprints in `.gitleaksignore`; do not replace them with path-wide or rule-wide exclusions.

```bash
uv run --locked --group security bandit -r scripts -q -s B404,B603

gitleaks git --no-banner --redact=100 --timeout 120 .
gitleaks dir --no-banner --redact=100 .

tmp="$(mktemp -d)"
uv export --locked --all-groups --no-group security --format pylock.toml --output-file "$tmp/pylock.audit.toml"
uv run --locked --group security pip-audit --locked "$tmp" --progress-spinner off
rm -rf "$tmp"
```

Because `pip-audit` audits PEP 751 lockfiles rather than `uv.lock` directly, audit input is generated ephemerally from the exact uv lock and is never committed as a second dependency authority.

A dependency SBOM is likewise a rebuildable projection of `uv.lock`, not a hand-maintained repository artifact. Reuse the same ephemeral PEP 751 projection and let `pip-audit` emit its native CycloneDX document rather than binding repository policy to uv's preview SBOM exporter:

```bash
tmp="$(mktemp -d)"
uv export --locked --all-groups --no-group security --format pylock.toml --output-file "$tmp/pylock.audit.toml"
uv run --locked --group security pip-audit --locked "$tmp" --progress-spinner off --format cyclonedx-json --output sbom.cdx.json
rm -rf "$tmp"
```

Generate that SBOM for a release/evidence bundle when needed; do not commit it merely to duplicate lockfile state.
