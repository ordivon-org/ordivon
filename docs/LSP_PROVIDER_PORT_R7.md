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
