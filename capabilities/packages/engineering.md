# Package: Engineering

Last census: 2026-09-14
Standing: **READY_FOR_REAL_WORK**

## Outcome scope

Turn requirements or a real defect/change request into a working, maintainable software or system result, including the necessary build, verification, integration, release, operation, maintenance, evolution or retirement work.

Engineering is a capability range, not a mandatory waterfall.

## Mature external knowledge owners

- ISO/IEC/IEEE 12207:2026 provides the common software life-cycle process framework.
- ISO/IEC/IEEE 15288:2023 provides the more general system life-cycle process framework and explicitly permits iterative, concurrent and recursive application rather than prescribing one lifecycle model or methodology.
- Domain/framework-specific engineering standards are selected when the entity of interest requires them.
- GitHub Spec Kit is used selectively as a source of proven agentic engineering practices; Ordivon does **not** depend on, fork, or reproduce its full CLI, workflow engine, templates, presets, extensions, bundles, integrations, feature numbering, task ledger, or artifact lifecycle.
- Superpowers is used selectively as a source of behavior-tested coding-agent disciplines such as fresh verification evidence, systematic root-cause debugging, context-isolated review/delegation and Skill behavior evaluation. Its mandatory brainstorming/TDD/task-review workflow is not adopted as a universal Ordivon lifecycle.

Ordivon does not publish a competing engineering lifecycle specification.

## Task-local engineering method kernel

For agent-driven implementation work, use the smallest useful subset of the following heuristic:

`FRAME -> PLAN -> EXECUTE -> VERIFY`

- **FRAME** — state goal, scope, constraints, acceptance evidence and material assumptions.
- **PLAN** — record only consequential approach decisions, alternatives, touchpoints, risks and verification strategy.
- **EXECUTE** — use the best mature executor/tool available; decomposition and dependency graphs may be transient.
- **VERIFY** — compare current reality against acceptance using the strongest practical evidence; do not treat executor assertions or process success as semantic completion.

The sequence is risk-adaptive, not mandatory. Small low-risk work may use `FRAME -> EXECUTE -> VERIFY`; additional planning, clarification, review, rollback, observability or independent validation is activated only when risk, uncertainty or coordination cost warrants it.

Testing is conditional; **verification is mandatory**.

Detailed rules and provenance are recorded in `knowledge/lessons/spec-kit-engineering-kernel.md`; complementary coding-agent discipline lessons are recorded in `knowledge/lessons/superpowers-engineering-discipline-kernel.md`.

## Observed local capability

- Codex and repository-scale codebase acquisition/review Skills;
- Git + GitHub CLI;
- Python/uv, Node/npm/pnpm, Java and common build tools including Make/CMake/Ninja;
- Docker and Podman;
- Runtime execution;
- Playwright skill for browser verification;
- n8n, Ansible and OpenTofu as available automation/configuration capabilities;
- Security, Artifact, Distribution, Network and Operations providers can be composed when the real engineering task requires them.

## Concrete current gaps

No generic Engineering gap is currently proven.

A missing language toolchain, test framework, simulator, compiler, SDK, cloud provider adapter, CI integration or specialist analysis tool becomes a gap only when the next real engineering workload requires it.

## Acceptance workload

The next real software/system change is the acceptance test:

`requirement/defect -> applicable engineering knowledge -> FRAME/PLAN as needed -> implementation -> VERIFY against current reality -> integration/release evidence -> observed target behavior`

Success is the real target outcome plus evidence, not conformance to an Ordivon-authored process sequence.
