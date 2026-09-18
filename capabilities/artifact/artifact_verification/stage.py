from __future__ import annotations

from dataclasses import dataclass
import importlib.metadata
from pathlib import Path
import shutil
import subprocess
from typing import Any, Callable

from artifact_core.contracts import file_fact
from artifact_trust.vsa import LOCAL_VSA_VERIFIER_ID
from .evidence import write_gate_receipt


ProfileValidator = Callable[[Path], dict[str, Any]]
PrimarySuffixResolver = Callable[[dict[str, Any]], str]
ArtifactVerifier = Callable[[Path], dict[str, Any]]
RequestValidator = Callable[[Path], dict[str, Any]]
DocumentSemanticVerifier = Callable[[Path, Path], dict[str, Any]]
DocumentDependencyVerifier = Callable[[Path, Path], dict[str, Any]]
PresentationInspector = Callable[[Path, Any], dict[str, Any]]
PresentationSemanticVerifier = Callable[[dict[str, Any], dict[str, Any]], dict[str, Any]]
PdfConformanceVerifier = Callable[[Path, str], dict[str, Any]]
HtmlVerifier = Callable[[Path], dict[str, Any]]


@dataclass(frozen=True)
class VerificationStageHooks:
    validate_profile: ProfileValidator
    primary_suffix: PrimarySuffixResolver
    verify_openxml_artifact: ArtifactVerifier
    validate_delivery_request: RequestValidator
    verify_document_semantic_correspondence: DocumentSemanticVerifier
    verify_document_dependencies: DocumentDependencyVerifier
    inspect_pptx: PresentationInspector
    verify_presentation_semantics: PresentationSemanticVerifier
    verify_pdf: ArtifactVerifier
    verify_pdf_conformance: PdfConformanceVerifier
    verify_html_conformance: HtmlVerifier
    verify_web_local: HtmlVerifier


