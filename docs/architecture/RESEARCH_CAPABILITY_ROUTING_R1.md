# Research Capability Routing R1

Date: 2026-09-29
Status: **CONVERGED SOURCE CANDIDATE / NOT LIVE-DEPLOYED**

## Decision

Admit a thin Research capability-definition and provider-routing composition, without creating a Research runtime, universal Registry, provider-status database, workflow engine, scientific ontology, or generic-Agent fallback.

The source model deliberately separates two objects:

```text
Research Capability Index
  stable capability meaning / semantic owner / completion owner / recipes
                    |
                    v
Research Routing Profile
  explicit problemClass -> specialist Skill/provider/workflow/data-plane route
                    |
                    v
current natural-owner observations
                    |
                    v
non-authoritative task-local resolution / typed HOLD
```

Natural-language interpretation remains Agent/caller-owned. Scientific semantics and completion remain Study/domain-owned.

## Canonical source split

### Capability definition

```text
profiles/research/capability-index/
  research-capability-index-r1.json
  research-capability-index-r1.schema.json
```

The index defines stable `research.*` capability semantics, source references, semantic/completion owners, Study applicability, route problem classes, and owner-native invocation recipes. It intentionally does **not** copy Skill candidate names. Skill candidates are derived from the routing profile.

### Provider / specialist routing

```text
.agents/skills/research-capability-routing/
  SKILL.md
  references/research-capability-routing-r1.json
  references/research-capability-routing-r1.schema.json
  scripts/route.py
```

The routing profile maps explicit Research problem classes to specialist Skills, Study-owned data-plane bindings, Snakemake, Temporal, Runtime, publication toolchains, standards bindings, or external providers. It consumes natural-owner observations and emits one exact route or a typed HOLD.

### Gateway projection retirement

The earlier source candidate generated a Gateway-local copy of the Research capability index/routing profile and exposed a Research-only `capability.resolve` path. Fresh executable-consumer census found no client that requires that duplicate semantic projection, while the canonical Research capability index and routing Skill already remain available at their natural owners.

The current source therefore retires:

```text
services/gateway/packaging/generate_research_routes.py
services/gateway/src/ordivon_gateway/research_routes.py
Gateway research.composition / research.* projection
Research-only capability.resolve
Gateway -> Skills owner bridge used only by capability.resolve
```

Generic Gateway `capability.search` and `capability.describe` remain because they have independent non-Research owner-routing value. Research semantic discovery/resolution remains canonical-index + routing-Skill + direct Skills-owner behavior rather than a copied Gateway policy surface.

This deletes duplicate policy projection without introducing a replacement registry or resolver.

## Existing owners preserved

- new Study creation/adoption + current data-plane defaults: `research-study-birth` / Research-v2 owner;
- reasoning/scientific method selection: `method-router` + domain/method authority;
- advisory procedures: Skills owner;
- scientific file/artifact DAG: Snakemake;
- durable process history/retry/wait/signals: Temporal;
- physical Workspace/Job/Attempt execution: Runtime;
- publication carrier mechanics: Artifact/toolchain;
- publication closure/perceptual QA: existing Research publication Skills/profiles;
- external standards: Authority Catalog + official sources;
- effect authorization: Security/provider IAM;
- scientific/domain completion: concrete Study or natural domain owner.

## Relation to Capability Projection Fabric

`CAPABILITY_PROJECTION_FABRIC_R1` still defines the generic CapabilityDefinition, Observation, Candidate, View, Admission, and Projection waist. Research R1 remains a concrete domain consumer of those separation laws, but its semantic taxonomy is not required to be copied into every generic capability projection.

The Research capability index is source-controlled definition metadata. The routing profile is domain composition metadata. Neither is provider availability truth. Gateway retains generic owner-routing/currentness projection for capabilities it actually serves, while Research semantics stay at the Research/Skill/Study natural owners.

The retired Gateway Research resolver did not authorize effects or establish scientific completion, but it duplicated canonical Research semantics and added a private Skills edge without a demonstrated executable consumer. Removing it narrows Gateway without changing Research capability meaning, routing behavior, or Study completion authority.

No `research.execute`, replacement `capability.resolve`, universal capability database, or Gateway workflow state is admitted.

