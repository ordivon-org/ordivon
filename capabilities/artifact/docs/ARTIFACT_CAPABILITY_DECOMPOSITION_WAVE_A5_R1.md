# Artifact Capability Decomposition — Wave A5 R1

## Standing

`VERIFY_STAGE_ORCHESTRATION_EXTRACTED_COMPATIBILITY_PRESERVED`

Wave A5 removes verify-stage orchestration and raw-evidence/local-VSA receipt production from the historical `scripts/artifact_delivery.py` monolith and assigns them to an explicit `artifact_verification` package.

This wave is intentionally narrow. It does **not** move concrete Open XML, PDF, Web, document-semantic, or presentation-semantic verifier implementations. Those remain separate capabilities supplied to the stage through explicit hooks.

## One-sentence boundary

Artifact Verification decides which locally available gates to execute for a validated profile, binds each raw result to an unsigned local VSA receipt, and computes executed/pending verification standing; individual format verifiers, target/visual evidence, external trust, packaging, and durable workflow remain independently owned.

## New package

```text
artifact_verification/
├── __init__.py
├── evidence.py
└── stage.py
```

### `evidence.py`

Owns the raw-result → local-VSA receipt boundary:

- deterministic JSON evidence emission;
- exact subject/profile binding through SLSA Verification Summary v1;
- unsigned local VSA emission;
- immediate VSA structural/semantic re-verification;
- gate receipt status derived from both raw gate result and VSA validation;
- exact file facts for raw evidence and VSA bytes.

It depends on:

- `artifact_core.contracts.file_fact`;
- `artifact_trust.vsa.verification_summary_statement`;
- `artifact_trust.vsa.verify_verification_summary`.

It does not import Artifact Delivery.

### `stage.py`

Owns verify-stage orchestration:

- profile admission outcome handling;
- profile/output-suffix fencing;
- artifact-presence fencing;
- profile-schema receipt;
- Office-package structural verification dispatch;
- document semantic/dependency gate orchestration when an exact request is present;
- presentation semantic gate orchestration;
- PDF structural/conformance orchestration;
- Web conformance/structural/accessibility/target orchestration;
- executed-gate failure aggregation;
- required-gate census;
- pending-required-gate calculation;
- `profileVerificationComplete` semantics.

Concrete verifier implementations are injected through `VerificationStageHooks`. This keeps the orchestration owner from becoming a second verifier monolith.

## Hook boundary

`VerificationStageHooks` binds the stage to the current verifier owners:

```text
validate_profile
primary_suffix
verify_openxml_artifact
validate_delivery_request
verify_document_semantic_correspondence
verify_document_dependencies
inspect_pptx
verify_presentation_semantics
verify_pdf
verify_pdf_conformance
verify_html_conformance
verify_web_local
```

The stage therefore decides **when** and **how results are assembled**, not **how each format is validated**.

## Delivery compatibility surface

`scripts/artifact_delivery.py` retains:

- `_verification_stage_hooks()` — 15-line compatibility wiring factory;
- `execute_verify_stage(...)` — 13-line compatibility wrapper;
- `_write_raw_and_vsa` as an alias to `artifact_verification.write_gate_receipt` for historical private callers.

Delivery no longer contains the 222-line verify-stage implementation or the 32-line raw/VSA writer.

The CLI verb `verify-stage` is unchanged and therefore remains compatible with the current Temporal adapter.

## Verification truth semantics retained

A5 preserves the existing distinction:

```text
stage status == PASS
        ≠
profileVerificationComplete == true
```

`status` only reports failures among gates actually executed by this stage.

`profileVerificationComplete` is true only when:

- no executed gate failed; and
- every profile-required gate has a generated receipt.

Target-native, visual-review, delivery-readback, and other externally supplied evidence remain pending when this stage does not own their execution.

Generated VSAs remain **unsigned local statements**. Signature/root-of-trust authenticity remains owned by `artifact_trust`.

## Dependency direction after A5

```text
Artifact Delivery CLI / compatibility facade
                 |
                 v
       artifact_verification.stage
                 |
          +------+------+
          |             |
          v             v
 explicit verifier    artifact_verification.evidence
 hooks                  |
          |              v
          |       artifact_trust.vsa
          v
 existing concrete verifier owners
```

No dependency from `artifact_verification` points back to `artifact_delivery`.

## Monolith reduction

Measured on the A5 candidate:

```text
artifact_delivery.py at decomposition start: ~3922 lines
artifact_delivery.py after A2:               3458 lines
artifact_delivery.py after A3:               2822 lines
artifact_delivery.py after A4:               2242 lines
artifact_delivery.py after A5:               2028 lines
```

A5 removes another ~214 lines from Delivery after compatibility wiring is added.

Line count is secondary. The substantive change is that verify-stage policy and evidence/VSA assembly now have explicit owners outside the CLI facade.

## TDD evidence

A5 ownership/behavior tests were written before implementation and observed RED because:

- `artifact_verification` did not exist;
- `_write_raw_and_vsa` was still implemented in Delivery;
- `execute_verify_stage` was still a 222-line Delivery implementation.

After implementation:

- A5 tests: 5 PASS;
- legacy `test_artifact_delivery.py`: 79 tests, 0 failures, 2 conditional skips;
- A2+A3+A4+A5+OCI targeted bundle: 31 PASS;
- Temporal Artifact delivery contract: 12 PASS;
- full Artifact regression: 339 tests, 0 failures, 4 conditional skips;
- `compileall`: PASS;
- `git diff --check`: PASS before final commit gate.

Candidate full-regression Runtime Job:

`job-01a0b2b5-c3a2-7782-b114-d2c763a6906d`

## Non-claims / next wave

A5 does **not** claim Artifact decomposition complete.

Largest remaining knots:

1. **Concrete verifier ownership** — presentation package inspection/semantic checks, document semantic/dependency verification, PDF/Web/OpenXML verifier code still live largely in Delivery.
2. **OCI residual Delivery imports** — OCI still imports `build_presentation_source`, `execute_verify_stage`, `validate_delivery_request`, and `write_json` through compatibility surfaces.
3. **Temporal adapter** — still knows Delivery CLI verbs and stage/output layout rather than a stable generic Artifact operation contract.
4. **Presentation aggregate gate** — `presentation_gate()` still combines multiple evidence families inside Delivery.
5. **Cross-format helpers / CLI** — Delivery still owns several verifier/tool helper functions and command parsing.

The next wave should target **concrete verifier ownership** in bounded families, beginning with presentation verification/evidence or document verification. It should not merge verifier implementations into `artifact_verification.stage`; the stage is now intentionally an orchestration layer.
