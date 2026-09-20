from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from artifact_core.contracts import file_fact
from artifact_core.profile_v1 import validate_profile_v1 as validate_profile
from artifact_evidence.delivery import (
    verify_delivery_evidence,
    verify_render_evidence,
    verify_target_evidence,
    verify_visual_review,
)

from .inspection import inspect_pptx, verify_openxml_evidence
from .semantics import verify_font_manifest, verify_presentation_semantics

PdfVerifier = Callable[[Path], dict[str, Any]]


@dataclass(frozen=True)
class PresentationGateHooks:
    verify_pdf: PdfVerifier


def presentation_gate(
    profile_path: Path,
    pptx: Path,
    pdf: Path | None,
    render_dir: Path | None,
    openxml_evidence: Path | None,
    target_evidence: Path | None,
    visual_evidence: Path | None,
    delivery_evidence: Iterable[Path],
    font_dir: Path,
    *,
    hooks: PresentationGateHooks,
) -> dict[str, Any]:
    profile_result = validate_profile(profile_path)
    profile = profile_result["profile"]
    gates = profile.get("gates", {})
    placeholders = profile.get("semanticPolicy", {}).get("placeholderPatterns", [])
    pptx_result = inspect_pptx(pptx, placeholders)
    slide_count = int(pptx_result.get("package", {}).get("slideCount", 0))

    if openxml_evidence is None:
        openxml_result = {
            "status": "NOT_RUN",
            "reason": "no DocumentFormat.OpenXml validation evidence supplied",
        }
    else:
        openxml_result = verify_openxml_evidence(openxml_evidence, pptx)

    if pptx_result.get("status") != "PASS":
        structural_status = "FAIL"
    elif openxml_result.get("status") != "PASS":
        structural_status = openxml_result.get("status", "FAIL")
    else:
        structural_status = "PASS"

    semantic_result = verify_presentation_semantics(profile, pptx_result)
    font_result = verify_font_manifest(
        profile,
        font_dir,
        pptx_result.get("package", {}).get("renderExplicitTypefaceNames", []),
    )

    if pdf is None:
        pdf_result: dict[str, Any] = {
            "status": "NOT_RUN",
            "reason": "no companion PDF supplied",
        }
    else:
        pdf_result = hooks.verify_pdf(pdf)

    if render_dir is None:
        render_result: dict[str, Any] = {
            "status": "NOT_RUN",
            "reason": "no rendered PNG directory supplied",
        }
    else:
        render_result = verify_render_evidence(render_dir, slide_count)

    if target_evidence is None:
        target_result: dict[str, Any] = {
            "status": "NOT_RUN",
            "reason": "no target PowerPoint evidence supplied",
        }
    else:
        target_result = verify_target_evidence(
            target_evidence,
            pptx,
            pdf,
            slide_count,
            render_result,
        )

    if visual_evidence is None:
        visual_result: dict[str, Any] = {
            "status": "NOT_RUN",
            "reason": "no digest-bound visual review evidence supplied",
        }
    elif render_result.get("status") != "PASS":
        visual_result = {
            "status": "FAIL",
            "reason": "render evidence integrity failed before visual review",
        }
    else:
        visual_result = verify_visual_review(
            visual_evidence,
            pptx,
            render_result,
        )

    delivery_paths = list(delivery_evidence)
    if not delivery_paths:
        delivery_result: dict[str, Any] = {
            "status": "NOT_RUN",
            "reason": "no destination read-back evidence supplied",
        }
    else:
        delivery_result = verify_delivery_evidence(
            delivery_paths,
            profile,
            pptx,
            pdf,
        )

    component = {
        "profileSchema": profile_result["status"],
        "structural": structural_status,
        "dependency": font_result["status"],
        "semantic": semantic_result["status"],
        "companionPdf": pdf_result["status"],
        "visual": visual_result["status"],
        "target": target_result["status"],
        "deliveryReadback": delivery_result["status"],
    }
    required_failures = [
        name
        for name, required in gates.items()
        if required and (name not in component or component[name] != "PASS")
    ]
    return {
        "status": "PASS" if not required_failures else "FAIL",
        "profileId": profile.get("id"),
        "artifact": file_fact(pptx),
        "requiredGateFailures": required_failures,
        "components": {
            "profile": profile_result,
            "pptx": pptx_result,
            "openXmlValidation": openxml_result,
            "semantic": semantic_result,
            "fonts": font_result,
            "pdf": pdf_result,
            "renders": render_result,
            "visualReview": visual_result,
            "target": target_result,
            "deliveryReadback": delivery_result,
        },
        "truthBoundary": (
            "PASS requires every profile-required gate represented here, including "
            "target PowerPoint evidence, visual review, and destination read-back. "
            "External delivery adapters still own the actual write/read effects."
        ),
    }
