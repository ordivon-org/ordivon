# Artifact Capability Decomposition — Wave A7 R1

## Standing

`DOCUMENT_VERIFIER_OWNER_EXTRACTED_COMPATIBILITY_PRESERVED`

Wave A7 removes Document-specific semantic-correspondence and dependency/toolchain verification implementations from `scripts/artifact_delivery.py` and assigns them to `artifact_verifiers.document`.

A7 complements the existing `artifact_capabilities.document` build provider: Document authoring and Document verification now have separate owners.

## One-sentence boundary

Document Verification owns normalized Markdown↔DOCX semantic correspondence through Pandoc plus exact document build-dependency/toolchain checks; it does not own request admission, build planning, document authoring, generic OpenXML validation, Word target behavior, visual/accessibility acceptance, delivery, trust, or workflow durability.

## New package

```text
artifact_verifiers/document/
├── __init__.py
├── semantics.py
├── dependencies.py
└── toolchain.py
```

### `semantics.py`

Owns:

- Pandoc inline-text projection;
- block-level semantic projection;
- metadata text projection;
- Markdown and DOCX Pandoc AST parsing;
- normalized source/document projection comparison;
- title/subtitle/author preservation checks;
- exact Pandoc executable fact/version/digest reporting.

Its truth boundary remains unchanged: source and artifact are parsed by the same locked Pandoc implementation, so PASS is correspondence evidence, not independent IV&V.

### `dependencies.py`

Owns:

- exact request-validation outcome consumption;
- expected document build-plan checks;
- locked Pandoc executable availability/version/digest;
- official Pandoc release archive digest;
- OpenXML validator runtime availability;
- exact source/profile/material facts propagated from request admission;
- toolchain-lock binding.

Request admission and build-plan compilation are supplied through `DocumentDependencyHooks`. The verifier therefore consumes Core-derived decisions rather than importing or duplicating Delivery orchestration.

### `toolchain.py`

Owns Document-verifier-specific provider selection and default paths:

- global Artifact toolchain root;
- Pandoc executable;
- Pandoc release archive;
- legacy fallback locations;
- toolchain lock path;
- OpenXML validator path;
- deterministic environment/global/legacy selection order.

## Dependency direction

```text
Artifact Core admission / build planning
              |
              | DocumentDependencyHooks
              v
artifact_verifiers.document.dependencies
              |
              +--> exact Pandoc / archive / OpenXML facts

Markdown + DOCX
      |
      v
artifact_verifiers.document.semantics
      |
      +--> locked Pandoc AST parser
```

Neither Document verifier module imports `artifact_delivery`.

## Verification-stage wiring

A5 verify-stage now binds directly to:

- `document_verify_semantics` for semantic correspondence;
- `_document_dependency_stage_verifier` for dependency verification.

The dependency adapter exists only to supply request-admission and build-plan hooks. It does not contain dependency-verification logic.

## Delivery compatibility surface

Historical callers retain:

```text
verify_document_semantic_correspondence   4 lines
verify_document_dependencies              9 lines
```

The following Pandoc implementation helpers no longer exist in Delivery:

```text
_pandoc_inline_text
_pandoc_semantic_projection
_pandoc_meta_text
_run_pandoc_ast
```

The shared `_selected_external_file()` helper remains in Delivery because non-verifier build paths still use it. A7 does not widen scope merely to remove a shared helper.

## Document symmetry after A7

```text
Document
├── Authoring
│   └── artifact_capabilities.document
│
└── Verification
    └── artifact_verifiers.document
        ├── semantics
        ├── dependencies
        └── toolchain
```

Builder success and verifier success remain separate claims.

## Monolith reduction

Measured on the A7 candidate:

```text
artifact_delivery.py at decomposition start: ~3922 lines
after A2:                                      3458
after A3:                                      2822
after A4:                                      2242
after A5:                                      2028
after A6:                                      1737
after A7:                                      1616
```

A7 removes another ~121 net lines from Delivery after compatibility/wiring code is added.

## TDD / verification evidence

A7 tests were written before implementation and observed RED because:

- `artifact_verifiers.document` did not exist;
- Pandoc semantic helpers were still implemented in Delivery;
- Document verifier functions were still full implementations;
- verify-stage still wired through Delivery verifier implementations.

After extraction:

- A7 decomposition tests: **5 PASS**;
- legacy `test_artifact_delivery.py`: **79 tests, 0 failures, 2 conditional skips**;
- A2+A3+A4+A5+A6+A7+OCI targeted bundle: **41 PASS**;
- Temporal Artifact delivery contract: **12 PASS**;
- full Artifact regression: **349 tests, 0 failures, 4 conditional skips**;
- `compileall`: PASS;
- `git diff --check`: PASS before final commit gate.

Candidate full-regression Runtime Job:

`job-01a0b2d0-92d4-7062-a41c-edb3ebe83662`

## Non-claims / next wave

A7 does not claim Artifact decomposition complete.

Largest remaining concrete verifier implementations still embedded in Delivery are:

1. **PDF verification** — qpdf structural verification and veraPDF conformance.
2. **Generic OpenXML verification** — external DocumentFormat.OpenXml validator execution.
3. **Web verification** — Nu HTML Checker and browser/local Web verification.
4. **OCI compatibility imports** — OCI still consumes Delivery compatibility surfaces.
5. **Temporal compatibility** — Temporal still speaks Delivery CLI/stage layout rather than a generic Artifact operation contract.
6. **CLI/cross-format helpers** — remaining facade logic and provider-specific helpers can be reduced only after bounded verifier owners exist.

The next bounded wave should extract **PDF Verification** or **Generic OpenXML Verification**, without broadening `artifact_verification.stage` into a verifier implementation layer.
