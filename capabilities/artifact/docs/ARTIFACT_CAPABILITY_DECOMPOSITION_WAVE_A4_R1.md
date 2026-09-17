# Artifact Capability Decomposition — Wave A4 R1

## Standing

`PRESENTATION_AUTHORING_OWNER_EXTRACTED_COMPATIBILITY_PRESERVED`

Wave A4 removes concrete Presentation authoring/provider mechanics from the historical `scripts/artifact_delivery.py` monolith and gives them an explicit capability owner under `artifact_capabilities.presentation`.

This wave is intentionally limited to authoring/provider mechanics and presentation-specific source/material admission. It does **not** move Open XML inspection, PowerPoint target verification, visual acceptance, accessibility acceptance, delivery read-back, or release trust.

## One-sentence boundary

Presentation Capability owns how admitted presentation sources and their exact materials are turned into native PPTX bytes through the selected authoring provider; Artifact Evidence and Delivery/verification gates independently decide whether those bytes satisfy package, target, visual, accessibility, and delivery requirements.

## New package

```text
artifact_capabilities/presentation/
├── __init__.py
├── admission.py
├── common.py
├── python_pptx.py
└── ppt_master.py
```

### `common.py`

Owns presentation-specific shared mechanics:

- exact template resolution and digest binding;
- raster-image resolution, format admission, digest binding, and image-byte validation;
- native presentation material census;
- semantic-SVG path confinement and project-relative target safety;
- semantic-SVG page/material census;
- template theme/master/layout package facts;
- layout lookup and placeholder facts;
- text styling/application helpers;
- `PresentationBuildHooks`, the explicit seam from authoring into independent post-build checks.

### `admission.py`

Owns presentation-source admission composition for:

- `presentation-source-v1`;
- `presentation-semantic-svg-source-v1`.

JSON-Schema validation remains supplied through an injected validator rather than being duplicated inside the capability package.

### `python_pptx.py`

Owns the native `python-pptx` authoring path:

- source/profile compatibility checks;
- declared-font enforcement;
- exact template/master/layout binding;
- placeholder binding;
- exact raster media binding;
- text/image native composition;
- native PPTX output generation;
- provider receipt facts.

It calls injected post-build hooks for ZIP normalization, PPTX inspection, and presentation semantic verification. Those hooks do not make Presentation Capability the owner of acceptance.

### `ppt_master.py`

Owns the external PPT Master authoring path:

- provider lock and exact checkout identity;
- tracked-worktree cleanliness;
- exact provider executable/script facts;
- confined semantic-SVG/material staging;
- SVG quality-gate invocation;
- PPT Master export invocation;
- provider execution receipts;
- native PPTX output generation.

Generated OOXML canonicalization and post-build PPTX/semantic verification are injected through the same explicit hook boundary.

## Delivery compatibility surface

`scripts/artifact_delivery.py` retains public compatibility wrappers:

- `build_presentation_source(...)`;
- `build_semantic_svg_presentation_source(...)`;
- `_admit_presentation_source(...)`;
- `_admit_semantic_svg_source(...)`.

The two build wrappers are each nine lines at the A4 cut and delegate directly to the capability package with `PresentationBuildHooks`.

Historical private helper names used by old tests/callers are retained as compatibility aliases to the new package. Delivery no longer defines the provider mechanics themselves.

## Separation from acceptance

The authoring package deliberately does not own:

- `inspect_pptx`;
- `verify_presentation_semantics`;
- Open XML SDK evidence;
- Microsoft PowerPoint target evidence;
- visual-review evidence;
- accessibility claims;
- delivery/read-back evidence;
- VSA/Sigstore/Cosign trust.

The dependency direction is therefore:

```text
Artifact Core / Build Binding
          |
          v
Presentation Capability
  ├── python-pptx provider
  └── PPT Master provider
          |
          | generated PPTX bytes
          v
independent post-build hooks
  ├── container normalization
  ├── PPTX inspection
  └── semantic verification
          |
          v
Evidence / Target / Visual / Delivery / Trust gates
```

This prevents authoring success from being promoted into target or visual acceptance.

## Monolith reduction

Measured on the exact A4 candidate:

```text
artifact_delivery.py at decomposition start: ~3922 lines
artifact_delivery.py after A2:               3458 lines
artifact_delivery.py after A3:               2822 lines
artifact_delivery.py after A4:               2242 lines
```

A4 therefore removes roughly another 580 lines from Delivery. Line count is only a secondary witness; the important change is authority movement into provider-specific capability modules.

## TDD / verification evidence

A4 ownership tests were written before implementation and observed RED because:

- `artifact_capabilities.presentation` did not exist;
- provider/helper functions were still defined in Delivery;
- the two public build functions were still large provider implementations.

After extraction:

- A4 decomposition tests: **5 PASS**;
- legacy `test_artifact_delivery.py`: **79 tests, 0 failures, 2 conditional skips**;
- A2 + A3 + A4 + OCI targeted bundle: **26 PASS**;
- Temporal Artifact delivery contract: **12 PASS**;
- full `test_artifact*.py` regression: **334 tests, 0 failures, 4 conditional skips**;
- `compileall`: PASS;
- `git diff --check`: PASS before final documentation/commit gate.

Full-regression Runtime Job:

`job-01a0b0de-6000-7a21-8249-e4f81e0a3a2d`

## Residual coupling / next wave

A4 does **not** claim Artifact decomposition complete. The largest remaining knots are now:

1. **Verify-stage orchestration** — `execute_verify_stage()` still couples format verification, evidence layout, and local VSA production inside Delivery.
2. **Presentation verification/evidence** — package inspection and presentation semantic checks remain in Delivery; they should move toward verifier/evidence owners without merging them back into authoring.
3. **Document semantic/dependency verification** — still co-located with Delivery orchestration.
4. **OCI residual Delivery imports** — `build_presentation_source`, `execute_verify_stage`, `validate_delivery_request`, and `write_json` remain compatibility dependencies.
5. **Temporal adapter contract** — still understands Delivery CLI verbs/stage layout instead of consuming a stable generic Artifact operation contract.
6. **CLI facade** — Delivery is substantially smaller but still owns verification orchestration and several cross-format helpers.

The next wave should target **verify-stage orchestration**, not continue splitting presentation authoring further. The authoring package now has a bounded owner and should remain separate from acceptance/evidence logic.
