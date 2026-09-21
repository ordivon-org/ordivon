# Chaoxing Auto-Sign Assistant MVP

Status: implementation skeleton / safe default

This MVP implements the durable automation core discovered during the repository study:

- session lifecycle abstraction
- account/course/class/activity identity
- activity polling and normalization boundary
- planner with AUTO_ALLOWED / USER_VERIFICATION_REQUIRED / UNSUPPORTED
- SQLite idempotence ledger
- explicit transport/parse/semantic result separation
- retry/recovery state machine
- notification projection

The default build intentionally ships with a disabled remote submit adapter. It does not implement location/QR/face spoofing or other presence-proof bypasses. A deployment may plug in an authorized submission adapter for flows the operator is allowed to automate.

## Demo

```bash
PYTHONPATH=experiments/chaoxing-autosign-mvp python -m chaoxing_mvp.cli
```

The demo uses an in-memory/fake provider and a temporary SQLite database.

## Tests

```bash
python -m unittest tests.test_chaoxing_autosign_mvp
```
