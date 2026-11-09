# MODERN_CRITERIA — 12 source-testable decisions

No numeric leaderboard. Each Owner gets PASS / PARTIAL / FAIL / UNKNOWN / N/A(reason) with file:line evidence and actual user-facing risk. The rules are constraints on effects, not an Nx/Turbo migration requirement.

| ID | Criterion | Falsifier | Actual source baseline |
| --- | --- | --- | --- |
| C01 | Natural owner / effect / data authority | Two Owners can write the same business truth | `tools/repo/owners.toml` |
| C02 | Domain/feature locality and deep interface | Cross-module change requires shotgun surgery | `services/harness/src/ordivon_harness/ordivon/run_continuity.py` |
| C03 | Enforced source dependencies | Cross-owner internals imported without declared seam | `tools/repo/check_owner_boundaries.py` |
| C04 | Shared code and thin adapters | One shallow facade reimplements another owner | `services/gateway/src/ordivon_gateway/mcp_server.py` |
| C05 | Identity, journal, CAS and evidence once | Conflicting current state in two active stores | `services/host/README.md` |
| C06 | Source-bound schema and release | Public contract claims drift from installed version | `services/runtime/docs/operations.md` |
| C07 | One effective cleanup/operation path | Multiple reclaimers independently drive active effects | `services/runtime/scripts/ordivon-runtime-lifecycle` |
| C08 | Dead assets and compatibility retirement | Retired plans survive as current task guidance | `services/runtime/planning/EXECUTION_FABRIC_R1_ROADMAP.md` |
| C09 | Source-true README / ADR / onboarding | Roadmap language presented as installed capability | `docs/architecture/STRUCTURE_R2.md` |
| C10 | Native verification and exact evidence | Model/test SUCCESS promoted to consumer SUCCESS | `tools/repo/check_architecture_docs.py` |
| C11 | Cross-platform and context boundary | Linux PG evidence used as Windows migration proof | `services/runtime/AGENTS.md` |
| C12 | Reuse before new layers / measured reduction | New registry/hook/control service replaces Git/PG/native tools | `.agents/skills/recursive-lego-calculus/SKILL.md` |

## Upstream proven patterns, not framework installation

- Nx: https://nx.dev/docs/features/enforce-module-boundaries — scope/tag-based static dependency rules.
- Turborepo: https://turborepo.dev/docs/reference/boundaries — package-local imports, experimental.
- Microsoft: https://learn.microsoft.com/en-us/dotnet/architecture/modern-web-apps-azure/common-web-application-architectures — domain depends on interfaces rather than infrastructure.
- Martin Fowler: https://martinfowler.com/bliki/MonolithFirst.html — modularity before unnecessary distribution.
- Google SRE: https://sre.google/workbook/eliminating-toil/ — remove operational toil at origin.
- Kubernetes TTL: https://kubernetes.io/docs/concepts/workloads/controllers/ttlafterfinished/ — terminal and owner distinction.
- Git worktrees: https://git-scm.com/docs/git-worktree — working tree is materialization, not immutable source.

## Existing native baseline before code mutation

- `python3 tools/repo/check_owner_boundaries.py` => exit 0; 2,320 scanned active files, 10 Python packages, 31 admitted seam policies, 38 witnessed source occurrences. It checks literal active-source paths and statically parsed Python imports, not all dynamic JS/Rust/OS connections.
- `python3 tools/repo/check_architecture_docs.py` => exit 0.
- `python3 tools/repo/check_composition_architecture.py` => exit 0.
