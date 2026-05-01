# Scope Drift — The Governance Rot Pattern

> Scope must be discoverable, not enumerated. A checker whose input set is maintained manually is guaranteed to rot.

## Two Instances, One Root Cause

### Instance 1: VD-005 — Document Registry Completeness (PV-N2H)

| Aspect | Detail |
|--------|--------|
| Checker | `check_document_registry.py` |
| Scope model | Enumerated: 31 registered docs |
| What happened | 142+ .md files existed under `docs/` that were unregistered |
| Why checker missed it | It only validated entries in the registry, not whether the registry was complete |
| PASS semantics | "31 registered docs are valid" — true but partial |
| Actual truth | Registry covered 31/173 docs in scope |
| Fix | Added `check_completeness()` — discovery scan against filesystem |

### Instance 2: pr-fast Ruff Gate — Wave Files Whitelist (PV-N7)

| Aspect | Detail |
|--------|--------|
| Checker | `run_verification_baseline.py` ruff format gate |
| Scope model | Enumerated: `wave_files` list (9 files) |
| What happened | `test_ordivon_verify_public_repo_dryrun.py` created, not in wave_files |
| Why checker missed it | It only checks files on the list, not all .py files in scope |
| PASS semantics | "9 wave files are formatted" — true but partial |
| Actual truth | Wave files = 9, actual product test files = 18+ |
| Fix | Not yet applied |

## Beyond Two: The Full Inventory

A scan of all checker scripts revealed at least **5 hand-maintained lists** that are scope-decay risks:

| # | File | List | Type | New-file risk |
|---|------|------|------|--------------|
| 1 | `run_verification_baseline.py` (full) | `wave_files` | Whitelist | High |
| 2 | `run_verification_baseline.py` (pr-fast) | `wave_files` | Whitelist | High |
| 3 | `check_architecture.py` | `ALLOWED_FILES` | Whitelist | Medium |
| 4 | `repo_governance_github_adapter.py` | `DEPENDABOT_EXPECTED_FILES` | Whitelist | Medium |
| 5 | `check_document_registry.py` (pre-fix) | Registered entries | Registry | Fixed |

Every one of these follows the same structure:

```
checker validates objects it knows about
    ↓
new object created outside the list
    ↓
checker continues to PASS
    ↓
PASS = false confidence in a larger universe
```

## Why It's Structural, Not Accidental

This is not "forgot to add a file to a list." This is what happens when
the scope definition model is **enumeration** rather than **discovery**.

Enumeration requires a human to remember to update the list. Discovery
asks the filesystem or registry what exists and checks everything.

A checker built on enumeration will always rot, because:
1. Every new phase creates new files
2. The person creating files is not the person maintaining the list
3. There is no automated feedback loop that says "your list is stale"

VD-005 fixed this for documents. The pr-fast wave_files list is the
same problem in a different checker — unfixed.

## The Generalization

**Every governance checker must define its scope by discovery, not enumeration.**

| Anti-pattern | Replacement |
|-------------|------------|
| `wave_files = [file1, file2, file3]` | `glob("tests/unit/product/*.py")` |
| `ALLOWED_FILES = {file1, file2}` | `load_allowlist("governance/architecture-allowlist.json")` with completeness check |
| `validate(registry_entries)` | `discover() → cross-reference(registry) → report_gaps()` |
| Silent exclusion | Exclusion with reason, owner, reviewed_at |

## What Should Change

### pr-fast wave_files → discovery

```python
# Current (rots):
wave_files = [
    "run_verification_baseline.py",
    "check_document_registry.py",
    ...
]

# Should be:
wave_files = discover_python_files([
    "scripts/check_*.py",
    "tests/unit/product/*.py",
    "tests/unit/governance/*.py",
])
```

### ALLOWED_FILES → governed exclusion file

The architecture checker's `ALLOWED_FILES` is a whitelist of exceptions.
This should be a governed file (like `document-registry-exclusions.json`)
with reason, owner, and reviewed_at per entry.

### DEPENDABOT_EXPECTED_FILES → same treatment

Any hand-maintained set of files that a checker depends on should either
be auto-discovered or governed with explicit exclusion metadata.

## The New Invariant

> **A checker's scope must be verifiable against the filesystem or registry,**
> **not asserted by a hand-maintained list.**
>
> **Any hand-maintained list that defines checker scope is a latent VD-005.**

## Relationship to Coverage Plane

This is exactly what the coverage plane was designed to catch — but currently
only applied to documents. The same principle must extend to code files,
checker inputs, and allowlists.

```
Coverage Plane (current):   documents under docs/
Coverage Plane (should be): all checker scope inputs
```

---

*Discovered: PV-N7 post-seal analysis*
*Status: open governance improvement — not yet implemented*
