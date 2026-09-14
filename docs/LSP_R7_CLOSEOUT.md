# LSP R7 Closeout

Status: core boundary closed; production provider selection deferred

## Objective

R7 asked whether Harness could compose mature Language Server Protocol capabilities
without transferring file-mutation authority, source identity, or Runtime consequence
ownership to the language server or its client library.

The answer is yes for the stable Harness boundary. The remaining uncertainty is now a
replaceable integration/provider choice rather than a Harness semantic gap.

## Closed architecture

```text
Harness Run / Tool Grant
    -> external LSP lifecycle provider
        initialize / configuration / diagnostics / request lifecycle
    -> WorkspaceEdit proposal
    -> Harness URI + version + exact snapshot binding
    -> CanonicalEditPlan
    -> Runtime workspace.patch
    -> durable physical receipt
```

The provider does not own workspace mutation. A file URI is not authority identity, an
LSP document version is not a substitute for the exact Harness source digest, and a
WorkspaceEdit is not an execution grant.

## Delivered Harness primitives

### WorkspaceEdit adapter

`ordivon_harness.lsp_workspace_edit.workspace_edit_to_canonical_plan()` converts a
JSON-shaped LSP WorkspaceEdit into the existing CanonicalEditPlan after explicit caller
bindings.

It currently supports:

- `WorkspaceEdit.changes`;
- TextDocumentEdit-only `documentChanges`;
- multiple non-overlapping edits per exact snapshot;
- UTF-8, UTF-16, and UTF-32 position encodings;
- URI aliases only when their bound source and proposed edits agree.

It fails closed on unbound URIs, conflicting aliases, version mismatch, unsupported
resource operations, overlapping edits, invalid positions, encoded-character splits,
unknown encodings, and no-op edits.

### Provider-neutral lifecycle port

`HarnessLspProviderPort` stabilizes only:

```text
initialize()
rename() -> WorkspaceEdit proposal
drain_diagnostics()
shutdown()
```

There is deliberately no apply/write/workspace-patch method. Provider capabilities that
claim direct workspace mutation are rejected.

Harness-facing rename positions use one-based lines plus zero-based Unicode-character
columns. Provider wrappers convert to the negotiated LSP encoding units.

## Verified provider paths

Two independent local language servers exercised the same adapter and the same Runtime
physical-write boundary:

```text
clangd 22.1.8 / C++ rename
    -> WorkspaceEdit
    -> CanonicalEditPlan: 1 file / 2 edits
    -> Runtime workspace.patch committed

Taplo 0.10.0 / TOML rename
    -> WorkspaceEdit
    -> CanonicalEditPlan: 1 file / 1 edit
    -> Runtime workspace.patch committed
```

The Taplo occurrence also verified the LSP default UTF-16 position semantics when the
server did not advertise another encoding.

## Lifecycle donor experiments

### bare pygls

Useful as an experimental transport donor, but the bare client probe did not handle
Taplo `workspace/configuration` requests or publish-diagnostics notifications without
additional handlers. It therefore was not selected as the default lifecycle provider.

### lsp-client 0.3.9

Normal lifecycle composition was substantially stronger:

```text
workspace/configuration handled = 1
publishDiagnostics notifications = 4
WorkspaceEdit proposal returned = yes
applyEdit mixin = absent
disk changed during lifecycle = no
disk changed after shutdown = no
typed WorkspaceEdit -> Harness JSON adapter = pass
```

The package also exposes mutating convenience APIs, but they are outside the Harness
provider port and were not invoked.

Fault probes refined this positive result:

```text
caller cancellation:
  proposal returned = no
  disk changed = no
  $/cancelRequest observed = no
  cleanup ended through bounded timeout/error path

server crash during rename:
  proposal returned = no
  request surfaced BrokenResourceError
  disk changed = no
  cleanup ended through bounded timeout/error path
```

Therefore `lsp-client` remains a functional replaceable provider candidate, but is not
admitted as the default provider or as a Harness core dependency.

### pylspclient 0.1.2

Local API/source inspection found no first-class rename API and no cancellation API. It
has a raw request method plus basic initialize/shutdown/exit support, so adopting it
would require more Harness-owned protocol and lifecycle glue than the current candidate.
It is rejected for the R7 default-provider role.

## Evidence set

Current R7 receipts:

```text
evidence/lsp-r7-clangd-runtime-patch-20260914.json
evidence/lsp-r7-taplo-runtime-patch-20260914.json
evidence/lsp-r7-lsp-client-lifecycle-20260914.json
evidence/lsp-r7-lifecycle-faults-20260914.json
```

The evidence index uses explicit implementation-path scopes for these verified slices,
so unrelated Harness additions do not erase valid evidence while changes inside the
bound implementation slice still invalidate currentness.

## Decision

R7 closes the **Harness LSP semantic and authority boundary**.

It does **not** select a permanent transport/provider. That is now an integration choice
behind `HarnessLspProviderPort`.

Current standing:

```text
WorkspaceEdit interpretation                VERIFIED
URI/version/snapshot authority fencing       VERIFIED
position encoding conversion                 VERIFIED
clangd provider path                         VERIFIED
Taplo provider path                          VERIFIED
Runtime-only physical mutation               VERIFIED
provider-neutral lifecycle port              IMPLEMENTED + REGRESSED
normal lsp-client lifecycle                  SUPPORTED
lsp-client cancellation cleanup              INCOMPLETE
lsp-client abnormal-exit cleanup              INCOMPLETE
pylspclient default-provider suitability      REJECTED
production/default LSP provider               NOT_SELECTED
public Agent Tool exposure                    NOT_ADMITTED
```

## Reopen criteria

Do not continue adding language servers or client libraries merely to accumulate
coverage. Reopen provider selection only when at least one of these is true:

1. a mature external client/provider demonstrates cleaner cancellation and abnormal-exit
   behavior while preserving proposal-only semantics;
2. a real Harness workload requires public LSP Tool exposure and therefore needs a
   concrete provider behind the Run/Tool Grant;
3. measured latency, reliability, or compatibility evidence shows the current external
   candidate is insufficient;
4. a mature external integration can replace the provider port without surrendering
   Harness authority or Runtime consequence ownership.

If no mature donor improves the failure lifecycle, any cleanup/cancellation adaptation
must remain outside Harness core behind the existing port.
