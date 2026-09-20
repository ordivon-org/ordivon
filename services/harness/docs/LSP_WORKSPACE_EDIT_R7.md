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

## Revision-bound verified provider path

After the pure adapter landed at:

```text
9c774b3 harness: add LSP WorkspaceEdit adapter
```

the local clangd rename flow was rerun from that exact revision. The observed path was:

```text
clangd 22.1.8
    -> textDocument/rename (square -> quad)
    -> WorkspaceEdit.changes
    -> pygls 2.1.1 transport donor
    -> Harness WorkspaceEdit adapter
    -> CanonicalEditPlan (1 file / 2 exact edits)
    -> Runtime workspace.patch
    -> committed
```

The server negotiated `utf-8` position encoding. Harness converted the proposal while
the source remained unchanged before Runtime admission. Runtime then committed from:

```text
before sha256:59f92d40809853654b25d0ba5c3c9692021b2820d6f927818b1a952d8f33b286
after  sha256:0bbf5c459448b66e3a4b7624820c81c8f594d49e9fca55ae7c99a9769c931fac
```

The verified receipt is:

```text
evidence/lsp-r7-clangd-runtime-patch-20260914.json
payload digest:
sha256:f16757f66ebfae75a815b5002c50a97e7aee50574639be1841bb5a55c949328d
```

This evidence admits the **provider path**, not a fixed transport dependency. `pygls`
remains experimental and absent from production dependencies. A second language server
or provider should be evaluated before selecting a default LSP transport/provider stack.

## Second provider — Taplo

The same committed adapter was exercised with the already-installed `taplo 0.10.0`
language server. Taplo advertises rename support and returned a standard
`WorkspaceEdit.changes` for TOML key rename `name -> title`.

Taplo did not advertise `positionEncoding`, so the provider path used the LSP default
`utf-16` semantics. Harness compiled one exact edit and Runtime committed:

```text
before sha256:291c2536d2d7fff1c726f0f11b9b286d717eca3b6da650330ed9187a6eade5cd
after  sha256:b51243ac16c473ecec65f0718264c65e36d9a5802e5e4ec58910f0b7ec769452
```

The verified receipt is:

```text
evidence/lsp-r7-taplo-runtime-patch-20260914.json
payload digest:
sha256:e8c6fb0040dac7c691373c24b3400d0e843bea7d1da345ce2fe22bc79f19e4b0
```

This proves the adapter is not clangd-specific: the same authority/snapshot/canonical
boundary works for at least two local language servers and two languages.

The transport conclusion remains deliberately negative. During the bare pygls/Taplo
probe, Taplo issued `workspace/configuration` and diagnostics traffic that the bare
LanguageClient probe did not handle. Rename still succeeded, but this is direct evidence
that transport lifecycle/configuration/diagnostic behavior needs a provider wrapper or a
more lifecycle-complete mature client before any default transport is selected.