def _qpdf_version() -> str:
    executable = shutil.which("qpdf")
    if not executable:
        return "unknown"
    proc = subprocess.run(
        [executable, "--version"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=10,
    )
    return proc.stdout.splitlines()[0] if proc.stdout else "unknown"


def execute_verify_stage(
    profile_path: Path,
    artifact: Path,
    output_dir: Path,
    request_path: Path | None = None,
    *,
    hooks: VerificationStageHooks,
) -> dict[str, Any]:
    """Execute only locally available verification gates and bind their evidence."""
    profile_result = hooks.validate_profile(profile_path)
    profile = profile_result.get("profile", {})
    artifact_class = profile.get("artifactClass")
    receipts: dict[str, Any] = {}
    failures: list[str] = []
    if profile_result.get("status") != "PASS":
        failures.append("delivery profile did not PASS validation")
    expected_suffix = hooks.primary_suffix(profile) if profile else None
    if expected_suffix and artifact.suffix.casefold() != expected_suffix:
        failures.append(
            f"artifact suffix {artifact.suffix} does not match profile primary output {expected_suffix}"
        )
    if not artifact.is_file():
        failures.append("artifact file is absent")
    if failures:
        return {
            "schemaVersion": 1,
            "kind": "artifact-delivery-verify-stage",
            "status": "FAIL",
            "profileId": profile.get("id"),
            "failures": failures,
            "receipts": receipts,
        }

    profile_raw = {
        "status": profile_result.get("status"),
        "profile": file_fact(profile_path),
        "jsonSchema": profile_result.get("jsonSchema"),
        "minimalContractErrors": profile_result.get("minimalContractErrors", []),
        "boundary": (
            "Delivery-profile schema/contract validation only; artifact-format, target, "
            "visual, accessibility and delivery gates remain independent."
        ),
    }
    receipts["profileSchema"] = write_gate_receipt(
        output_dir,
        "profileSchema",
        artifact,
        profile_path,
        profile_raw,
        LOCAL_VSA_VERIFIER_ID,
        {"jsonschema": importlib.metadata.version("jsonschema")},
    )

    if artifact_class in {"presentation", "document", "spreadsheet"}:
        raw = hooks.verify_openxml_artifact(artifact)
        version = str(
            raw.get("validatorOutput", {})
            .get("validator", {})
            .get("packageVersion", "unknown")
        )
        receipts["structural"] = write_gate_receipt(
            output_dir,
            "structural",
            artifact,
            profile_path,
            raw,
            LOCAL_VSA_VERIFIER_ID,
            {"DocumentFormat.OpenXml": version},
        )
        if artifact_class == "document" and request_path is not None:
            request_validation = hooks.validate_delivery_request(request_path)
            if request_validation.get("status") == "PASS":
                source_path = Path(request_validation["resolved"]["source"]["path"])
                semantic_raw = hooks.verify_document_semantic_correspondence(
                    source_path, artifact
                )
            else:
                semantic_raw = {
                    "status": "FAIL",
                    "artifact": file_fact(artifact),
                    "request": file_fact(request_path),
                    "failures": [
                        "delivery request did not PASS before document semantic verification"
                    ],
                }
            receipts["semantic"] = write_gate_receipt(
                output_dir,
                "semantic",
                artifact,
                profile_path,
                semantic_raw,
                LOCAL_VSA_VERIFIER_ID,
                {"Pandoc": str(semantic_raw.get("pandoc", {}).get("version", "unknown"))},
            )
            dependency_raw = hooks.verify_document_dependencies(request_path, artifact)
            receipts["dependency"] = write_gate_receipt(
                output_dir,
                "dependency",
                artifact,
                profile_path,
                dependency_raw,
                LOCAL_VSA_VERIFIER_ID,
                {
                    "Pandoc": str(
                        dependency_raw.get("pandoc", {}).get("version", "unknown")
                    ),
                    "OpenXML": "locked-runtime",
                },
            )
        if artifact_class == "presentation":
            inspected = hooks.inspect_pptx(
                artifact,
                profile.get("semanticPolicy", {}).get("placeholderPatterns", []),
            )
            semantic = hooks.verify_presentation_semantics(profile, inspected)
            raw_semantic = {
                "status": (
                    "PASS"
                    if inspected.get("status") == "PASS"
                    and semantic.get("status") == "PASS"
                    else "FAIL"
                ),
                "artifact": file_fact(artifact),
                "inspection": inspected,
                "semantic": semantic,
                "boundary": (
                    "Presentation-local package/slide semantic checks only; target "
                    "rendering, visual review and delivery remain separate."
                ),
            }
            receipts["semantic"] = write_gate_receipt(
                output_dir,
                "semantic",
                artifact,
                profile_path,
                raw_semantic,
                LOCAL_VSA_VERIFIER_ID,
                {"python-pptx": importlib.metadata.version("python-pptx")},
            )
    elif artifact_class in {"fixed-view", "archive", "accessible"}:
        raw = hooks.verify_pdf(artifact)
        receipts["structural"] = write_gate_receipt(
            output_dir,
            "structural",
            artifact,
            profile_path,
            raw,
            LOCAL_VSA_VERIFIER_ID,
            {"qpdf": _qpdf_version()},
        )
        if profile.get("gates", {}).get("conformance") is True:
            flavour = profile.get("conformancePolicy", {}).get("pdfFlavour")
            if not isinstance(flavour, str):
                conformance_raw = {
                    "status": "FAIL",
                    "error": (
                        "profile requires conformance but omits "
                        "conformancePolicy.pdfFlavour"
                    ),
                }
            else:
                conformance_raw = hooks.verify_pdf_conformance(artifact, flavour)
            receipts["conformance"] = write_gate_receipt(
                output_dir,
                "conformance",
                artifact,
                profile_path,
                conformance_raw,
                LOCAL_VSA_VERIFIER_ID,
                {"veraPDF": "1.30.2"},
            )
    elif artifact_class == "web":
        conformance = hooks.verify_html_conformance(artifact)
        vnu_version = str(conformance.get("validator", {}).get("version") or "unknown")
        receipts["conformance"] = write_gate_receipt(
            output_dir,
            "conformance",
            artifact,
            profile_path,
            conformance,
            LOCAL_VSA_VERIFIER_ID,
            {"Nu Html Checker": vnu_version},
        )
        receipts["structural"] = write_gate_receipt(
            output_dir,
            "structural",
            artifact,
            profile_path,
            conformance,
            LOCAL_VSA_VERIFIER_ID,
            {"Nu Html Checker": vnu_version},
        )
        web = hooks.verify_web_local(artifact)
        output = (
            web.get("verifierOutput", {})
            if isinstance(web.get("verifierOutput"), dict)
            else {}
        )
        browsers = (
            output.get("browsers", {})
            if isinstance(output.get("browsers"), dict)
            else {}
        )
        chromium = (
            browsers.get("chromium", {})
            if isinstance(browsers.get("chromium"), dict)
            else {}
        )
        accessibility_passed = (
            chromium.get("status") == "PASS"
            and chromium.get("accessibility", {}).get("status") == "PASS"
        )
        receipts["accessibility"] = write_gate_receipt(
            output_dir,
            "accessibility",
            artifact,
            profile_path,
            web,
            LOCAL_VSA_VERIFIER_ID,
            {
                "@axe-core/playwright": str(
                    output.get("tooling", {}).get("axePlaywright", "unknown")
                ),
                "@playwright/test": str(
                    output.get("tooling", {}).get("playwright", "unknown")
                ),
            },
            accessibility_passed,
        )
        required_names = (
            [str(profile.get("targetRenderer", {}).get("name"))]
            if profile.get("targetRenderer", {}).get("required") is True
            else []
        )
        required_names.extend(
            str(item.get("name"))
            for item in profile.get("secondaryRenderers", [])
            if item.get("required") is True
        )
        browser_by_name = {
            str(item.get("name")): item
            for item in browsers.values()
            if isinstance(item, dict) and item.get("name")
        }
        target_passed = bool(required_names) and all(
            browser_by_name.get(name, {}).get("status") == "PASS"
            for name in required_names
        )
        target_raw = {
            "status": "PASS" if target_passed else "FAIL",
            "artifact": file_fact(artifact),
            "requiredRenderers": required_names,
            "browserResults": browser_by_name,
            "failures": [
                name
                for name in required_names
                if browser_by_name.get(name, {}).get("status") != "PASS"
            ],
            "boundary": (
                "Target renderer policy requires every profile-required "
                "primary/secondary renderer. Unsupported-host WebKit remains a hard "
                "failure rather than a local compatibility waiver."
            ),
        }
        receipts["target"] = write_gate_receipt(
            output_dir,
            "target",
            artifact,
            profile_path,
            target_raw,
            LOCAL_VSA_VERIFIER_ID,
            {
                "@playwright/test": str(
                    output.get("tooling", {}).get("playwright", "unknown")
                )
            },
            target_passed,
        )
    else:
        failures.append(
            f"no verify-stage adapters for artifactClass={artifact_class!r}"
        )

    executed_failures = [
        gate for gate, item in receipts.items() if item.get("status") != "PASS"
    ]
    required_gates = {
        name for name, flag in profile.get("gates", {}).items() if flag is True
    }
    generated = set(receipts)
    pending = sorted(required_gates - generated)
    if executed_failures:
        failures.append(
            "executed verifier gate(s) failed: "
            + ", ".join(sorted(executed_failures))
        )
    return {
        "schemaVersion": 1,
        "kind": "artifact-delivery-verify-stage",
        "status": "PASS" if not failures else "FAIL",
        "profileId": profile.get("id"),
        "artifact": file_fact(artifact),
        "receipts": receipts,
        "profileRequiredGates": sorted(required_gates),
        "pendingRequiredGates": pending,
        "profileVerificationComplete": not failures and not pending,
        "failures": failures,
        "boundary": (
            "Verify-stage status covers only adapters executed here. "
            "profileVerificationComplete is the stronger statement and remains false "
            "until every profile-required gate has independent evidence. Generated "
            "VSAs are unsigned local statements; external trust requires "
            "signature/root-of-trust verification."
        ),
    }