## Gateway source candidate

The intentional public-surface contraction advances Gateway source identity to:

```text
packageVersion = 0.9.0
surfaceEpoch   = 6
public tool removed = capability.resolve
```

The generated `research.*` projection and Gateway-specific Skills owner edge are removed with that tool. `capability.search` and `capability.describe` remain generic owner-routing/currentness projections.

This is a **source candidate only** until normal Gateway release/deployment acceptance occurs. It does not claim that any current public carrier runs `0.9.0`, and it does not infer client catalog refresh from source currentness. Research routing remains usable through the canonical Research index, routing Skill, direct Skills owner, Study owner, Runtime, Temporal, publication toolchains, and other named natural owners.

## Route families

The routing profile covers 25 explicit problem classes spanning scholarly discovery/citation/synthesis, hypothesis/design, EDA/statistics/visualization/writing/review, rich/scholarly document parsing, Research data-plane actions, scientific DAG, durable process, physical execution, provenance, rendering, and publication closure.

Three graph-shaped systems remain intentionally distinct:

```text
scientific file/artifact DAG -> Snakemake
durable application/process state -> Temporal
physical effect commitment/evidence -> Runtime
```

No universal DAG abstraction is introduced.

## Research-v2 currentness boundary

Research-v2 remains the owner of Study Birth and current data-plane defaults. The routing profile names only binding coordinates and requires a current `study-data-plane` observation. It does not freeze DuckDB/Polars/Arrow/Parquet/Snakemake or any future replacement as permanent global truth.

Provider/tool/library presence likewise does not establish currentness. Skills use `skills.resolve/read`; Runtime uses Runtime/Gateway owner truth; Temporal and external providers use provider-native state; caller-bound connectors use current application connection state.

## Typed HOLD rule

If no specialist route is currently admissible, routing must return a typed HOLD such as:

```text
HOLD_CURRENTNESS_REQUIRED
HOLD_NO_READY_ROUTE
HOLD_NO_COMPATIBLE_ROUTE
```

A HOLD never implies a generic-Agent fallback. Repair/activate the missing natural owner or revise the explicit task requirement.

## Real dogfood

The pre-convergence routing candidate was exercised against Paper1/Paper2/Paper3 workloads. Examples included:

- Paper1 analytical query -> Study data-plane DuckDB binding;
- Paper1 validation -> Study data-plane validation set;
- Paper1 scientific DAG -> Snakemake;
- Paper1 durable process -> Temporal;
- Paper1 physical execution -> Runtime;
- Paper2 scholarly discovery -> `paper-lookup` Skill;
- Paper2 citation identity -> `citation-management` Skill;
- Paper3 publication closure/perceptual conformance -> project Research publication Skills;
- unavailable Docling/GROBID or degraded literature synthesis -> typed HOLD rather than generic fallback.

Dogfood evidence is dated observation evidence, not a provider-status database.

## Verification

Canonical source verification:

```bash
mise run research-routing:verify
```

This verifies:

1. routing profile against Draft 2020-12 schema;
2. capability index against Draft 2020-12 schema;
3. unique capability identities and valid route problem-class references;
4. deterministic specialist routing and typed HOLD behavior;
5. no generic-Agent fallback;
6. Study data-plane provider values come from owner observations;
7. route decisions do not claim authorization/execution/domain completion;
8. Snakemake, Temporal, and Runtime remain distinct;
9. canonical Research verification has no dependency on a generated Gateway semantic projection or Research-specific Gateway resolver.

Gateway owner qualification remains independently:

```bash
mise run gateway:verify
```

`repo:ci` now includes `research-routing:verify`; source qualification still does not establish live deployment or client catalog refresh.

## Acceptance boundary

R1 source can be called converged only when `research-routing:verify`, `gateway:verify`, `skills:verify`, `research-study:verify`, and repository architecture/CI gates pass on one current-main candidate.

Research routing live standing is established by the natural owners it selects, not by a Gateway Research projection. If Gateway `0.9.0` is deployed, its release receipt/readback and client catalog refresh qualify only the contracted generic Gateway surface; Research capability semantics continue to bind through the canonical index/routing Skill and direct owner observations.
