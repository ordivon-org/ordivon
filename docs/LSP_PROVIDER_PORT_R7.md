# LSP Provider Port R7

Status: provider-neutral lifecycle boundary prototype

## Why this port exists

`WorkspaceEdit` lowering is now proven across clangd/C++ and Taplo/TOML, but transport
lifecycle remains replaceable. Harness must not depend on a particular LSP client library
for authority semantics.

The stable boundary is therefore:

```text
Harness Run / Tool authority
    -> HarnessLspProviderPort
        initialize
        rename -> WorkspaceEdit proposal
        drain diagnostics
        shutdown
    -> WorkspaceEdit authority binding
    -> CanonicalEditPlan
    -> Runtime workspace.patch
```

There is deliberately no `apply`, `write`, or `workspace.patch` operation on the provider
port. External client libraries may contain convenience mutation APIs, but Harness does
not expose them through this contract.

## Request coordinates

Harness-facing rename requests use one-based lines and zero-based **Unicode-character**
columns. This keeps model/Run semantics independent from negotiated LSP position encoding.
The provider wrapper converts the Unicode column to UTF-8, UTF-16, or UTF-32 units using
`unicode_column_to_lsp_character()` after initialization reports the effective encoding.

Every request also carries the exact source digest and document version. A returned
WorkspaceEdit is still a proposal: URI aliases and current source snapshots are rebound
and checked separately by `workspace_edit_to_canonical_plan()`.

## Lifecycle observations

The port exposes diagnostics as observations. Configuration requests and dynamic
registration are provider mechanics reported as ready capabilities; they do not become
Task truth or file-mutation permission.

A provider declaring direct workspace mutation is rejected by the Harness port model.

## External donor standing

Local experiments found:

- bare `pygls 2.1.1` can carry initialize/read/rename/shutdown but required explicit
  handlers for Taplo `workspace/configuration` and publish-diagnostics traffic;
- `lsp-client 0.3.9` provides first-class server-request/notification mixins, explicit
  local servers, capability negotiation, and `request_rename_edits()` that returns a raw
  WorkspaceEdit without applying it;
- its separate convenience `request_rename()` and apply-edit capability do mutate files,
  so those APIs are outside the Harness provider contract;
- its `value_serialize()` output feeds the existing JSON-shaped Harness WorkspaceEdit
  adapter directly;
- a custom Taplo client composed from rename + configuration + diagnostics handlers
  handled one configuration request, received diagnostics, returned the rename proposal,
  and left disk bytes unchanged through shutdown.

`lsp-client` is therefore the current lifecycle-provider candidate, not a Harness core
dependency. Harness's repository boundary currently forbids project optional dependencies;
a concrete integration should live behind this port and remain replaceable.

## Revision-bound lifecycle donor evidence

After the provider-neutral port landed at:

```text
c7df6ef harness: add proposal-only LSP provider port
```

a fresh occurrence used exactly `lsp-client 0.3.9` with the local Taplo server. The
composition included rename, configuration-request handling, diagnostics, and log
notifications, but deliberately omitted the library's apply-edit mixin.

Observed lifecycle result:

```text
workspace/configuration handled = 1
publishDiagnostics notifications = 4
WorkspaceEdit proposal returned = yes
provider applyEdit mixin = absent
disk changed during lifecycle = no
disk changed after shutdown = no
typed WorkspaceEdit -> Harness JSON adapter = pass
```

The external package's mutating convenience APIs remain outside the Harness port. The
port itself exposes no apply/write operation.

Verified receipt:

```text
evidence/lsp-r7-lsp-client-lifecycle-20260914.json
payload digest:
sha256:6981aec36c5b90c8063894fbd0d94bf88e1130bb729e81c8bad22c7e663effc7
```

Standing: `lsp-client` is supported as the current **replaceable lifecycle-provider
candidate**. It is not admitted as a Harness core dependency and no default provider is
final until integration packaging, Run/Tool Grant binding, cancellation, and abnormal
server-exit behavior are closed.

## Fault lifecycle evidence

A controlled fake LSP server was used after `cd45070` to exercise two failure paths
without depending on Taplo timing.

Cancellation result:

```text
caller cancellation triggered = yes
WorkspaceEdit returned = no
disk changed = no
$/cancelRequest observed by server = no
graceful shutdown/exit observed = no
context cleanup = bounded timeout/error path (~3.5 s)
```

Abnormal server-exit result:

```text
server exited during textDocument/rename = yes
WorkspaceEdit returned = no
request surfaced BrokenResourceError = yes
disk changed = no
context cleanup = bounded timeout/error path (~4.0 s)
```

Verified negative receipt:

```text
evidence/lsp-r7-lifecycle-faults-20260914.json
payload digest:
sha256:0677bc871733bf260e78bec3c10350cf597c4f26918ac3823f90849d66997acd
```

This refines the provider decision. `lsp-client 0.3.9` remains functionally compatible
with the proposal-only Harness port and preserves physical non-mutation in these tested
failures, but its cancellation and abnormal-exit cleanup is not clean enough to select it
as the default provider directly. Harness should compare another mature lifecycle client
before writing custom cleanup glue. If no better donor exists, any adaptation belongs
outside Harness core behind `HarnessLspProviderPort`.
