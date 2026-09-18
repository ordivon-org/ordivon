#!/usr/bin/env python3
"""Standard-native Artifact Build & Delivery R1 gates.

This module deliberately does not define a universal document model. It checks
build/delivery facts around native artifacts and delegates format conformance to
mature validators whenever available.
"""

from __future__ import annotations

import argparse
import copy
import datetime as dt
import hashlib
import importlib.util
import importlib.metadata
import io
import json
import os
from pathlib import Path, PurePosixPath
import posixpath
import re
import shutil
import subprocess
import struct
import sys
import tempfile
import urllib.parse
import xml.etree.ElementTree as ET
import zipfile
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from artifact_core.admission import AdmissionHooks, admit_delivery_request
from artifact_core.json_validation import validate_json_document as core_validate_json_document
from artifact_core.build_bindings import BuildCapabilityBindingRegistry
from artifact_core.build_planning import compile_delivery_plan_from_validation
from artifact_core.contracts import file_fact, sha256_file
from artifact_core.profile_v1 import validate_profile_v1 as validate_profile
from artifact_trust.provenance import slsa_statement, verify_release_provenance
import artifact_trust.vsa as trust_vsa
from artifact_capabilities.dispatch import execute_build_adapter
from artifact_capabilities.presentation import (
    DETERMINISTIC_OPC_CORE_TIMESTAMP,
    DETERMINISTIC_ZIP_DATETIME,
    PresentationBuildHooks,
    _canonicalize_ppt_creation_ids as presentation_canonicalize_ppt_creation_ids,
    canonicalize_generated_ooxml_metadata as presentation_canonicalize_ooxml,
    normalize_zip_member_timestamps as presentation_normalize_zip_timestamps,
    admit_presentation_source as presentation_admit_source,
    admit_semantic_svg_source as presentation_admit_semantic_svg_source,
    build_presentation_source as presentation_build_source,
    build_semantic_svg_presentation_source as presentation_build_semantic_svg_source,
)
import artifact_capabilities.presentation.common as presentation_common
import artifact_capabilities.presentation.ppt_master as presentation_ppt_master
from artifact_verifiers.document import (
    DocumentDependencyHooks,
    verify_document_dependencies as document_verify_dependencies,
    verify_document_semantic_correspondence as document_verify_semantics,
)
from artifact_verifiers.web import (
    verify_html_conformance as web_verify_conformance,
    verify_web_local as web_verify_local,
    vnu_jar as web_vnu_jar,
)
from artifact_verifiers.openxml import (
    verify_openxml_artifact as openxml_verify_artifact,
)
from artifact_verifiers.pdf import (
    verapdf_executable as pdf_verapdf_executable,
    verify_pdf as pdf_verify_structural,
    verify_pdf_conformance as pdf_verify_conformance,
)
from artifact_verifiers.presentation import (
    PresentationGateHooks,
    inspect_pptx as presentation_inspect_pptx,
    presentation_gate as presentation_verification_gate,
    verify_font_manifest as presentation_verify_fonts,
    verify_openxml_evidence as presentation_verify_openxml_evidence,
    verify_presentation_semantics as presentation_verify_semantics,
)
from artifact_verification import (
    VerificationStageHooks,
    execute_verify_stage as verification_execute_stage,
    write_gate_receipt,
)
from artifact_evidence.delivery import (
    verify_delivery_evidence,
    verify_file_fact,
    verify_readback,
    verify_render_evidence,
    verify_target_evidence,
    verify_visual_review,
)

BUILD_BINDING_REGISTRY = BuildCapabilityBindingRegistry(ROOT / "artifact-delivery")
GLOBAL_ARTIFACT_TOOLCHAIN_ROOT = Path(os.environ.get("ARTIFACT_TOOLCHAIN_ROOT", "/opt/ordivon/external/artifact-toolchain"))
GLOBAL_PANDOC = GLOBAL_ARTIFACT_TOOLCHAIN_ROOT / "pandoc/3.10.2/bin/pandoc"
GLOBAL_PANDOC_ARCHIVE = GLOBAL_ARTIFACT_TOOLCHAIN_ROOT / "pandoc/3.10.2/pandoc-3.10.2-linux-amd64.tar.gz"
GLOBAL_VERAPDF = GLOBAL_ARTIFACT_TOOLCHAIN_ROOT / "verapdf/1.30.2/verapdf"


def _selected_external_file(env_name: str, global_candidate: Path, legacy_candidate: Path) -> Path:
    configured = os.environ.get(env_name)
    if configured:
        return Path(configured)
    if global_candidate.is_file():
        return global_candidate
    if legacy_candidate.is_file():
        return legacy_candidate
    return global_candidate


