# Artifact Capability Decomposition — Wave A6 R1

## Standing

`PRESENTATION_VERIFIER_OWNER_EXTRACTED_COMPATIBILITY_PRESERVED`

Wave A6 removes Presentation-specific verification implementations from the historical `scripts/artifact_delivery.py` monolith and assigns them to an independent `artifact_verifiers.presentation` package.

A6 complements A4: Presentation authoring and Presentation verification now have separate owners.

## One-sentence boundary

Presentation Verification owns PPTX package inspection, presentation-local semantic checks, exact font dependency verification, Open XML evidence validation, and aggregation of independently supplied presentation evidence; it does not own authoring, PowerPoint execution, visual review production, delivery effects, PDF verification, trust, or workflow durability.

## New package

```text
artifact_verifiers/
├── __init__.py
└── presentation/
    ├── __init__.py
    ├── inspection.py
    ├── semantics.py
    └── gate.py
```

### `inspection.py`

Owns:

- PPTX ZIP/OPC admission;
- unsafe package-path detection;
- required PPT package-part census;
- internal relationship resolution and missing-target detection;
- slide count / hidden-slide count;
- exact slide-size and aspect-ratio observation;
- placeholder-text scans;
- render-relevant explicit typeface census;
- theme typeface census;
- Open XML evidence digest binding;
- Open XML SDK implementation/API/version/error-count checks.

Its package inspection explicitly does not claim ISO/IEC 29500 schema validation.

### `semantics.py`

Owns:

- minimum/maximum slide-count policy;
- declared-vs-observed aspect-ratio policy;
- exact required font-file existence/digest facts;
- undeclared render-explicit typeface detection.

### `gate.py`

Owns Presentation aggregate acceptance assembly across:

- profile schema;
- PPTX structural/package inspection;
- external Open XML evidence;
- presentation semantic policy;
- font/dependency policy;
- companion PDF result;
- render evidence;
- target PowerPoint evidence;
- visual-review evidence;
- delivery read-back evidence.

The PDF verifier is injected through `PresentationGateHooks` because PDF verification remains outside the Presentation verifier owner.

Render/target/visual/delivery verification functions are consumed from `artifact_evidence.delivery`, which already owns those evidence contracts.

## Dependency direction

```text
Presentation Authoring (A4)
        |
        | generated PPTX
        v
artifact_verifiers.presentation
  ├── inspection
  ├── semantics
  └── gate
        |
        +--> artifact_evidence.delivery
        |
        +--> injected PDF verifier
```

The new verifier package does not import `artifact_delivery`.

The A4 authoring hooks and A5 verification-stage hooks now bind directly to:

- `artifact_verifiers.presentation.inspect_pptx`;
- `artifact_verifiers.presentation.verify_presentation_semantics`.

They no longer route back through Delivery compatibility wrappers.

## Delivery compatibility surface

Delivery retains thin public wrappers for historical CLI/tests/callers:

```text
inspect_pptx                       2 lines
verify_openxml_evidence            2 lines
verify_presentation_semantics      2 lines
verify_font_manifest               6 lines
presentation_gate                 10 lines
```

The implementations are no longer owned by Delivery.

## Presentation symmetry after A6

```text
Presentation
├── Authoring
│   └── artifact_capabilities.presentation
│       ├── python_pptx
│       └── ppt_master
│
└── Verification
    └── artifact_verifiers.presentation
        ├── inspection
        ├── semantics
        └── gate
```

This deliberately prevents builder success from becoming verifier success.

## Monolith reduction

Measured on the A6 candidate:

```text
artifact_delivery.py at decomposition start: ~3922 lines
after A2:                                      3458
after A3:                                      2822
after A4:                                      2242
after A5:                                      2028
after A6:                                      1737
```

A6 removes another ~291 net lines from Delivery after compatibility imports/wrappers.

## TDD / verification evidence

A6 tests were written before implementation and observed RED because:

- `artifact_verifiers` did not exist;
- Presentation verifier implementations were still large Delivery functions;
- no independent verifier package surface existed.

The first implementation pass left `presentation_gate` as a 23-line wrapper and the ownership test remained RED. The wrapper was reduced without behavioral change; A6 then went GREEN.

Candidate evidence:

- A6 decomposition tests: **5 PASS**;
- legacy `test_artifact_delivery.py`: **79 tests, 0 failures, 2 conditional skips**;
- A2+A3+A4+A5+A6+OCI targeted bundle: **36 PASS**;
- Temporal Artifact delivery contract: **12 PASS**;
- full Artifact regression: **344 tests, 0 failures, 4 conditional skips**;
- `compileall`: PASS;
- `git diff --check`: PASS before final documentation/commit gate.

Candidate full-regression Runtime Job:

`job-01a0b2c3-0ff2-76d1-88eb-6ed381b9eddd`

## Non-claims / next wave

A6 does not claim Artifact decomposition complete.

Largest remaining concrete verifier owners still embedded in Delivery are:

1. **Document verification** — Pandoc semantic correspondence and dependency/toolchain verification.
2. **PDF verification** — qpdf structural verification and veraPDF conformance.
3. **OpenXML generic verification** — external validator execution for Office packages.
4. **Web verification** — Nu HTML Checker and browser/local Web verification.
5. **OCI compatibility imports** — OCI still consumes several Delivery compatibility surfaces.
6. **Temporal compatibility** — Temporal still speaks Delivery CLI/stage layout rather than a generic Artifact operation contract.

The next bounded wave should extract **Document Verification** rather than broadening `artifact_verification.stage`.
