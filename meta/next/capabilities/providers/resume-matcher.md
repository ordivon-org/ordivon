# Provider: Resume-Matcher

Status: **STABLE CLI + PRESERVATION VERIFIED / NARROW ARTIFACT PROVIDER**
Pinned release: `v1.4.0`
Commit: `dcd0962656e3e1ac2b4490689159362f9d48cd32`
Verified runtime: **Python 3.13**

Default host Python 3.15 failed dependency resolution because the tested onnxruntime wheel set lacked cp315. Python 3.13 is therefore part of the provider execution contract.

Resume-Matcher is admitted initially for schema, dry-run preservation, parse checking and scoring. Application CRUD is excluded so it cannot become a second application-state authority.

## Persistence boundary

`get_status` reports SQLite by default. That default is allowed only inside disposable provider-local smoke tests. Ordivon Career must not introduce durable SQLite. Any persisted Resume-Matcher deployment requires explicit PostgreSQL configuration and a real consumer.

## Verified preservation behavior

A synthetic canonical master was created and read back before deriving drafts. Summary/bullet rewrites passed. Changing the education institution failed with `education.identity`. This is the valuable provider behavior: preservation and grounding checks, not its ATS score.

ATS/match scores are advisory diagnostics only and must never be typed as hiring probability or employer judgment.
