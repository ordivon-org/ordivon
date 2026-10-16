# Ordivon Monorepo Agent Rules

1. Work inside the natural owner directory.
2. Run that owner's native verification before claiming completion.
3. Do not import another owner's internals merely because they are in the same Git tree.
4. Cross-owner effects use the producing/consuming owners' explicit contracts.
5. Root tooling may orchestrate checks but may not redefine owner truth.
6. Do not unify lockfiles, environments, databases, releases, or scientific state as a repository-cleanup shortcut.
7. Keep source relocation separate from semantic refactoring.
8. Before designing a test template or automation, consult `docs/architecture/TESTING_UPSTREAM_ADOPTION_R1.md`; reuse the Owner's existing upstream framework and existing mature Skills. SKIP and NOT_RUN are not PASS.
9. When a test task begins, use existing Skills MCP `skills.search` and `skills.read` for upstream TDD/debugging/verification, then call the Owner's `mise tasks ls` and focused native test; do not treat a scoped PASS as whole-owner acceptance.
