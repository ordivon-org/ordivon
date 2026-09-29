from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from artifact_capabilities.dispatch import execute_build_adapter
from artifact_capabilities.presentation import (
    PresentationBuildHooks,
    admit_presentation_source,
    admit_semantic_svg_source,
    build_presentation_source,
    build_semantic_svg_presentation_source,
    canonicalize_generated_ooxml_metadata,
    normalize_zip_member_timestamps,
)
from artifact_core.admission import AdmissionHooks, admit_delivery_request
from artifact_core.build_bindings import BuildCapabilityBindingRegistry
from artifact_core.build_planning import compile_delivery_plan_from_validation
from artifact_core.contracts import file_fact, sha256_file
from artifact_core.json_validation import validate_json_document
from artifact_core.profile_v1 import validate_profile_v1
from artifact_verification import VerificationStageHooks, execute_verify_stage
from artifact_verifiers.document import (
    DocumentDependencyHooks,
    verify_document_dependencies,
    verify_document_semantic_correspondence,
)
from artifact_verifiers.document import toolchain as document_toolchain
from artifact_verifiers.openxml import verify_openxml_artifact
from artifact_verifiers.pdf import verify_pdf, verify_pdf_conformance
from artifact_verifiers.presentation import (
    inspect_pptx,
    verify_presentation_semantics,
)
from artifact_verifiers.web import verify_html_conformance, verify_web_local

from .build import BuildOperationHandler
from .common import OperationHandler, PreparedOperation
from .package import PackageOperationHandler
from .preparation import PrepareOperationHandler
from .trust import TrustOperationHandler, validate_trust_material
from .verification import VerifyOperationHandler

ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_ROOT = ROOT / "artifact-delivery"
DEFAULT_PROFILE_SCHEMA = ARTIFACT_ROOT / "profile-v1.schema.json"
DEFAULT_REQUEST_SCHEMA = ARTIFACT_ROOT / "request-v1.schema.json"
DEFAULT_PRESENTATION_SOURCE_SCHEMA = (
    ARTIFACT_ROOT / "presentation-source-v1.schema.json"
)
DEFAULT_PRESENTATION_SEMANTIC_SVG_SOURCE_SCHEMA = (
    ARTIFACT_ROOT / "presentation-semantic-svg-source-v1.schema.json"
)
BUILD_BINDING_REGISTRY = BuildCapabilityBindingRegistry(ARTIFACT_ROOT)

_PRIMARY_SUFFIXES = {
    "pptx": ".pptx",
    "docx": ".docx",
    "xlsx": ".xlsx",
    "html": ".html",
    "pdf": ".pdf",
    "pdf-a-4": ".pdf",
    "pdf-ua-2": ".pdf",
}


def _primary_suffix(profile: dict[str, Any]) -> str:
    fmt = str(profile.get("primaryOutput", {}).get("format", ""))
    suffix = _PRIMARY_SUFFIXES.get(fmt)
    if suffix is None:
        raise RuntimeError(f"unsupported primary output format: {fmt}")
    return suffix


def _request_output_name(request_id: str, suffix: str) -> str:
    stem = re.sub(r"[^A-Za-z0-9._-]+", "-", request_id).strip("-._") or "artifact"
    return stem + suffix


def _resolve_request_path(request_path: Path, relative: str) -> Path:
    candidate = Path(relative)
    if candidate.is_absolute():
        return candidate.resolve()
    return (request_path.resolve().parent / candidate).resolve()


