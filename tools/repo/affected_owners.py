#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from functools import lru_cache
import os
import subprocess
import tomllib
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Iterable

MANIFEST_PATH = Path(__file__).with_name("owners.toml")


@dataclass(frozen=True)
class Owner:
    name: str
    root: str
    task: str
    queue_task: str


def load_owners(path: Path = MANIFEST_PATH) -> tuple[Owner, ...]:
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    if data.get("schema_version") != 1:
        raise ValueError("owner manifest schema_version must be 1")
    if data.get("truth_role") != "repository-mechanics-only-not-domain-authority":
        raise ValueError("owner manifest truth_role must remain repository-mechanics-only")
    rows = data.get("owners")
    if not isinstance(rows, list) or not rows:
        raise ValueError("owner manifest must contain at least one [[owners]] row")

    owners: list[Owner] = []
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ValueError(f"owner row {index} must be a table")
        name = row.get("name")
        semantic_name = row.get("semantic_name", name)
        if not isinstance(semantic_name, str) or not semantic_name.strip() or semantic_name != semantic_name.strip():
            raise ValueError(f"owner row {index} semantic_name must be a canonical nonempty string")
        root = row.get("root")
        task = row.get("verify_task")
        queue_task = row.get("queue_verify_task", task)
        if not all(isinstance(value, str) and value.strip() for value in (name, root, task, queue_task)):
            raise ValueError(
                f"owner row {index} requires non-empty name/root/verify_task and optional queue_verify_task"
            )
        if root.startswith("/") or not root.endswith("/"):
            raise ValueError(f"owner {name}: root must be repository-relative and end with '/': {root}")
        normalized = _normalize(root).rstrip("/") + "/"
        if normalized != root:
            raise ValueError(f"owner {name}: root is not canonical: {root}")
        owners.append(Owner(name=name, root=root, task=task, queue_task=queue_task))

    names = [owner.name for owner in owners]
    roots = [owner.root for owner in owners]
    tasks = [owner.task for owner in owners]
    queue_tasks = [owner.queue_task for owner in owners]
    for label, values in (
        ("name", names),
        ("root", roots),
        ("verify_task", tasks),
        ("queue_verify_task", queue_tasks),
    ):
        if len(values) != len(set(values)):
            raise ValueError(f"owner manifest contains duplicate {label}")

    for i, left in enumerate(owners):
        for right in owners[i + 1 :]:
            if left.root.startswith(right.root) or right.root.startswith(left.root):
                raise ValueError(
                    f"owner roots must not overlap: {left.name}={left.root} {right.name}={right.root}"
                )
    return tuple(owners)



CROSS_CUTTING_PATHS = frozenset(
    {
        "mise.toml",
        ".github/workflows/ci.yml",
        "tools/repo/owners.toml",
        "tools/repo/affected_owners.py",
        "tools/repo/test_affected_owners.py",
        "tools/repo/convergence_plan.py",
        "tools/repo/test_convergence_plan.py",
        "tools/repo/check_github_governance.py",
        "tools/repo/dependency_contracts.toml",
        "tools/repo/check_owner_boundaries.py",
        "tools/repo/test_owner_boundaries.py",
    }
)


def _normalize(path: str) -> str:
    value = path.strip()
    if value.startswith("/") or ".." in value.split("/") or chr(92) in value:
        raise ValueError(f"noncanonical repository path: {path}")
    return PurePosixPath(value).as_posix()


@lru_cache(maxsize=1)
def _default_owners() -> tuple[Owner, ...]:
    return load_owners()


def __getattr__(name: str):
    # Preserve the existing public tuple while exact-cut classification stays
    # independent of mutable working-tree configuration, including on import.
    if name == "OWNERS":
        return _default_owners()
    raise AttributeError(name)


# Verification admission is strict for executable owners. Read-only owner
# discovery stays permissive so unknown paths remain inspectable.
EXECUTABLE_OWNER_ROOTS = (
    "apps/",
    "services/",
    "platform/",
    "capabilities/",
    "domains/",
    "packages/",
    "extensions/",
)


def require_registered_execution_paths(
    paths: Iterable[str], *, owners: tuple[Owner, ...] | None = None
) -> None:
    owners = _default_owners() if owners is None else owners
    unregistered = sorted({
        path for raw in paths
        if (path := _normalize(raw)).startswith(EXECUTABLE_OWNER_ROOTS)
        and not any(path.startswith(owner.root) for owner in owners)
    })
    if unregistered:
        raise ValueError(f"unregistered owner path: {', '.join(unregistered)}")


def owners_for_paths(
    paths: Iterable[str], *, owners: tuple[Owner, ...] | None = None
) -> tuple[Owner, ...]:
    owners = _default_owners() if owners is None else owners
    normalized = tuple(_normalize(path) for path in paths if path.strip())
    if any(path in CROSS_CUTTING_PATHS for path in normalized):
        return owners
    selected: list[Owner] = []
    for owner in owners:
        if any(path.startswith(owner.root) for path in normalized):
            selected.append(owner)
    return tuple(selected)


def changed_paths(base: str, head: str) -> tuple[str, ...]:
    # Preserve both sides of a cross-owner move, rather than allowing Git's
    # similarity detection to hide the source owner from verification.
    proc = subprocess.run(
        [
            "git", "diff", "--name-only", "--no-renames", "-z",
            "--diff-filter=ACDMRTUXB", f"{base}...{head}",
        ],
        check=True,
        stdout=subprocess.PIPE,
    )
    return tuple(os.fsdecode(path) for path in proc.stdout.split(b"\0") if path)



