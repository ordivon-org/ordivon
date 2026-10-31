# Provider: Career-Ops

Status: **NARROW DETERMINISTIC DIAGNOSTIC REPLAYED / BROADER WORKFLOW DONOR ONLY**
Pinned release: `@santifer/career-ops@1.38.0`
Release gitHead: `115bc9873e3d43e23883f3c8f16436617facc62c`

The package-level CLI is a workspace scaffolder: `npx @santifer/career-ops init [folder]`. Career diagnostics such as `jd-skill-gap.mjs` and `keyword-match.mjs` live inside the initialized stable-release workspace; they are not top-level npm subcommands.

The only behavior currently qualified for admission is the deterministic skill-gap diagnostic. Ordivon replays the exact stable release against committed synthetic fixtures with `meta/next/scripts/replay_career_provider_qualification.py`. Broader workflow/rubric/agent behavior remains a donor/reference until a real consumer is separately qualified.

## Currentness rule

The executable contract is the stable release. The initialized `1.38.0` script rejects `node keyword-match.mjs --url ...` with `Unknown option: --url`, while a newer upstream-main interface had documented URL/JD-text behavior. Main remains discovery evidence until the released artifact is independently replayed.

## Authority boundary

Career-Ops produces derived diagnostics only. Its file-first tracker is provider-local implementation and is not Ordivon durable truth. A gap result is not employer eligibility, hiring probability, submission receipt, or external outcome truth.
