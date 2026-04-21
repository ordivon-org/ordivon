# Local Dev Runbook

## Goal

Boot the system locally without guessing where runtime data, policies, and entrypoints live.

## Current Entrypoints

- API: `apps/api/`
- Web: `apps/web/`
- Python package implementation during migration: `pfios/`

## Notes

- Treat root architecture folders as the destination for new code.
- Treat `data/` as local runtime output, not committed source-of-truth.
- Treat `infra/scripts/` as operational only; avoid adding business workflows there.
