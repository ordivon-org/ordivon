# Artifact Capability Decomposition — Wave A9 R1

## Standing

`OPENXML_VERIFIER_OWNER_EXTRACTED_COMPATIBILITY_PRESERVED`

Wave A9 removes the generic DocumentFormat.OpenXml validator execution from `scripts/artifact_delivery.py` and assigns it to the cross-family `artifact_verifiers.openxml` package.

## One-sentence boundary

OpenXML Verification owns selection and execution of the production-stable DocumentFormat.OpenXml validator plus parsing/binding of its machine-checkable result; it does not own Office authoring, target-application rendering, visual acceptance, delivery, trust, or workflow durability.

## New package

```text
artifact_verifiers/openxml/
├── __init__.py
├── toolchain.py
└── validator.py
```

### `toolchain.py`

Owns:

- the production-stable validator default;
- `ARTIFACT_OPENXML_VALIDATOR` override selection;
- the single default path authority for consumers that require the validator runtime.

The production default is:

```text
/root/.local/share/ordivon-workstation/artifact-openxml-v1/current/bin/validate-openxml
```

### `validator.py`

Owns:

- exact artifact fact binding;
- validator availability semantics;
- external validator execution;
- bounded execution timeout;
- JSON result parsing;
- PASS/FAIL derivation from process exit plus validator result;
- parse-error/stderr capture;
- explicit non-claim for Office target rendering, visual acceptance, and delivery.

Missing validator remains `NOT_RUN`, preserving existing behavior.

## Cross-family role

The verifier is deliberately not Presentation- or Document-specific:

```text
Presentation ─┐
Document ─────┼──> artifact_verifiers.openxml
Spreadsheet ──┘
```

A5 verification-stage now binds directly to:

```text
verify_openxml_artifact=openxml_verify_artifact
```

so Office structural verification no longer routes through Delivery.

## Document dependency reuse

A7 Document dependency verification previously carried a second OpenXML validator default path.

A9 removes that duplicate authority.

`artifact_verifiers.document.dependencies` now calls:

```text
openxml_validator_executable()
```

from the new OpenXML toolchain owner.

The Document toolchain module therefore owns only Document/Pandoc-specific toolchain identity.

## Assurance correction

The pre-A9 OpenXML environment test required the production validator path string to appear literally inside `artifact_delivery.py`.

That checked the correct path but the wrong owner.

A9 changes the assurance to require the path in:

```text
artifact_verifiers/openxml/toolchain.py
```

and explicitly verifies that the same literal is absent from Delivery.

This preserves the production-default assurance while removing a category error in ownership.

## Delivery compatibility surface

Historical callers retain:

```text
verify_openxml_artifact   2 lines
```

The wrapper delegates to `artifact_verifiers.openxml.verify_openxml_artifact`.

## Truth boundary retained

OpenXML PASS establishes the bounded schema/semantic result emitted by the production DocumentFormat.OpenXml validator.

It does not establish:

- Microsoft PowerPoint/Word/Excel target behavior;
- visual correctness;
- accessibility;
- delivery success;
- independent IV&V.

Those remain separate evidence families.

## Monolith reduction

Measured on the A9 candidate:

```text
artifact_delivery.py at decomposition start: ~3922 lines
after A2:                                      3458
after A3:                                      2822
after A4:                                      2242
after A5:                                      2028
after A6:                                      1737
after A7:                                      1616
after A8:                                      1546
after A9:                                      1520
```

A9 removes another ~26 net lines from Delivery. The larger architectural value is the first cross-family concrete verifier owner.

## TDD / verification evidence

A9 tests were written before implementation and observed RED because:

- `artifact_verifiers.openxml` did not exist;
- OpenXML validator execution remained in Delivery;
- verify-stage still wired through Delivery;
- Document dependencies duplicated the OpenXML validator path;
- the environment assurance still treated Delivery as the toolchain owner.

After extraction:

- A9 decomposition tests: **6 PASS**;
- updated OpenXML environment tests: **7 PASS**;
- legacy `test_artifact_delivery.py`: **79 tests, 0 failures, 2 conditional skips**;
- A2–A9 + OpenXML environment + OCI targeted bundle: **59 PASS**;
- Temporal Artifact delivery contract: **12 PASS**;
- full Artifact regression: **360 tests, 0 failures, 4 conditional skips**;
- `compileall`: PASS;
- `git diff --check`: PASS before final commit gate.

Candidate full-regression Runtime Job:

`job-01a0b364-6577-7253-bcd5-17462fd3c207`

## Non-claims / next wave

A9 does not claim Artifact decomposition complete.

The largest concrete verifier implementation still embedded in Delivery is now **Web Verification**:

- Nu HTML Checker conformance;
- local browser/runtime verification;
- browser accessibility/target evidence production.

After Web extraction, remaining work should focus on OCI compatibility imports, Temporal generic operation contracts, and reducing residual CLI/cross-format compatibility helpers rather than inventing new verifier ownership layers.
