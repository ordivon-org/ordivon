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

## 3. Four architectural layers

### A. Human Knowledge

Externally owned mature bodies of knowledge:

- Knowledge Management;
- Decision Support / Operations Research;
- Systems Engineering;
- BPM/workflow methods;
- Verification & Validation;
- domain sciences;
- standards;
- algorithms;
- tools and services.

Ordivon references and maps these. It does not redefine them by default.

### B. Knowledge-to-Action layer

The primary Ordivon-owned layer:

- Problem/ProblemClass mapping;
- Knowledge registry metadata;
- Capability registry;
- decision mappings;
- composition recipes;
- validator/acceptance mappings;
- provenance/evidence links;
- migration/disposition records.

### C. Execution environment

Replaceable mature infrastructure, currently including where appropriate:

- Temporal for durable long-running workflows;
- n8n for integration-edge automation;
- Snakemake/CI/domain-native workflows where they fit better;
- Ordivon Runtime only for exact local physical execution while it remains useful;
- PostgreSQL/object storage/Git for durable state and artifacts;
- OpenTelemetry for telemetry;
- MCP/native APIs/CLI/browser interfaces for tool access;
- container/OS/network facilities supplied by mature external systems.

No execution technology is part of Ordivon's ontology.

### D. Reality

The actual system, service, study, game, artifact, environment or other entity being changed. Reality is the ultimate verification boundary.

## 4. Common flow

The common flow is intentionally small:

1. KNOW — retrieve relevant human knowledge and prior evidence.
2. DEFINE — model the entity of interest, boundaries, requirements, constraints and problem class.
3. DECIDE — select or solve among mature alternatives using DSS/OR/decision methods when useful.
4. PLAN — compose deterministic workflows and agentic decisions into an executable plan.
5. ACT — invoke tools and services.
6. VERIFY — evaluate against explicit acceptance criteria using domain-appropriate validators.
7. LEARN — record reusable composition/evidence relationships; update knowledge mappings, not private theory unless a real gap is proven.

## 5. System/Domain classification

Top-level Ordivon organization is not a flat list of E2Es.

```text
Ordivon
├── Domain Life-Cycle Profiles
│   ├── Game
│   ├── Research
│   ├── Software / Engineering
│   └── future domains
├── Cross-Cutting Disciplines
│   ├── Security
│   ├── Quality
│   ├── Safety
│   └── Accessibility
├── Enabling Capabilities
│   ├── Compute
│   ├── Network
│   ├── Artifact processing
│   ├── Distribution
│   └── Agent execution
└── Shared Knowledge / Decision / Verification mappings
```

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

## 7. Common contracts: promote only after proof

Candidate common objects:

- Problem;
- ProblemClass;
- Requirement;
- Constraint;
- KnowledgeSource;
- Standard;
- Method;
- Algorithm;
- Capability;
- ToolProvider;
- Decision;
- Workflow;
- Validator;
- Evidence;
- Result.

These are not frozen ontology. A contract enters `schemas/` only after at least two materially different domains need the same semantics; promotion to a stable Common Core should preferably survive Game, Research and Software/Engineering use.

## 8. Ownership rule

For every proposed Ordivon implementation, ask in order:

1. Is this already a mature discipline, standard, algorithm, tool or infrastructure capability?
2. Can configuration/profile/tailoring solve the current need?
3. Can a thin adapter solve the mismatch?
4. Is there measured evidence of a residual gap affecting a real task?
5. Only then consider minimal custom implementation.

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

## 10. Initial vertical-slice strategy

1. Game — first real vertical slice and first domain taxonomy/standards/tool/validator mapping.
2. Research — deliberately different domain to challenge common assumptions.
3. Software/Engineering — third domain to determine what truly belongs in the shared core.
4. Only then consolidate stable cross-domain contracts.

No universal platform is built before these slices demonstrate demand.
