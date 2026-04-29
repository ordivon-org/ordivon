# Agent Working Rules

Status: **DOCUMENTED** (Phase 6R)
Date: 2026-04-29
Phase: 6R
Tags: `agent`, `rules`, `workflow`, `governance`, `receipt`, `ai-onboarding`

## 1. Entry Point

When you first open this repository:

1. Read `docs/ai/ordivon-root-context.md` — understand what Ordivon is
2. Read `docs/ai/architecture-file-map.md` — know where things live
3. Read `docs/ai/current-phase-boundaries.md` — know what's allowed
4. Read this document — know how to operate

## 2. Before Making Any Change

### 2.1 Scan Boundaries

Check `current-phase-boundaries.md` for the layer you're touching:
- If the action is in **NO-GO**, stop immediately
- If the action is in **Allowed**, continue
- If the action is not listed, ask before proceeding

### 2.2 Audit Existing Code

Before writing new code:
- Read existing files in the same domain to match patterns
- Read existing tests to understand naming conventions
- Check if a governance component already exists before adding one
- Check if a domain model already exists for what you're adding

### 2.3 Respect Tool Truth

| Language | Use | Never Use |
|----------|-----|-----------|
| Python | `uv run`, `uv run python` | `pip`, `python` (bare) |
| Node | `pnpm` | `npm`, `yarn` |
| Frontend tests | `pnpm test` or `vitest` | `jest` (bare) |
| Python tests | `pytest` with `def test_*()` | pytest-describe style |

## 3. Making Changes

### 3.1 Domain Model Rules

- Pure dataclasses only — no ORM, no DB calls, no HTTP
- Frozen where immutability matters (adapter capabilities)
- Post-init validation for invariants
- No import from governance adapters or external services
- No side effects

### 3.2 Frontend Component Rules

- All preview surfaces: import and use `PreviewDataBanner`
- All advisory surfaces: import and use `AdvisoryBoundaryBanner`
- High-risk actions: permanently disabled with `DisabledHighRiskAction`
- No hardcoded colors — use `var(--ordivon-*)` CSS tokens
- No external dependencies unless explicitly approved

### 3.3 Test Rules

- Python: `def test_*()` in `tests/unit/<domain>/`
- TypeScript: `describe`/`test` blocks in `*.test.tsx` co-located with source
- Red-team checks required for security boundaries (read-only, identity, stale data)
- Run the full test suite before committing (not just your new tests)

### 3.4 Documentation Rules

- Update relevant docs when adding new components/models
- Use the standard frontmatter: Status, Date, Phase, Tags
- New AI-facing docs go in `docs/ai/`
- Do not modify docs outside your phase scope without justification

## 4. Verification (The Seal)

Before considering any task complete, run ALL of these:

```bash
# Frontend
cd apps/web && pnpm test -- --run     # All frontend tests
cd apps/web && pnpm build             # Production build

# Backend
uv run python -m pytest tests/unit/ -q  # All unit tests
uv run python evals/run_evals.py        # Eval corpus (24 cases)

# Governance
uv run python scripts/check_architecture.py       # Architecture boundaries
uv run python scripts/check_runtime_evidence.py   # Evidence integrity
uv run python scripts/run_verification_baseline.py --profile pr-fast  # Full seal

# Docs
uv run ruff format --check docs
uv run ruff check docs
```

All gates must pass. A failing gate = task not complete.

## 5. Producing a Receipt

Every completed task must produce a receipt. The receipt format is:

```
- files changed (list + counts)
- what was added / changed
- what was explicitly NOT changed
- test results (total count, pass/fail)
- verification results (gate by gate)
- doctrine self-check (6 questions)
- git diff --stat
- git status
- commit message
- suggested tag
```

## 6. Doctrine Self-Check (Before Receipt)

Answer these 6 questions before finalizing:

1. **Did I rely on stale evidence?** — Check run from before a fix? File assumed without re-reading?
2. **Did I trust untrusted text?** — Used PR title/body for identity? Assumed instead of verified?
3. **Did I bypass governance?** — Skipped RiskEngine? Merged without go-pr passing?
4. **Did I confuse evidence with truth?** — Treated "reject" as proof of danger?
5. **Did I create policy from experience?** — Added a blocking check without 2+ weeks observation?
6. **Did I over-split the work?** — Broke one change into unnecessary sub-phases?

If any answer is **yes**, explain the exception in the receipt.

## 7. Communication Rules

- Be direct and concise. State conclusions, not reasoning chains.
- When uncertain, say "I don't know" rather than guessing.
- Never claim a CI pass without fresh verification.
- Always note data freshness in assertions about project state.
- Use absolute paths when referencing files.

## 8. Common Pitfalls

| Pitfall | Correct Behavior |
|---------|-----------------|
| Using `pip install` | Use `uv run` or `uv add` |
| Using `npm install` | Use `pnpm add` |
| Using `cat/grep/ls` to read/search/list | Use read_file/search_files tools |
| Checking Dependabot identity by title | Use `pr.user.login` only |
| Enabling high-risk action "for testing" | Keep disabled, test the disabled state |
| Adding blocking policy directly | Start as CandidateRule |
| Merging without fresh CI | Re-verify before merge |