DEFAULT_SCHEMA = ROOT / "artifact-delivery/profile-v1.schema.json"
DEFAULT_REQUEST_SCHEMA = ROOT / "artifact-delivery/request-v1.schema.json"
DEFAULT_PRESENTATION_SOURCE_SCHEMA = ROOT / "artifact-delivery/presentation-source-v1.schema.json"
DEFAULT_PRESENTATION_SEMANTIC_SVG_SOURCE_SCHEMA = ROOT / "artifact-delivery/presentation-semantic-svg-source-v1.schema.json"
PPT_MASTER_PROVIDER_LOCK = ROOT / "artifact-delivery/ppt-master-provider-v1.lock.json"
DEFAULT_OPC_MEMBER_PROJECTION_SCHEMA = ROOT / "artifact-delivery/opc-member-projection-v1.schema.json"
DEFAULT_WINDOWS_FONTS = Path("/mnt/c/Windows/Fonts")
DEFAULT_VSA_TRUST_POLICY_SCHEMA = trust_vsa.DEFAULT_VSA_TRUST_POLICY_SCHEMA
IN_TOTO_STATEMENT_V1 = trust_vsa.IN_TOTO_STATEMENT_V1
SLSA_PROVENANCE_V1 = "https://slsa.dev/provenance/v1"
SLSA_VERIFICATION_SUMMARY_V1 = trust_vsa.SLSA_VERIFICATION_SUMMARY_V1
SLSA_VERSION = trust_vsa.SLSA_VERSION
LOCAL_VSA_VERIFIER_ID = trust_vsa.LOCAL_VSA_VERIFIER_ID
SIGSTORE_BUNDLE_V03 = trust_vsa.SIGSTORE_BUNDLE_V03
INTOTO_DSSE_PAYLOAD_TYPE = trust_vsa.INTOTO_DSSE_PAYLOAD_TYPE
COSIGN_STANDARD_BUNDLE_MIN_VERSION = trust_vsa.COSIGN_STANDARD_BUNDLE_MIN_VERSION
COSIGN_LOCK_PATH = trust_vsa.COSIGN_LOCK_PATH
COSIGN_SELECTED_BINARY = trust_vsa.COSIGN_SELECTED_BINARY
COSIGN_ARCH_PACKAGE = trust_vsa.COSIGN_ARCH_PACKAGE
COSIGN_ARCH_PACKAGE_SIGNATURE = trust_vsa.COSIGN_ARCH_PACKAGE_SIGNATURE
_COSIGN_PROVENANCE_CACHE = trust_vsa._COSIGN_PROVENANCE_CACHE
VSA_GATE_NAMES = trust_vsa.VSA_GATE_NAMES
ASSEMBLY_GATE_NAMES = trust_vsa.ASSEMBLY_GATE_NAMES
OOXML_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
PRESENTATION_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"
DRAWING_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")






def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))





def normalize_zip_member_timestamps(
    path: Path, value: tuple[int, int, int, int, int, int] = DETERMINISTIC_ZIP_DATETIME,
) -> dict[str, Any]:
    return presentation_normalize_zip_timestamps(path, value)


def _canonicalize_ppt_creation_ids(
    payload: bytes, member_name: str, used_values: set[int] | None = None,
) -> tuple[bytes, int]:
    return presentation_canonicalize_ppt_creation_ids(payload, member_name, used_values)









def canonicalize_generated_ooxml_metadata(path: Path) -> dict[str, Any]:
    return presentation_canonicalize_ooxml(path)





def validate_json_document(
    document_path: Path, schema_path: Path, expected_kind: str | None = None,
) -> dict[str, Any]:
    return core_validate_json_document(document_path, schema_path, expected_kind)



def _presentation_build_hooks() -> PresentationBuildHooks:
    return PresentationBuildHooks(
        validate_json_document=validate_json_document,
        inspect_pptx=presentation_inspect_pptx,
        verify_semantics=presentation_verify_semantics,
        normalize_python_pptx=normalize_zip_member_timestamps,
        canonicalize_ppt_master=canonicalize_generated_ooxml_metadata,
    )


# Compatibility-only private projections for historical tests/callers.
_resolve_semantic_svg_source_path = presentation_common._resolve_semantic_svg_source_path
_safe_project_relative_path = presentation_common._safe_project_relative_path
_semantic_svg_source_material_facts = presentation_common._semantic_svg_source_material_facts
_ppt_master_provider_facts = presentation_ppt_master._ppt_master_provider_facts
_resolve_presentation_template = presentation_common._resolve_presentation_template
_resolve_presentation_image = presentation_common._resolve_presentation_image
_presentation_source_material_facts = presentation_common._presentation_source_material_facts
_presentation_template_package_fact = presentation_common._presentation_template_package_fact
_presentation_layout_by_id = presentation_common._presentation_layout_by_id
_presentation_layout_fact = presentation_common._presentation_layout_fact
_apply_text_to_shape = presentation_common._apply_text_to_shape
_hex_color = presentation_common._hex_color


def _resolve_request_path(request_path: Path, relative: str) -> Path:
    candidate = Path(relative)
    if candidate.is_absolute():
        return candidate.resolve()
    return (request_path.resolve().parent / candidate).resolve()










def build_semantic_svg_presentation_source(
    source_path: Path,
    profile_path: Path,
    output_path: Path,
    source_schema_path: Path = DEFAULT_PRESENTATION_SEMANTIC_SVG_SOURCE_SCHEMA,
) -> dict[str, Any]:
    return presentation_build_semantic_svg_source(
        source_path, profile_path, output_path, source_schema_path, hooks=_presentation_build_hooks()
    )



def _admit_presentation_source(source_path: Path) -> tuple[dict[str, Any] | None, list[dict[str, Any]], list[str]]:
    return presentation_admit_source(
        source_path, validate_json_document=validate_json_document, source_schema_path=DEFAULT_PRESENTATION_SOURCE_SCHEMA
    )



def _admit_semantic_svg_source(source_path: Path) -> tuple[dict[str, Any] | None, list[dict[str, Any]], list[str]]:
    return presentation_admit_semantic_svg_source(
        source_path, validate_json_document=validate_json_document, source_schema_path=DEFAULT_PRESENTATION_SEMANTIC_SVG_SOURCE_SCHEMA
    )



def validate_delivery_request(
    request_path: Path,
    request_schema_path: Path = DEFAULT_REQUEST_SCHEMA,
    profile_schema_path: Path = DEFAULT_SCHEMA,
) -> dict[str, Any]:
    hooks = AdmissionHooks(
        validate_json_document=validate_json_document,
        validate_profile=validate_profile,
        source_validators={
            "presentation-source-v1": _admit_presentation_source,
            "presentation-semantic-svg-source-v1": _admit_semantic_svg_source,
        },
        file_fact=file_fact,
        sha256_file=sha256_file,
    )
    return admit_delivery_request(
        request_path,
        request_schema_path=request_schema_path,
        profile_schema_path=profile_schema_path,
        hooks=hooks,
    )



