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

### Gateway release projection

```text
services/gateway/packaging/generate_research_routes.py
  + capability index
  + routing profile
      -> services/gateway/src/ordivon_gateway/research_routes.py
```

`research_routes.py` is a generated release projection, not a second hand-authored authority. The generator embeds the exact index/routing digests, and `--check` verifies both source-digest currentness and semantic equivalence after normal Ruff formatting.

This yields one definition/provider source pair and multiple projections rather than duplicated Research policy.

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

`CAPABILITY_PROJECTION_FABRIC_R1` defines CapabilityDefinition, Observation, Candidate, View, Admission, and Projection. Research R1 is a concrete domain consumer of that waist.

The Research capability index is source-controlled definition metadata. The routing profile is domain composition metadata. Neither is provider availability truth. Gateway may project these definitions northbound because it adds stable discovery, current Skill binding, compatibility, and owner separation, but Gateway owns none of the underlying scientific/provider truth.

The source candidate therefore adds `research.*` entries to Gateway discovery and adds one read-only composition primitive:

```text
capability.search
capability.resolve
```

`capability.resolve` may bind exact current Skill bytes through the private Skills owner and may expose canonical invocation recipes. It does not execute the Skill, run the recipe, authorize an effect, or establish scientific completion.

No `research.execute`, `package.invoke`, universal capability database, or Gateway workflow state is admitted.

## Gateway source candidate

The converged source candidate advances Gateway to:

```text
packageVersion = 0.8.0
surfaceEpoch   = 5
new public tool = capability.resolve
```

It also adds an optional authenticated `skills` owner edge:

```text
ORDIVON_GATEWAY_SKILLS_URL
ORDIVON_GATEWAY_SKILLS_BEARER_TOKEN_FILE
```

Linux uses a systemd credential drop-in and Windows materialization accepts an explicit Skills URL + bearer path. Endpoint presence without machine identity remains `not configured`.

This is a **source candidate only** until normal Gateway release/deployment acceptance occurs. The live Gateway observed during convergence remained 0.7.0, with Runtime routes unconfigured and no live Research projection. ChatGPT connector catalog currentness is an additional consumer-owned state and must be re-established after release.

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
9. generated Gateway projection is source-digest current and semantically identical to the canonical index + routing profile.

Gateway owner qualification remains independently:

```bash
mise run gateway:verify
```

`repo:ci` now includes `research-routing:verify`; source qualification still does not establish live deployment or client catalog refresh.

## Acceptance boundary

R1 source can be called converged only when `research-routing:verify`, `gateway:verify`, `skills:verify`, `research-study:verify`, and repository architecture/CI gates pass on one current-main candidate.

R1 can be called live only after an exact Gateway release receipt/readback proves the 0.8 surface and authenticated Skills owner behavior, followed by a fresh consumer/connector tool-catalog refresh and at least one real `capability.search -> capability.resolve` Research dogfood path.
