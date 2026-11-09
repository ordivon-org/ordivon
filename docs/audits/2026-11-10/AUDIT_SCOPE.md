# AUDIT_SCOPE — Ordivon source baseline

SourceCut: ef17d6879d12faa61fff3bb762b0d500d73c9113
Tracked files: 5002; owner roots: 21; source control: one monorepo.

## Authority and boundary

Source: Git objects and tools/repo/owners.toml (schema_version=1). Runtime Job, Host Work, Harness Run, Domain state, installed binaries and Windows SQLite live state remain separately authoritative. Computing is not an independent current top-level root; inspect packages/composition and tools/formal. This document does not introduce a new governance authority.

## Hard exclusions

No new features, tests, consumers, product flows, registries, libraries, or framework installations. Existing tests may verify source reductions. No database or production deletion. Dirty workspaces and external installations are out of tracked-file scope.

## Execution phases

Phase0 pin SourceCut and the 12 criteria; Phase1 byte-level complete census; Phase2 module review with concrete paths; Phase3 small source-only refactor DAG and Git rollback; Phase4 execute only unclaimed path modifications; Phase5 record exact after-state and unresolved semantics.

## Evidence limitations

All 5002 files were hashed and Python AST parsed, but complete dynamic semantic consumer closure is NOT established per path. Zero static refs is not proof of no installed consumer. Six audit documents are a dated evidence package, while docs/architecture/OWNER_MODULARITY_STRUCTURE_LIFECYCLE_PROGRAM_R1.md is the active whole-system programme.


## Owner metadata actually declared in source (not live installation)

UNKNOWN means the current README/frontmatter/package root contains no matching field; it is not a fabricated default. Version is the Python/Cargo/package.json package declaration, not a database migration revision.

| Owner | Current package version | requires-python | README schema_version | lifecycle | source_role |
|---|---|---|---|---|---|
| authority-catalog | 0.1.0 | ==3.15.1 | UNKNOWN | UNKNOWN | UNKNOWN |
| capability-catalog | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| composition | 0.1.0 | ==3.15.1 | UNKNOWN | UNKNOWN | UNKNOWN |
| control-plugin | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| runtime | UNKNOWN | UNKNOWN | 1 | active | canonical |
| host | 0.8.0 | ==3.15.1 | UNKNOWN | UNKNOWN | UNKNOWN |
| harness | 0.6.0 | ==3.15.1 | 1 | active | canonical |
| gateway | 0.10.8 | ==3.15.1 | UNKNOWN | UNKNOWN | UNKNOWN |
| skills | 0.1.0 | ==3.15.1 | UNKNOWN | UNKNOWN | UNKNOWN |
| security | 0.1.0 | ==3.15.1 | UNKNOWN | UNKNOWN | UNKNOWN |
| workstation | 0.0.0 | ==3.15.1 | UNKNOWN | UNKNOWN | UNKNOWN |
| network | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| artifact | 0.0.0 | ==3.15.1 | UNKNOWN | UNKNOWN | UNKNOWN |
| distribution | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| media | 0.1.0-alpha.0 | ==3.15.1 | UNKNOWN | UNKNOWN | UNKNOWN |
| preservation | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| game | 0.1.0-alpha.1 | UNKNOWN | 1 | active | canonical |
| capital | 0.1.0 | ==3.15.1 | UNKNOWN | UNKNOWN | UNKNOWN |
| data | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| web | 0.1.0 | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| chaoxing-autosign | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