def compile_delivery_plan(request_path: Path) -> dict[str, Any]:
    validation = validate_delivery_request(request_path)
    return compile_delivery_plan_from_validation(
        request_path,
        validation,
        registry=BUILD_BINDING_REGISTRY,
        sha256_file=sha256_file,
    )



def _primary_suffix(profile: dict[str, Any]) -> str:
    suffixes = {
        "pptx": ".pptx",
        "docx": ".docx",
        "xlsx": ".xlsx",
        "html": ".html",
        "pdf": ".pdf",
        "pdf-a-4": ".pdf",
        "pdf-ua-2": ".pdf",
    }
    fmt = str(profile.get("primaryOutput", {}).get("format", ""))
    suffix = suffixes.get(fmt)
    if suffix is None:
        raise RuntimeError(f"unsupported primary output format: {fmt}")
    return suffix


def _request_output_name(request_id: str, suffix: str) -> str:
    stem = re.sub(r"[^A-Za-z0-9._-]+", "-", request_id).strip("-._") or "artifact"
    return stem + suffix


def execute_build_stage(request_path: Path, output_directory: Path | None = None) -> dict[str, Any]:
    plan = compile_delivery_plan(request_path)
    if plan.get("status") != "PASS":
        return {
            "schemaVersion": 1,
            "kind": "artifact-delivery-build-stage",
            "status": "FAIL",
            "plan": plan,
            "failures": ["derived delivery plan did not PASS"],
        }
    validation = validate_delivery_request(request_path)
    request = validation["request"]
    profile = validation["profileValidation"]["profile"]
    source_path = Path(validation["resolved"]["source"]["path"])
    profile_path = Path(validation["resolved"]["profile"]["path"])
    if output_directory is None:
        output_directory = _resolve_request_path(request_path, str(request["outputDirectory"]))
    output_directory.mkdir(parents=True, exist_ok=True)
    suffix = _primary_suffix(profile)
    output_path = output_directory / _request_output_name(str(request["requestId"]), suffix)
    adapter = plan["buildAdapter"]
    pandoc = _selected_external_file("ARTIFACT_PANDOC", GLOBAL_PANDOC, ROOT / ".cache/artifact-toolchain/pandoc/current/bin/pandoc")
    adapter_result = execute_build_adapter(
        adapter,
        source_path=source_path,
        profile_path=profile_path,
        output_path=output_path,
        presentation_builders={
            "python-pptx-presentation-source-v1": build_presentation_source,
            "ppt-master-semantic-svg-v1": build_semantic_svg_presentation_source,
        },
        pandoc=pandoc,
    )
    failures: list[str] = []
    if adapter_result.get("status") != "PASS":
        failures.append(f"build adapter did not PASS: {adapter}")
    if not output_path.is_file():
        failures.append("primary output file is absent")
    return {
        "schemaVersion": 1,
        "kind": "artifact-delivery-build-stage",
        "status": "PASS" if not failures else "FAIL",
        "request": file_fact(request_path),
        "plan": plan,
        "adapterResult": adapter_result,
        "artifact": file_fact(output_path) if output_path.is_file() else None,
        "failures": failures,
        "boundary": "Build-stage PASS means exact request/profile/source bytes produced the primary artifact through the selected adapter. Independent verification, target rendering, packaging, provenance and release gates are not implied.",
    }










def verify_document_semantic_correspondence(
    source: Path, document: Path, pandoc: Path | None = None,
) -> dict[str, Any]:
    return document_verify_semantics(source, document, pandoc)



def verify_document_dependencies(
    request_path: Path, document: Path, pandoc: Path | None = None,
    pandoc_archive: Path | None = None, toolchain_lock: Path | None = None,
    openxml_validator: Path | None = None,
) -> dict[str, Any]:
    return document_verify_dependencies(
        request_path, document, pandoc, pandoc_archive, toolchain_lock,
        openxml_validator, hooks=_document_dependency_hooks(),
    )




















def build_presentation_source(
    source_path: Path,
    profile_path: Path,
    output_path: Path,
    source_schema_path: Path = DEFAULT_PRESENTATION_SOURCE_SCHEMA,
) -> dict[str, Any]:
    return presentation_build_source(
        source_path, profile_path, output_path, source_schema_path, hooks=_presentation_build_hooks()
    )





def _normalized_posix_relative(value: str, field: str) -> PurePosixPath:
    if not isinstance(value, str) or not value or "\\" in value:
        raise RuntimeError(f"{field} must be one normalized POSIX relative path")
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or str(path) != value or value in {".", ""}:
        raise RuntimeError(f"{field} must be one normalized POSIX relative path")
    return path


def _normalized_sha256(value: Any, field: str) -> str:
    if not isinstance(value, str):
        raise RuntimeError(f"{field} must be sha256:<64-hex>")
    lowered = value.lower()
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", lowered):
        raise RuntimeError(f"{field} must be sha256:<64-hex>")
    return lowered


