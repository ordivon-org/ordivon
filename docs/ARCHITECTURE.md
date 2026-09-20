# Architecture

## 1. Mission

Ordivon is a compositional problem-solving environment. It exists to reduce the distance between a real problem and a verified result by making mature human knowledge and existing capabilities discoverable, selectable, composable, executable and verifiable by agents.

The repository must remain thinner than the external systems it composes.

## 2. Reference model

```text
                         REALITY
                            |
                         Problem
                            |
                            v
                  +-------------------+
                  | DEFINE / MAP      |
                  | Systems Eng.      |
                  +---------+---------+
                            |
                            v
+------------------------------------------------+
|              HUMAN KNOWLEDGE                   |
| KM | Domain Science | Standards | Methods       |
| Algorithms | Tools | Prior Evidence             |
+-----------------------+------------------------+
                        |
                        v
                 +---------------+
                 |   DSS / OR    |
                 | choose/solve  |
                 +------+--------+
                        |
                        v
                 +---------------+
                 | BPM / Planner |
                 | compose       |
                 +------+--------+
                        |
                        v
                  Agent + Tools
                        |
                       ACT
                        |
                        v
                 +---------------+
                 |      V&V      |
                 |   Evidence    |
                 +------+--------+
                        |
              +---------+---------+
              |                   |
            PASS                 FAIL
              |                   |
           Deliver          Re-diagnose
              |                   |
              +-------> Knowledge+
```

## 3. Persistent model vs active working set

Ordivon must not freeze the current list of disciplines, domains, standards, tools or infrastructure into a permanent architecture. Separate durable rules from the task-local working set.

### Persistent rules

Only a small set of invariants should be durable:

- start from a real problem/outcome;
- prefer mature external knowledge and capabilities over reinvention;
- make responsibility/authority explicit where actions have consequences;
- compose capabilities according to the current problem and constraints;
- verify outcomes with applicable evidence;
- retain reusable evidence-backed knowledge while keeping providers replaceable.

### Active working set

For a particular task Ordivon loads whatever is useful at that moment, for example:

- KM, DSS/OR, Systems Engineering, BPM or V&V methods;
- research, software engineering, game or other domain knowledge;
- applicable standards and algorithms;
- currently available tools, agents and services;
- Temporal, n8n, Snakemake, CI, Runtime, databases, observability or other execution facilities.

This set is analogous to working memory/cache: task-scoped, replaceable and discardable. Its current contents do not define Ordivon and do not imply a required dependency graph or upgrade path.

### Reality

The actual system, service, study, game, artifact, environment or other entity being changed remains the ultimate verification boundary.

## 4. Common flow

The common flow is intentionally small:

1. KNOW — retrieve relevant human knowledge and prior evidence.
2. DEFINE — model the entity of interest, boundaries, requirements, constraints and problem class.
3. DECIDE — select or solve among mature alternatives using DSS/OR/decision methods when useful.
4. PLAN — compose deterministic workflows and agentic decisions into an executable plan.
5. ACT — invoke tools and services.
6. VERIFY — evaluate against explicit acceptance criteria using domain-appropriate validators.
7. LEARN — record reusable composition/evidence relationships; update knowledge mappings, not private theory unless a real gap is proven.

## 5. Classification is a view, not a topology

Terms such as Domain Life-Cycle Profile, Cross-Cutting Discipline and Enabling Capability are classification aids. They help explain the role of something in a particular context; they are not permanent branches of an Ordivon object tree.

For example, Network may be an enabling capability in one task and the Entity of Interest in another. Security may be a cross-cutting concern in one task and a security service life cycle in another. Classification is contextual and may change with the problem boundary.

See `docs/CLASSIFICATION.md`.

## 6. E2E definition

`E2E` remains only as an internal shorthand for a complete life-cycle view of a clearly defined entity of interest.

An E2E profile is not a software subsystem. It is a domain-tailored composition of:

- entity/system/service of interest;
- life-cycle model;
- selected life-cycle processes;
- domain practices;
- information items;
- enabling systems/capabilities;
- verification and validation.

## 7. Common core is capability-neutral

The Common Core does not permanently contain KM, DSS/OR, Systems Engineering, Research, Engineering, BPM, V&V, a particular standard, or a particular tool. Those are mature capability families that may be activated when useful.

The durable core only needs enough semantics to acquire, contextualize, compose, invoke and verify external capabilities without making their current identities permanent. Mature external concepts and representations should be reused directly whenever possible; local bridge schemas exist only where machine-actionable interoperability requires them.

Therefore `Research`, `Engineer`, `Game`, `Temporal`, `n8n`, `MCP`, a specific standard, and similar names belong to catalogs, profiles, adapters or active working sets—not to a fixed progression encoded in Core.

## 8. Ownership rule

For every proposed Ordivon implementation, ask in order:

1. Is this already a mature discipline, standard, algorithm, tool, infrastructure capability **or product surface**?
2. What semantic object does it naturally own, and is that authority already represented by a mature provider?
3. Can configuration/profile/tailoring solve the current need?
4. Can direct reuse or a thin adapter solve the mismatch?
5. Is there measured evidence of a residual gap affecting a real task?
6. Only then consider minimal custom implementation.

Use `docs/CAPABILITY_AUTHORITY_MAP_R1.md` as the current cross-project routing view for natural authorities, provider activation triggers, do-not-build boundaries and verification boundaries. The map is a replaceable view, not a fixed architecture.

## 9. Verification rule

Execution success is never semantic success.

```text
process/tool success
        !=
domain requirement satisfied
        !=
real-world outcome validated
```

Agent statements are observations, not final authority. Verification should prefer independent domain validators, tests, benchmarks, formal checks or observable external state.

## 10. No fixed evolution path

Architecture does not prescribe `Game -> Research -> Software`, `KM -> DSS -> BPM`, or any other mandatory upgrade sequence. Current projects are merely the workloads and capabilities available at hand.

Work selection is demand-driven:

```text
current real problem
        -> discover relevant mature capabilities
        -> load a bounded working set
        -> compose/execute/verify
        -> retain useful evidence and mappings
        -> release the working set
```

A future task may start in Research, Engineering, Game, Finance, Security, Media or an unforeseen domain. Ordivon should be able to change that active set without an architectural migration.

## 11. Composition Science research framing

docs/COMPOSITION_SCIENCE_R1.md formalizes a research program above the existing LEGO lenses:

    Primitive Space
      -> Composition Space
      -> Dynamic / Control Space
      -> Verification Space
      -> Reachability
      -> Falsification
      -> reusable composition knowledge

This does not create a universal Ordivon ontology. It is a research framing for asking whether the scarce work in a given problem is primitive creation, relation/composition search, dynamic/control design, or verification.

Architecture-level consequences are narrower:

- search mature primitive/provider space before building;
- treat relations and dynamics as first-class rather than incidental glue;
- preserve natural authority during composition;
- build only the evidence-backed residual;
- retain problem -> composition -> evidence relationships as reusable knowledge.

The hypothesis that composition becomes a dominant innovation bottleneck in mature or agent-rich ecosystems remains open to prospective falsification.
