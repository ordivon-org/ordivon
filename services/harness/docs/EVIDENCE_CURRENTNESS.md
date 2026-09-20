# Evidence Currentness

Harness evidence distinguishes immutable historical receipts from `verified` receipts
that still describe the current implementation.

## Default rule

A verified receipt without an explicit implementation scope retains the legacy
conservative rule: any later change under the verified implementation roots invalidates
it. Those roots are currently `src/`, `pyproject.toml`, `uv.lock`, and the P0 scale
acceptance implementation script.

This remains the safe default for evidence whose implementation boundary has not been
made explicit.

## Scoped verified receipts

A verified evidence-index entry may opt into `implementationPaths` when its implementation
slice is known precisely. Each entry is either:

- an exact file path; or
- a directory prefix ending in `/`.

Scoped receipts must include at least one `src/` implementation path plus both
`pyproject.toml` and `uv.lock`. Paths outside the verified implementation roots,
duplicates, absolute paths, and `.` / `..` traversal are rejected.

Currentness is then evaluated only against changes inside those declared paths:

```text
verified revision
    + explicit implementationPaths
    + git diff revision..HEAD
        -> any scoped implementation change? stale
        -> only unrelated slice changes? still current
```

This is not an exemption mechanism. The scope is part of the claim. If a provider,
bridge, loop, canonicalizer, dependency contract, or other implementation component is
material to the evidence, it must be included in that receipt's scope.

## Why the scope exists

Harness now contains independently evolving capability slices. For example, adding the
LSP `WorkspaceEdit` adapter does not change the previously measured Adaptive Edit loop,
provider bridge, or canonical edit implementation. Repository-wide `src/` invalidation
would therefore discard still-current evidence for an unrelated addition.

The scoped form preserves two properties simultaneously:

1. unrelated capability additions do not erase valid evidence;
2. any change to the declared implementation slice still fails currentness closed.

Receipts should remain unscoped unless their implementation boundary is defensible.
