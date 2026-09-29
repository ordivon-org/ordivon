# Documentation

This directory contains maintained explanatory and reference documentation for the current repository model.

Lifecycle boundaries:

- current architecture, terminology, principles, provider-selection guidance and maintained operating references may live here;
- active plans, preregistrations and temporary migration ratchets belong in `planning/`;
- point-in-time acceptance results and experiment observations belong in `evidence/`;
- retirement, cutover, cleanup, census and other historical disposition records belong in `migrations/records/`;
- current provider-local availability belongs in `catalogs/capabilities/providers/` and must distinguish a dated observation from a presently revalidated fact.

A Markdown file is not machine authority merely because it is under `docs/`. Executable truth belongs to source, schemas, lockfiles, provider-native state and validation tools appropriate to the subject.

When a document is fully superseded and has no remaining current consumer, remove it from the working tree and rely on Git history rather than retaining a permanent construction archive.