def project_source_classification(repo: Path, source_revision: str) -> dict:
    """Rebuild source navigation; never selects verification or qualifies a LEGO."""
    from collections import Counter
    from tempfile import TemporaryDirectory

    try:
        from tools.repo import source_history_legos as source
    except ModuleNotFoundError:
        import source_history_legos as source

    source._require_exact_git_oid(repo, source_revision)
    exact = source.git(repo, "--no-replace-objects", "rev-parse", "--verify",
                       source_revision + "^{commit}").strip()
    if exact != source_revision:
        raise ValueError("sourceRevision must identify the exact requested commit")
    tree = source.current_tree(repo, source_revision)
    manifest_path = "tools/repo/owners.toml"
    manifest_identity = tree.get(manifest_path, "")
    if not manifest_identity.startswith(("100644:blob:", "100755:blob:")):
        raise ValueError("owner manifest must be a regular source-cut file")
    text = source.git(repo, "--no-replace-objects", "show",
                      source_revision + ":" + manifest_path)
    data = tomllib.loads(text)
    with TemporaryDirectory(prefix="ordivon-source-classification-") as temp:
        path = Path(temp) / "owners.toml"
        path.write_text(text, encoding="utf-8", errors="surrogateescape")
        native_owners = load_owners(path)
    semantic_by_owner = {
        owner["name"]: owner.get("semantic_name", owner["name"])
        for owner in data["owners"]
    }
    regions = data.get("source_regions", [])
    if not isinstance(regions, list):
        raise ValueError("source regions must be an array")
    names = set()
    for region in regions:
        if not isinstance(region, dict) or set(region) - {"name", "description", "paths", "exclude"}:
            raise ValueError("source region fields are navigation-only")
        name = region.get("name")
        if not isinstance(name, str) or not name.strip() or name in names:
            raise ValueError("source region names must be nonempty and unique")
        names.add(name)
        description = region.get("description", name)
        if (not isinstance(description, str)
                or not description.strip() or description != description.strip()):
            raise ValueError("source region description must be a canonical nonempty string")
        if not isinstance(region.get("paths"), list) or not region["paths"]:
            raise ValueError("source region requires literal paths")
        if not isinstance(region.get("exclude", []), list):
            raise ValueError("source region exclusions must be literal paths")
        for rule in region["paths"] + region.get("exclude", []):
            if not isinstance(rule, str) or not rule:
                raise ValueError("source region requires nonempty literal paths")
            normalized = _normalize(rule).rstrip("/") + ("/" if rule.endswith("/") else "")
            if normalized != rule or rule in {".", "./", "/"}:
                raise ValueError("source region rule must be canonical and non-root")

    def matches(path: str, rule: str) -> bool:
        return path.startswith(rule) if rule.endswith("/") else path == rule

    # Source placement is nested under existing exact physical owner roots.
    # These structural roles never certify LEGO semantics or consumer contracts.
    source_section_roles = {
        # Project-specific path roles remain source/navigation hints only;
        # no role grants execution authority or an R2.1 LEGO identity.
        "authorities": "AUTHORITY_DECLARATION_SOURCE",
        "artifact-delivery": "ARTIFACT_DELIVERY_SOURCE",
        "knowledge": "KNOWLEDGE_RESOURCE_SOURCE",
        "consumers": "CONSUMER_PROFILE_SOURCE",
        "capabilities": "CAPABILITY_DESCRIPTION_SOURCE",
        "domains": "DOMAIN_PROFILE_SOURCE",
        "workstation": "WORKSTATION_SETUP_SOURCE",
        "labs": "EXPERIMENT_LAB_SOURCE",
        "artifact_capabilities": "ARTIFACT_CAPABILITY_SOURCE",
        "artifact_verifiers": "ARTIFACT_VALIDATOR_SOURCE",
        "artifact_core": "ARTIFACT_CORE_SOURCE",
        "artifact_operations": "ARTIFACT_OPERATION_SOURCE",
        "artifact_evidence": "EVIDENCE_SOURCE",
        "artifact_trust": "TRUST_CONTRACT_SOURCE",
        "artifact_verification": "VERIFICATION_SUPPORT_SOURCE",
        "media-v2": "VERSIONED_MEDIA_SOURCE",
        "acceptance": "ACCEPTANCE_EVIDENCE_SOURCE",
        "reference": "REFERENCE_MATERIAL_SOURCE",
        "creative-library": "CREATIVE_RESOURCE_LIBRARY_SOURCE",
        "play": "INTERACTION_SOURCE",
        "n8n": "WORKFLOW_INTEGRATION_SOURCE",
        "windows": "WINDOWS_PLATFORM_SOURCE",
        "examples": "EXAMPLE_SOURCE",
        "profiles": "PROFILE_SOURCE",
        "platform": "PLATFORM_INTEGRATION_SOURCE",
        "plugins": "PLUGIN_SOURCE",
        "infra": "INFRASTRUCTURE_SOURCE",
        "registry": "REGISTRY_NAMED_SOURCE",
        "grafana": "VISUALIZATION_TOOL_SOURCE",
        "tempo": "TRACE_STORAGE_SOURCE",
        "temporal": "WORKFLOW_ENGINE_SOURCE",
        "fuzz": "FUZZ_TEST_SOURCE",
        "threat-models": "THREAT_MODEL_SOURCE",
        "manifests": "DEPLOYMENT_MANIFEST_SOURCE",
        "containers": "CONTAINER_PACKAGING_SOURCE",
        "host": "HOST_INTEGRATION_SOURCE",
        ".github": "REPOSITORY_AUTOMATION_SOURCE",
        ".ordivon": "LOCAL_ORCHESTRATION_METADATA_SOURCE",
        ".config": "DEVELOPER_CONFIGURATION_SOURCE",
        ".clusterfuzzlite": "SECURITY_FUZZ_AUTOMATION_SOURCE",
        "src": "IMPLEMENTATION_SOURCE", "crates": "IMPLEMENTATION_SOURCE",
        "packages": "PACKAGE_SOURCE", "apps": "APPLICATION_SOURCE",
        "tests": "TEST_SOURCE", "test": "TEST_SOURCE",
        "formal": "FORMAL_SOURCE", "contracts": "CONTRACT_SOURCE",
        "schemas": "SCHEMA_SOURCE", "schema": "SCHEMA_SOURCE",
        "docs": "DOCUMENTATION_SOURCE", "planning": "PLANNING_SOURCE",
        "scripts": "SCRIPT_SOURCE", "evidence": "EVIDENCE_SOURCE",
        "fixtures": "FIXTURE_SOURCE", "config": "CONFIGURATION_SOURCE",
        "policies": "POLICY_SOURCE", "policy": "POLICY_SOURCE",
        "migrations": "MIGRATION_SOURCE", "history": "HISTORY_SOURCE",
        "research": "RESEARCH_SOURCE", "experiments": "EXPERIMENT_SOURCE",
        "experimental": "EXPERIMENT_SOURCE", "evals": "EVALUATION_SOURCE",
        "artifacts": "ARTIFACT_SOURCE", "productions": "PRODUCTION_SOURCE",
        "data-products": "DATA_PRODUCT_SOURCE", "data": "DATA_SOURCE",
        "systemd": "SERVICE_INSTALL_SOURCE",
        "ansible": "PROVISIONING_SOURCE", "tofu": "PROVISIONING_SOURCE",
        "postgresql": "PERSISTENCE_DEPLOYMENT_SOURCE",
        "observability": "OBSERVABILITY_SOURCE",
        "inventory": "INVENTORY_SOURCE",
        "providers": "PROVIDER_ADAPTER_SOURCE",
        "adapters": "ADAPTER_SOURCE",
        "standards": "STANDARD_SOURCE",
        "packaging": "DISTRIBUTION_PACKAGE_SOURCE",
        "tools": "TOOL_SOURCE",
        "(root-files)": "MIXED_ROOT_CARRIER_FORMS_NOT_ONE_RESPONSIBILITY",
    }
    # Narrow, evidence-grounded names, not inferred from "destroyer"/"wave".
    # Actual consumers:
    # domains/capital/docs/V2_DIRECT_MIGRATION_2026-09-13.md
    # domains/capital/tests/test_wave_b_contract.py
    source_section_overrides = {
        "capital/destroyer": "FALSIFICATION_CORPUS_SOURCE",
        "capital/wave_b": "FROZEN_HISTORICAL_REPLAY_FIXTURE_SOURCE",
    }
    # Stable, source-only file forms. These are descriptions of the *carrier*,
    # not function, consumer, correctness, or a move instruction. Exact
    # basename precedence avoids labeling every JSON as a schema/contract.
    exact_file_forms = {
        "README.md": "PROJECT_README",
        "AGENTS.md": "AGENT_INSTRUCTIONS",
        "CONTRIBUTING.md": "CONTRIBUTOR_GUIDE",
        "SECURITY.md": "SECURITY_POLICY_DOCUMENT",
        "SKILL.md": "AGENT_SKILL_INSTRUCTION_SOURCE",
        "CHANGELOG.md": "RELEASE_CHANGELOG",
        "LICENSE": "LICENSE_NOTICE",
        "LICENSE.md": "LICENSE_NOTICE",
        "MIGRATION_PROVENANCE.md": "MIGRATION_PROVENANCE_RECORD",
        "pyproject.toml": "PYTHON_PACKAGE_MANIFEST",
        "uv.lock": "PYTHON_DEPENDENCY_LOCK",
        ".python-version": "PYTHON_TOOLCHAIN_VERSION",
        "Cargo.toml": "RUST_PACKAGE_MANIFEST",
        "Cargo.lock": "RUST_DEPENDENCY_LOCK",
        "rust-toolchain.toml": "RUST_TOOLCHAIN_VERSION",
        "deny.toml": "RUST_DEPENDENCY_POLICY",
        "package.json": "NODE_PACKAGE_MANIFEST",
        "pnpm-lock.yaml": "NODE_DEPENDENCY_LOCK",
        "pnpm-workspace.yaml": "NODE_WORKSPACE_MANIFEST",
        "tsconfig.json": "TYPESCRIPT_COMPILER_CONFIGURATION",
        ".node-version": "NODE_TOOLCHAIN_VERSION",
        "mise.toml": "TASK_TOOLCHAIN_CONFIGURATION",
        "Taskfile.yml": "TASK_AUTOMATION_CONFIGURATION",
        ".gitignore": "GIT_IGNORE_RULES",
        ".gitattributes": "GIT_ATTRIBUTE_RULES",
        ".editorconfig": "EDITOR_FORMAT_CONFIGURATION",
        ".gitleaksignore": "SECRET_SCANNER_EXCLUSIONS",
        ".gitleaks.toml": "SECRET_SCANNER_CONFIGURATION",
        ".env.example": "ENVIRONMENT_CONFIGURATION_EXAMPLE",
        "alembic.ini": "DATABASE_MIGRATION_CONFIGURATION",
        "mcp.json": "MCP_PLUGIN_CONFIGURATION",
        "mcp-surface.json": "MCP_SURFACE_DECLARATION",
        "plugin.json": "PLUGIN_PACKAGE_MANIFEST",
        "composition-v1.json": "DISTRIBUTION_COMPOSITION_DECLARATION",
        "external-lock.json": "EXTERNAL_RESOURCE_LOCK",
        "SOURCE_BOUNDARY.json": "SOURCE_BOUNDARY_DECLARATION",
        "CODEOWNERS": "GIT_CHANGE_REVIEW_ROUTING",
        "Dockerfile": "CONTAINER_BUILD_RECIPE",
        ".gitkeep": "GIT_DIRECTORY_PLACEHOLDER",
        "tofurc": "OPENTOFU_CLI_CONFIGURATION",
        "py.typed": "PYTHON_TYPED_PACKAGE_MARKER",
        "requirements-tooling.lock.txt": "TOOLING_DEPENDENCY_LOCK",
        "requirements-tooling.txt": "TOOLING_DEPENDENCY_MANIFEST",
    }

    known_suffix_forms = {
        ".service": "SYSTEMD_SERVICE_UNIT",
        ".target": "SYSTEMD_TARGET_UNIT",
        ".timer": "SYSTEMD_TIMER_UNIT",
        ".container": "QUADLET_CONTAINER_UNIT",
        ".commit-map": "GIT_COMMIT_MAPPING_RECORD",
        ".conf": "SERVICE_CONFIGURATION_FILE",
        ".xml": "XML_DOCUMENT_SOURCE",
        ".xmi": "XML_MODEL_INTERCHANGE_SOURCE",
        ".mdx": "MARKDOWN_COMPONENT_CONTENT",
        ".html": "HTML_DOCUMENT_SOURCE",
        ".css": "CSS_STYLESHEET_SOURCE",
        ".jsonld": "LINKED_DATA_JSONLD_SOURCE",
        ".jsonl": "JSON_LINES_RECORD_SOURCE",
        ".geojson": "GEOSPATIAL_GEOJSON_SOURCE",
        ".csv": "TABULAR_CSV_DATA_SOURCE",
        ".tf": "TERRAFORM_CONFIGURATION_SOURCE",
        ".nix": "NIX_BUILD_SOURCE",
        ".hcl": "HCL_CONFIGURATION_SOURCE",
        ".cs": "CSHARP_SOURCE_FILE",
        ".csproj": "DOTNET_PROJECT_MANIFEST",
        ".cpp": "CPP_SOURCE_FILE",
        ".gd": "GODOT_SCRIPT_SOURCE",
        ".godot": "GODOT_PROJECT_CONFIGURATION",
        ".tscn": "GODOT_SCENE_RESOURCE",
        ".tres": "GODOT_RESOURCE",
        ".png": "PNG_IMAGE_ASSET",
        ".svg": "SVG_VECTOR_ASSET",
        ".webp": "WEBP_IMAGE_ASSET",
        ".jpg": "JPEG_IMAGE_ASSET",
        ".jpeg": "JPEG_IMAGE_ASSET",
        ".wav": "WAVE_AUDIO_ASSET",
        ".flac": "FLAC_AUDIO_ASSET",
        ".ogg": "OGG_AUDIO_ASSET",
        ".mkv": "MATROSKA_VIDEO_ASSET",
        ".mp4": "MP4_VIDEO_ASSET",
        ".blend": "BLENDER_PROJECT_ASSET",
        ".glb": "GLB_3D_ASSET",
        ".gpkg": "GEOPACKAGE_DATA_ASSET",
        ".step": "CAD_STEP_ASSET",
        ".otio": "OPENTIMELINEIO_TIMELINE_ASSET",
        ".vtt": "WEBVTT_TIMED_TEXT",
        ".srt": "SUBRIP_TIMED_TEXT",
        ".ttml": "TTML_TIMED_TEXT",
        ".pdf": "PDF_DOCUMENT_ASSET",
        ".typ": "TYPST_SOURCE_FILE",
        ".sha256": "SHA256_DIGEST_RECORD",
        ".sha": "SHA_DIGEST_RECORD",
        ".pub": "PUBLIC_KEY_MATERIAL",
        ".pod": "POD_SPECIFICATION_SOURCE",
        ".qnt": "QUINT_FORMAL_MODEL",
        ".dfy": "DAFNY_FORMAL_SOURCE",
        ".jsonc": "JSON_WITH_COMMENTS_CONFIGURATION",
        ".j2": "JINJA_TEMPLATE",
        ".mako": "MAKO_TEMPLATE",
        ".patch": "PATCH_FILE_SOURCE",
        ".env": "ENVIRONMENT_CONFIGURATION_FILE",
        ".example": "EXAMPLE_CONFIGURATION",
        ".carrier": "OPAQUE_CARRIER_FILE",
        ".sdoc": "STRUCTURED_DOCUMENT_CARRIER",
        ".typed": "TYPING_MARKER_FILE",
    }

    def source_file_form(path: str, source_identity: str) -> str:
        name = path.rsplit("/", 1)[-1]
        if name in exact_file_forms:
            return exact_file_forms[name]
        if name.endswith(".schema.json"):
            return "JSON_SCHEMA_SOURCE"
        for suffix, form in known_suffix_forms.items():
            if name.endswith(suffix):
                return form
        if "." not in name or name.startswith(".") and name.count(".") == 1:
            if source_identity.startswith("100755:blob:"):
                return "EXECUTABLE_ENTRYPOINT_FILE"
            return "EXTENSIONLESS_OPAQUE_SOURCE"
        if name.endswith((".tla", ".cfg", ".lean", ".smt2", ".als")):
            return "FORMAL_MODEL_OR_CONFIGURATION_SOURCE"
        if name.endswith(".md"):
            return "MARKDOWN_CONTENT_SOURCE"
        if name.endswith(".json"):
            return "JSON_STRUCTURED_DATA_SOURCE"
        if name.endswith((".toml", ".ini")):
            return "STRUCTURED_CONFIGURATION_SOURCE"
        if name.endswith((".yaml", ".yml")):
            return "YAML_CONFIGURATION_OR_DATA_SOURCE"
        if name.endswith(".py"):
            return "PYTHON_SOURCE_FILE"
        if name.endswith(".rs"):
            return "RUST_SOURCE_FILE"
        if name.endswith((".ts", ".tsx")):
            return "TYPESCRIPT_SOURCE_FILE"
        if name.endswith((".js", ".mjs")):
            return "JAVASCRIPT_SOURCE_FILE"
        if name.endswith((".sh", ".bash", ".ps1", ".bat", ".cmd")):
            return "COMMAND_SCRIPT_SOURCE"
        if name.endswith((".sql", ".rego")):
            return "QUERY_OR_POLICY_SOURCE"
        if name.endswith((".lock", ".lock.json")):
            return "VERSION_LOCK_SOURCE"
        if name.endswith(".txt"):
            return "PLAIN_TEXT_SOURCE"
        return "UNQUALIFIED_FILE_FORM"

    # Qualify nested lexical source territory names, independently of owner
    # authority and independently of semantic LEGO composition. No recursive
    # rescan of physical files: Git remains the only source tree.
    named_cells = {
        "next/authorities/observations": "RECORDED_OBSERVATIONS_SOURCE",
        "next/authorities/records": "AUTHORITY_RECORDS_SOURCE",
        "next/knowledge/lessons": "KNOWLEDGE_LESSONS_SOURCE",
        "next/knowledge/graphs": "KNOWLEDGE_GRAPH_SOURCE",
        "next/domains/game": "GAME_DOMAIN_SOURCE",
        "runtime/crates/ordivon-runtime-core": "RUNTIME_CORE_CRATE_SOURCE",
        "artifact/artifact-delivery/shadow-contracts": "ARTIFACT_SHADOW_CONTRACT_SOURCE",
        "harness/src/ordivon_harness": "HARNESS_IMPLEMENTATION_PACKAGE_SOURCE",
        "capital/src/ordivon_capital": "CAPITAL_IMPLEMENTATION_PACKAGE_SOURCE",
        "security/labs/agent-admission-rs": "SECURITY_EXPERIMENT_CRATE_SOURCE",
        "workstation/providers/cloudflare": "CLOUDFLARE_PROVIDER_CONFIGURATION_SOURCE",
        "capital/wave_b/fixtures": "HISTORICAL_PORTFOLIO_TEST_FIXTURE_SOURCE",
        "media/research/expression": "MEDIA_EXPRESSION_RESEARCH_SOURCE",
        "next/evidence/acceptance": "NEXT_ACCEPTANCE_EVIDENCE_SOURCE",
        "runtime/research/foundations": "RUNTIME_FOUNDATIONAL_RESEARCH_SOURCE",
        "media/productions/archive-archipelago-001": "MEDIA_ARCHIVE_ARCHIPELAGO_PRODUCTION",
        "harness/evidence/system1-decision": "HARNESS_DECISION_EVIDENCE_SOURCE",
        "next/migrations/records": "NEXT_HISTORICAL_MIGRATION_RECORDS",
        "runtime/research/programme": "RUNTIME_RESEARCH_PROGRAMME_SOURCE",
        "next/evidence/data-lifecycle": "NEXT_DATA_LIFECYCLE_EVIDENCE_SOURCE",
        "next/capabilities/providers": "NEXT_PROVIDER_CAPABILITY_DESCRIPTIONS",
        "media/productions/live-relay-001": "MEDIA_LIVE_RELAY_PRODUCTION",
        "preservation/artifacts/creative-preservation": "CREATIVE_PRESERVATION_ARTIFACTS",
        "artifact/artifact-delivery/shadow-v2": "ARTIFACT_SHADOW_V2_SOURCE",
        "media/research/media": "MEDIA_RESEARCH_CONTENT_SOURCE",
        "runtime/scripts/tests": "RUNTIME_SCRIPT_TEST_SOURCE",
        "media/productions/runtime-introduction": "MEDIA_RUNTIME_INTRODUCTION_PRODUCTION",
        "media/src/ordivon_studio": "MEDIA_STUDIO_IMPLEMENTATION_SOURCE",
        "next/evidence/browser-security": "BROWSER_SECURITY_EVIDENCE_SOURCE",
        "artifact/artifact-delivery/shadow-bindings": "ARTIFACT_SHADOW_BINDING_SOURCE",
        "artifact/artifact-delivery/shadow-profiles": "ARTIFACT_SHADOW_PROFILE_SOURCE",
        "network/consumers/finance": "FINANCE_NETWORK_CONSUMER_CONTRACTS",
        "runtime/crates/ordivon-runtime-mcp": "RUNTIME_MCP_CRATE_SOURCE",
        "media/productions/ordivon-book-v0": "MEDIA_BOOK_PRODUCTION_SOURCE",
        "workstation/workstation/providers": "WORKSTATION_PROVIDER_SOURCE",
        "capital/evidence/acceptance": "CAPITAL_ACCEPTANCE_EVIDENCE_SOURCE",
        "artifact/artifact-delivery/examples": "ARTIFACT_DELIVERY_EXAMPLES",
        "artifact/artifact-delivery/golden": "ARTIFACT_GOLDEN_FIXTURE_SOURCE",
        "harness/evals/fresh_agent_ab": "FRESH_AGENT_EVALUATION_SOURCE",
        "media/apps/motion-remotion": "REMOTION_MEDIA_APPLICATION",
        "media/research/equipment": "MEDIA_EQUIPMENT_RESEARCH_SOURCE",
        "capital/tools/legacy_replay": "CAPITAL_LEGACY_REPLAY_TOOLS",
        "next/capabilities/packages": "NEXT_PACKAGE_CAPABILITY_DECLARATIONS",
        "network/consumers/browserless": "BROWSERLESS_NETWORK_CONSUMER_CONTRACTS",
        "gateway/src/ordivon_gateway": "GATEWAY_IMPLEMENTATION_PACKAGE_SOURCE",
        "composition/src/ordivon_composition": "COMPOSITION_IMPLEMENTATION_PACKAGE_SOURCE",
        "host/src/ordivon_host_v2": "HOST_V2_IMPLEMENTATION_PACKAGE_SOURCE",
        "artifact/artifact-delivery/consumer-acceptance": "ARTIFACT_DELIVERY_CONSUMER_ACCEPTANCE_SOURCE",
        "artifact/artifact_capabilities/publication": "ARTIFACT_PUBLICATION_CAPABILITY_SOURCE",
        "artifact/artifact_verifiers/document": "ARTIFACT_DOCUMENT_VERIFIER_SOURCE",
        "artifact/artifact_verifiers/pdf": "ARTIFACT_PDF_VERIFIER_SOURCE",
        "artifact/artifact_verifiers/presentation": "ARTIFACT_PRESENTATION_VERIFIER_SOURCE",
        "artifact/artifact_verifiers/web": "ARTIFACT_WEB_VERIFIER_SOURCE",
        "capital/tools/nautilus_rc4": "CAPITAL_NAUTILUS_RC4_TOOL_SOURCES",
        "capital/tools/tigerbeetle_0_17_9": "CAPITAL_TIGERBEETLE_PINNED_TOOL_SOURCE",
        "game/test/fixtures": "GAME_NATIVE_TEST_FIXTURE_SOURCE",
        "gateway/packaging/windows": "GATEWAY_WINDOWS_PACKAGING_SOURCE",
        "gateway/planning/external-pull-worker-r3": "GATEWAY_EXTERNAL_PULL_PLANNING_SOURCE",
        "harness/evals/harness-edit-addressing-002": "HARNESS_ADDRESS_EDIT_EVALUATION_SOURCE",
        "harness/evals/harness-edit-multiregion-003": "HARNESS_MULTI_REGION_EDIT_EVALUATION_SOURCE",
        "harness/evals/harness-repository-repair-001": "HARNESS_REPOSITORY_REPAIR_EVALUATION_SOURCE",
        "harness/research/experiments": "HARNESS_EXPERIMENT_RESEARCH_SOURCE",
        "host/migrations/versions": "HOST_DATABASE_MIGRATION_VERSIONS_SOURCE",
        "media/apps/preview": "MEDIA_PREVIEW_APPLICATION_SOURCE",
        "media/artifacts/creative-library": "MEDIA_CREATIVE_LIBRARY_ARTIFACT_SOURCE",
        "media/media-v2/tests": "MEDIA_V2_TEST_SOURCE",
        "media/play/media-ecology-20260830": "MEDIA_ECOLOGY_INTERACTION_SOURCE",
        "media/productions/convergence-object-001": "MEDIA_CONVERGENCE_OBJECT_PRODUCTION_SOURCE",
        "media/productions/convergence-sonic-ident": "MEDIA_CONVERGENCE_AUDIO_IDENT_SOURCE",
        "media/productions/fishing-fable-lego-study-r1": "MEDIA_FISHING_FABLE_LEGO_STUDY_SOURCE",
        "media/productions/friction-loop-field-zine": "MEDIA_FRICTION_LOOP_ZINE_PRODUCTION_SOURCE",
        "media/productions/mhs-hardware-boundary": "MEDIA_HARDWARE_BOUNDARY_PRODUCTION_SOURCE",
        "media/productions/ordivon-system-constellation-atlas": "MEDIA_SYSTEM_ATLAS_PRODUCTION_SOURCE",
        "network/consumers/chat-ingress": "NETWORK_CHAT_INGRESS_CONSUMER_PROFILE_SOURCE",
        "network/consumers/claude": "NETWORK_CLAUDE_CONSUMER_PROFILE_SOURCE",
        "network/consumers/supply-chain": "NETWORK_SUPPLY_CHAIN_CONSUMER_PROFILE_SOURCE",
        "network/consumers/x-reality": "NETWORK_X_API_TRANSPORT_CONSUMER_SOURCE",
        "network/history/rounds": "NETWORK_HISTORICAL_ROUND_SOURCE",
        "network/providers/surfshark": "NETWORK_SURFSHARK_PROVIDER_PROFILE_SOURCE",
        "next/data-products/experimental-episode-corpus-r1": "NEXT_EPISODE_CORPUS_DATA_PRODUCT_SOURCE",
        "next/evidence/agent-campaigns": "NEXT_AGENT_CAMPAIGN_EVIDENCE_SOURCE",
        "next/evidence/analysis": "NEXT_ANALYSIS_EVIDENCE_SOURCE",
        "next/experimental/episode-store-r1": "NEXT_EPISODE_STORE_EXPERIMENT_SOURCE",
        "next/experiments/autonomous-interest-r5": "NEXT_AUTONOMOUS_INTEREST_R5_EXPERIMENT_SOURCE",
        "next/experiments/autonomous-interest-r6": "NEXT_AUTONOMOUS_INTEREST_R6_EXPERIMENT_SOURCE",
        "next/experiments/autonomous-interest-r7": "NEXT_AUTONOMOUS_INTEREST_R7_EXPERIMENT_SOURCE",
        "next/experiments/chaoxing-autosign-mvp": "NEXT_CHAOXING_SIGNIN_EXPERIMENT_SOURCE",
        "runtime/packaging/systemd": "RUNTIME_SYSTEMD_PACKAGING_SOURCE",
        "runtime/research/authority": "RUNTIME_AUTHORITY_RESEARCH_SOURCE",
        "runtime/research/core": "RUNTIME_CORE_RESEARCH_SOURCE",
        "security/contracts/agent-request-verifier-v1": "SECURITY_AGENT_REQUEST_CONTRACT_SOURCE",
        "security/fixtures/browser-security": "SECURITY_BROWSER_TEST_FIXTURE_SOURCE",
        "security/src/ordivon_security_v2": "SECURITY_V2_IMPLEMENTATION_SOURCE",
        "skills/src/ordivon_skills": "SKILLS_CATALOG_BINDING_IMPLEMENTATION_SOURCE",
        "workstation/inventory/queries": "WORKSTATION_OSQUERY_INVENTORY_QUERY_SOURCE",
        "workstation/tofu/agent-birth-handoff": "WORKSTATION_AGENT_PROVISIONING_HANDOFF_SOURCE",
        "workstation/workstation/nix": "WORKSTATION_NIX_CONFIGURATION_SOURCE",
        "workstation/workstation/windows": "WORKSTATION_WINDOWS_INTEGRATION_SOURCE",
        # Additional grounded source-only fallbacks/roles from PR #989.
        # Peer-specific exact roles above take precedence.
        "media/productions/*": "AUTHORED_MEDIA_PRODUCTION_INSTANCE_SOURCE",
        "next/experiments/*": "NEXT_EXPERIMENT_INSTANCE_SOURCE",
        "network/consumers/*": "NETWORK_CONSUMER_REQUIREMENT_SOURCE",
        "network/acceptance/*": "NETWORK_SCOPED_ACCEPTANCE_SOURCE",
        "harness/evals/*": "HARNESS_EVALUATION_FIXTURE_SOURCE",
        "capital/tools/*": "CAPITAL_EXTERNAL_TOOL_INTEGRATION_SOURCE",
        "artifact/artifact_verifiers/*": "ARTIFACT_FORMAT_VERIFIER_SOURCE",
        "security/tests/fixtures": "SECURITY_TEST_FIXTURE_SOURCE",
        "artifact/artifact_capabilities/presentation": "ARTIFACT_PRESENTATION_CAPABILITY_SOURCE",
        "network/reference/linux": "NETWORK_LINUX_REFERENCE_SOURCE",
        "runtime/packaging/windows": "RUNTIME_WINDOWS_SERVICE_PACKAGE_SOURCE",
        "skills/plugins/ordivon-skills-bridge": "SKILLS_MCP_CLIENT_PLUGIN_CONFIGURATION_SOURCE",
        "gateway/systemd/ordivon-gateway.service.d": "GATEWAY_SYSTEMD_DROPIN_TEMPLATE_SOURCE",
        "media/media-v2/bin": "MEDIA_V2_LAUNCHER_SOURCE",
        # Additional path-grounded second-level source-form locations; no LEGO qualification.
        "artifact/artifact-delivery/node": "ARTIFACT_NODE_TOOLCHAIN_BINDING_SOURCE",
        "artifact/planning/prototypes": "ARTIFACT_PROTOTYPE_PLANNING_SOURCE",
        "media/media-v2/profiles": "MEDIA_V2_PROFILE_SOURCE",
        "capital/contracts/legacy_protocol_v1": "CAPITAL_HISTORICAL_PROTOCOL_CONTRACT_SOURCE",
        "capital/data-products/crypto-public-shadow-r2": "CAPITAL_CRYPTO_SHADOW_DATA_PRODUCT_SOURCE",
        "capital/fixtures/r5_legacy_bounded": "CAPITAL_LEGACY_BOUNDED_FIXTURE_SOURCE",
        "next/evidence/data-products": "NEXT_DATA_PRODUCT_EVIDENCE_SOURCE",
        "next/policies/research-adopted-r1": "NEXT_RESEARCH_POLICY_REFERENCE_SOURCE",
        "network/history/evidence": "NETWORK_HISTORICAL_EVIDENCE_SOURCE",
        "harness/fixtures/harness-replacement-repository-repair-v1": "HARNESS_REPOSITORY_REPAIR_FIXTURE_SOURCE",
        "runtime/examples/runtime-demo": "RUNTIME_DEMONSTRATION_EXAMPLE_SOURCE",
        "runtime/research/engineering": "RUNTIME_ENGINEERING_RESEARCH_SOURCE",
        "artifact/artifact-delivery/donor-r1": "ARTIFACT_DONOR_MANIFEST_AND_WITNESS_SOURCE",
        "artifact/artifact-delivery/python-uv": "ARTIFACT_PYTHON_UV_TOOLCHAIN_SOURCE",
        "artifact/artifact_operations/providers": "ARTIFACT_OPERATION_PROVIDER_MODULE_SOURCE",
        "media/creative-library/web": "MEDIA_CREATIVE_LIBRARY_WEB_INTERFACE_SOURCE",
        "media/docs/resolve-compatibility": "MEDIA_RESOLVE_COMPATIBILITY_EVIDENCE_SOURCE",
        "media/packages/identity": "MEDIA_IDENTITY_TOKEN_PACKAGE_SOURCE",
        "media/packages/visuals": "MEDIA_VISUAL_COMPONENT_PACKAGE_SOURCE",
        "capital/evidence/data-products": "CAPITAL_DATA_PRODUCT_CONSUMPTION_EVIDENCE_SOURCE",
        "harness/.github/ISSUE_TEMPLATE": "HARNESS_GITHUB_ISSUE_TEMPLATE_SOURCE",
        "harness/.github/workflows": "HARNESS_GITHUB_WORKFLOW_SOURCE",
        "harness/evidence/browser-security": "HARNESS_BROWSER_SECURITY_OBSERVATION_SOURCE",
        "harness/fixtures/harness-edit-addressing-repeated-v1": "HARNESS_REPEATED_EDIT_ADDRESSING_FIXTURE_SOURCE",
        "harness/fixtures/harness-edit-multiregion-v1": "HARNESS_MULTIREGION_EDIT_FIXTURE_SOURCE",
        "harness/research/fixtures": "HARNESS_RESEARCH_TEST_FIXTURE_SOURCE",
        "runtime/.github/ISSUE_TEMPLATE": "RUNTIME_GITHUB_ISSUE_TEMPLATE_SOURCE",
        "runtime/.github/workflows": "RUNTIME_GITHUB_WORKFLOW_SOURCE",
        "runtime/platform/windows": "RUNTIME_WINDOWS_JOB_BRIDGE_SOURCE",
        "skills/tests/fixtures": "SKILLS_PLUGIN_SCHEMA_TEST_FIXTURES",
        "workstation/contracts/asyncapi": "WORKSTATION_ASYNCAPI_CONTRACT_SOURCE",
        "workstation/systemd/service-profiles": "WORKSTATION_SYSTEMD_PROFILE_SOURCE",
        "artifact/artifact-delivery/openxml-nix": "ARTIFACT_OPENXML_NIX_TOOLCHAIN_SOURCE",
        "artifact/artifact-delivery/openxml-validator": "ARTIFACT_OPENXML_VALIDATOR_SOURCE",
        "artifact/tests/fixtures": "ARTIFACT_TEST_FIXTURE_SOURCE",
        "harness/docs/superpowers": "HARNESS_HISTORICAL_IMPLEMENTATION_PLAN_SOURCE",
        "next/docs/superpowers": "NEXT_HISTORICAL_AGENT_METHOD_PLAN_SOURCE",
        "harness/research/authority": "HARNESS_RESEARCH_AUTHORITY_RECORD_SOURCE",
        "harness/src/anc_canonical": "HARNESS_CANONICALIZATION_PYTHON_MODULE_SOURCE",
        "harness/tests/fixtures": "HARNESS_BOUNDARY_TEST_FIXTURE_SOURCE",
        "host/packaging/systemd": "HOST_SYSTEMD_SERVICE_PACKAGE_SOURCE",
        "media/.github/workflows": "MEDIA_GITHUB_WORKFLOW_SOURCE",
        "media/media-v2/migrations": "MEDIA_V2_HISTORICAL_MIGRATION_SOURCE",
        "network/.github/workflows": "NETWORK_GITHUB_WORKFLOW_SOURCE",
        "network/capabilities/wireguard": "NETWORK_WIREGUARD_REFERENCE_SOURCE",
        "next/evidence/experimental-episode": "NEXT_EXPERIMENTAL_EPISODE_EVIDENCE_SOURCE",
        "security/contracts/agent-admission-v1": "SECURITY_AGENT_ADMISSION_CONTRACT_SOURCE",
        "security/contracts/gateway-capability-authz-v1": "SECURITY_GATEWAY_AUTHORIZATION_CONTRACT_SOURCE",
        "security/fixtures/clean": "SECURITY_CLEAN_TEST_FIXTURE_SOURCE",
        "security/fixtures/smoke": "SECURITY_SMOKE_TEST_FIXTURE_SOURCE",
        "security/providers/packer": "SECURITY_PACKER_PROVIDER_CONFIGURATION_SOURCE",
        "workstation/n8n/workflows": "WORKSTATION_N8N_WORKFLOW_SOURCE",
        "workstation/observability/gatus": "WORKSTATION_GATUS_OBSERVABILITY_SOURCE",
        "artifact/.github/workflows": "ARTIFACT_GITHUB_WORKFLOW_SOURCE",
        "artifact/artifact-delivery/policy": "ARTIFACT_DELIVERY_REGO_POLICY_SOURCE",
        "artifact/artifact-delivery/verification": "ARTIFACT_DELIVERY_JSON_SCHEMA_SOURCE",
        "artifact/config/zot": "ARTIFACT_ZOT_LOCAL_REGISTRY_CONFIGURATION_SOURCE",
        "capital/.github/workflows": "CAPITAL_GITHUB_WORKFLOW_SOURCE",
        "capital/data/derived": "CAPITAL_DERIVED_DATA_DIRECTORY_PLACEHOLDER",
        "capital/data/raw": "CAPITAL_RAW_DATA_DIRECTORY_PLACEHOLDER",
        "capital/infra/systemd": "CAPITAL_SYSTEMD_CLOCK_SYNC_DECLARATION",
        "capital/schema/legacy_protocol_v1": "CAPITAL_HISTORICAL_PROTOCOL_SCHEMA_SOURCE",
        "distribution/.github/workflows": "DISTRIBUTION_GITHUB_WORKFLOW_SOURCE",
        "distribution/tests/fixtures": "DISTRIBUTION_PROVIDER_OPENAPI_TEST_FIXTURE",
        "harness/schemas/agent-automation": "HARNESS_AGENT_AUTOMATION_JSON_SCHEMA_SOURCE",
        "host/.github/workflows": "HOST_GITHUB_WORKFLOW_SOURCE",
        "media/artifacts/creative-archive": "MEDIA_CREATIVE_ARCHIVE_HISTORICAL_RECORD_SOURCE",
        "network/capabilities/failover": "NETWORK_FAILOVER_ACCEPTANCE_SCRIPT_SOURCE",
        "network/config/blackbox": "NETWORK_BLACKBOX_EXPORTER_CONFIGURATION_SOURCE",
        "network/config/prometheus": "NETWORK_PROMETHEUS_CONFIGURATION_SOURCE",
        "network/config/sing-box": "NETWORK_SING_BOX_CONFIGURATION_SOURCE",
        "network/config/sysctl": "NETWORK_SYSCTL_CONFIGURATION_SOURCE",
        "network/config/toxiproxy": "NETWORK_TOXIPROXY_CONFIGURATION_SOURCE",
        "next/.github/workflows": "NEXT_GITHUB_WORKFLOW_SOURCE",
        "next/authorities/generated": "NEXT_GENERATED_AUTHORITY_INDEX_SOURCE",
        "next/capabilities/artifact": "NEXT_ARTIFACT_CAPABILITY_DESCRIPTION_SOURCE",
        "next/capabilities/profiles": "NEXT_CAPABILITY_PROFILE_DECLARATION_SOURCE",
        "runtime/docs/evidence": "RUNTIME_HISTORICAL_VERIFICATION_RECORD_SOURCE",
        "runtime/docs/reference": "RUNTIME_TOOL_REFERENCE_DOCUMENT_SOURCE",
        "runtime/docs/superpowers": "RUNTIME_HISTORICAL_DEVELOPMENT_PLAN_SOURCE",
        "security/fixtures/agent-admission": "SECURITY_AGENT_ADMISSION_TEST_FIXTURE_SOURCE",
        "security/profiles/migration": "SECURITY_HISTORICAL_GITLEAKS_MIGRATION_PROFILE_SOURCE",
        "security/profiles/product": "SECURITY_GITLEAKS_PRODUCT_CONFIGURATION_SOURCE",
        "security/profiles/zap": "SECURITY_LOCAL_ZAP_PROFILE_SOURCE",
        "workstation/.github/workflows": "WORKSTATION_GITHUB_WORKFLOW_SOURCE",
        "workstation/contracts/cloudevents": "WORKSTATION_CLOUDEVENTS_SCHEMA_SOURCE",
        "workstation/contracts/outbox": "WORKSTATION_POSTGRES_OUTBOX_EXAMPLE_SOURCE",
        "workstation/inventory/snapshots": "WORKSTATION_HISTORICAL_INVENTORY_SNAPSHOT_SOURCE",
    }

    # Agent-facing interface FORM is a source navigation facet, not an
    # authority, public SDK guarantee, installed service, or a LEGO identity.
    # Declare it in the existing exact-cut classifier; no second registry.
    source_interface_rules = {
        "AGENT_PLUGIN_MANIFEST": (
            "extensions/ordivon-control-plane/plugin.json",
            "platform/skills/plugins/ordivon-skills-bridge/plugin.json",
        ),
        "MCP_CONNECTION_CONFIG": (
            "extensions/ordivon-control-plane/mcp.json",
            "platform/skills/plugins/ordivon-skills-bridge/mcp.json",
        ),
        "SOURCE_SKILL_METHOD": (
            ".agents/skills/recursive-lego-calculus/SKILL.md",
        ),
        "MCP_SERVER_ADAPTER": (
            "services/gateway/src/ordivon_gateway/mcp_server.py",
            "services/host/src/ordivon_host_v2/mcp_server.py",
            "services/host/src/ordivon_host_v2/social_work_mcp.py",
            "services/runtime/crates/ordivon-runtime-mcp/src/server/",
            "platform/skills/scripts/skills_mcp.py",
        ),
        "MCP_CLIENT_ADAPTER": (
            "services/harness/src/ordivon_harness/mcp_http_client.py",
        ),
        "PUBLIC_MCP_SURFACE_MANIFEST": (
            "services/gateway/mcp-surface.json",
            "services/host/mcp-surface.json",
        ),
        "HTTP_API_SERVER_ADAPTER": (
            "services/gateway/src/ordivon_gateway/worker_http.py",
            "apps/web/src/server.ts",
        ),
        "CAPABILITY_ROUTE_ADAPTER": (
            "services/gateway/src/ordivon_gateway/routes.py",
            "services/gateway/src/ordivon_gateway/upstream.py",
        ),
        "CLI_ENTRY_SOURCE": (
            "services/harness/src/ordivon_harness/cli.py",
            "services/harness/src/ordivon_harness/independent_cli.py",
            "services/runtime/crates/ordivon-runtime-core/src/bin/ordivon-runtime-doctor.rs",
            "services/runtime/crates/ordivon-runtime-core/src/bin/ordivon-runtime-inspect.rs",
        ),
        "INTERNAL_RUNNER_ENTRY_SOURCE": (
            "services/runtime/crates/ordivon-runtime-core/src/bin/ordivon-runtime-runner.rs",
        ),
        "AGENT_PLUGIN_ADAPTER": (
            "services/harness/src/ordivon_harness/agent_plugin.py",
            "services/harness/src/ordivon_harness/plugin_mcp.py",
        ),
        "TOOL_PROGRAM_SOURCE": (
            "services/harness/src/ordivon_harness/tool_program.py",
        ),
        "PACKAGE_PUBLIC_API_SOURCE": (
            "services/harness/src/ordivon_harness/api.py",
        ),
        "SOURCE_SKILL_CATALOG": (
            "platform/skills/src/ordivon_skills/catalog.py",
            "platform/skills/src/ordivon_skills/scanner.py",
            "platform/skills/src/ordivon_skills/parser.py",
        ),
    }
    all_interface_rules = [
        (rule, form) for form, rules in source_interface_rules.items()
        for rule in rules
    ]
    if len(all_interface_rules) != len(set(rule for rule, _ in all_interface_rules)):
        raise ValueError("source interface rules must have unique physical path selectors")

    def source_interface_form(path: str) -> str | None:
        # Never assign running server semantics to conformance fixtures,
        # regardless of their residence in a server implementation folder.
        if path.startswith(
            "services/runtime/crates/ordivon-runtime-mcp/src/server/tests/"
        ) or path == "services/runtime/crates/ordivon-runtime-mcp/src/server/tests.rs":
            return None
        forms = {
            form for rule, form in all_interface_rules
            if matches(path, rule)
        }
        if len(forms) > 1:
            raise ValueError(f"ambiguous source-only interface classification: {path}")
        return next(iter(forms)) if forms else None

    root_by_owner = {o.name: o.root for o in native_owners}
    entries = []
    for path, identity in sorted(tree.items()):
        # Git path bytes are identity. Do not strip/normalize filenames here.
        owner = next((o.name for o in native_owners if path.startswith(o.root)), None)
        matched = []
        if owner is None:
            matched = [
                region["name"] for region in regions
                if any(matches(path, rule) for rule in region["paths"])
                and not any(matches(path, rule) for rule in region.get("exclude", []))
            ]
        standing = ("REGISTERED_OWNER_SOURCE" if owner is not None else
                    "DECLARED_SOURCE_REGION" if len(matched) == 1 else
                    "AMBIGUOUS" if matched else "UNASSIGNED")
        region_label = next(
            (r.get("description", r["name"]) for r in regions if len(matched) == 1
             and r["name"] == matched[0]), None
        )
        section = None
        section_role = None
        source_cell = None
        source_cell_role = None
        if owner is not None:
            tail = path[len(root_by_owner[owner]):]
            parts = tail.split("/")
            section_key = parts[0] if len(parts) > 1 else "(root-files)"
            section = f"{owner}/{section_key}"
            section_role = source_section_overrides.get(
                section,
                source_section_roles.get(section_key, "UNQUALIFIED_SECTION"),
            )
            if len(parts) > 2:
                source_cell = f"{section}/{parts[1]}"
                source_cell_role = named_cells.get(
                    source_cell,
                    named_cells.get(f"{section}/*", "UNQUALIFIED_NESTED_CELL"),
                )
            elif len(parts) == 2:
                source_cell = f"{section}/(direct-files)"
                source_cell_role = "DIRECT_SECTION_FILES"
            else:
                source_cell = section
                source_cell_role = "ROOT_MANIFEST_AND_ENTRYPOINT_FILES"
        file_form = source_file_form(path, identity)
        interface_form = source_interface_form(path)
        file_form_standing = (
            "GIT_EXECUTABLE_MODE_OBSERVED"
            if file_form == "EXECUTABLE_ENTRYPOINT_FILE"
            else "OPAQUE_FORM_NEEDS_CONTENT_EVIDENCE"
            if file_form in {
                "UNQUALIFIED_FILE_FORM", "EXTENSIONLESS_OPAQUE_SOURCE",
                "OPAQUE_CARRIER_FILE", "STRUCTURED_DOCUMENT_CARRIER",
            }
            else "FILENAME_OR_EXTENSION_ONLY_NOT_CONTENT_PROVEN"
        )
        # Display label is navigational: transform existing lexical names;
        # never substitute it for a responsibility, consumer, or alias identity.
        source_cell_display = (
            " / ".join(
                [semantic_by_owner.get(owner, owner)]
                + [
                    segment.replace("_", " ").replace("-", " ")
                    for segment in source_cell.split("/")[1:]
                ]
            )
            if owner is not None and source_cell is not None else None
        )
        entries.append({
            "sourceCell": source_cell,
            "sourceCellDisplayName": source_cell_display,
            "sourceCellRole": source_cell_role,
            "sourceFileForm": file_form,
            "sourceFileFormStanding": file_form_standing,
            "sourceInterfaceForm": interface_form,
            "sourceInterfaceStanding": (
                "SOURCE_ONLY_NOT_INSTALLED_OR_CAPABILITY_ADMITTED"
                if interface_form is not None else "UNQUALIFIED_AS_PUBLIC_INTERFACE"
            ),
            "sourceSection": section,
            "sourceSectionRole": section_role,
            "semanticName": semantic_by_owner.get(owner, owner) if owner is not None
                            else region_label,
            "classificationLayer": "REPOSITORY_VERIFICATION_REGION" if owner
                                   else "SOURCE_NAVIGATION_ONLY",
            "path": path, "sourceIdentity": identity, "verificationOwner": owner,
            "sourceRegion": matched[0] if len(matched) == 1 else None,
            "classificationStanding": standing,
            "matchedRules": ["owners:" + owner] if owner is not None else
                            ["source_regions:" + name for name in matched],
        })
    counts = Counter(row["classificationStanding"] for row in entries)
    return {
        "kind": "ordivon.repository-source-classification",
        "truthRole": "SOURCE_NAVIGATION_NOT_OWNER_OR_LEGO_QUALIFICATION",
        "sourceRevision": source_revision,
        "sourceTree": source.git(repo, "--no-replace-objects", "rev-parse",
                                 source_revision + "^{tree}").strip(),
        "ownerManifestIdentity": manifest_identity,
        "classifierSourceIdentity": tree.get("tools/repo/affected_owners.py"),
        "proofReuseAdmissible": False,
        "summary": {
            "distinctOwnerCells": len({
                row["sourceCell"] for row in entries
                if row["sourceCell"] is not None
            }),
            "namedNestedCells": len({
                row["sourceCell"] for row in entries
                if row["sourceCellRole"] in named_cells.values()
            }),
            "opaqueFileFormPaths": sum(
                row["sourceFileFormStanding"] == "OPAQUE_FORM_NEEDS_CONTENT_EVIDENCE"
                for row in entries
            ),
            "gitExecutableFormPaths": sum(
                row["sourceFileFormStanding"] == "GIT_EXECUTABLE_MODE_OBSERVED"
                for row in entries
            ),
            "unqualifiedSourceFileForms": sum(
                row["sourceFileForm"] == "UNQUALIFIED_FILE_FORM"
                for row in entries
            ),
            "distinctOwnerSections": len({
                row["sourceSection"] for row in entries
                if row["sourceSection"] is not None
            }),
            "mixedRootCarrierPaths": sum(
                row["sourceSectionRole"] == "MIXED_ROOT_CARRIER_FORMS_NOT_ONE_RESPONSIBILITY"
                for row in entries
            ),
            "unqualifiedOwnerSectionPaths": sum(
                row["sourceSectionRole"] == "UNQUALIFIED_SECTION"
                for row in entries
            ),
            "trackedPaths": len(entries),
            "registeredOwnerPaths": counts["REGISTERED_OWNER_SOURCE"],
            "declaredRegionPaths": counts["DECLARED_SOURCE_REGION"],
            "unassigned": counts["UNASSIGNED"], "ambiguous": counts["AMBIGUOUS"],
        },
        "entries": entries,
    }