def project_opc_members(package_path: Path, manifest_path: Path, output_root: Path) -> dict[str, Any]:
    validation = validate_json_document(
        manifest_path,
        DEFAULT_OPC_MEMBER_PROJECTION_SCHEMA,
        "artifact-delivery-opc-member-projection",
    )
    if validation.get("status") != "PASS":
        return {
            "status": "FAIL",
            "package": file_fact(package_path) if package_path.is_file() else {"path": str(package_path)},
            "manifest": file_fact(manifest_path),
            "failures": ["OPC member projection manifest schema did not PASS"],
            "validation": validation,
        }
    manifest = validation["document"]
    if package_path.is_symlink():
        raise RuntimeError("OPC parent package must be one regular non-symlink file")
    package = package_path.resolve()
    if not package.is_file():
        raise RuntimeError("OPC parent package must be one regular non-symlink file")
    parent_digest = "sha256:" + sha256_file(package)
    expected_parent = _normalized_sha256(manifest["parentPackage"]["sha256"], "parentPackage.sha256")
    if parent_digest != expected_parent:
        raise RuntimeError(f"OPC parent package digest mismatch: expected {expected_parent}, observed {parent_digest}")
    expected_parent_size = int(manifest["parentPackage"]["expectedSizeBytes"])
    if package.stat().st_size != expected_parent_size:
        raise RuntimeError(
            f"OPC parent package size mismatch: expected {expected_parent_size}, observed {package.stat().st_size}"
        )
    if not zipfile.is_zipfile(package):
        raise RuntimeError("OPC parent package is not a ZIP/OPC package")

    if output_root.exists() and output_root.is_symlink():
        raise RuntimeError("OPC projection output root must be a real directory")
    root = output_root.resolve()
    root.mkdir(parents=True, exist_ok=True)
    if not root.is_dir():
        raise RuntimeError("OPC projection output root must be a real directory")

    projected: list[dict[str, Any]] = []
    replayed = 0
    declared_parts: set[str] = set()
    declared_outputs: set[str] = set()
    with zipfile.ZipFile(package) as archive:
        all_infos = archive.infolist()
        unsafe = _safe_zip_names(info.filename for info in all_infos)
        if unsafe:
            raise RuntimeError(f"OPC package contains unsafe member paths: {unsafe[:5]}")
        by_name: dict[str, list[zipfile.ZipInfo]] = {}
        for info in all_infos:
            by_name.setdefault(info.filename, []).append(info)

        for index, raw in enumerate(manifest["members"]):
            part = str(_normalized_posix_relative(raw["part"], f"members[{index}].part"))
            output_relative = _normalized_posix_relative(
                raw["outputRelativePath"], f"members[{index}].outputRelativePath"
            )
            expected_digest = _normalized_sha256(raw["sha256"], f"members[{index}].sha256")
            expected_size = int(raw["expectedSizeBytes"])
            if part in declared_parts:
                raise RuntimeError(f"OPC projection manifest duplicates part: {part}")
            if str(output_relative) in declared_outputs:
                raise RuntimeError(f"OPC projection manifest duplicates outputRelativePath: {output_relative}")
            declared_parts.add(part)
            declared_outputs.add(str(output_relative))
            matches = by_name.get(part, [])
            if len(matches) != 1:
                raise RuntimeError(f"OPC projected part must occur exactly once: {part} count={len(matches)}")
            info = matches[0]
            if info.is_dir():
                raise RuntimeError(f"OPC projected part is a directory: {part}")
            if info.flag_bits & 0x1:
                raise RuntimeError(f"OPC projected part is encrypted and not admitted: {part}")
            if info.file_size != expected_size:
                raise RuntimeError(
                    f"OPC projected part size mismatch for {part}: expected {expected_size}, observed {info.file_size}"
                )
            data = archive.read(info)
            observed_digest = "sha256:" + hashlib.sha256(data).hexdigest()
            if observed_digest != expected_digest:
                raise RuntimeError(
                    f"OPC projected part digest mismatch for {part}: expected {expected_digest}, observed {observed_digest}"
                )

            target = root.joinpath(*output_relative.parts)
            target_parent = target.parent
            target_parent.mkdir(parents=True, exist_ok=True)
            cursor = root
            for component in output_relative.parts[:-1]:
                cursor = cursor / component
                if cursor.is_symlink():
                    raise RuntimeError(f"OPC projection output parent is a symlink: {cursor}")
            if target.exists() or target.is_symlink():
                if target.is_symlink() or not target.is_file():
                    raise RuntimeError(f"OPC projection target is not a regular file: {target}")
                existing_digest = "sha256:" + sha256_file(target)
                if target.stat().st_size != expected_size or existing_digest != expected_digest:
                    raise RuntimeError(f"OPC projection refuses to overwrite conflicting target: {target}")
                replayed += 1
            else:
                temporary = target.with_name(f".{target.name}.{os.getpid()}.part")
                if temporary.exists() or temporary.is_symlink():
                    temporary.unlink()
                try:
                    with temporary.open("xb") as handle:
                        handle.write(data)
                        handle.flush()
                        os.fsync(handle.fileno())
                    if temporary.stat().st_size != expected_size or "sha256:" + sha256_file(temporary) != expected_digest:
                        raise RuntimeError(f"OPC projected temporary bytes changed before commit: {part}")
                    os.replace(temporary, target)
                finally:
                    if temporary.exists():
                        temporary.unlink()
            projected.append({
                "part": part,
                "outputRelativePath": str(output_relative),
                "expectedSizeBytes": expected_size,
                "sha256": expected_digest,
                "output": file_fact(target),
            })
    return {
        "status": "PASS",
        "kind": "artifact-delivery-opc-member-projection-receipt",
        "truthRole": "exact-package-part-byte-projection-only-not-domain-or-visual-acceptance",
        "package": file_fact(package),
        "manifest": file_fact(manifest_path),
        "projectionId": manifest["projectionId"],
        "outputRoot": str(root),
        "members": projected,
        "replayedMemberCount": replayed,
        "nonClaims": [
            "no provider/source identity beyond the parent package binding",
            "no visual parity claim",
            "no accessibility claim",
            "no business-content validation claim",
        ],
    }


