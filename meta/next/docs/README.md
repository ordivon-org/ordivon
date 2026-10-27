# Documentation

This directory contains maintained explanatory and reference documentation for the current repository model.

Lifecycle boundaries:

- current architecture, terminology, principles, provider-selection guidance and maintained operating references may live here;
- active plans, preregistrations and temporary migration ratchets belong in `planning/`;
- point-in-time acceptance results and experiment observations belong in `evidence/`;
- retirement, cutover, cleanup, census and other historical disposition records belong in `migrations/records/`;
- current provider-local availability belongs in `capabilities/providers/` and must distinguish a dated observation from a presently revalidated fact.

A Markdown file is not machine authority merely because it is under `docs/`. Executable truth belongs to source, schemas, lockfiles, provider-native state and validation tools appropriate to the subject.

When a document is fully superseded and has no remaining current consumer, remove it from the working tree and rely on Git history rather than retaining a permanent construction archive.

## Agent-native source and carrier names

Resolve what a path **is** before inferring what it **does**. Prefer stable,
lowercase, responsibility-specific labels in navigation and communication;
do not rename import paths or service identities without a traced consumer
cutover.

| Source/effect distinction | Mechanical interpretation |
| --- | --- |
| `primary-source-repository` / `independent-git-source` | Different Git object stores and exact revision identities, not independent LEGOs by directory count |
| `linked-git-worktree` | A checkout sharing another repository's Git common directory; a worktree is not an independent source authority |
| `source-mirror` | Copied or shared path/blob content; identical blobs do not establish a safe replacement or consumer cutover |
| `non-git-data-corpus` / `upstream-reference-copy` | Physical evidence or vendor source, not a tracked Git package with inferred currentness |
| `composition-contract-document` | Canonical contract at `packages/composition/docs/`, not a pointer kept under Meta |
| `mcp-client-descriptor` / `mcp-server-implementation` | Configuration and running protocol implementation have distinct source and environment claims |
| `declared-provider-configuration` / `installed-provider-observation` | Source bytes alone cannot establish live executable, network or process identity |

The former temporary Meta compatibility pointers for Cognitive Circuit R1 and
Interface Contract Evolution R2 had no source consumers and were removed.
The canonical, actually maintained documents remain at
`packages/composition/docs/COGNITIVE_CIRCUIT_R1.md` and
`packages/composition/docs/INTERFACE_CONTRACT_EVOLUTION_R2.md`.

A source label is not a formal correctness verdict or a license to delete
a runtime consumer. For removal, identify the actual reader and compare the
mature replacement's input, output, state, failure and environment contract.
For a clean source-only duplicate, keep the natural implementation and delete
the obsolete wrapper. Other unproven consumers remain UNKNOWN.