def project_source_classification_delta(
    repo: Path, before_revision: str, after_revision: str,
) -> dict:
    """Exact Git-source navigation delta, including unedited reclassified paths.

    In particular, owner/source-region policy changes can affect unchanged
    file identities. The result is neither consumer impact nor proof reuse.
    """
    before = project_source_classification(repo, before_revision)
    after = project_source_classification(repo, after_revision)
    # This process uses ONE implementation of the projector for both cuts.
    # If the projector itself changed, a same-code comparison cannot prove
    # which historical classifications differed; expose that lost knowledge.
    classifier_changed = before["classifierSourceIdentity"] != after["classifierSourceIdentity"]
    older = {item["path"]: item for item in before["entries"]}
    newer = {item["path"]: item for item in after["entries"]}
    changes = []
    for path in sorted(older.keys() | newer.keys()):
        previous, current = older.get(path), newer.get(path)
        if previous == current:
            continue
        source_changed = (
            previous is None or current is None
            or previous["sourceIdentity"] != current["sourceIdentity"]
        )
        classification_changed = (
            previous is None or current is None
            or any(previous[name] != current[name] for name in (
                "verificationOwner", "sourceRegion", "classificationStanding",
                "matchedRules", "semanticName", "sourceSection",
                "sourceSectionRole", "sourceCell", "sourceCellRole",
                "sourceCellDisplayName", "sourceFileForm", "sourceFileFormStanding",
                "sourceInterfaceForm", "sourceInterfaceStanding",
                "classificationLayer",
            ))
        )
        changes.append({
            "path": path, "before": previous, "after": current,
            "sourceChanged": source_changed,
            "classificationChanged": classification_changed,
        })
    return {
        "kind": "ordivon.repository-source-classification-delta",
        "truthRole": "SOURCE_NAVIGATION_NOT_CONSUMER_IMPACT_OR_PROOF_REUSE",
        "beforeRevision": before_revision,
        "afterRevision": after_revision,
        "beforeTree": before["sourceTree"],
        "afterTree": after["sourceTree"],
        "beforeOwnerManifestIdentity": before["ownerManifestIdentity"],
        "afterOwnerManifestIdentity": after["ownerManifestIdentity"],
        "beforeClassifierSourceIdentity": before["classifierSourceIdentity"],
        "afterClassifierSourceIdentity": after["classifierSourceIdentity"],
        "classifierSourceChanged": classifier_changed,
        "requiresWholeClassificationReprojection": classifier_changed,
        "deltaCompleteness": (
            "UNKNOWN_SOURCE_CLASSIFIER_IMPLEMENTATION_CHANGED"
            if classifier_changed else
            "SAME_CLASSIFIER_VERSION_OBSERVED_SOURCE_DELTA_ONLY"
        ),
        "proofReuseAdmissible": False,
        "summary": {
            "previousPaths": before["summary"]["trackedPaths"],
            "currentPaths": after["summary"]["trackedPaths"],
            "changedEntries": len(changes),
            "classificationOnlyChanges": sum(
                item["classificationChanged"] and not item["sourceChanged"]
                for item in changes
            ),
            "unchangedEntries": len(older.keys() & newer.keys()) - sum(
                item["before"] is not None and item["after"] is not None
                for item in changes
            ),
            "unassigned": after["summary"]["unassigned"],
            "ambiguous": after["summary"]["ambiguous"],
        },
        "changes": changes,
    }