def compose_reference_hybrid_source(
    semantic_source_path: Path,
    reference_map_path: Path,
    visual_root: Path,
    output_path: Path,
) -> dict[str, Any]:
    semantic_validation = validate_json_document(
        semantic_source_path,
        DEFAULT_PRESENTATION_SOURCE_SCHEMA,
        "presentation-source",
    )
    reference_validation = validate_json_document(
        reference_map_path,
        DEFAULT_PRESENTATION_SOURCE_SCHEMA,
        "presentation-source",
    )
    if semantic_validation.get("status") != "PASS" or reference_validation.get("status") != "PASS":
        return {
            "status": "FAIL",
            "failures": ["semantic source and reference map must both pass the presentation-source schema"],
            "semanticValidation": semantic_validation,
            "referenceValidation": reference_validation,
        }
    semantic = json.loads(json.dumps(semantic_validation["document"]))
    reference = reference_validation["document"]
    failures: list[str] = []
    for field in ("profileId", "aspectRatio", "slideSizeInches"):
        if semantic.get(field) != reference.get(field):
            failures.append(f"semantic/reference {field} mismatch")
    semantic_slides = semantic.get("slides", [])
    reference_slides = reference.get("slides", [])
    if len(semantic_slides) != len(reference_slides):
        failures.append("semantic/reference slide count mismatch")
    root = visual_root.resolve()
    width = float(semantic.get("slideSizeInches", {}).get("width", 0))
    height = float(semantic.get("slideSizeInches", {}).get("height", 0))
    for index, (slide, ref_slide) in enumerate(zip(semantic_slides, reference_slides), 1):
        if slide.get("id") != ref_slide.get("id"):
            failures.append(f"slide identity mismatch at index {index}")
            continue
        legacy = ref_slide.get("legacySource")
        if not isinstance(legacy, dict) or int(legacy.get("slideIndex", -1)) != index:
            failures.append(f"reference map lacks exact legacySource binding for slide {index}")
            continue
        digest = _normalized_sha256("sha256:" + str(legacy.get("sha256", "")), f"slides[{index-1}].legacySource.sha256")
        visual = root / f"slide-{index:02d}.jpeg"
        if not visual.is_file() or visual.is_symlink():
            failures.append(f"projected visual is absent/non-regular for slide {index}: {visual}")
            continue
        observed = "sha256:" + sha256_file(visual)
        if observed != digest:
            failures.append(f"projected visual digest mismatch for slide {index}: expected {digest}, observed {observed}")
            continue
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_parent = output_path.resolve().parent
        relative_visual = os.path.relpath(visual, output_parent).replace(os.sep, "/")
        image = {
            "kind": "image",
            "id": "frozen-visual-authority",
            "path": relative_visual,
            "sha256": digest.removeprefix("sha256:"),
            "box": {"x": 0.0, "y": 0.0, "w": width, "h": height},
            "decorative": False,
            "altText": (
                f"Frozen visual authority for slide {index}; native semantic overlays remain independently editable, "
                "and accessibility/use review is still required."
            ),
        }
        elements = slide.get("elements")
        if not isinstance(elements, list):
            failures.append(f"semantic slide elements are invalid for slide {index}")
            continue
        if any(element.get("id") == image["id"] for element in elements if isinstance(element, dict)):
            failures.append(f"semantic slide already contains reserved hybrid element id on slide {index}")
            continue
        slide["elements"] = [image, *elements]
    if failures:
        return {
            "status": "FAIL",
            "semanticSource": file_fact(semantic_source_path),
            "referenceMap": file_fact(reference_map_path),
            "failures": failures,
        }
    semantic["presentationId"] = str(semantic.get("presentationId", "presentation")) + "-hybrid"
    note = str(semantic.get("notes") or "").strip()
    boundary = (
        "Hybrid source mechanically composes frozen raster visual authority beneath native semantic overlays. "
        "Decorative raster standing is composition-only; accessibility, visual parity, target-render and business-content acceptance remain independent gates."
    )
    semantic["notes"] = (note + " " + boundary).strip()
    write_json(output_path, semantic)
    validation = validate_json_document(output_path, DEFAULT_PRESENTATION_SOURCE_SCHEMA, "presentation-source")
    if validation.get("status") != "PASS":
        return {
            "status": "FAIL",
            "semanticSource": file_fact(semantic_source_path),
            "referenceMap": file_fact(reference_map_path),
            "hybridSource": file_fact(output_path),
            "failures": ["composed hybrid source failed presentation-source schema"],
            "validation": validation,
        }
    return {
        "status": "PASS",
        "kind": "artifact-delivery-reference-hybrid-source-receipt",
        "truthRole": "frozen-raster-plus-native-semantic-composition-only-not-acceptance",
        "semanticSource": file_fact(semantic_source_path),
        "referenceMap": file_fact(reference_map_path),
        "hybridSource": file_fact(output_path),
        "visualRoot": str(root),
        "slideCount": len(semantic_slides),
        "nonClaims": [
            "no accessibility claim",
            "no visual parity claim",
            "no Microsoft PowerPoint target claim",
            "no business-content validation claim",
        ],
    }


def _safe_zip_names(names: Iterable[str]) -> list[str]:
    bad: list[str] = []
    for name in names:
        p = PurePosixPath(name)
        if p.is_absolute() or ".." in p.parts:
            bad.append(name)
    return bad


def _relationship_base(rels_name: str) -> str:
    if rels_name == "_rels/.rels":
        return ""
    marker = "/_rels/"
    if marker not in rels_name or not rels_name.endswith(".rels"):
        return ""
    left, right = rels_name.split(marker, 1)
    owner = posixpath.join(left, right[:-5])
    return posixpath.dirname(owner)


