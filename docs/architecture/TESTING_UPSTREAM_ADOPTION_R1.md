# Upstream-first testing — Agent operating guide (2026-10-16)

This is **navigation**, not a new test framework, a new Skill, or a second CI authority. Follow `AGENTS.md`: work in natural Owner directories; do not replace Owner verification with a generic green signal.

## Default Spec → SOP → Plan → Tool → Acceptance

1. **Spec**: state the observable behavior, failing counterexample, legitimate-equivalent control and pass/fail condition.
2. **Established SOP**: choose an upstream-native unit, property, integration, contract, browser E2E, or Godot visual/input testing practice; never create a per-Bug Skill.
3. **Execution Plan**: bind existing mature Skills (`user-agents/tdd`, `user-agents/diagnosing-bugs`, `obra-superpowers/verification-before-completion`) and actual Owner Tools.
4. **Execute** focused native test, then the Owner's `mise run verify` or documented queue qualification.
5. **Acceptance** reports exact source SHA, tool/runtime, test count, positive/negative/equivalent cases and separate **PASS / FAIL / SKIP / NOT_RUN / ENV_BLOCKED** status. Local green does not equal protected GitHub green.

## Use these existing mature sources, not another Ordivon framework

| Natural task | Preferred upstream / official docs | Ordivon native entry / decision |
| --- | --- | --- |
| Python behavior, fixtures, parameter tables | [pytest](https://github.com/pytest-dev/pytest), [fixtures](https://docs.pytest.org/en/stable/how-to/fixtures.html), [parametrize](https://docs.pytest.org/en/stable/how-to/parametrize.html) | `cd services/host && uv run python -m pytest -q tests/FILE.py`; also Harness/Gateway owner |
| Python generated invariants | [Hypothesis](https://github.com/HypothesisWorks/hypothesis) | Already in Host dev dependencies. Test real public behavior, shrink counterexamples |
| Disposable PostgreSQL | [testcontainers-python](https://github.com/testcontainers/testcontainers-python) | Already in Host dev dependencies; qualified small real PG18 trial, **not** approved to replace Host queue (see binding caveat) |
| Rust focused unit tests | [cargo-nextest](https://github.com/nextest-rs/nextest), [JUnit reference](https://nexte.st/docs/machine-readable/junit/) | `cd services/runtime && cargo nextest run --locked --lib -p ordivon-runtime-core --no-default-features --features transactional-runtime -E 'test(public_requests_reject_unknown_fields_and_path_escape)' -P ci`; native optional fast feedback |
| Rust complete source gate | [Cargo](https://github.com/rust-lang/cargo) | Keep `cd services/runtime && mise run verify` (Cargo + clippy + environment + docs). Nextest does not replace it |
| Browser end-to-end | [Playwright](https://github.com/microsoft/playwright) | Already pinned in Web, Game TS and Harness. Invoke existing Owner E2E tasks |
| TypeScript unit | [Node test runner](https://nodejs.org/api/test.html) | `cd apps/web && pnpm test`; `cd domains/game && pnpm test`. No new Vitest requirement |
| Native Godot 4 | [GUT](https://github.com/bitwes/Gut), [gdUnit4](https://github.com/godot-gdunit-labs/gdUnit4) | Candidate only. Verify actual project/engine/Godot headless input & video before installing either |
| Only if repeatable scaffold gap appears | [Cookiecutter](https://github.com/cookiecutter/cookiecutter), [Copier](https://github.com/copier-org/copier) | Do not install another generator globally until official Owner tools prove insufficient |
| Owner and CI tasks | [mise](https://github.com/jdx/mise), [GitHub Actions](https://github.com/actions/runner) | Owner `verify_task`, `queue_verify_task`, `tools/repo/affected_owners.py`; no parallel scheduler |

These repositories were checked against GitHub stars, recent activity and license metadata on 2026-10-16. A high star count is a **discovery filter**, not evidence of an installed tool or a reason to duplicate Node / Cargo / Python runners.

## Upstream-native test templates, not custom scaffolding

- Python: use pytest's **parametrize** for valid, invalid and equivalent cases; use **fixtures** to scope external dependencies; Hypothesis to generate inputs and shrink real failures. Source: official pytest/Hypothesis links above.
- PostgreSQL: `from testcontainers.community.postgres import PostgresContainer` with `with PostgresContainer("postgres:18", driver=None) as db: ...` is a working upstream context manager. A 2026-10-16 real local trial showed PG server version **180006** and successful teardown. **Safety caveat:** testcontainers-python 4.15.0 by default binds port to `0.0.0.0` and `::`, whereas Host's existing queue script binds `127.0.0.1`. Do not silently substitute it on shared/production host; a safe upstream-supported loopback bind must be demonstrated first. For disposable hosted CI, evaluate runner isolation separately.
- Rust: `cargo nextest` is already installed (0.9.143 in the inspected environment). An exact native sample selected **1 PASS / 389 filtered**, not a full-suite PASS. The optional source-local `services/runtime/.config/nextest.toml` CI profile writes a JUnit report in the native nextest output location; see official docs. Keep the established cargo verify gates.
- Godot: **no default GUT/gdUnit4 installation**; browser tests do not imply real Godot input or frame-based qualification.
- CI: use established Owner selection and real dependencies. A root `mise.toml` or `owners.toml` change may select all Owners, even if intended for one. Do not equate SKIP with PASS.

## Explicitly deferred, not silently constructed

Do **not** build `.agents/skills/ordivon-test-*` phases, a global test-results database, another test dispatcher, or new approval gates. Do not add Nx, Vitest, Cypress, Act, Playwright MCP or custom test-generation services without a specific unmet native consumer. Favor upstream instructions/templates over copying their internal code.

**Historical example only:** GitHub PR #129 (U4/Host PostgreSQL CI) currently has a separate required GitHub CI failure at Runtime supply-chain policy due to rustls 0.23.45 advisories. Its local Host PASS is not protected-main acceptance. This guide deliberately does not modify Runtime security dependencies or disguise that failure.