def project_source_classification_gaps(classification: dict) -> dict:
    """Compress real SOURCE-only unknowns for Agent-native classification work.

    Total Git path membership does not prove content role qualification. Keep
    every unqualified carrier visible without a second truth registry or any
    physical renames. Source plan/manifest claims are not actual consumers.
    """
    grouped: dict[tuple[str, str], dict] = {}
    reasons = (
        ("UNASSIGNED_OR_AMBIGUOUS_PATH", "classificationStanding",
         {"UNASSIGNED", "AMBIGUOUS"}, "path"),
        ("UNQUALIFIED_SECTION", "sourceSectionRole",
         {"UNQUALIFIED_SECTION"}, "sourceSection"),
        ("MIXED_ROOT_CARRIERS", "sourceSectionRole",
         {"MIXED_ROOT_CARRIER_FORMS_NOT_ONE_RESPONSIBILITY"}, "sourceSection"),
        ("UNQUALIFIED_NESTED_CELL", "sourceCellRole",
         {"UNQUALIFIED_NESTED_CELL"}, "sourceCell"),
        ("OPAQUE_FILE_FORM", "sourceFileFormStanding",
         {"OPAQUE_FORM_NEEDS_CONTENT_EVIDENCE"}, "sourceCell"),
    )
    for entry in classification["entries"]:
        for reason, prop, values, grouping in reasons:
            if entry[prop] not in values:
                continue
            locator = entry[grouping] or entry["path"]
            key = (reason, locator)
            slot = grouped.setdefault(key, {
                "gapKind": reason,
                "sourceLocator": locator,
                "pathCount": 0,
                "sampleGitPaths": [],
                "standing": "UNKNOWN_SOURCE_CLASSIFICATION_NOT_LEGO_OR_CONSUMER",
            })
            slot["pathCount"] += 1
            if len(slot["sampleGitPaths"]) < 3:
                slot["sampleGitPaths"].append(entry["path"])
    groups = sorted(grouped.values(),
                    key=lambda g: (g["gapKind"], -g["pathCount"], g["sourceLocator"]))
    by_kind = {}
    for reason, _, _, _ in reasons:
        entries = [r for r in groups if r["gapKind"] == reason]
        by_kind[reason] = {
            "groups": len(entries),
            "paths": sum(row["pathCount"] for row in entries),
        }
    return {
        "kind": "ordivon.repository-source-classification-gap-projection",
        "sourceRevision": classification["sourceRevision"],
        "sourceTree": classification["sourceTree"],
        "ownerManifestIdentity": classification["ownerManifestIdentity"],
        "classifierSourceIdentity": classification["classifierSourceIdentity"],
        "truthRole": "SOURCE_NAVIGATION_GAPS_NOT_SEMANTIC_LEGO_PROOF_OR_INSTALLATION",
        "pathClassification": {
            "trackedPaths": classification["summary"]["trackedPaths"],
            "unassigned": classification["summary"]["unassigned"],
            "ambiguous": classification["summary"]["ambiguous"],
        },
        "gapSummary": by_kind,
        "groups": groups,
        "proofReuseAdmissible": False,
        "semanticCompletion": "UNKNOWN",
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Select monorepo owners affected by an exact Git range."
    )
    parser.add_argument("--classify-source-revision", help="exact-cut source navigation; does not select verification")
    parser.add_argument("--classification-gaps", action="store_true", help="compact unqualified source sections/cells, mixed roots and opaque file forms")
    parser.add_argument("--classify-source-delta-base", help="compare exact Git source identity and source-region membership; no consumer/proof-reuse inference")
    parser.add_argument("--source-path", action="append", default=[], help="restrict exact-cut source navigation output to canonical paths")
    parser.add_argument("--base")
    parser.add_argument("--head")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--changed-file", action="append", default=[])
    parser.add_argument(
        "--format",
        choices=("json", "names", "tasks", "queue-tasks"),
        default="json",
    )
    return parser