def _resolve_relationship_target(base: str, target: str) -> str | None:
    target = target.split("#", 1)[0]
    parsed = urllib.parse.urlparse(target)
    if parsed.scheme:
        return None
    if target.startswith("/"):
        resolved = posixpath.normpath(target.lstrip("/"))
    else:
        resolved = posixpath.normpath(posixpath.join(base, target))
    if resolved.startswith("../") or resolved == "..":
        return None
    return resolved


def inspect_pptx(path: Path, placeholder_patterns: Iterable[str] = ()) -> dict[str, Any]:
    return presentation_inspect_pptx(path, placeholder_patterns)



def verify_openxml_evidence(evidence_path: Path, artifact: Path) -> dict[str, Any]:
    return presentation_verify_openxml_evidence(evidence_path, artifact)



def verify_presentation_semantics(profile: dict[str, Any], pptx_result: dict[str, Any]) -> dict[str, Any]:
    return presentation_verify_semantics(profile, pptx_result)



def verify_font_manifest(
    profile: dict[str, Any],
    font_dir: Path,
    observed_typefaces: Iterable[str] = (),
) -> dict[str, Any]:
    return presentation_verify_fonts(profile, font_dir, observed_typefaces)



def verify_pdf(path: Path) -> dict[str, Any]:
    return pdf_verify_structural(path)



def _verapdf_executable() -> Path | None:
    return pdf_verapdf_executable()



def verify_pdf_conformance(path: Path, flavour: str) -> dict[str, Any]:
    return pdf_verify_conformance(path, flavour)



def verify_openxml_artifact(path: Path) -> dict[str, Any]:
    return openxml_verify_artifact(path)



def _vnu_jar() -> Path | None:
    return web_vnu_jar()



def verify_html_conformance(path: Path) -> dict[str, Any]:
    return web_verify_conformance(path)



def verify_web_local(path: Path) -> dict[str, Any]:
    return web_verify_local(path)



ni_sha256_uri = trust_vsa.ni_sha256_uri
verification_summary_statement = trust_vsa.verification_summary_statement
verify_verification_summary = trust_vsa.verify_verification_summary
validate_vsa_trust_policy = trust_vsa.validate_vsa_trust_policy
verify_sigstore_vsa_bundle_shape = trust_vsa.verify_sigstore_vsa_bundle_shape
_version_at_least = trust_vsa._version_at_least


def _delivery_trust_toolchain_config() -> trust_vsa.TrustToolchainConfig:
    return trust_vsa.TrustToolchainConfig(
        lock_path=COSIGN_LOCK_PATH,
        selected_binary=COSIGN_SELECTED_BINARY,
        arch_package=COSIGN_ARCH_PACKAGE,
        arch_package_signature=COSIGN_ARCH_PACKAGE_SIGNATURE,
    )


def _cosign_executable() -> Path | None:
    return trust_vsa._cosign_executable(_delivery_trust_toolchain_config())


def _cosign_selection_provenance(
    executable: Path,
    executable_digest: str,
    cosign_lock: dict[str, Any],
) -> dict[str, Any]:
    return trust_vsa._cosign_selection_provenance(
        executable, executable_digest, cosign_lock, _delivery_trust_toolchain_config()
    )


def cosign_tool_fact() -> dict[str, Any]:
    return trust_vsa.cosign_tool_fact(_delivery_trust_toolchain_config())


def verify_signed_verification_summary(
    statement_path: Path,
    bundle_path: Path,
    subject: Path,
    profile_path: Path,
    trust_policy_path: Path,
    signer_id: str,
) -> dict[str, Any]:
    return trust_vsa.verify_signed_verification_summary(
        statement_path,
        bundle_path,
        subject,
        profile_path,
        trust_policy_path,
        signer_id,
        toolchain=_delivery_trust_toolchain_config(),
    )




# Compatibility alias for historical private callers; implementation is owned by artifact_verification.
_write_raw_and_vsa = write_gate_receipt


def _document_dependency_hooks() -> DocumentDependencyHooks:
    return DocumentDependencyHooks(
        validate_delivery_request=validate_delivery_request,
        compile_delivery_plan=compile_delivery_plan,
    )


def _document_dependency_stage_verifier(
    request_path: Path, document: Path,
) -> dict[str, Any]:
    return document_verify_dependencies(
        request_path, document, hooks=_document_dependency_hooks()
    )


def _verification_stage_hooks() -> VerificationStageHooks:
    return VerificationStageHooks(
        validate_profile=validate_profile,
        primary_suffix=_primary_suffix,
        verify_openxml_artifact=openxml_verify_artifact,
        validate_delivery_request=validate_delivery_request,
        verify_document_semantic_correspondence=document_verify_semantics,
        verify_document_dependencies=_document_dependency_stage_verifier,
        inspect_pptx=presentation_inspect_pptx,
        verify_presentation_semantics=presentation_verify_semantics,
        verify_pdf=pdf_verify_structural,
        verify_pdf_conformance=pdf_verify_conformance,
        verify_html_conformance=web_verify_conformance,
        verify_web_local=web_verify_local,
    )


def execute_verify_stage(
    profile_path: Path,
    artifact: Path,
    output_dir: Path,
    request_path: Path | None = None,
) -> dict[str, Any]:
    return verification_execute_stage(
        profile_path,
        artifact,
        output_dir,
        request_path,
        hooks=_verification_stage_hooks(),
    )



