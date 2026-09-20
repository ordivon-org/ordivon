# Studio Content Authority

## Purpose

Studio contains source-bound Claims, production manifests, editable creative sources, research priors, generated renders, review packets, selected media bytes, storage receipts, and publication Outputs. These objects answer different questions. They must not collapse into one creative or factual authority.

## Authority map

- [`../README.md`](../README.md) is the repository orientation and reader-path entry.
- [`../STUDIO.md`](../STUDIO.md) owns the current first-principles Studio design and technical responsibility boundaries.
- [`media-model.md`](media-model.md) owns the meaning and relationship of Blob, Asset, Claim, TimedText, Receipt, Production, and Output.
- [`../research/expression/README.md`](../research/expression/README.md) owns the Art & Expression research boundary and current cross-medium research programme. Research priors inform judgment; they do not create universal taste rules.
- Production manifests and their selected editable sources own production-local intent, source bindings, working state, and output declarations.
- Claim records bind allowed expression to exact source-owner revisions. A Claim is a production input, not a replacement for the source repository.
- Source repositories and their native evidence remain authoritative for current product/research facts.
- Exact selected binary/media bytes are owned by the durable byte authority named by their records; Git may be the exact-byte authority for canonical tracked text/code.
- Render/QC/review receipts prove only their scoped mechanical or review consequences.
- A published Output owns its exact delivery bytes and declared source Production revision. Publication does not make it the source project's current authority.

## Repository source-integration currentness

For a present-tense claim about the **Media repository, current Studio capability plane, or outstanding repository/publication work**, first resolve the canonical upstream repository `main` after explicitly observing remote freshness. In the current Git topology this is the fetched commit corresponding to `origin/main`. A local `refs/heads/main`, worktree `HEAD`, detached Runtime Workspace, or Workspace name can bind exact historical source bytes but does not by itself establish the present repository horizon.

Historical audits remain authoritative for what they observed at their own source/time fence; they are not automatically a live work queue. A stale source can therefore create a **phantom outstanding-work** failure: an external publication, merge, remote configuration, migration, or other bounded item that was genuinely open in the audit may already be complete now. Present work admission must re-enter through the current source horizon and, where the item is externally owned, re-observe the relevant external owner rather than replay the historical instruction.

This repository relation is separate from Media semantic authority, Production-local source bindings, current source-owner facts referenced by Claims, and external publication/platform state. Source integration tells an Agent which current Media repository surface to read; it does not turn Git recency into creative truth, external platform truth, or current production intent.

## Human-response evidence

Mechanical correctness, factual binding, browser/image transport, and Agent-observer success do not establish human comprehension, preference, trust, recall, emotional response, or aesthetic quality.

When a Production decision actually depends on such a human-response claim, retain only bounded evidence for the exact reviewed artifact and question. One observation must not be generalized into universal audience or taste authority.

## Historical versus current expression

A Production may truthfully preserve a historical Claim tied to revision `R` after the owner has moved to revision `R+1`. It must not silently reinterpret the old Production as describing the new owner state. A current re-expression requires an explicit source rebind and review.

## Generated and transient material

Generated renders, contact sheets, previews, critique text, caches, proxies, indexes, and temporary model generations are disposable unless a current Production or accepted decision names them as retained evidence or selected bytes.

Intermediate Agent critique is transient by default. The durable consequence is normally the source diff, selected artifact, updated Production cognition when needed, and bounded evidence that lets later work recover the decision.

## Status and reopen conditions

Accepted as the Studio authority map for the current repository structure.

Reopen when:

- a new medium introduces an authority that the current model cannot express;
- a publication platform begins owning creative state rather than consuming Outputs;
- human-response evidence gains a repeated shared contract that current production-local records cannot hold cleanly;
- a new storage mechanism changes which system owns exact selected bytes;
- two current Studio documents claim the same semantic authority.
