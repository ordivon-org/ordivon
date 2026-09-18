from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import posixpath
import re
from typing import Any, Iterable
import urllib.parse
import zipfile

from artifact_core.contracts import file_fact, sha256_file
from artifact_core.json_validation import validate_json_document

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PRESENTATION_SOURCE_SCHEMA = ROOT / "artifact-delivery/presentation-source-v1.schema.json"
DEFAULT_OPC_MEMBER_PROJECTION_SCHEMA = ROOT / "artifact-delivery/opc-member-projection-v1.schema.json"


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
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


def _safe_zip_names(names: Iterable[str]) -> list[str]:
    bad: list[str] = []
    for name in names:
        path = PurePosixPath(name)
        if path.is_absolute() or ".." in path.parts:
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


def project_opc_members(
    package_path: Path,
    manifest_path: Path,
    output_root: Path,
    *,
    schema_path: Path = DEFAULT_OPC_MEMBER_PROJECTION_SCHEMA,
) -> dict[str, Any]:
    validation = validate_json_document(
        manifest_path,
        schema_path,
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
            target.parent.mkdir(parents=True, exist_ok=True)
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
    *,
    schema_path: Path = DEFAULT_PRESENTATION_SOURCE_SCHEMA,
) -> dict[str, Any]:
    semantic_validation = validate_json_document(
        semantic_source_path,
        schema_path,
        "presentation-source",
    )
    reference_validation = validate_json_document(
        reference_map_path,
        schema_path,
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
        digest = _normalized_sha256(
            "sha256:" + str(legacy.get("sha256", "")),
            f"slides[{index-1}].legacySource.sha256",
        )
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
    _write_json(output_path, semantic)
    validation = validate_json_document(output_path, schema_path, "presentation-source")
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
