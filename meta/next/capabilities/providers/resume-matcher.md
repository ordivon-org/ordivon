# Provider experiment: Resume-Matcher

Status: **EXPERIMENT ONLY / NO ADMITTED CONSUMER**
Pinned release: `v1.4.0`
Commit: `dcd0962656e3e1ac2b4490689159362f9d48cd32`
Verified runtime for the historical experiment: **Python 3.13**

The provider demonstrated a useful preservation property on synthetic data: after creating and reading back a provider-canonical master, summary/bullet rewrites passed while an education-institution identity mutation failed with `education.identity`.

That experiment is **not an admitted Career binding**. The demonstrated path required stateful `create_master_resume` plus `get_resume`, and the observed default backend was ephemeral SQLite. This does not match a stateless initial tool boundary or Ordivon's PostgreSQL-first durable-state rule.

Resume-Matcher may be reconsidered only when a real consumer requires its preservation validator and the exact canonical-source/persistence composition is qualified. Its application CRUD, generic scoring, rendering and tracker roles remain excluded.
