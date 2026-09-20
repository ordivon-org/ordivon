# Artifact Capability Decomposition — Wave A8 R1

## Standing

`PDF_VERIFIER_OWNER_EXTRACTED_COMPATIBILITY_PRESERVED`

Wave A8 removes PDF structural and conformance verifier implementations from `scripts/artifact_delivery.py` and assigns them to `artifact_verifiers.pdf`.

## One-sentence boundary

PDF Verification owns qpdf-based structural checking, veraPDF profile-conformance checking, and PDF verifier toolchain selection; it does not own PDF authoring, human accessibility review, target-viewer acceptance, visual review, delivery, trust, or workflow durability.

## New package

```text
artifact_verifiers/pdf/
├── __init__.py
├── structural.py
├── conformance.py
└── toolchain.py
```

### `structural.py`

Owns:

- qpdf executable selection consumption;
- `qpdf --check` execution;
- exact artifact fact binding;
- structural PASS/FAIL;
- bounded stdout/stderr diagnostics;
- explicit non-claim that qpdf establishes PDF/A or PDF/UA conformance.

### `conformance.py`

Owns:

- supported veraPDF flavour policy;
- veraPDF JSON execution;
- conformance result parsing;
- profile name;
- failed-rule / failed-check counts;
- parse-error capture;
- exact artifact binding;
- explicit machine-checkable-conformance-only truth boundary.

### `toolchain.py`

Owns:

- qpdf PATH selection;
- configured/global/legacy/system veraPDF precedence;
- Artifact toolchain root;
- global veraPDF 1.30.2 location;
- local legacy fallback location.

## Direct consumers

A5 verify-stage now binds directly to:

```text
verify_pdf             -> pdf_verify_structural
verify_pdf_conformance -> pdf_verify_conformance
```

Presentation aggregate verification now injects:

```text
PresentationGateHooks(
    verify_pdf=pdf_verify_structural
)
```

Therefore neither verification-stage nor Presentation verification needs to route PDF verification through Delivery compatibility wrappers.

## Delivery compatibility surface

Historical CLI/tests/callers retain:

```text
verify_pdf               2 lines
_verapdf_executable      2 lines
verify_pdf_conformance   2 lines
```

Those functions now delegate to `artifact_verifiers.pdf`.

## Truth boundaries retained

`verify_pdf()` establishes only qpdf structural/package evidence.

It explicitly does **not** establish:

- PDF/A;
- PDF/UA;
- human accessibility;
- target-viewer behavior;
- visual acceptance.

`verify_pdf_conformance()` establishes only the selected veraPDF profile result. Human accessibility/use review and target-viewer acceptance remain independent evidence.

Missing veraPDF continues to produce `NOT_RUN`, while unsupported flavour and non-compliant validation remain failures as before.

## Monolith reduction

Measured on the A8 candidate:

```text
artifact_delivery.py at decomposition start: ~3922 lines
after A2:                                      3458
after A3:                                      2822
after A4:                                      2242
after A5:                                      2028
after A6:                                      1737
after A7:                                      1616
after A8:                                      1546
```

A8 removes another ~70 net lines from Delivery after compatibility imports/wrappers.

## TDD / verification evidence

A8 tests were written before implementation and observed RED because:

- `artifact_verifiers.pdf` did not exist;
- PDF verifier implementations remained in Delivery;
- verify-stage still wired through Delivery;
- Presentation companion-PDF verification still wired through Delivery.

After extraction:

- A8 decomposition tests: **5 PASS**;
- legacy `test_artifact_delivery.py`: **79 tests, 0 failures, 2 conditional skips**;
- A2+A3+A4+A5+A6+A7+A8+OCI targeted bundle: **46 PASS**;
- Temporal Artifact delivery contract: **12 PASS**;
- full Artifact regression: **354 tests, 0 failures, 4 conditional skips**;
- `compileall`: PASS;
- `git diff --check`: PASS before final commit gate.

Candidate full-regression Runtime Job:

`job-01a0b343-dbb8-76f3-9b1f-a743e62570a7`

## Non-claims / next wave

A8 does not claim Artifact decomposition complete.

Largest remaining concrete verifier implementations still embedded in Delivery are:

1. **Generic OpenXML verification** — external DocumentFormat.OpenXml validator execution.
2. **Web verification** — Nu HTML Checker and browser/local Web verification.
3. **OCI compatibility imports** — OCI still consumes Delivery compatibility surfaces.
4. **Temporal compatibility** — Temporal still speaks Delivery CLI/stage layout instead of a generic Artifact operation contract.
5. **Residual cross-format/CLI helpers** — remaining facade logic should only be removed after bounded owners exist.

The next bounded wave should extract **Generic OpenXML Verification** before Web, because Presentation and Document both already consume OpenXML evidence and the boundary is format-independent.
