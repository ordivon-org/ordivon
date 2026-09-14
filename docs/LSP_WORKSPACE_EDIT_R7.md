# LSP WorkspaceEdit R7

Status: prototype adapter validated locally; transport/provider dependency not yet admitted

## Objective

Use mature Language Server Protocol implementations for semantic code intelligence while
keeping Harness authority and Runtime physical consequence boundaries unchanged.

The intended composition is:

```text
Language Server
    -> LSP client transport
    -> WorkspaceEdit proposal
    -> Harness URI/version/snapshot/encoding validation
    -> CanonicalEditPlan
    -> Runtime workspace.patch
```

The language server is not a file-mutation authority. A returned `WorkspaceEdit` is a
proposal that must be rebound to Harness-owned source identity before it can become a
physical effect.

## Implemented R7 adapter slice

`ordivon_harness.lsp_workspace_edit.workspace_edit_to_canonical_plan()` accepts:

- a JSON-shaped LSP `WorkspaceEdit`;
- explicit `LspDocumentBinding` values from server URI to an already-authorized exact
  `SourceSnapshot`;
- the negotiated LSP position encoding (`utf-8`, `utf-16`, or `utf-32`).

It produces the existing `CanonicalEditPlan`, so Runtime lowering and durable Patch
reconciliation remain unchanged.

Supported mutation proposals:

- `WorkspaceEdit.changes` containing non-overlapping TextEdits;
- `WorkspaceEdit.documentChanges` containing TextDocumentEdits only;
- multiple TextEdits for one exact file snapshot;
- multiple server URI aliases for one Harness path only when their proposed edit sets
  are identical.

Fail-closed cases include:

- URI without an explicit Harness binding;
- conflicting URI aliases for one Harness path;
- numeric `TextDocumentEdit` version differing from the caller-owned document version;
- versioned edit when the caller has no document-version binding;
- unsupported/resource operations (`CreateFile`, `RenameFile`, `DeleteFile`);
- overlapping text edits;
- position outside the exact snapshot;
- UTF-8/UTF-16 offsets that split an encoded character;
- unknown position encoding;
- no-op edits.

A `null` LSP document version is not treated as proof of freshness. It means only that
the server did not assert a version. Physical currentness is still fenced by the exact
`SourceSnapshot.digest` carried into Runtime `workspace.patch.expectedDigest`.

## Position semantics

LSP `Position.character` is an offset in the negotiated encoding, not necessarily a
Unicode-character column. Runtime Patch uses one-based lines and zero-based Unicode
character columns. The adapter therefore converts:

```text
LSP 0-based line + encoding-unit character
    -> exact source text position
    -> Runtime 1-based line + Unicode-character column
```

This is required for non-ASCII text, especially UTF-16 surrogate pairs.

## URI identity law

A `file://` URI is provider data, not Harness authority.

```text
server URI
    != workspace authority
    != source identity
```

The provider/integration layer must explicitly bind each accepted URI to a Harness
relative path and exact `SourceSnapshot`. Different URIs may bind the same path when a
server exposes path aliases. Identical alias edit sets are deduplicated; conflicting
sets fail closed.

## Local donor probe

The local machine currently provides `clangd 22.1.8`. A temporary, non-production
`pygls 2.1.1` LanguageClient probe successfully exercised:

- initialize / initialized;
- didOpen;
- definition;
- hover;
- rename returning a standard WorkspaceEdit;
- shutdown / exit.

A real rename (`square -> quad`) was lowered through this adapter into two canonical
text edits and then into one digest-fenced Runtime `workspace.patch`. Runtime committed
the physical result while the LSP client/server remained proposal-only.

`pygls` is **not** currently a Harness production dependency. It is an experimental
transport donor. The stable R7 waist is the JSON-shaped WorkspaceEdit adapter, so a
future provider can use pygls, another mature client, or a host-native LSP service
without changing Harness mutation authority.

## Deliberate exclusions

R7 does not yet admit:

- LSP resource operations;
- server-initiated `workspace/applyEdit` as direct write authority;
- automatic language-server installation/provisioning;
- a fixed production LSP client library;
- file-watcher ownership;
- LSP-generated edits outside the Run/Tool Grant.

These remain provider/integration decisions and require separate authority evidence.

## Next evidence gate

Before admitting a production LSP transport provider:

1. commit and fully regress the pure WorkspaceEdit adapter;
2. rerun the local clangd rename on that exact committed revision;
3. retain a revision-bound evidence receipt covering proposal -> canonical plan -> real
   Runtime Patch;
4. compare at least one second language server/provider before fixing a default client;
5. keep server provisioning and mutation authority outside the adapter contract.