class DirectPythonOperationProvider:
    """Direct composition of Artifact Python owners behind ArtifactOperation.

    This is the default local provider. It does not know Temporal and does not invoke
    the historical Delivery CLI. External tools remain owned by their capability,
    verifier, trust, and OCI provider modules.
    """

    def __init__(self) -> None:
        self.build_registry = BUILD_BINDING_REGISTRY
        self.pandoc = document_toolchain.selected_external_file(
            "ARTIFACT_PANDOC",
            document_toolchain.GLOBAL_PANDOC,
        )
        self.operation_handlers: dict[str, OperationHandler] = {
            "prepare": PrepareOperationHandler(self.compile_delivery_plan),
            "build": BuildOperationHandler(self.execute_build_stage),
            "verify": VerifyOperationHandler(
                ARTIFACT_ROOT,
                production_verify=self.execute_verify_stage,
            ),
            "verify-trust": TrustOperationHandler(),
            "package": PackageOperationHandler(),
        }

    def _admit_presentation_source(
        self, source_path: Path
    ) -> tuple[dict[str, Any] | None, list[dict[str, Any]], list[str]]:
        return admit_presentation_source(
            source_path,
            validate_json_document=validate_json_document,
            source_schema_path=DEFAULT_PRESENTATION_SOURCE_SCHEMA,
        )

    def _admit_semantic_svg_source(
        self, source_path: Path
    ) -> tuple[dict[str, Any] | None, list[dict[str, Any]], list[str]]:
        return admit_semantic_svg_source(
            source_path,
            validate_json_document=validate_json_document,
            source_schema_path=DEFAULT_PRESENTATION_SEMANTIC_SVG_SOURCE_SCHEMA,
        )

    def validate_delivery_request(
        self,
        request_path: Path,
        request_schema_path: Path = DEFAULT_REQUEST_SCHEMA,
        profile_schema_path: Path = DEFAULT_PROFILE_SCHEMA,
    ) -> dict[str, Any]:
        return admit_delivery_request(
            request_path,
            request_schema_path=request_schema_path,
            profile_schema_path=profile_schema_path,
            hooks=AdmissionHooks(
                validate_json_document=validate_json_document,
                validate_profile=validate_profile_v1,
                source_validators={
                    "presentation-source-v1": self._admit_presentation_source,
                    "presentation-semantic-svg-source-v1": self._admit_semantic_svg_source,
                },
                file_fact=file_fact,
                sha256_file=sha256_file,
            ),
        )

    def compile_delivery_plan(self, request_path: Path) -> dict[str, Any]:
        validation = self.validate_delivery_request(request_path)
        return compile_delivery_plan_from_validation(
            request_path,
            validation,
            registry=self.build_registry,
            sha256_file=sha256_file,
        )

    def _presentation_build_hooks(self) -> PresentationBuildHooks:
        return PresentationBuildHooks(
            validate_json_document=validate_json_document,
            inspect_pptx=inspect_pptx,
            verify_semantics=verify_presentation_semantics,
            normalize_python_pptx=normalize_zip_member_timestamps,
            canonicalize_ppt_master=canonicalize_generated_ooxml_metadata,
        )

    def build_presentation_source(
        self, source_path: Path, profile_path: Path, output_path: Path
    ) -> dict[str, Any]:
        return build_presentation_source(
            source_path,
            profile_path,
            output_path,
            DEFAULT_PRESENTATION_SOURCE_SCHEMA,
            hooks=self._presentation_build_hooks(),
        )

    def build_semantic_svg_presentation_source(
        self, source_path: Path, profile_path: Path, output_path: Path
    ) -> dict[str, Any]:
        return build_semantic_svg_presentation_source(
            source_path,
            profile_path,
            output_path,
            DEFAULT_PRESENTATION_SEMANTIC_SVG_SOURCE_SCHEMA,
            hooks=self._presentation_build_hooks(),
        )

    def execute_build_stage(
        self, request_path: Path, output_directory: Path | None = None
    ) -> dict[str, Any]:
        plan = self.compile_delivery_plan(request_path)
        if plan.get("status") != "PASS":
            return {
                "schemaVersion": 1,
                "kind": "artifact-delivery-build-stage",
                "status": "FAIL",
                "plan": plan,
                "failures": ["derived delivery plan did not PASS"],
            }

        validation = self.validate_delivery_request(request_path)
        request = validation["request"]
        profile = validation["profileValidation"]["profile"]
        source_path = Path(validation["resolved"]["source"]["path"])
        profile_path = Path(validation["resolved"]["profile"]["path"])
        if output_directory is None:
            output_directory = _resolve_request_path(
                request_path, str(request["outputDirectory"])
            )
        output_directory.mkdir(parents=True, exist_ok=True)
        output_path = output_directory / _request_output_name(
            str(request["requestId"]), _primary_suffix(profile)
        )
        adapter = plan["buildAdapter"]
        adapter_result = execute_build_adapter(
            adapter,
            source_path=source_path,
            profile_path=profile_path,
            output_path=output_path,
            presentation_builders={
                "python-pptx-presentation-source-v1": self.build_presentation_source,
                "ppt-master-semantic-svg-v1": self.build_semantic_svg_presentation_source,
            },
            pandoc=self.pandoc,
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
            "boundary": (
                "Build-stage PASS means exact request/profile/source bytes produced "
                "the primary artifact through the selected adapter. Independent "
                "verification, target rendering, packaging, provenance and release "
                "gates are not implied."
            ),
        }

    def _document_dependency_hooks(self) -> DocumentDependencyHooks:
        return DocumentDependencyHooks(
            validate_delivery_request=self.validate_delivery_request,
            compile_delivery_plan=self.compile_delivery_plan,
        )

    def _document_dependency_stage_verifier(
        self, request_path: Path, document: Path
    ) -> dict[str, Any]:
        return verify_document_dependencies(
            request_path,
            document,
            hooks=self._document_dependency_hooks(),
        )

    def verify_document_dependencies(
        self,
        request_path: Path,
        document: Path,
        pandoc: Path | None = None,
        pandoc_archive: Path | None = None,
        toolchain_lock: Path | None = None,
        openxml_validator: Path | None = None,
    ) -> dict[str, Any]:
        return verify_document_dependencies(
            request_path,
            document,
            pandoc,
            pandoc_archive,
            toolchain_lock,
            openxml_validator,
            hooks=self._document_dependency_hooks(),
        )

    def _verification_stage_hooks(self) -> VerificationStageHooks:
        return VerificationStageHooks(
            validate_profile=validate_profile_v1,
            primary_suffix=_primary_suffix,
            verify_openxml_artifact=verify_openxml_artifact,
            validate_delivery_request=self.validate_delivery_request,
            verify_document_semantic_correspondence=verify_document_semantic_correspondence,
            verify_document_dependencies=self._document_dependency_stage_verifier,
            inspect_pptx=inspect_pptx,
            verify_presentation_semantics=verify_presentation_semantics,
            verify_pdf=verify_pdf,
            verify_pdf_conformance=verify_pdf_conformance,
            verify_html_conformance=verify_html_conformance,
            verify_web_local=verify_web_local,
        )

    def execute_verify_stage(
        self,
        profile_path: Path,
        artifact: Path,
        output_dir: Path,
        request_path: Path | None = None,
    ) -> dict[str, Any]:
        return execute_verify_stage(
            profile_path,
            artifact,
            output_dir,
            request_path,
            hooks=self._verification_stage_hooks(),
        )

    @staticmethod
    def validate_trust_material(value: dict[str, Any]) -> dict[str, Any]:
        """Compatibility facade; trust-material authority lives in trust.py."""
        return validate_trust_material(value)

    def _operation_handler(self, operation_kind: str) -> OperationHandler:
        try:
            return self.operation_handlers[operation_kind]
        except KeyError as error:
            raise RuntimeError(
                f"unsupported Artifact operation kind: {operation_kind}"
            ) from error

    def prepare_operation(self, operation: dict[str, Any]) -> PreparedOperation:
        return self._operation_handler(operation["operationKind"]).prepare(operation)

    def produce(
        self,
        operation_kind: str,
        context: dict[str, Any],
        output_directory: Path,
    ) -> tuple[dict[str, str], dict[str, Any]]:
        return self._operation_handler(operation_kind).produce(context, output_directory)
