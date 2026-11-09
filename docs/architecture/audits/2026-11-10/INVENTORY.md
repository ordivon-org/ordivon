# INVENTORY — source tree at source SHA ef17d6879d12faa61fff3bb762b0d500d73c9113

All 5,002 tracked files have an exact path, source owner, type, bytes and line estimate in [INVENTORY_FILES.tsv](INVENTORY_FILES.tsv). This is a mechanical inventory, not a claim of complete human semantic review. Untracked build outputs, .git and node_modules are excluded.

## Real Git root directories

| Directory | Tracked files |
| --- | ---: |
| `services` | 1407 |
| `capabilities` | 1054 |
| `domains` | 786 |
| `platform` | 663 |
| `catalogs` | 532 |
| `packages` | 105 |
| `docs` | 104 |
| `studies` | 89 |
| `tools` | 65 |
| `.agents` | 63 |
| `extensions` | 47 |
| `apps` | 46 |
| `profiles` | 17 |
| `.github` | 13 |
| `tests` | 2 |
| `.gitignore` | 1 |
| `.gitleaksignore` | 1 |
| `AGENTS.md` | 1 |
| `CONTRIBUTING.md` | 1 |
| `LICENSE` | 1 |
| `README.md` | 1 |
| `SECURITY.md` | 1 |
| `mise.toml` | 1 |
| `renovate.json` | 1 |

## Natural Owners

The owner registry is `tools/repo/owners.toml` with `schema_version=1` (repository mechanics only). README metadata below is parsed only when frontmatter is present; `not_declared` means no such declaration, not an invented lifecycle status.

| Owner | Directory | Tracked paths | README schema_version | lifecycle | Local entry files / top subtrees |
| --- | --- | ---: | --- | --- | --- |
| authority-catalog | `catalogs/authorities` | 376 | `not_declared` | `not_declared` | README.md, mise.toml, pyproject.toml; observations(182), records(176), scripts(5), schemas(3), evidence(2), .gitignore(1) |
| capability-catalog | `catalogs/capabilities` | 77 | `not_declared` | `not_declared` | README.md, AGENTS.md; providers(36), packages(13), evidence(5), ele(4), scripts(4), tests(4) |
| composition | `packages/composition` | 86 | `not_declared` | `not_declared` | README.md, AGENTS.md, mise.toml, pyproject.toml; src(24), tests(23), formal(16), docs(7), policies(4), scripts(4) |
| control-plugin | `extensions/ordivon-control-plane` | 2 | `not_declared` | `not_declared` | ; mcp.json(1), plugin.json(1) |
| runtime | `services/runtime` | 452 | `1` | `active` | README.md, AGENTS.md, mise.toml, Cargo.toml, pyproject.toml; crates(139), research(132), scripts(67), docs(23), formal(18), packaging(11) |
| host | `services/host` | 117 | `not_declared` | `not_declared` | README.md, AGENTS.md, mise.toml, pyproject.toml; tests(38), src(37), migrations(15), docs(6), packaging(4), planning(4) |
| harness | `services/harness` | 731 | `1` | `active` | README.md, mise.toml, pyproject.toml; tests(182), evidence(139), research(97), scripts(87), src(62), evals(48) |
| gateway | `services/gateway` | 107 | `not_declared` | `not_declared` | README.md, AGENTS.md, pyproject.toml; tests(31), src(26), formal(18), packaging(12), planning(7), systemd(6) |
| skills | `extensions/chatgpt-skills-mcp` | 45 | `not_declared` | `not_declared` | README.md, mise.toml, pyproject.toml; tests(19), src(9), docs(3), scripts(3), config(2), plugins(2) |
| security | `platform/security` | 162 | `not_declared` | `not_declared` | README.md, mise.toml, pyproject.toml; labs(29), tests(24), scripts(23), docs(15), src(14), contracts(13) |
| workstation | `platform/workstation` | 265 | `not_declared` | `not_declared` | README.md, mise.toml, pyproject.toml; providers(58), tests(40), workstation(40), ansible(20), docs(16), scripts(13) |
| network | `platform/network` | 236 | `not_declared` | `not_declared` | README.md, AGENTS.md, mise.toml; consumers(105), tests(32), providers(20), acceptance(16), config(10), reference(9) |
| artifact | `capabilities/artifact` | 425 | `not_declared` | `not_declared` | README.md, mise.toml, pyproject.toml; artifact-delivery(180), tests(72), scripts(43), docs(28), artifact_capabilities(22), artifact_verifiers(21) |
| distribution | `capabilities/distribution` | 30 | `not_declared` | `not_declared` | README.md, mise.toml; evidence(15), scripts(6), adapters(3), .gitignore(1), README.md(1), docs(1) |
| media | `capabilities/media` | 553 | `not_declared` | `not_declared` | README.md, AGENTS.md, mise.toml, pyproject.toml, package.json, pnpm-workspace.yaml; productions(213), research(110), src(70), tests(26), scripts(21), apps(19) |
| preservation | `capabilities/preservation` | 46 | `not_declared` | `not_declared` | README.md; artifacts(32), docs(5), scripts(3), systemd(2), README.md(1), SOURCE_BOUNDARY.json(1) |
| game | `domains/game` | 387 | `1` | `active` | README.md, AGENTS.md, mise.toml, package.json; examples(333), test(9), scripts(8), knowledge(7), research(7), docs(6) |
| capital | `domains/capital` | 399 | `not_declared` | `not_declared` | README.md, mise.toml, pyproject.toml; tests(100), src(65), tools(53), scripts(50), config(28), evidence(26) |
| data | `packages/data` | 19 | `not_declared` | `not_declared` | README.md, AGENTS.md, mise.toml; src(5), docs(4), formal(3), scripts(2), tests(2), AGENTS.md(1) |
| web | `apps/web` | 35 | `not_declared` | `not_declared` | README.md, mise.toml, package.json, pnpm-workspace.yaml; src(15), test(7), evidence(3), .gitignore(1), README.md(1), agent-native-e2e.sh(1) |
| chaoxing-autosign | `apps/chaoxing-autosign` | 11 | `not_declared` | `not_declared` | README.md; chaoxing_mvp(9), README.md(1), tests(1) |

## Live boundary facts and risks

- 21 registered natural Owners; two root-only source regions `tools/repo` and `tools/formal`. There is no currently registered top-level `computing/` Owner.
- Source roots include services Host/Runtime/Harness/Gateway, platform Security/Network/Workstation, capabilities Artifact/Media/Distribution/Preservation, domains Capital/Game, packages Composition/Data, apps Web/Chaoxing, and catalogs.
- The repository target `docs/architecture/STRUCTURE_R2.md` is only partially deployed; do not globally rename roots to `packages`.
- Physical deployment differs from a source directory: Runtime Linux systemd lifecycle.service executes PG-native `ordivon-runtime-pg-reclaim`.
- Important source modules: `services/harness/src/ordivon_harness/ordivon/run_continuity.py` (3186 lines), `services/runtime/crates/ordivon-runtime-core/src/runtime/engine.rs` (1860), `apps/web/src/app.ts` (721), `apps/web/src/store.ts` (810), `capabilities/artifact/artifact_operations/providers/direct_python.py` (606).
- Missing README lifecycle metadata does not imply a wrong schema. Each owner may have its own manifest format.