def main() -> int:
    args = _parser().parse_args()
    if args.classify_source_revision:
        if args.all or args.base or args.head or args.changed_file or args.format != "json":
            raise SystemExit("source classification cannot be combined with verification selection")
        if args.classify_source_delta_base:
            if args.classification_gaps:
                raise SystemExit("classification gaps require one exact source revision")
            if args.source_path:
                raise SystemExit("source delta must include all reclassified paths")
            result = project_source_classification_delta(
                Path.cwd(), args.classify_source_delta_base, args.classify_source_revision
            )
        else:
            result = project_source_classification(Path.cwd(), args.classify_source_revision)
            if args.classification_gaps:
                if args.source_path:
                    raise SystemExit("classification gap inventory requires full Git tree")
                result = project_source_classification_gaps(result)
            if args.source_path:
                # Use the independently verified exact-Git query contract from
                # peer candidate ccd7395; do not create a competing selector.
                paths = sorted(set(args.source_path))
                for path in paths:
                    if not path or path != _normalize(path) or path.startswith("/"):
                        raise SystemExit("source query requires exact canonical Git path")
                index = {entry["path"]: entry for entry in result["entries"]}
                result["entries"] = [index[path] for path in paths if path in index]
                result["query"] = {
                    "mode": "EXACT_SOURCE_PATHS_ONLY",
                    "requested": paths,
                    "absentFromSourceCut": [path for path in paths if path not in index],
                    "queryScope": "SOURCE_PATH_PRESENCE_NOT_CONSUMER_PROOF_OR_CI_SELECTION",
                }
        print(json.dumps(result, sort_keys=True))
        return 0
    if args.classify_source_delta_base or args.source_path or args.classification_gaps:
        raise SystemExit("source query requires --classify-source-revision")
    if args.all:
        selected = _default_owners()
        paths: tuple[str, ...] = ()
    else:
        if args.changed_file:
            paths = tuple(args.changed_file)
        else:
            if not args.base or not args.head:
                raise SystemExit("--base and --head are required unless --all or --changed-file is used")
            paths = changed_paths(args.base, args.head)
        require_registered_execution_paths(paths)
        selected = owners_for_paths(paths)

    if args.format == "names":
        for owner in selected:
            print(owner.name)
    elif args.format == "tasks":
        for owner in selected:
            print(owner.task)
    elif args.format == "queue-tasks":
        for owner in selected:
            print(owner.queue_task)
    else:
        print(
            json.dumps(
                {
                    "changedPaths": list(paths),
                    "owners": [
                        {
                            "name": owner.name,
                            "root": owner.root,
                            "task": owner.task,
                            "queueTask": owner.queue_task,
                        }
                        for owner in selected
                    ],
                },
                sort_keys=True,
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
