# Ordivon 2026-11-10 — source-stock audit scope

SourceCut: origin/main ef17d6879d12faa61fff3bb762b0d500d73c9113, 2026-11-10 +08. Frozen Git source truth, not installed/runtime/domain truth.

Goal: audit and simplify all current monorepo source (Host, Runtime, Harness, Gateway, Computing-related Composition/Data/Profiles, Security, Workstation, Network, Artifact, Media, Game, Capital, Web, Catalogs, root). No features, test-suite expansion, new consumer routes, product increment, duplicate Registry/Agent, global policy/hooks or non-Owner state mutation. Source-only deletion/merge/clarify/repair with rollback and existing native verification.

Authority: tools/repo/owners.toml schema_version=1, 21 natural Owner roots and 2 source regions. This mechanical manifest is navigation only, not a DDD aggregate or semantic state owner. AGENTS.md and the closest Owner README/AGENTS/Skill remain the procedural starting points, not evidence of installed truth. Computing is a responsibility allocation question, not automatically a distinct deployed subsystem.

Phase 0: identify exact root, owners, schema versions, live lifecycle, no-go overlaps and criteria. Phase 1: inventory all 5002 Git-tracked files; classify path, Owner, file kind and source bytes; AST/JSON parse where possible; inspect domain modules and entrypoints. Phase 2: evaluate major modules against ten checkable criteria using source/consumer evidence. Phase 3: dependency-bound small removal/repair plan; no new tests or consumers. Phase 4: act only within natural Owner, avoid concurrent PRs, run current native checks and retain Git rollback. Phase 5: frozen before/after evidence and honest merge/deploy/nonclaims.

Output: this scope; MODERN_CRITERIA.md; INVENTORY.md; FILE_LEDGER.tsv; AUDIT_REPORT.md; REFACTOR_PLAN.md; BASELINE_AFTER_AUDIT.md. The ledger is frozen metadata, not a living duplicate Source of Truth or proof that every line was semantically understood.

File inclusion: git ls-files at exact SourceCut. Ignore git internals, node_modules, .venv, target, runtime state, untracked working dirs and secrets. Do not open secret contents. Static lexical non-use is a hypothesis, not a closed dynamic consumer proof.

Actual authority boundaries: Host=Work/Space/Topic/Message/continuity PG, Runtime=Workspace/Job/Attempt/physical evidence, Harness=Agent tool/provider traces, Gateway=northbound routing, Security=principals, Network=transport, Workstation=deployment, Artifact=content/technical qualification, Game/Media/Capital/Web=domain acceptance, packages/composition=contract composition, packages/data=interop and producers own original data. Journal/CAS are not universally Host-owned; inspect the concrete owner of each fact.

Collaboration: Host Space topic 03-refinement records requests, source evidence and independent counterexamples. Handoff fields: SourceCut; owner; state; completed changes; existing verification commands and outputs; files/sha; outstanding UNKNOWN; next action/acceptance. Space messages are not independent CI/merge/consumer truth.