def aggregate_vsa_gates(
    profile_path: Path,
    subject: Path,
    gate_paths: dict[str, Path],
    allow_local_unsigned: bool = False,
    bundles: dict[str, Path] | None = None,
    trust_policy_path: Path | None = None,
    signer_ids: dict[str, str] | None = None,
) -> dict[str, Any]:
    return trust_vsa.aggregate_vsa_gates(
        profile_path,
        subject,
        gate_paths,
        allow_local_unsigned=allow_local_unsigned,
        bundles=bundles,
        trust_policy_path=trust_policy_path,
        signer_ids=signer_ids,
        toolchain=_delivery_trust_toolchain_config(),
    )


def snapshot_materials(paths: Iterable[Path]) -> dict[str, Any]:
    materials = [file_fact(path) for path in paths]
    return {
        "capturedAt": utc_now(),
        "materials": materials,
        "note": "Operational immutable-input snapshot. Durable build provenance should be emitted as an in-toto Statement/SLSA Provenance predicate.",
    }


def _require_uri(value: str, field: str) -> str:
    parsed = urllib.parse.urlparse(value)
    if not parsed.scheme:
        raise RuntimeError(f"{field} must be a URI")
    return value




def presentation_gate(
    profile_path: Path, pptx: Path, pdf: Path | None, render_dir: Path | None,
    openxml_evidence: Path | None, target_evidence: Path | None,
    visual_evidence: Path | None, delivery_evidence: Iterable[Path], font_dir: Path,
) -> dict[str, Any]:
    return presentation_verification_gate(
        profile_path, pptx, pdf, render_dir, openxml_evidence, target_evidence,
        visual_evidence, delivery_evidence, font_dir,
        hooks=PresentationGateHooks(verify_pdf=pdf_verify_structural),
    )



def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def emit(value: Any, output: Path | None) -> None:
    if output is not None:
        write_json(output, value)
    print(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False))


def _parse_named_values(items: Iterable[str], option_name: str, path_values: bool = False) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for item in items:
        if "=" not in item:
            raise RuntimeError(f"{option_name} requires name=value")
        name, value = item.split("=", 1)
        if not name or not value or name in result:
            raise RuntimeError(f"duplicate/invalid {option_name} name: {name!r}")
        result[name] = Path(value) if path_values else value
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("validate-profile")
    p.add_argument("profile", type=Path)
    p.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    p.add_argument("--output", type=Path)

    p = sub.add_parser("validate-request")
    p.add_argument("request", type=Path)
    p.add_argument("--schema", type=Path, default=DEFAULT_REQUEST_SCHEMA)
    p.add_argument("--output", type=Path)

    p = sub.add_parser("compile-request")
    p.add_argument("request", type=Path)
    p.add_argument("--output", type=Path)

    p = sub.add_parser("build-request")
    p.add_argument("request", type=Path)
    p.add_argument("--output-directory", type=Path)
    p.add_argument("--output", type=Path)

    p = sub.add_parser("validate-presentation-source")
    p.add_argument("source", type=Path)
    p.add_argument("--schema", type=Path, default=DEFAULT_PRESENTATION_SOURCE_SCHEMA)
    p.add_argument("--output", type=Path)

    p = sub.add_parser("build-presentation-source")
    p.add_argument("--source", type=Path, required=True)
    p.add_argument("--profile", type=Path, required=True)
    p.add_argument("--pptx", type=Path, required=True)
    p.add_argument("--source-schema", type=Path, default=DEFAULT_PRESENTATION_SOURCE_SCHEMA)
    p.add_argument("--output", type=Path)

    p = sub.add_parser("project-opc-members")
    p.add_argument("--package", type=Path, required=True)
    p.add_argument("--manifest", type=Path, required=True)
    p.add_argument("--output-root", type=Path, required=True)
    p.add_argument("--output", type=Path)

    p = sub.add_parser("compose-reference-hybrid-source")
    p.add_argument("--semantic-source", type=Path, required=True)
    p.add_argument("--reference-map", type=Path, required=True)
    p.add_argument("--visual-root", type=Path, required=True)
    p.add_argument("--hybrid-source", type=Path, required=True)
    p.add_argument("--output", type=Path)

    p = sub.add_parser("verify-stage")
    p.add_argument("--profile", type=Path, required=True)
    p.add_argument("--artifact", type=Path, required=True)
    p.add_argument("--output-directory", type=Path, required=True)
    p.add_argument("--request", type=Path)
    p.add_argument("--output", type=Path)

    p = sub.add_parser("verify-vsa")
    p.add_argument("--statement", type=Path, required=True)
    p.add_argument("--subject", type=Path, required=True)
    p.add_argument("--profile", type=Path, required=True)
    p.add_argument("--allowed-verifier", action="append", default=[])
    p.add_argument("--output", type=Path)

    p = sub.add_parser("validate-vsa-trust-policy")
    p.add_argument("policy", type=Path)
    p.add_argument("--schema", type=Path, default=DEFAULT_VSA_TRUST_POLICY_SCHEMA)
    p.add_argument("--output", type=Path)

    p = sub.add_parser("verify-signed-vsa")
    p.add_argument("--statement", type=Path, required=True)
    p.add_argument("--bundle", type=Path, required=True)
    p.add_argument("--subject", type=Path, required=True)
    p.add_argument("--profile", type=Path, required=True)
    p.add_argument("--trust-policy", type=Path, required=True)
    p.add_argument("--signer-id", required=True)
    p.add_argument("--output", type=Path)

    p = sub.add_parser("aggregate-vsa-gates")
    p.add_argument("--profile", type=Path, required=True)
    p.add_argument("--subject", type=Path, required=True)
    p.add_argument("--gate", action="append", default=[], help="gateName=path/to/vsa.json")
    p.add_argument("--bundle", action="append", default=[], help="gateName=path/to/sigstore-bundle.json")
    p.add_argument("--signer", action="append", default=[], help="gateName=trusted-signer-id")
    p.add_argument("--trust-policy", type=Path)
    p.add_argument("--allow-local-unsigned", action="store_true")
    p.add_argument("--output", type=Path)

    p = sub.add_parser("inspect-pptx")
    p.add_argument("pptx", type=Path)
    p.add_argument("--placeholder", action="append", default=[])
    p.add_argument("--output", type=Path)

    p = sub.add_parser("verify-pdf")
    p.add_argument("pdf", type=Path)
    p.add_argument("--output", type=Path)

    p = sub.add_parser("verify-pdf-conformance")
    p.add_argument("pdf", type=Path)
    p.add_argument("--flavour", required=True, choices=("4", "4f", "4e", "ua1", "ua2", "wt1r", "wt1a"))
    p.add_argument("--output", type=Path)

    p = sub.add_parser("snapshot")
    p.add_argument("material", type=Path, nargs="+")
    p.add_argument("--output", type=Path, required=True)

    p = sub.add_parser("verify-readback")
    p.add_argument("source", type=Path)
    p.add_argument("readback", type=Path)
    p.add_argument("--destination", required=True)
    p.add_argument("--destination-reference", required=True)
    p.add_argument("--artifact-role", choices=("primary", "companion"), required=True)
    p.add_argument("--output", type=Path)

    p = sub.add_parser("attest-slsa")
    p.add_argument("--profile", type=Path, required=True)
    p.add_argument("--subject", type=Path, action="append", required=True)
    p.add_argument("--material", type=Path, action="append", default=[])
    p.add_argument("--builder-id", required=True)
    p.add_argument("--build-type", required=True)
    p.add_argument("--output", type=Path, required=True)

    p = sub.add_parser("gate-presentation")
    p.add_argument("--profile", type=Path, required=True)
    p.add_argument("--pptx", type=Path, required=True)
    p.add_argument("--pdf", type=Path)
    p.add_argument("--render-dir", type=Path)
    p.add_argument("--openxml-evidence", type=Path)
    p.add_argument("--target-evidence", type=Path)
    p.add_argument("--visual-evidence", type=Path)
    p.add_argument("--delivery-evidence", type=Path, action="append", default=[])
    p.add_argument("--font-dir", type=Path, default=DEFAULT_WINDOWS_FONTS)
    p.add_argument("--output", type=Path)

    args = parser.parse_args()
    try:
        if args.command == "validate-profile":
            value = validate_profile(args.profile, args.schema)
        elif args.command == "validate-request":
            value = validate_delivery_request(args.request, args.schema)
        elif args.command == "compile-request":
            value = compile_delivery_plan(args.request)
        elif args.command == "build-request":
            value = execute_build_stage(args.request, args.output_directory)
        elif args.command == "validate-presentation-source":
            value = validate_json_document(args.source, args.schema, "presentation-source")
        elif args.command == "build-presentation-source":
            value = build_presentation_source(args.source, args.profile, args.pptx, args.source_schema)
        elif args.command == "project-opc-members":
            value = project_opc_members(args.package, args.manifest, args.output_root)
        elif args.command == "compose-reference-hybrid-source":
            value = compose_reference_hybrid_source(
                args.semantic_source, args.reference_map, args.visual_root, args.hybrid_source
            )
        elif args.command == "verify-stage":
            value = execute_verify_stage(args.profile, args.artifact, args.output_directory, args.request)
        elif args.command == "verify-vsa":
            value = verify_verification_summary(args.statement, args.subject, args.profile, args.allowed_verifier)
        elif args.command == "validate-vsa-trust-policy":
            value = validate_vsa_trust_policy(args.policy, args.schema)
        elif args.command == "verify-signed-vsa":
            value = verify_signed_verification_summary(
                args.statement, args.bundle, args.subject, args.profile, args.trust_policy, args.signer_id
            )
        elif args.command == "aggregate-vsa-gates":
            gate_paths = _parse_named_values(args.gate, "--gate", path_values=True)
            bundle_paths = _parse_named_values(args.bundle, "--bundle", path_values=True)
            signer_ids = _parse_named_values(args.signer, "--signer")
            value = aggregate_vsa_gates(
                args.profile,
                args.subject,
                gate_paths,
                args.allow_local_unsigned,
                bundle_paths,
                args.trust_policy,
                signer_ids,
            )
        elif args.command == "inspect-pptx":
            value = inspect_pptx(args.pptx, args.placeholder)
        elif args.command == "verify-pdf":
            value = verify_pdf(args.pdf)
        elif args.command == "verify-pdf-conformance":
            value = verify_pdf_conformance(args.pdf, args.flavour)
        elif args.command == "snapshot":
            value = snapshot_materials(args.material)
        elif args.command == "verify-readback":
            value = verify_readback(
                args.source,
                args.readback,
                args.destination,
                args.destination_reference,
                args.artifact_role,
            )
        elif args.command == "attest-slsa":
            value = slsa_statement(args.subject, args.material, args.profile, args.builder_id, args.build_type)
        elif args.command == "gate-presentation":
            value = presentation_gate(
                args.profile,
                args.pptx,
                args.pdf,
                args.render_dir,
                args.openxml_evidence,
                args.target_evidence,
                args.visual_evidence,
                args.delivery_evidence,
                args.font_dir,
            )
        else:  # pragma: no cover
            raise AssertionError(args.command)
        emit(value, getattr(args, "output", None))
        status = value.get("status") if isinstance(value, dict) else None
        if args.command == "attest-slsa" or args.command == "snapshot":
            return 0
        return 0 if status == "PASS" else 1
    except Exception as error:
        print(json.dumps({"status": "ERROR", "error": str(error)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
